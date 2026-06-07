#!/usr/bin/env python3
"""Assess local significance for current WCDA weekly QPO candidate peaks."""

from __future__ import annotations

import argparse
import contextlib
import io
import multiprocessing as mp
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd
import pycwt as wavelet
from scipy.signal import find_peaks


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import run_wwz, standardize_flux  # noqa: E402
from utils.project_paths import ALIGNED_DIR, PERIODICITY_DIR, PROJECT_ROOT  # noqa: E402
from utils.source_registry import SOURCE_REGISTRY, WCDA_WEEK_SURVEY_SOURCE_IDS, get_source  # noqa: E402


SOURCE_CONFIG = {
    "mkn421": {
        "label": get_source("mkn421").label,
        "aligned": get_source("mkn421").expected_aligned_week_path(),
        "periodicity": get_source("mkn421").periodicity_dir,
    },
    "mkn501": {
        "label": get_source("mkn501").label,
        "aligned": get_source("mkn501").expected_aligned_week_path(),
        "periodicity": get_source("mkn501").periodicity_dir,
    },
}
DEFAULT_SOURCES = tuple(SOURCE_CONFIG)
SURVEY_ALIGNED_DIR = ALIGNED_DIR / "agn_wcda_weekly_survey"
SURVEY_PERIODICITY_DIR = PERIODICITY_DIR / "agn_wcda_weekly_survey"
SURVEY_SIGNIFICANCE_SUMMARY = SURVEY_PERIODICITY_DIR / "agn_wcda_weekly_significance_summary.csv"
DEFAULT_N_SURROGATES = 1000
DEFAULT_SEED = 421501
GLOBAL_PEAK_PROMINENCE_FRACTION = 0.10
GLOBAL_PEAK_MIN_DISTANCE_BINS = 2
WWZ_LOCAL_WINDOW_FRACTION = 0.10
FIG_DPI = 180


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=sorted(SOURCE_REGISTRY),
        default=None,
        help="Source ids to process. Defaults to mkn421/mkn501, or all 10 survey sources with --wcda-week-survey.",
    )
    parser.add_argument(
        "--wcda-week-survey",
        action="store_true",
        help="Use the 10-source AGN WCDA weekly survey aligned/periodicity directories.",
    )
    parser.add_argument("--n-surrogates", type=int, default=DEFAULT_N_SURROGATES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--wwz-parallel", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.n_surrogates < 1:
        raise ValueError("--n-surrogates must be positive.")

    all_rows = []
    run_configs = _resolve_run_configs(args)
    for source_index, (source_id, config) in enumerate(run_configs.items()):
        rng = np.random.default_rng(args.seed + source_index)
        rows = assess_source(
            source_id,
            config["label"],
            config["aligned"],
            config["periodicity"],
            n_surrogates=args.n_surrogates,
            rng=rng,
            wwz_parallel=args.wwz_parallel,
            workers=args.workers,
        )
        output_csv = config["periodicity"] / "wcda_weekly_local_significance.csv"
        pd.DataFrame(rows).to_csv(output_csv, index=False)
        all_rows.extend(rows)
        print(f"[OK] wrote {output_csv.relative_to(PROJECT_ROOT)}")

    if args.wcda_week_survey:
        SURVEY_PERIODICITY_DIR.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(all_rows).to_csv(SURVEY_SIGNIFICANCE_SUMMARY, index=False)
        print(f"[OK] wrote {SURVEY_SIGNIFICANCE_SUMMARY.relative_to(PROJECT_ROOT)}")


def _resolve_run_configs(args: argparse.Namespace) -> dict[str, dict]:
    if args.wcda_week_survey:
        source_ids = args.sources or list(WCDA_WEEK_SURVEY_SOURCE_IDS)
        return {
            source_id: {
                "label": get_source(source_id).label,
                "aligned": SURVEY_ALIGNED_DIR / source_id / "wcda_weekly_aligned.csv",
                "periodicity": SURVEY_PERIODICITY_DIR / source_id,
            }
            for source_id in source_ids
        }

    source_ids = args.sources or list(DEFAULT_SOURCES)
    unknown = sorted(set(source_ids) - set(SOURCE_CONFIG))
    if unknown:
        raise ValueError(f"Non-survey mode only has default configs for {sorted(SOURCE_CONFIG)}; got {unknown}.")
    return {source_id: SOURCE_CONFIG[source_id] for source_id in source_ids}


def assess_source(
    source_id: str,
    source_label: str,
    aligned_path: Path,
    periodicity_dir: Path,
    *,
    n_surrogates: int,
    rng: np.random.Generator,
    wwz_parallel: bool,
    workers: int,
) -> list[dict]:
    aligned = _load_weekly_light_curve(aligned_path)
    cwt = _load_npz_dict(periodicity_dir / "wcda_weekly_cwt.npz")
    wwz = _load_npz_dict(periodicity_dir / "wcda_weekly_wwz.npz")

    cwt_rows, cwt_refs = _assess_cwt(source_id, source_label, aligned, cwt)
    wwz_rows, wwz_refs = _assess_wwz(
        source_id,
        source_label,
        aligned,
        wwz,
        n_surrogates=n_surrogates,
        rng=rng,
        parallel=wwz_parallel,
        workers=workers,
    )

    _plot_cwt_global_significance(
        periodicity_dir / "wcda_weekly_cwt_global_significance.png",
        source_label,
        cwt,
        cwt_rows,
        cwt_refs,
    )
    _plot_wwz_global_significance(
        periodicity_dir / "wcda_weekly_wwz_global_significance.png",
        source_label,
        wwz,
        wwz_rows,
        wwz_refs,
    )

    return cwt_rows + wwz_rows


def _load_weekly_light_curve(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"mjd", "wcda_flux_excess", "wcda_flux_excess_err"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    out = df.loc[:, ["mjd", "wcda_flux_excess", "wcda_flux_excess_err"]].copy()
    for col in out.columns:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    mask = (
        np.isfinite(out["mjd"])
        & np.isfinite(out["wcda_flux_excess"])
        & np.isfinite(out["wcda_flux_excess_err"])
        & (out["wcda_flux_excess_err"] > 0)
    )
    return out.loc[mask].sort_values("mjd").reset_index(drop=True)


def _load_npz_dict(path: Path) -> dict:
    with np.load(path) as data:
        return {key: data[key] for key in data.files}


def _candidate_peaks(period: np.ndarray, power: np.ndarray, period_min: float, period_max: float) -> tuple[np.ndarray, np.ndarray]:
    period = np.asarray(period, dtype=float)
    power = np.asarray(power, dtype=float)
    mask = np.isfinite(period) & np.isfinite(power) & (period >= period_min) & (period <= period_max)
    order = np.argsort(period[mask])
    period_plot = period[mask][order]
    power_plot = power[mask][order]
    if len(period_plot) < 3:
        return period_plot, np.array([], dtype=int)

    power_range = float(np.nanmax(power_plot) - np.nanmin(power_plot))
    if not np.isfinite(power_range) or power_range <= 0:
        return period_plot, np.array([], dtype=int)

    peaks, _ = find_peaks(
        power_plot,
        prominence=GLOBAL_PEAK_PROMINENCE_FRACTION * power_range,
        distance=GLOBAL_PEAK_MIN_DISTANCE_BINS,
    )
    return period_plot, peaks


def _assess_cwt(source_id: str, source_label: str, aligned: pd.DataFrame, cwt: dict) -> tuple[list[dict], dict]:
    flux = aligned["wcda_flux_excess"].to_numpy(dtype=float)
    y = standardize_flux(flux)
    alpha = _lag1_autocorr(y)
    mother = wavelet.Morlet(6)
    scales = float(cwt["s0"]) * 2 ** (np.arange(int(cwt["J"]) + 1) * float(cwt["dj"]))
    global_dof = np.full_like(scales, fill_value=len(y), dtype=float)
    signif_95, _ = wavelet.significance(
        y,
        float(cwt["dt"]),
        scales,
        sigma_test=1,
        alpha=alpha,
        significance_level=0.95,
        dof=global_dof,
        wavelet=mother,
    )
    signif_99, _ = wavelet.significance(
        y,
        float(cwt["dt"]),
        scales,
        sigma_test=1,
        alpha=alpha,
        significance_level=0.99,
        dof=global_dof,
        wavelet=mother,
    )

    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    period_plot, peaks = _candidate_peaks(period, gws, float(cwt["period_min"]), float(cwt["period_max"]))
    rows: list[dict] = []
    t_span = _time_span(aligned)
    for peak_idx in peaks:
        peak_period = float(period_plot[peak_idx])
        source_idx = int(np.nanargmin(np.abs(period - peak_period)))
        rows.append(
            {
                "source_id": source_id,
                "source": source_label,
                "series": "wcda_weekly",
                "method": "CWT",
                "period_days": peak_period,
                "cycles": t_span / peak_period,
                "observed_statistic": float(gws[source_idx]),
                "statistic_name": "Global wavelet spectrum",
                "null_model": "AR(1) red noise via PyCWT time-averaged significance",
                "local_fap": np.nan,
                "global_fap": np.nan,
                "local_confidence": np.nan,
                "global_confidence": np.nan,
                "reference_95": float(signif_95[source_idx]),
                "reference_99": float(signif_99[source_idx]),
                "above_95": bool(gws[source_idx] >= signif_95[source_idx]),
                "above_99": bool(gws[source_idx] >= signif_99[source_idx]),
                "n_surrogates": 0,
                "exceed_count": 0,
                "global_exceed_count": 0,
                "local_window_min_days": np.nan,
                "local_window_max_days": np.nan,
                "ar1_alpha": alpha,
                "note": _candidate_note(peak_period, t_span, float(cwt["period_min"]), float(cwt["period_max"])),
            }
        )

    return rows, {"period": period, "signif_95": signif_95, "signif_99": signif_99, "alpha": alpha}


def _assess_wwz(
    source_id: str,
    source_label: str,
    aligned: pd.DataFrame,
    wwz: dict,
    *,
    n_surrogates: int,
    rng: np.random.Generator,
    parallel: bool,
    workers: int,
) -> tuple[list[dict], dict]:
    period = np.asarray(wwz["period_axis"], dtype=float)
    global_wwz = np.asarray(wwz["global_wwz"], dtype=float)
    period_plot, peaks = _candidate_peaks(period, global_wwz, float(wwz["period_min"]), float(wwz["period_max"]))
    if len(peaks) == 0:
        return [], {"period": period, "q95": np.full_like(period, np.nan), "q99": np.full_like(period, np.nan)}

    t = aligned["mjd"].to_numpy(dtype=float)
    y = aligned["wcda_flux_excess"].to_numpy(dtype=float)
    yerr = aligned["wcda_flux_excess_err"].to_numpy(dtype=float)
    y_mean = float(np.nanmean(y))
    y_std = float(np.nanstd(y, ddof=1))
    alpha = _lag1_autocorr(standardize_flux(y))
    alpha = float(np.clip(alpha, -0.95, 0.95))

    candidate_periods = [float(period_plot[idx]) for idx in peaks]
    observed_local_max = []
    local_windows = []
    for peak_period in candidate_periods:
        window_min = peak_period * (1.0 - WWZ_LOCAL_WINDOW_FRACTION)
        window_max = peak_period * (1.0 + WWZ_LOCAL_WINDOW_FRACTION)
        mask = np.isfinite(period) & (period >= window_min) & (period <= window_max)
        if not np.any(mask):
            nearest = int(np.nanargmin(np.abs(period - peak_period)))
            mask = np.zeros_like(period, dtype=bool)
            mask[nearest] = True
        observed_local_max.append(float(np.nanmax(global_wwz[mask])))
        local_windows.append((window_min, window_max, mask))

    sim_seeds = rng.integers(0, np.iinfo(np.uint32).max, size=n_surrogates, dtype=np.uint32)
    tasks = [
        (
            int(sim_seed),
            t,
            yerr,
            len(y),
            alpha,
            y_mean,
            y_std,
            float(wwz["period_min"]),
            float(wwz["period_max"]),
            int(wwz["time_divisions"]),
            float(wwz["decay_constant"]),
            float(wwz["freq_step_factor"]),
            parallel,
        )
        for sim_seed in sim_seeds
    ]
    if workers > 1 and n_surrogates > 1:
        with mp.Pool(processes=int(workers)) as pool:
            surrogate_global = np.vstack(pool.map(_run_wwz_surrogate_global, tasks))
    else:
        surrogate_global = np.vstack([_run_wwz_surrogate_global(task) for task in tasks])

    surrogate_local_max = np.empty((n_surrogates, len(candidate_periods)), dtype=float)
    for sim_idx, sim_global in enumerate(surrogate_global):
        for peak_idx, (_window_min, _window_max, mask) in enumerate(local_windows):
            surrogate_local_max[sim_idx, peak_idx] = float(np.nanmax(sim_global[mask]))
    surrogate_global_max = np.nanmax(surrogate_global, axis=1)

    q95 = np.nanpercentile(surrogate_global, 95, axis=0)
    q99 = np.nanpercentile(surrogate_global, 99, axis=0)
    t_span = _time_span(aligned)
    rows: list[dict] = []
    for peak_idx, peak_period in enumerate(candidate_periods):
        exceed_count = int(np.count_nonzero(surrogate_local_max[:, peak_idx] >= observed_local_max[peak_idx]))
        local_fap = (exceed_count + 1.0) / (n_surrogates + 1.0)
        global_exceed_count = int(np.count_nonzero(surrogate_global_max >= observed_local_max[peak_idx]))
        global_fap = (global_exceed_count + 1.0) / (n_surrogates + 1.0)
        window_min, window_max, _mask = local_windows[peak_idx]
        source_idx = int(np.nanargmin(np.abs(period - peak_period)))
        rows.append(
            {
                "source_id": source_id,
                "source": source_label,
                "series": "wcda_weekly",
                "method": "WWZ",
                "period_days": peak_period,
                "cycles": t_span / peak_period,
                "observed_statistic": observed_local_max[peak_idx],
                "statistic_name": "Local-window max global WWZ",
                "null_model": "AR(1) Gaussian surrogate on same weekly sampling",
                "local_fap": local_fap,
                "global_fap": global_fap,
                "local_confidence": 1.0 - local_fap,
                "global_confidence": 1.0 - global_fap,
                "reference_95": float(q95[source_idx]),
                "reference_99": float(q99[source_idx]),
                "above_95": bool(observed_local_max[peak_idx] >= q95[source_idx]),
                "above_99": bool(observed_local_max[peak_idx] >= q99[source_idx]),
                "n_surrogates": n_surrogates,
                "exceed_count": exceed_count,
                "global_exceed_count": global_exceed_count,
                "local_window_min_days": window_min,
                "local_window_max_days": window_max,
                "ar1_alpha": alpha,
                "note": _candidate_note(peak_period, t_span, float(wwz["period_min"]), float(wwz["period_max"])),
            }
        )

    return rows, {"period": period, "q95": q95, "q99": q99, "alpha": alpha}


def _lag1_autocorr(y: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    y = y[np.isfinite(y)]
    if len(y) < 3:
        return 0.0
    y0 = y[:-1] - np.nanmean(y[:-1])
    y1 = y[1:] - np.nanmean(y[1:])
    denom = float(np.sqrt(np.sum(y0 * y0) * np.sum(y1 * y1)))
    if denom <= 0 or not np.isfinite(denom):
        return 0.0
    return float(np.clip(np.sum(y0 * y1) / denom, -0.95, 0.95))


def _simulate_ar1(n: int, alpha: float, mean: float, std: float, rng: np.random.Generator) -> np.ndarray:
    if n < 1:
        return np.array([], dtype=float)
    innovation_std = np.sqrt(max(1.0 - alpha**2, 1e-8))
    x = np.empty(n, dtype=float)
    x[0] = rng.normal()
    for idx in range(1, n):
        x[idx] = alpha * x[idx - 1] + innovation_std * rng.normal()
    x = (x - np.mean(x)) / np.std(x, ddof=1)
    return mean + std * x


def _run_wwz_surrogate_global(task: tuple) -> np.ndarray:
    (
        seed,
        t,
        yerr,
        n,
        alpha,
        y_mean,
        y_std,
        period_min,
        period_max,
        time_divisions,
        decay_constant,
        freq_step_factor,
        parallel,
    ) = task
    rng = np.random.default_rng(seed)
    sim_y = _simulate_ar1(n, alpha, y_mean, y_std, rng)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        sim = run_wwz(
            t,
            sim_y,
            yerr,
            period_min=period_min,
            period_max=period_max,
            time_divisions=time_divisions,
            decay_constant=decay_constant,
            freq_step_factor=freq_step_factor,
            parallel=parallel,
        )
    return np.asarray(sim["global_wwz"], dtype=float)


def _time_span(aligned: pd.DataFrame) -> float:
    t = aligned["mjd"].to_numpy(dtype=float)
    return float(np.nanmax(t) - np.nanmin(t))


def _candidate_note(period: float, t_span: float, period_min: float, period_max: float) -> str:
    notes = ["Quick-look candidate peak; no source/method/survey trial correction."]
    cycles = t_span / period if period > 0 else np.nan
    if np.isfinite(cycles) and cycles < 4.0:
        notes.append("Fewer than four observed cycles.")
    boundary_fraction = 0.02
    if period <= period_min * (1.0 + boundary_fraction) or period >= period_max * (1.0 - boundary_fraction):
        notes.append("Near search boundary; treat cautiously.")
    return " ".join(notes)


def _plot_cwt_global_significance(path: Path, source_label: str, cwt: dict, rows: list[dict], refs: dict) -> None:
    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    mask = (
        np.isfinite(period)
        & np.isfinite(gws)
        & (period >= float(cwt["period_min"]))
        & (period <= float(cwt["period_max"]))
    )
    order = np.argsort(period[mask])
    period_plot = period[mask][order]
    gws_plot = gws[mask][order]
    sig95 = np.asarray(refs["signif_95"], dtype=float)[mask][order]
    sig99 = np.asarray(refs["signif_99"], dtype=float)[mask][order]

    fig, ax = plt.subplots(figsize=(8.5, 4.4), constrained_layout=True)
    ax.plot(period_plot, gws_plot, color="black", lw=1.5, label="Observed GWS")
    ax.plot(period_plot, sig95, color="#255c99", lw=1.1, ls="-.", label="AR(1) 95% local reference")
    ax.plot(period_plot, sig99, color="#7a3e9d", lw=1.1, ls=":", label="AR(1) 99% local reference")
    _draw_peak_markers(ax, rows)
    ax.set_xscale("log")
    ax.set_xlim(float(cwt["period_min"]), float(cwt["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Global wavelet spectrum")
    ax.set_title(f"{source_label} WCDA weekly CWT local significance")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    ax.text(
        0.01,
        0.02,
        f"AR(1) alpha = {float(refs['alpha']):.3f}; theory reference only, no trial correction",
        transform=ax.transAxes,
        fontsize=8,
        color="#5f6c7b",
    )
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def _plot_wwz_global_significance(path: Path, source_label: str, wwz: dict, rows: list[dict], refs: dict) -> None:
    period = np.asarray(wwz["period_axis"], dtype=float)
    global_wwz = np.asarray(wwz["global_wwz"], dtype=float)
    mask = (
        np.isfinite(period)
        & np.isfinite(global_wwz)
        & (period >= float(wwz["period_min"]))
        & (period <= float(wwz["period_max"]))
    )
    order = np.argsort(period[mask])
    period_plot = period[mask][order]
    wwz_plot = global_wwz[mask][order]
    q95 = np.asarray(refs["q95"], dtype=float)[mask][order]
    q99 = np.asarray(refs["q99"], dtype=float)[mask][order]

    fig, ax = plt.subplots(figsize=(8.5, 4.4), constrained_layout=True)
    ax.plot(period_plot, wwz_plot, color="black", lw=1.5, label="Observed global WWZ")
    ax.plot(period_plot, q95, color="#255c99", lw=1.1, ls="-.", label="Surrogate 95% pointwise reference")
    ax.plot(period_plot, q99, color="#7a3e9d", lw=1.1, ls=":", label="Surrogate 99% pointwise reference")
    _draw_peak_markers(ax, rows, show_fap=True)
    ax.set_xscale("log")
    ax.set_xlim(float(wwz["period_min"]), float(wwz["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Mean WWZ")
    ax.set_title(f"{source_label} WCDA weekly WWZ local significance")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    n_surrogates = int(rows[0]["n_surrogates"]) if rows else 0
    ax.text(
        0.01,
        0.02,
        f"AR(1) surrogate N = {n_surrogates}; local/global FAP, no trial correction",
        transform=ax.transAxes,
        fontsize=8,
        color="#5f6c7b",
    )
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def _draw_peak_markers(ax: plt.Axes, rows: list[dict], *, show_fap: bool = False) -> None:
    if not rows:
        return
    y_min, y_max = ax.get_ylim()
    y_text = y_min + 0.88 * (y_max - y_min)
    for idx, row in enumerate(rows):
        period = float(row["period_days"])
        ax.axvline(period, color="red", ls="--", lw=1.1, alpha=0.9)
        label = f"{period:.1f} d"
        if show_fap and np.isfinite(row["local_fap"]):
            label += f"\npl={float(row['local_fap']):.3f}"
            if np.isfinite(row.get("global_fap", np.nan)):
                label += f"\npg={float(row['global_fap']):.3f}"
        ax.text(
            period,
            y_text,
            label,
            color="red",
            fontsize=8,
            rotation=90,
            ha="right",
            va="top",
        )
        y_text = y_min + (0.88 - 0.10 * ((idx + 1) % 3)) * (y_max - y_min)


if __name__ == "__main__":
    main()
