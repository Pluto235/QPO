#!/usr/bin/env python3
"""Daily-cadence counterpart of weekly_qpo_local_significance.py: assess local/global
significance for the Mrk 421 / Mrk 501 v2 daily N0 flux CWT/WWZ candidate peaks, using
the identical AR(1) methodology (CWT: PyCWT theoretical AR(1) significance; WWZ: AR(1)
Gaussian surrogate Monte Carlo) so daily results are directly comparable to the existing
weekly significance products.

Sources t/y/yerr directly from the already-computed
data/processed/periodicity/periodicity_v2/<source>/wcda_daily_flux_wwz.npz (the exact
cleaned/merged series that produced the existing GWS/WWZ curves), rather than re-deriving
from the aligned CSV, to guarantee consistency with the already-published daily figures.

Run: ~/miniconda3/envs/py310/bin/python src/pipeline/daily_qpo_local_significance.py \
    --n-surrogates 1000 --workers 8
"""
from __future__ import annotations

import argparse
import contextlib
import io
import multiprocessing as mp
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pycwt as wavelet
from scipy.signal import find_peaks

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import run_wwz, standardize_flux  # noqa: E402

PERIODICITY_V2_DIR = SRC_DIR.parent / "data" / "processed" / "periodicity" / "periodicity_v2"
DEFAULT_SOURCES = ("mkn421", "mkn501")
SOURCE_LABELS = {"mkn421": "Mrk 421", "mkn501": "Mrk 501"}
DEFAULT_N_SURROGATES = 1000
DEFAULT_SEED = 421501
GLOBAL_PEAK_PROMINENCE_FRACTION = 0.10
GLOBAL_PEAK_MIN_DISTANCE_BINS = 2
WWZ_LOCAL_WINDOW_FRACTION = 0.10
FIG_DPI = 180


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sources", nargs="+", default=list(DEFAULT_SOURCES))
    p.add_argument("--n-surrogates", type=int, default=DEFAULT_N_SURROGATES)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--workers", type=int, default=8)
    return p.parse_args(argv)


def _load_npz(path: Path) -> dict:
    with np.load(path, allow_pickle=True) as f:
        return {k: f[k] for k in f.files}


def _candidate_peaks(period, power, period_min, period_max):
    period = np.asarray(period, dtype=float)
    power = np.asarray(power, dtype=float)
    mask = np.isfinite(period) & np.isfinite(power) & (period >= period_min) & (period <= period_max)
    order = np.argsort(period[mask])
    period_plot, power_plot = period[mask][order], power[mask][order]
    if len(period_plot) < 3:
        return period_plot, np.array([], dtype=int)
    power_range = float(np.nanmax(power_plot) - np.nanmin(power_plot))
    if not np.isfinite(power_range) or power_range <= 0:
        return period_plot, np.array([], dtype=int)
    peaks, _ = find_peaks(power_plot, prominence=GLOBAL_PEAK_PROMINENCE_FRACTION * power_range,
                           distance=GLOBAL_PEAK_MIN_DISTANCE_BINS)
    return period_plot, peaks


def _lag1_autocorr(y):
    y = np.asarray(y, dtype=float)
    y = y[np.isfinite(y)]
    if len(y) < 3:
        return 0.0
    y0, y1 = y[:-1] - np.nanmean(y[:-1]), y[1:] - np.nanmean(y[1:])
    denom = float(np.sqrt(np.sum(y0 * y0) * np.sum(y1 * y1)))
    if denom <= 0 or not np.isfinite(denom):
        return 0.0
    return float(np.clip(np.sum(y0 * y1) / denom, -0.95, 0.95))


def _simulate_ar1(n, alpha, mean, std, rng):
    if n < 1:
        return np.array([], dtype=float)
    innovation_std = np.sqrt(max(1.0 - alpha**2, 1e-8))
    x = np.empty(n, dtype=float)
    x[0] = rng.normal()
    for i in range(1, n):
        x[i] = alpha * x[i - 1] + innovation_std * rng.normal()
    x = (x - np.mean(x)) / np.std(x, ddof=1)
    return mean + std * x


