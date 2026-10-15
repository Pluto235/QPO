#!/usr/bin/env python3
"""Strict four-source 2-day CWT/WWZ diagnostics, local and reproducible."""
from __future__ import annotations

import os
for _name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name]='1'

import argparse
import contextlib
import hashlib
import importlib.metadata
import io
import json
import multiprocessing as mp
from pathlib import Path
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from methods.detector_controls import (CachedWWZ,adjacent_ar1,prepare_light_curves,
                                       sample_masked_ar1,wwz_significance)
from methods.periodicity import run_cwt,run_wwz
from pipeline.official_lc_qpo_analysis import _assess_cwt
from pipeline.periodicity_v1 import _plot_periodicity_summary,_save_cwt,_save_wwz
from utils.project_paths import PROJECT_ROOT,WCDA_2DAY_DIR,ALIGNED_DIR,PERIODICITY_DIR,ensure_dir

SOURCES=('Crab','IC443','Blank175','J1952')
KEY='detector_controls_20261011'
EXPECTED={'Crab':799,'IC443':676,'Blank175':309,'J1952':540}
_OPERATOR=None
_NULL=None


def parse_args(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources',nargs='+',choices=SOURCES,default=list(SOURCES))
    p.add_argument('--input-dir',type=Path,default=WCDA_2DAY_DIR/KEY)
    p.add_argument('--aligned-dir',type=Path,default=ALIGNED_DIR/KEY)
    p.add_argument('--periodicity-dir',type=Path,default=PERIODICITY_DIR/KEY)
    p.add_argument('--period-min',type=float,default=10.)
    p.add_argument('--period-max',type=float,default=600.)
    p.add_argument('--n-surrogates',type=int,default=1000)
    p.add_argument('--seed',type=int,default=20261012)
    p.add_argument('--workers',type=int,choices=(1,2),default=2)
    p.add_argument('--wwz-time-divisions',type=int,default=80)
    p.add_argument('--wwz-freq-step-factor',type=float,default=.5)
    p.add_argument('--mark-global-peaks-on-maps',action='store_true')
    p.add_argument('--render-only',action='store_true')
    p.add_argument('--no-report',action='store_true')
    args=p.parse_args(argv)
    if not 0<args.period_min<args.period_max or args.n_surrogates<1 or args.wwz_time_divisions<2 or args.wwz_freq_step_factor<=0:
        p.error('Invalid period range, simulation count or WWZ grid')
    args.sources=[s for s in SOURCES if s in args.sources]
    return args


def _initialize_worker(t,tau,freq,mask,alpha,mean,std):
    global _OPERATOR,_NULL
    _OPERATOR=CachedWWZ(t,tau,freq,.0125)
    _NULL=(mask,alpha,mean,std)


def _simulate(seed):
    y=sample_masked_ar1(seed,*_NULL)
    return _OPERATOR.power(y).mean(axis=0)


def _load_npz(path):
    with np.load(path,allow_pickle=False) as data:
        return {k:data[k] for k in data.files}


def _save_json(path,value):
    temp=path.with_suffix('.json.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    temp.replace(path)


def _config(args,source,input_hash):
    return dict(source=source,input_sha256=input_hash,period_min=args.period_min,period_max=args.period_max,
        n_surrogates=args.n_surrogates,seed=args.seed+SOURCES.index(source),
        wwz_time_divisions=args.wwz_time_divisions,wwz_freq_step_factor=args.wwz_freq_step_factor,
        decay_constant=.0125,quality_policy='strict_known_flags_v1',cadence_days=2)


def analyze_source(args,source):
    input_path=args.input_dir/f'{source}_2day.csv'
    input_hash=hashlib.sha256(input_path.read_bytes()).hexdigest()
    config=_config(args,source,input_hash)
    out=ensure_dir(args.periodicity_dir/source.lower())
    aligned_out=ensure_dir(args.aligned_dir/source.lower())
    metadata_path=out/'run_metadata.json'
    if metadata_path.exists():
        saved=json.loads(metadata_path.read_text())
        if saved['config']!=config:
            raise ValueError(f'{source}: saved config differs; use a separate output directory')
        print(f'[{source}] reusing completed calculations',flush=True)
        return
    start=time.perf_counter()
    raw=pd.read_csv(input_path)
    audit,observed,grid=prepare_light_curves(raw)
    if len(raw)==803 and len(observed)!=EXPECTED[source]:
        raise ValueError(f'{source}: unexpected strict selection count {len(observed)}')
    audit.to_csv(aligned_out/'selection_audit.csv',index=False)
    observed.to_csv(aligned_out/'wwz_observed.csv',index=False)
    grid.to_csv(aligned_out/'cwt_grid.csv',index=False)
    t=observed.mjd.to_numpy(float)
    y=observed.flux.to_numpy(float)
    err=observed.flux_err.to_numpy(float)
    alpha,pairs=adjacent_ar1(t,y)
    print(f'[{source}] retained={len(y)}/{len(raw)}; CWT interpolated={grid.is_interpolated.sum()}; alpha={alpha:.6f} ({pairs} real pairs)',flush=True)
    cwt=run_cwt(grid.mjd.to_numpy(),grid.flux.to_numpy(),period_min=args.period_min,period_max=args.period_max)
    cwt_rows,cwt_refs=_assess_cwt(source.lower(),source,'2day',grid.mjd.to_numpy(),grid.flux.to_numpy(),cwt,alpha_override=alpha)
    direct_start=time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):
        wwz=run_wwz(t,y,err,period_min=args.period_min,period_max=args.period_max,
            time_divisions=args.wwz_time_divisions,freq_step_factor=args.wwz_freq_step_factor,parallel=False)
    direct_seconds=time.perf_counter()-direct_start
    operator=CachedWWZ(t,wwz['tau_mat'][:,0],wwz['freq_mat'][0],.0125)
    cached_start=time.perf_counter()
    cached=operator.power(y)
    cached_seconds=time.perf_counter()-cached_start
    np.testing.assert_allclose(cached,wwz['wwz_mat'],rtol=2e-7,atol=2e-8)
    parity_error=float(np.max(abs(cached-wwz['wwz_mat'])))
    print(f'[{source}] libwwz {direct_seconds:.2f}s; cached {cached_seconds:.3f}s; max grid difference={parity_error:.3g}',flush=True)
    # Check one actual null realization against libwwz, in addition to the data.
    mask=audit.retained.to_numpy(bool)
    mean,std=float(y.mean()),float(y.std(ddof=1))
    seeds=np.random.default_rng(config['seed']).integers(0,np.iinfo(np.uint32).max,size=args.n_surrogates,dtype=np.uint32)
    probe=sample_masked_ar1(int(seeds[0]),mask,alpha,mean,std)
    with contextlib.redirect_stdout(io.StringIO()):
        probe_reference=run_wwz(t,probe,err,period_min=args.period_min,period_max=args.period_max,
            time_divisions=args.wwz_time_divisions,freq_step_factor=args.wwz_freq_step_factor,parallel=False)
    probe_cached=operator.power(probe)
    np.testing.assert_allclose(probe_cached,probe_reference['wwz_mat'],rtol=2e-7,atol=2e-8)
    null_parity_error=float(np.max(abs(probe_cached-probe_reference['wwz_mat'])))
    del operator,cached,probe_reference,probe_cached
    init=(t,wwz['tau_mat'][:,0],wwz['freq_mat'][0],mask,alpha,mean,std)
    simulated=[]
    sim_start=time.perf_counter()
    if args.workers==1:
        _initialize_worker(*init)
        iterator=map(_simulate,map(int,seeds))
        for i,spectrum in enumerate(iterator,1):
            simulated.append(spectrum)
            if i%100==0 or i==len(seeds):
                print(f'[{source}] surrogates {i}/{len(seeds)} ({time.perf_counter()-sim_start:.1f}s)',flush=True)
        global _OPERATOR
        _OPERATOR=None
    else:
        with mp.get_context('spawn').Pool(args.workers,initializer=_initialize_worker,initargs=init) as pool:
            for i,spectrum in enumerate(pool.imap(_simulate,map(int,seeds),chunksize=10),1):
                simulated.append(spectrum)
                if i%100==0 or i==len(seeds):
                    print(f'[{source}] surrogates {i}/{len(seeds)} ({time.perf_counter()-sim_start:.1f}s)',flush=True)
    simulated=np.asarray(simulated)
    period=wwz['period_axis']
    search=(period>=args.period_min)&(period<=args.period_max)
    wwz_rows,wwz_refs=wwz_significance(period[search],wwz['global_wwz'][search],simulated[:,search],alpha=alpha,span=float(np.ptp(t)))
    wwz_refs.update(period_min=args.period_min,period_max=args.period_max)
    for row in cwt_rows:
        row['four_source_fap']=np.nan
    for row in cwt_rows+wwz_rows:
        row.update(source=source,source_id=source.lower(),selection='strict',
            note='Conditional diagnostic: fixed quality mask; Gaussian AR(1); selection mechanism not simulated')
    columns=list(dict.fromkeys(list(cwt_rows[0]) if cwt_rows else ['source','method','period_days','local_fap','global_fap','four_source_fap']))
    columns=list(dict.fromkeys(columns+[k for row in wwz_rows for k in row]))
    pd.DataFrame(cwt_rows+wwz_rows,columns=columns).to_csv(out/'candidate_significance.csv',index=False)
    _save_cwt(out/'cwt.npz',cwt)
    _save_wwz(out/'wwz.npz',wwz)
    np.savez_compressed(out/'significance_refs.npz',**{f'cwt_{k}':v for k,v in cwt_refs.items()},
                        **{f'wwz_{k}':v for k,v in wwz_refs.items()})
    np.savez_compressed(out/'surrogate_global_spectra.npz',period=period,spectra=simulated,seeds=seeds)
    low,high=np.percentile(y,[1,99])
    pad=.1*(high-low)
    low,high=float(low-pad),float(high+pad)
    clipped=int(np.count_nonzero((y-err<low)|(y+err>high)))
    versions={name:importlib.metadata.version(name) for name in ('numpy','pandas','matplotlib','scipy','pycwt','libwwz')}
    code_hashes={str(p.relative_to(PROJECT_ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (Path(__file__),PROJECT_ROOT/'src/methods/detector_controls.py',
                  PROJECT_ROOT/'src/methods/periodicity.py',PROJECT_ROOT/'src/pipeline/official_lc_qpo_analysis.py',
                  PROJECT_ROOT/'src/pipeline/periodicity_v1.py')}
    _save_json(metadata_path,dict(status='complete',config=config,
        completed_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        input_path=str(input_path.resolve()),raw_rows=len(raw),retained_rows=len(y),
        cwt_rows=len(grid),interpolated_rows=int(grid.is_interpolated.sum()),
        mjd_min=float(raw.mjd.min()),mjd_max=float(raw.mjd.max()),
        retained_mjd_min=float(t.min()),retained_mjd_max=float(t.max()),
        max_retained_gap_days=float(np.diff(t).max()),ar1_alpha=alpha,ar1_real_pairs=pairs,
        pivot_energy_TeV=float(observed.E0_TeV.iloc[0]),flux_min=float(y.min()),flux_max=float(y.max()),
        display_ylim=[low,high],display_clipped_count=clipped,
        exclusion_counts={reason:int(audit.exclusion_reason.str.split(';').apply(lambda x:reason in x).sum())
            for reason in ('invalid_fit','nonfinite_flux','invalid_error','invalid_exposure','at_boundary','error_unreliable','low_exposure','extreme_flux')},
        model_status='diagnostic_unresolved_roi_residual' if source=='J1952' else 'not_specified',
        observed_parity_max_abs=parity_error,null_parity_max_abs=null_parity_error,
        direct_wwz_seconds=direct_seconds,cached_wwz_seconds=cached_seconds,
        elapsed_seconds=time.perf_counter()-start,versions=versions,code_sha256=code_hashes,
        python=sys.executable,workers=args.workers,threads_per_worker=1,
        wwz_frequency_bins=len(period),wwz_time_bins=wwz['wwz_mat'].shape[0],
        null_description='Gaussian AR(1) on the original complete 2-day grid, then fixed strict mask; no extra measurement-noise draw'))


def render_source(args,source):
    out=args.periodicity_dir/source.lower()
    meta=json.loads((out/'run_metadata.json').read_text())
    input_path=args.input_dir/f'{source}_2day.csv'
    if hashlib.sha256(input_path.read_bytes()).hexdigest()!=meta['config']['input_sha256']:
        raise ValueError(f'{source}: input changed after computation')
    observed=pd.read_csv(args.aligned_dir/source.lower()/'wwz_observed.csv')
    cwt,wwz=_load_npz(out/'cwt.npz'),_load_npz(out/'wwz.npz')
    refs=_load_npz(out/'significance_refs.npz')
    cwt_refs={k[4:]:v for k,v in refs.items() if k.startswith('cwt_')}
    wwz_refs={k[4:]:v for k,v in refs.items() if k.startswith('wwz_')}
    title=f"{source} WCDA 2-day flux · strict selection {len(observed)}/{meta['raw_rows']} · E0={meta['pivot_energy_TeV']:g} TeV"
    if source=='J1952':
        title+=' · diagnostic model'
    _plot_periodicity_summary(out/f'{source}_strict_2day_cwt_wwz.png',title,
        observed.mjd.to_numpy(),observed.flux.to_numpy(),observed.flux_err.to_numpy(),cwt,wwz,
        include_global_row=True,cwt_significance=cwt_refs,wwz_significance=wwz_refs,
        light_curve_ylim=tuple(meta['display_ylim']),mark_lc_clipping=True,
        global_legends_above=True,mark_global_peaks_on_maps=args.mark_global_peaks_on_maps)
    print(f'[{source}] rendered composite',flush=True)


def main(argv=None):
    args=parse_args(argv)
    for source in args.sources:
        if not args.render_only:
            analyze_source(args,source)
        render_source(args,source)
    frames=[pd.read_csv(args.periodicity_dir/s.lower()/'candidate_significance.csv') for s in args.sources]
    pd.concat(frames,ignore_index=True).to_csv(args.periodicity_dir/'four_source_candidate_summary.csv',index=False)
    if not args.no_report:
        from pipeline.build_detector_controls_report import build_report
        build_report(args)


if __name__=='__main__':
    main()
