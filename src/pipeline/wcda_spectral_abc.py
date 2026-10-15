#!/usr/bin/env python3
"""Prepare/collect an isolated 8-day WCDA spectral-index sensitivity experiment.

Run on IHEP with --repo pointing at its WCDA production checkout. A is the
unchanged release; B and C use the archived full-interval PL index and +/-1
local statistical error. The full-interval fit uses the official aggregate
response, not a simultaneous variable-normalization fit to the 8-day bins.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import sys

import yaml


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def variants(gamma, error):
    if not (math.isfinite(gamma) and math.isfinite(error) and error > 0
            and 1 < gamma - error < gamma + error < 4):
        raise ValueError('Invalid or boundary-limited spectral reference')
    return {'B': gamma, 'C_minus': gamma - error, 'C_plus': gamma + error}


def dump_csv(path, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def prepare(repo, work):
    baseline = repo / 'JOBs_official_lc_20260817_8day'
    reference = repo / 'JOBs_official_qpo_spectral_fits_dge_policy_r5/fits'
    if work.exists():
        raise FileExistsError(f'Refusing to replace existing experiment: {work}')
    rows = list(csv.DictReader((baseline / 'fit_jobs.csv').open()))
    rows = [r for r in rows if r['source'] in ('Mkn421', 'Mkn501')]
    assert len(rows) == 400
    spectra = {}
    for source in ('Mkn421', 'Mkn501'):
        ref = reference / source.lower()
        par = yaml.safe_load((ref / 'out/ParRes.yaml').read_text())
        statuses = re.findall(r'STATUS\s*:\s*(\w+)', (ref / 'fit.log').read_text())
        assert statuses and statuses[-1] == 'OK'
        assert par['DGE']['Active'] == 0
        sed = par['SRC']['Src0']['SEDModel']
        assert sed['type'] == 'PL' and par['SRC']['Src0']['Epiv'] == 3
        gamma, error = float(sed['alpha'][0]), float(sed['alpha'][-1])
        spectra[source] = {'gamma': gamma, 'error': error, 'variants': variants(gamma, error),
                           'reference_directory': str(ref),
                           'reference_sha256': {name: digest(ref / name) for name in
                                                ('Fit.yaml', 'ParInit.yaml', 'out/ParRes.yaml', 'fit.log')}}
    program = Path(rows[0]['src_main']).parent
    assert digest(program / 'Src_Main') == '46f46d541188982c95c3bcdd8fab778e04aa0725cc9b26c6721e489b3d8ddedb'
    work.mkdir(parents=True)
    (work / 'logs').mkdir()
    jobs = []
    config_hashes = {}
    for row in rows:
        original_fit = yaml.safe_load((repo / row['fit_yaml']).read_text())
        original_par = yaml.safe_load((repo / row['parinit_yaml']).read_text())
        assert original_par['DGE']['Active'] == 0
        assert original_par['SRC']['Src0']['SEDModel']['alpha'][0] == 2.6
        config = program / row['lc_data_config']
        data = yaml.safe_load(config.read_text())
        assert data['Mapfile'] == row['mapfile']
        assert data[row['response_slot']] == row['response_file']
        config_hashes[str(config)] = digest(config)
        for variant, gamma in spectra[row['source']]['variants'].items():
            job = work / 'fits' / variant / row['source'] / row['name']
            job.mkdir(parents=True)
            # Src_Main iterates SRC keys in order; preserve the release ordering.
            fit = copy.deepcopy(original_fit)
            par = copy.deepcopy(original_par)
            fit['Output']['Outdir'] = os.path.relpath(job / 'out', program)
            par['SRC']['Src0']['SEDModel']['alpha'][0] = gamma
            assert par['SRC']['Src0']['SEDModel']['alpha'][3] == 1
            for name, obj in [('Fit.yaml', fit), ('ParInit.yaml', par)]:
                (job / name).write_text(yaml.safe_dump(obj, sort_keys=False))
            new = dict(row, variant=variant, gamma=gamma)
            for field, name in [('fit_yaml', 'Fit.yaml'), ('parinit_yaml', 'ParInit.yaml'),
                                ('outdir', 'out'), ('parres', 'out/ParRes.yaml'), ('log', 'fit.log')]:
                new[field] = str(job / name)
            jobs.append(new)
    dump_csv(work / 'fit_jobs.csv', jobs)
    runner = work / 'run.sh'
    runner.write_text('#!/bin/bash\nset -eo pipefail\ncd ' + shlex.quote(str(repo)) +
                      '\nexec /usr/bin/python ' + shlex.quote(str(repo / 'MakeLC/standard_flux_lc.py')) +
                      ' run-fit-chunk --jobs-csv ' + shlex.quote(str(work / 'fit_jobs.csv')) +
                      ' --start "$1" --stop "$2"\n')
    runner.chmod(0o755)
    (work / 'args').write_text(''.join(f'{i} {i+1}\n' for i in range(len(jobs))))
    submit = (baseline / 'fit.sub').read_text()
    submit = submit.replace(str(baseline.relative_to(repo)), str(work))
    submit = submit.replace('run_fit_chunk.sh', 'run.sh').replace('fit_chunks.args', 'args')
    submit = submit.replace('qpo_official_lc_fit', 'qpo_spectral_abc_8day')
    (work / 'fit.sub').write_text(submit)
    pilot_indices = [next(i for i, row in enumerate(jobs) if row['source'] == s)
                     for s in ('Mkn421', 'Mkn501')]
    (work / 'pilot.args').write_text(''.join(f'{i} {i+1}\n' for i in pilot_indices))
    (work / 'pilot.sub').write_text(submit.replace(str(work / 'args'), str(work / 'pilot.args')))
    (work / 'provenance.json').write_text(json.dumps({
        'spectra': spectra, 'expected_fits': len(jobs), 'cadence': '8day', 'dge_active': False,
        'reference_scope': 'Official full-interval aggregate fit; +/-1 sigma local statistical error only',
        'baseline_manifest_sha256': digest(baseline / 'fit_jobs.csv'),
        'manifest_sha256': digest(work / 'fit_jobs.csv'),
        'runner_dependency_sha256': digest(repo / 'MakeLC/standard_flux_lc.py'),
        'src_main_sha256': digest(program / 'Src_Main'), 'data_config_sha256': config_hashes,
    }, indent=2))
    print(json.dumps({'work': str(work), 'fits': len(jobs), 'spectra': spectra}, indent=2))


def collect(repo, work):
    sys.path.insert(0, str(repo / 'MakeLC'))
    from standard_flux_lc import parse_par_value, parse_ts_from_log
    rows = list(csv.DictReader((work / 'fit_jobs.csv').open()))
    outputs = []
    missing = 0
    for row in rows:
        parres = Path(row['parres'])
        log = Path(row['log'])
        ts, status = parse_ts_from_log(log)
        finished = log.exists() and re.search(
            r'\*\*\* main : number of iteration is \d+\s*$', log.read_text(errors='replace'))
        flux = error = math.nan
        if parres.exists() and finished:
            par = yaml.safe_load(parres.read_text())
            sed = par['SRC']['Src0']['SEDModel']
            # Public YAML rounds the input index when serializing fit results.
            assert abs(parse_par_value(sed['alpha'])[0] - float(row['gamma'])) < 1e-4
            assert par['DGE']['Active'] == 0
            value, err, order = parse_par_value(sed['F0'])
            flux, error = value * float(order), err * float(order)
        else:
            missing += 1
            status = 'pending' if parres.exists() else 'missing_parres'
        outputs.append({k: row[k] for k in ['source', 'variant', 'gamma', 'mjd', 'name', 'response_period']} |
                       {'N0': flux, 'N0_err': error, 'TS': ts, 'fit_status': status})
    dump_csv(work / 'lightcurves.csv', outputs)
    print(json.dumps({'total': len(rows), 'missing': missing,
                      'OK': sum(r['fit_status'] == 'OK' for r in outputs)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['prepare', 'collect', 'self-check'])
    p.add_argument('--repo', type=Path, default=Path.cwd())
    p.add_argument('--work', type=Path)
    args = p.parse_args()
    if args.action == 'self-check':
        assert variants(2.8, 0.1) == {'B': 2.8, 'C_minus': 2.6999999999999997, 'C_plus': 2.9}
        try:
            variants(2.8, -0.1)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid uncertainty accepted')
        print('self-check passed')
    else:
        if args.work is None:
            p.error('--work is required')
        globals()[args.action](args.repo.resolve(), args.work.resolve())