def _run_wwz_surrogate_global(task):
    (seed, t, yerr, n, alpha, y_mean, y_std, period_min, period_max,
     time_divisions, decay_constant, freq_step_factor) = task
    rng = np.random.default_rng(seed)
    sim_y = _simulate_ar1(n, alpha, y_mean, y_std, rng)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        sim = run_wwz(t, sim_y, yerr, period_min=period_min, period_max=period_max,
                       time_divisions=time_divisions, decay_constant=decay_constant,
                       freq_step_factor=freq_step_factor, parallel=False)
    return np.asarray(sim["global_wwz"], dtype=float)


def _time_span(t):
    return float(np.nanmax(t) - np.nanmin(t))


def _candidate_note(period, t_span, period_min, period_max):
    notes = ["Quick-look candidate peak; no source/method/survey trial correction."]
    cycles = t_span / period if period > 0 else np.nan
    if np.isfinite(cycles) and cycles < 4.0:
        notes.append("Fewer than four observed cycles.")
    if period <= period_min * 1.02 or period >= period_max * 0.98:
        notes.append("Near search boundary; treat cautiously.")
    return " ".join(notes)


def assess_cwt(source_id, label, t, y, cwt):
    y_std = standardize_flux(y)
    alpha = _lag1_autocorr(y_std)
    mother = wavelet.Morlet(6)
    scales = float(cwt["s0"]) * 2 ** (np.arange(int(cwt["J"]) + 1) * float(cwt["dj"]))
    global_dof = np.full_like(scales, fill_value=len(y_std), dtype=float)
    signif_95, _ = wavelet.significance(y_std, float(cwt["dt"]), scales, sigma_test=1, alpha=alpha,
                                         significance_level=0.95, dof=global_dof, wavelet=mother)
    signif_99, _ = wavelet.significance(y_std, float(cwt["dt"]), scales, sigma_test=1, alpha=alpha,
                                         significance_level=0.99, dof=global_dof, wavelet=mother)
    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    period_min, period_max = float(cwt["period_min"]), float(cwt["period_max"])
    period_plot, peaks = _candidate_peaks(period, gws, period_min, period_max)
    t_span = _time_span(t)
    rows = []
    for peak_idx in peaks:
        peak_period = float(period_plot[peak_idx])
        source_idx = int(np.nanargmin(np.abs(period - peak_period)))
        rows.append({
            "source_id": source_id, "source": label, "series": "wcda_daily", "method": "CWT",
            "period_days": peak_period, "cycles": t_span / peak_period,
            "observed_statistic": float(gws[source_idx]), "statistic_name": "Global wavelet spectrum",
            "null_model": "AR(1) red noise via PyCWT time-averaged significance",
            "local_fap": np.nan, "global_fap": np.nan, "local_confidence": np.nan, "global_confidence": np.nan,
            "reference_95": float(signif_95[source_idx]), "reference_99": float(signif_99[source_idx]),
            "above_95": bool(gws[source_idx] >= signif_95[source_idx]),
            "above_99": bool(gws[source_idx] >= signif_99[source_idx]),
            "n_surrogates": 0, "exceed_count": 0, "global_exceed_count": 0,
            "local_window_min_days": np.nan, "local_window_max_days": np.nan, "ar1_alpha": alpha,
            "note": _candidate_note(peak_period, t_span, period_min, period_max),
        })
    return rows, {"period": period, "gws": gws, "signif_95": signif_95, "signif_99": signif_99,
                   "alpha": alpha, "period_min": period_min, "period_max": period_max}


