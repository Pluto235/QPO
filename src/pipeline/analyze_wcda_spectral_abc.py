#!/usr/bin/env python3
"""Compare A/B/C on a common valid-bin mask with the existing QPO screen."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.project_paths import PROCESSED_DATA_DIR
from pipeline.official_lc_qpo_analysis import parse_args, run_source

VARIANTS = ('A', 'B', 'C_minus', 'C_plus')
COLORS = ('#0072B2', '#D55E00', '#009E73', '#CC79A7')


def common_mask(frames):
    valid = []
    for frame in frames.values():
        assert not frame.name.duplicated().any()
        good = frame.fit_status.eq('OK') & np.isfinite(frame.N0) & np.isfinite(frame.N0_err) & frame.N0_err.gt(0)
        valid.append(set(frame.loc[good, 'name']))
    return set.intersection(*valid)


def run(root, source, workers, render_only):
    raw = pd.read_csv(root / 'lightcurves.csv')
    baseline = list((PROCESSED_DATA_DIR / 'wcda_8day/official_20260817').glob(f'LHAASO-WCDA_{source}_*_flux.csv'))
    assert len(baseline) == 1
    frames = {'A': pd.read_csv(baseline[0])}
    for variant in VARIANTS[1:]:
        frames[variant] = raw.loc[raw.source.eq(source) & raw.variant.eq(variant)].copy()
        frames[variant]['cadence'] = '8day'
        assert frames[variant].fit_status.isin(['OK', 'NotOK']).all(), 'Unfinished or unresolved fits'
    assert all(len(f) == 200 for f in frames.values()), 'Incomplete collection'
    common = common_mask(frames)
    assert len(common) >= 8
    frames = {k: f.loc[f.name.isin(common)].sort_values('mjd').copy() for k, f in frames.items()}
    t = frames['A'].mjd.to_numpy()
    assert all(np.array_equal(f.mjd.to_numpy(), t) for f in frames.values())
    args = parse_args(['--n-surrogates', '200', '--workers', str(workers)])
    stats = []
    products = {}
    for variant, frame in frames.items():
        destination = root / source / variant
        destination.mkdir(parents=True, exist_ok=True)
        input_path = destination / 'input.csv'
        frame.to_csv(input_path, index=False)
        if not render_only:
            run_source(args, '8day', source, input_path, destination / 'aligned', destination / 'periodicity', 20260817)
        product = destination / 'periodicity/8day' / source.lower()
        products[variant] = product
        result = pd.read_csv(product / 'wcda_official_8day_significance.csv')
        result.insert(0, 'variant', variant)
        stats.append(result)
    pd.concat(stats).to_csv(root / f'{source}_significance.csv', index=False)
    a = frames['A'].N0.to_numpy()
    metrics = []
    for variant, f in frames.items():
        b = f.N0.to_numpy()
        scale = float(np.dot(a, b) / np.dot(a, a))
        period_a = frames['A'].groupby('response_period').N0.mean()
        period_ratio = f.groupby('response_period').N0.mean() / period_a.where(period_a > 0)
        period_ratio = period_ratio[np.isfinite(period_ratio)]
        metrics.append({'source': source, 'variant': variant, 'gamma': float(f.gamma.iloc[0]),
                        'common_bins': len(common), 'excluded_bins': 200-len(common),
                        'mean_flux_ratio': float(b.mean()/a.mean()), 'scale_least_squares': scale,
                        'pearson_r': float(np.corrcoef(a, b)[0, 1]),
                        'shape_rms_fraction': float(np.sqrt(np.mean((b-scale*a)**2))/b.mean()),
                        'response_mean_ratio_p05': float(period_ratio.quantile(.05)),
                        'response_mean_ratio_p95': float(period_ratio.quantile(.95))})
    pd.DataFrame(metrics).to_csv(root / f'{source}_metrics.csv', index=False)
    plot(root, source, frames, products, metrics)
    print(json.dumps(metrics, indent=2), flush=True)


def plot(root, source, frames, products, metrics):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'legend.frameon': False, 'axes.grid': True, 'grid.alpha': .15})
    fig, axes = plt.subplots(2, 2, figsize=(13, 6.5), constrained_layout=True)
    a = frames['A'].N0.to_numpy()
    t = frames['A'].mjd.to_numpy()
    axes[0, 0].errorbar(t, a/1e-12, yerr=frames['A'].N0_err.to_numpy()/1e-12,
                        fmt='none', ecolor='0.75', elinewidth=.6, zorder=0)
    for variant, color, metric in zip(VARIANTS, COLORS, metrics):
        frame = frames[variant]
        label = f'{variant.replace("_", " ")}: Γ={metric["gamma"]:.5f}'
        axes[0, 0].plot(t, frame.N0.to_numpy()/1e-12, color=color, lw=1,
                        ls='-' if variant in ('A', 'B') else '--', label=label)
        if variant != 'A':
            residual = (frame.N0.to_numpy() - metric['scale_least_squares'] * a) / frame.N0.mean()
            axes[0, 1].plot(t, 100*residual, color=color, lw=.9, label=variant.replace('_', ' '))
        product = products[variant]
        cwt = np.load(product / 'wcda_official_8day_cwt.npz')
        wwz = np.load(product / 'wcda_official_8day_wwz.npz')
        for ax, p, power in [(axes[1, 0], cwt['period'], cwt['gws']),
                             (axes[1, 1], wwz['period_axis'], wwz['global_wwz'])]:
            visible = np.isfinite(p) & np.isfinite(power) & (p >= 32) & (p <= 600)
            p, power = p[visible], power[visible]
            order = np.argsort(p)
            ax.plot(p[order], power[order], color=color, lw=1.4,
                    ls='-' if variant in ('A', 'B') else '--', label=variant.replace('_', ' '))
    axes[0, 0].set(title='8-day light curves', ylabel=r'$N_0$ at 3 TeV [$10^{-12}$ TeV$^{-1}$ cm$^{-2}$ s$^{-1}$]', xlabel='MJD')
    axes[0, 0].legend(fontsize=8, ncol=2)
    axes[0, 1].axhline(0, color='gray', lw=.7)
    axes[0, 1].set(title='Shape change after removing one overall scale', ylabel='Residual / mean flux [%]', xlabel='MJD')
    axes[0, 1].legend(fontsize=8)
    axes[1, 0].set(title='CWT global spectrum', xlabel='Period [days]', ylabel='Standardized power', xlim=(32, 600))
    axes[1, 1].set(title='WWZ global spectrum', xlabel='Period [days]', ylabel='WWZ power', xlim=(32, 600))
    axes[1, 1].legend(fontsize=8, ncol=2)
    fig.suptitle(f'{source.replace("Mkn", "Mrk ")} · spectral-index sensitivity · {len(t)}/200 common bins', fontsize=14)
    for extension in ('png', 'pdf'):
        fig.savefig(root / f'{source}_comparison.{extension}', dpi=300)
    plt.close(fig)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=PROCESSED_DATA_DIR / 'spectral_abc_20260908')
    p.add_argument('--source', choices=['Mkn421', 'Mkn501'], required=True)
    p.add_argument('--workers', type=int, default=16)
    p.add_argument('--render-only', action='store_true')
    a = p.parse_args()
    run(a.root.resolve(), a.source, a.workers, a.render_only)
