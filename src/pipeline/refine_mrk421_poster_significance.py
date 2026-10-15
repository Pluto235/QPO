#!/usr/bin/env python3
"""Refine the saved slide-8 WWZ null ensemble, preserving its data and grid."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from methods.detector_controls import CachedWWZ
from methods.periodicity import run_wwz
from pipeline.official_lc_qpo_analysis import _simulate_ar1, _plot_wwz_significance
from pipeline.official_lc_xgm_window_qpo_analysis import presentation_flux_limits, save_significance_refs
from pipeline.periodicity_v1 import _plot_periodicity_summary
from utils.project_paths import PERIODICITY_DIR, PROJECT_ROOT

INPUT_KEY = 'bright_window_59800_60500_highres'
OUTPUT_KEY = INPUT_KEY + '_ar1_1000_20261014'
SEED = 20260817
N_SURROGATES = 1000


def load_npz(path):
    with np.load(path, allow_pickle=False) as saved:
        return dict(saved)


def main():
    start = time.perf_counter()
    parent = PERIODICITY_DIR / 'official_lc_20260817'
    source = parent / INPUT_KEY / 'mkn421'
    output = parent / OUTPUT_KEY / 'mkn421'
    output.mkdir(parents=True, exist_ok=True)
    old_stem = 'wcda_official_2day_' + INPUT_KEY
    stem = 'wcda_official_2day_' + OUTPUT_KEY
    cwt = load_npz(source / f'{old_stem}_cwt.npz')
    wwz = load_npz(source / f'{old_stem}_wwz.npz')
    old_refs = load_npz(source / f'{old_stem}_significance_refs.npz')
    rows = pd.read_csv(source / f'{old_stem}_candidate_significance.csv')
    t, y, err = (wwz[k] for k in ('t', 'y', 'yerr'))
    assert len(t) == 349 and wwz['wwz_mat'].shape == (240, 267)
    assert np.all((t >= 59800) & (t <= 60500))
    assert float(wwz['period_min']) == 10 and float(wwz['period_max']) == 200
    assert int(old_refs['wwz_n_surrogates']) == 200
    alpha = float(rows.ar1_alpha.iloc[0])
    mean, std = float(y.mean()), float(y.std(ddof=1))
    operator = CachedWWZ(t, wwz['tau_mat'][:, 0], wwz['freq_mat'][0], float(wwz['decay_constant']))
    cached = operator.power(y)
    np.testing.assert_allclose(cached, wwz['wwz_mat'], rtol=2e-7, atol=2e-8)
    observed_error = float(np.max(abs(cached - wwz['wwz_mat'])))
    seeds = np.random.default_rng(SEED).integers(0, np.iinfo(np.uint32).max, size=N_SURROGATES, dtype=np.uint32)

    # Validate a real null draw as well as the observed map before acceleration.
    probe = _simulate_ar1(len(y), alpha, mean, std, np.random.default_rng(int(seeds[0])))
    direct = run_wwz(t, probe, err, period_min=10, period_max=200,
                     time_divisions=240, freq_step_factor=.25, decay_constant=float(wwz['decay_constant']))
    probe_cached = operator.power(probe)
    np.testing.assert_allclose(probe_cached, direct['wwz_mat'], rtol=2e-7, atol=2e-8)
    null_error = float(np.max(abs(probe_cached - direct['wwz_mat'])))
    print(f'Parity passed: observed max error={observed_error:.3g}; null={null_error:.3g}', flush=True)
    simulated = np.empty((N_SURROGATES, len(wwz['period_axis'])))
    for i, seed in enumerate(seeds):
        sample = _simulate_ar1(len(y), alpha, mean, std, np.random.default_rng(int(seed)))
        simulated[i] = operator.power(sample).mean(axis=0)
        if (i + 1) % 100 == 0:
            print(f'Surrogates {i + 1}/{N_SURROGATES}; elapsed={time.perf_counter() - start:.1f}s', flush=True)

    # The first 200 must reproduce the original ensemble, including tail counts.
    for percentile, key in ((95, 'wwz_q95'), (99, 'wwz_q99')):
        np.testing.assert_allclose(np.percentile(simulated[:200], percentile, axis=0), old_refs[key], rtol=2e-7, atol=2e-8)
    q95, q99 = np.percentile(simulated, [95, 99], axis=0)
    period = wwz['period_axis']
    for i, row in rows.loc[rows.method.eq('WWZ')].iterrows():
        mask = (period >= row.local_window_min_days) & (period <= row.local_window_max_days)
        observed = float(wwz['global_wwz'][mask].max())
        assert np.count_nonzero(simulated[:200, mask].max(axis=1) >= observed) == row.exceed_count
        assert np.count_nonzero(simulated[:200].max(axis=1) >= observed) == row.global_exceed_count
        local_count = int(np.count_nonzero(simulated[:, mask].max(axis=1) >= observed))
        global_count = int(np.count_nonzero(simulated.max(axis=1) >= observed))
        nearest = int(np.argmin(abs(period - row.period_days)))
        for key, value in dict(n_surrogates=N_SURROGATES, reference_95=q95[nearest], reference_99=q99[nearest],
                above_95=observed >= q95[nearest], above_99=observed >= q99[nearest],
                exceed_count=local_count, global_exceed_count=global_count,
                local_fap=(local_count + 1) / (N_SURROGATES + 1), global_fap=(global_count + 1) / (N_SURROGATES + 1),
                local_confidence=1 - (local_count + 1) / (N_SURROGATES + 1), global_confidence=1 - (global_count + 1) / (N_SURROGATES + 1)).items():
            rows.loc[i, key] = value
    cwt_refs = dict(period=cwt['period'], gws=cwt['gws'], reference_95=old_refs['cwt_reference_95'],
                    reference_99=old_refs['cwt_reference_99'], signif_95=old_refs['cwt_reference_95'],
                    signif_99=old_refs['cwt_reference_99'], period_min=10., period_max=200.)
    wwz_refs = dict(period=period, global_wwz=wwz['global_wwz'], q95=q95, q99=q99,
                    n_surrogates=N_SURROGATES, alpha=alpha, period_min=10., period_max=200.)
    rows.to_csv(output / f'{stem}_candidate_significance.csv', index=False)
    save_significance_refs(output / f'{stem}_significance_refs.npz', cwt_refs, wwz_refs)
    np.savez_compressed(output / 'surrogate_global_spectra.npz', spectra=simulated, seeds=seeds, period=period)
    label = 'Mrk 421 official WCDA 2-day flux · MJD 59800–60500'
    _plot_periodicity_summary(output / f'{stem}_periodicity.png', label, t, y, err, cwt, wwz,
        color_scale='linear', include_global_row=True, cwt_significance=cwt_refs, wwz_significance=wwz_refs,
        light_curve_ylim=presentation_flux_limits(y, err),
        light_curve_note='Flux-axis clipping is display-only; timing uses all retained values.', mark_global_peaks_on_maps=True)
    _plot_wwz_significance(output / f'{stem}_wwz_significance.png', label, wwz_refs,
                           rows.loc[rows.method.eq('WWZ')].to_dict('records'), N_SURROGATES)
    inputs = [source / f'{old_stem}_{suffix}' for suffix in ('cwt.npz', 'wwz.npz', 'significance_refs.npz', 'candidate_significance.csv')]
    code = [Path(__file__), PROJECT_ROOT / 'src/methods/detector_controls.py', PROJECT_ROOT / 'src/methods/periodicity.py',
            PROJECT_ROOT / 'src/pipeline/official_lc_qpo_analysis.py', PROJECT_ROOT / 'src/pipeline/periodicity_v1.py']
    metadata = dict(status='complete', n_surrogates=N_SURROGATES, seed=SEED, ar1_alpha=alpha,
        slurm_job_id=os.environ.get('SLURM_JOB_ID'), python=sys.version,
        versions={name: importlib.metadata.version(name) for name in ('numpy', 'scipy', 'pandas', 'matplotlib')},
        copied_dependencies={'pycwt': '0.3.0a22', 'libwwz': '1.3.4'},
        observed_map_max_abs_error=observed_error, null_map_max_abs_error=null_error, first_200_quantiles_and_counts_match=True,
        elapsed_seconds=time.perf_counter() - start, input_key=INPUT_KEY, output_key=OUTPUT_KEY,
        input_sha256={str(p.relative_to(PROJECT_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        code_sha256={str(p.relative_to(PROJECT_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in code},
        null_model='Same Gaussian AR(1) on retained-index sampling as slide 8; no additional measurement-noise draw.',
        trials='Full period-grid correction only; no additional source, method, or selected-window correction.',
        cwt='Original analytic AR(1) significance unchanged; Monte Carlo update applies to WWZ only.')
    (output / 'run_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(rows.loc[rows.method.eq('WWZ'), ['period_days', 'n_surrogates', 'local_fap', 'global_fap']].to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