def assess_wwz(source_id, label, t, y, yerr, wwz, *, n_surrogates, seed, workers):
    period = np.asarray(wwz["period_axis"], dtype=float)
    global_wwz = np.asarray(wwz["global_wwz"], dtype=float)
    period_min, period_max = float(wwz["period_min"]), float(wwz["period_max"])
    period_plot, peaks = _candidate_peaks(period, global_wwz, period_min, period_max)
    if len(peaks) == 0:
        return [], {"period": period, "global_wwz": global_wwz, "q95": np.full_like(period, np.nan),
                     "q99": np.full_like(period, np.nan), "period_min": period_min, "period_max": period_max}

    y_mean, y_std_val = float(np.nanmean(y)), float(np.nanstd(y, ddof=1))
    alpha = float(np.clip(_lag1_autocorr(standardize_flux(y)), -0.95, 0.95))

    candidate_periods = [float(period_plot[idx]) for idx in peaks]
    observed_local_max, local_windows = [], []
    for peak_period in candidate_periods:
        window_min, window_max = peak_period * (1 - WWZ_LOCAL_WINDOW_FRACTION), peak_period * (1 + WWZ_LOCAL_WINDOW_FRACTION)
        mask = np.isfinite(period) & (period >= window_min) & (period <= window_max)
        if not np.any(mask):
            nearest = int(np.nanargmin(np.abs(period - peak_period)))
            mask = np.zeros_like(period, dtype=bool)
            mask[nearest] = True
        observed_local_max.append(float(np.nanmax(global_wwz[mask])))
        local_windows.append((window_min, window_max, mask))

    rng = np.random.default_rng(seed)
    sim_seeds = rng.integers(0, np.iinfo(np.uint32).max, size=n_surrogates, dtype=np.uint32)
    tasks = [
        (int(s), t, yerr, len(y), alpha, y_mean, y_std_val, period_min, period_max,
         int(wwz["time_divisions"]), float(wwz["decay_constant"]), float(wwz["freq_step_factor"]))
        for s in sim_seeds
    ]
    print(f"  [{source_id}] WWZ: running {n_surrogates} AR(1) surrogates across {workers} workers ...")
    if workers > 1 and n_surrogates > 1:
        with mp.Pool(processes=int(workers)) as pool:
            surrogate_global = np.vstack(pool.map(_run_wwz_surrogate_global, tasks))
    else:
        surrogate_global = np.vstack([_run_wwz_surrogate_global(t_) for t_ in tasks])

    surrogate_local_max = np.empty((n_surrogates, len(candidate_periods)), dtype=float)
    for sim_idx, sim_global in enumerate(surrogate_global):
        for peak_idx, (_wmin, _wmax, mask) in enumerate(local_windows):
            surrogate_local_max[sim_idx, peak_idx] = float(np.nanmax(sim_global[mask]))
    surrogate_global_max = np.nanmax(surrogate_global, axis=1)

    q95 = np.nanpercentile(surrogate_global, 95, axis=0)
    q99 = np.nanpercentile(surrogate_global, 99, axis=0)
    t_span = _time_span(t)
    rows = []
    for peak_idx, peak_period in enumerate(candidate_periods):
        exceed = int(np.count_nonzero(surrogate_local_max[:, peak_idx] >= observed_local_max[peak_idx]))
        local_fap = (exceed + 1.0) / (n_surrogates + 1.0)
        gexceed = int(np.count_nonzero(surrogate_global_max >= observed_local_max[peak_idx]))
        global_fap = (gexceed + 1.0) / (n_surrogates + 1.0)
        window_min, window_max, _m = local_windows[peak_idx]
        source_idx = int(np.nanargmin(np.abs(period - peak_period)))
        rows.append({
            "source_id": source_id, "source": label, "series": "wcda_daily", "method": "WWZ",
            "period_days": peak_period, "cycles": t_span / peak_period,
            "observed_statistic": observed_local_max[peak_idx], "statistic_name": "Local-window max global WWZ",
            "null_model": "AR(1) Gaussian surrogate on same daily sampling",
            "local_fap": local_fap, "global_fap": global_fap,
            "local_confidence": 1.0 - local_fap, "global_confidence": 1.0 - global_fap,
            "reference_95": float(q95[source_idx]), "reference_99": float(q99[source_idx]),
            "above_95": bool(observed_local_max[peak_idx] >= q95[source_idx]),
            "above_99": bool(observed_local_max[peak_idx] >= q99[source_idx]),
            "n_surrogates": n_surrogates, "exceed_count": exceed, "global_exceed_count": gexceed,
            "local_window_min_days": window_min, "local_window_max_days": window_max, "ar1_alpha": alpha,
            "note": _candidate_note(peak_period, t_span, period_min, period_max),
        })
    return rows, {"period": period, "global_wwz": global_wwz, "q95": q95, "q99": q99,
                   "period_min": period_min, "period_max": period_max}


def plot_cwt_significance(path, label, cwt_refs, rows):
    # Axis convention matches weekly_qpo_local_significance.py's
    # _plot_cwt_global_significance: period on x-axis (log), power on y-axis (linear).
    fig, ax = plt.subplots(figsize=(8.5, 4.4), constrained_layout=True)
    ax.plot(cwt_refs["period"], cwt_refs["gws"], color="black", lw=1.5, label="Observed GWS")
    ax.plot(cwt_refs["period"], cwt_refs["signif_95"], color="#255c99", lw=1.1, ls="-.", label="AR(1) 95% reference")
    ax.plot(cwt_refs["period"], cwt_refs["signif_99"], color="#7a3e9d", lw=1.1, ls=":", label="AR(1) 99% reference")
    for row in rows:
        ax.axvline(row["period_days"], color="#8a95a5", lw=0.6, alpha=0.6)
    ax.set_xscale("log")
    ax.set_xlim(cwt_refs["period_min"], cwt_refs["period_max"])
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Global wavelet spectrum")
    ax.set_title(f"{label} — daily CWT vs. AR(1) reference")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def plot_wwz_significance(path, label, wwz_refs, rows, n_surrogates):
    # Axis convention matches weekly_qpo_local_significance.py's
    # _plot_wwz_global_significance: period on x-axis (log), power on y-axis (linear).
    fig, ax = plt.subplots(figsize=(8.5, 4.4), constrained_layout=True)
    ax.plot(wwz_refs["period"], wwz_refs["global_wwz"], color="black", lw=1.5, label="Observed WWZ")
    ax.plot(wwz_refs["period"], wwz_refs["q95"], color="#255c99", lw=1.1, ls="-.", label="AR(1) surrogate 95%")
    ax.plot(wwz_refs["period"], wwz_refs["q99"], color="#7a3e9d", lw=1.1, ls=":", label="AR(1) surrogate 99%")
    for row in rows:
        ax.axvline(row["period_days"], color="#8a95a5", lw=0.6, alpha=0.6)
    ax.set_xscale("log")
    ax.set_xlim(wwz_refs["period_min"], wwz_refs["period_max"])
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Mean WWZ power")
    ax.set_title(f"{label} — daily WWZ vs. AR(1) surrogate ({n_surrogates} realizations)")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def main(argv=None):
    args = parse_args(argv)
    all_rows = []
    for source_id in args.sources:
        label = SOURCE_LABELS[source_id]
        src_dir = PERIODICITY_V2_DIR / source_id
        cwt = _load_npz(src_dir / "wcda_daily_flux_cwt.npz")
        wwz = _load_npz(src_dir / "wcda_daily_flux_wwz.npz")
        t, y, yerr = wwz["t"], wwz["y"], wwz["yerr"]
        print(f"[{source_id}] N={len(t)}, MJD {t.min():.1f}-{t.max():.1f}")

        cwt_rows, cwt_refs = assess_cwt(source_id, label, t, y, cwt)
        wwz_rows, wwz_refs = assess_wwz(source_id, label, t, y, yerr, wwz,
                                         n_surrogates=args.n_surrogates, seed=args.seed, workers=args.workers)
        all_rows.extend(cwt_rows + wwz_rows)

        plot_cwt_significance(src_dir / "wcda_daily_flux_cwt_global_significance.png", label, cwt_refs, cwt_rows)
        plot_wwz_significance(src_dir / "wcda_daily_flux_wwz_global_significance.png", label, wwz_refs, wwz_rows,
                               args.n_surrogates)
        # Cache the full reference curves (not just per-candidate scalars) so a future
        # plotting/styling fix doesn't require re-running the expensive WWZ surrogate MC.
        np.savez(
            src_dir / "wcda_daily_flux_significance_curves.npz",
            cwt_period=cwt_refs["period"], cwt_gws=cwt_refs["gws"],
            cwt_signif_95=cwt_refs["signif_95"], cwt_signif_99=cwt_refs["signif_99"],
            wwz_period=wwz_refs["period"], wwz_global_wwz=wwz_refs["global_wwz"],
            wwz_q95=wwz_refs["q95"], wwz_q99=wwz_refs["q99"],
        )
        print(f"[{source_id}] done: {len(cwt_rows)} CWT candidates, {len(wwz_rows)} WWZ candidates")

    import pandas as pd
    out_csv = PERIODICITY_V2_DIR / "daily_significance_summary.csv"
    pd.DataFrame(all_rows).to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")


if __name__ == "__main__":
    main()
