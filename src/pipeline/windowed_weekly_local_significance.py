#!/usr/bin/env python3
"""Run fixed-window WCDA weekly local-significance checks."""

from __future__ import annotations

import argparse
import contextlib
import io
import multiprocessing as mp
import os
import sys
import time
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

from methods.periodicity import run_cwt, run_wwz, standardize_flux  # noqa: E402
from utils.project_paths import ALIGNED_DIR, PERIODICITY_DIR, PROJECT_ROOT  # noqa: E402
from utils.source_registry import SOURCE_REGISTRY, get_source  # noqa: E402


DEFAULT_SOURCE_ID = "mkn421"
DEFAULT_START_MJD = 59500.0
DEFAULT_END_MJD = 60500.0
DEFAULT_N_SURROGATES = 1000
DEFAULT_SEED = 4215950060500
DEFAULT_PERIOD_MIN = 50.0
DEFAULT_PERIOD_MAX = 600.0
DEFAULT_TARGET_PERIOD_DAYS = 140.0
DEFAULT_TARGET_WINDOW_FRACTION = 0.10
DEFAULT_WWZ_TIME_DIVISIONS = 80
DEFAULT_WWZ_FREQ_STEP_FACTOR = 0.5
WWZ_LOCAL_WINDOW_FRACTION = 0.10
FIG_DPI = 180
PROGRESS_EVERY = 50
GLOBAL_PEAK_PROMINENCE_FRACTION = 0.05
GLOBAL_PEAK_MIN_DISTANCE_BINS = 2
TARGET_COLOR = "#f59e0b"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", choices=sorted(SOURCE_REGISTRY), default=DEFAULT_SOURCE_ID)
    parser.add_argument("--start-mjd", type=float, default=DEFAULT_START_MJD)
    parser.add_argument("--end-mjd", type=float, default=DEFAULT_END_MJD)
    parser.add_argument("--n-surrogates", type=int, default=DEFAULT_N_SURROGATES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--period-min", type=float, default=DEFAULT_PERIOD_MIN)
    parser.add_argument("--period-max", type=float, default=DEFAULT_PERIOD_MAX)
    parser.add_argument("--target-period-days", type=float, default=DEFAULT_TARGET_PERIOD_DAYS)
    parser.add_argument("--target-window-fraction", type=float, default=DEFAULT_TARGET_WINDOW_FRACTION)
    parser.add_argument("--wwz-time-divisions", type=int, default=DEFAULT_WWZ_TIME_DIVISIONS)
    parser.add_argument("--wwz-freq-step-factor", type=float, default=DEFAULT_WWZ_FREQ_STEP_FACTOR)
    parser.add_argument("--wwz-parallel", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.start_mjd >= args.end_mjd:
        raise ValueError("--start-mjd must be smaller than --end-mjd.")
    if args.n_surrogates < 1:
        raise ValueError("--n-surrogates must be positive.")
    if args.period_min >= args.period_max:
        raise ValueError("--period-min must be smaller than --period-max.")
    if args.target_period_days <= 0:
        raise ValueError("--target-period-days must be positive.")
    if not (0 < args.target_window_fraction < 1):
        raise ValueError("--target-window-fraction must be between 0 and 1.")

    run_window(
        source_id=args.source_id,
        start_mjd=args.start_mjd,
        end_mjd=args.end_mjd,
        n_surrogates=args.n_surrogates,
        seed=args.seed,
        workers=args.workers,
        period_min=args.period_min,
        period_max=args.period_max,
        target_period_days=args.target_period_days,
        target_window_fraction=args.target_window_fraction,
        wwz_time_divisions=args.wwz_time_divisions,
        wwz_freq_step_factor=args.wwz_freq_step_factor,
        wwz_parallel=args.wwz_parallel,
    )


def run_window(
    *,
    source_id: str,
    start_mjd: float,
    end_mjd: float,
    n_surrogates: int,
    seed: int,
    workers: int,
    period_min: float,
    period_max: float,
    target_period_days: float,
    target_window_fraction: float,
    wwz_time_divisions: int,
    wwz_freq_step_factor: float,
    wwz_parallel: bool,
) -> None:
    source = get_source(source_id)
    window_key = _window_key(start_mjd, end_mjd)
    aligned_out_dir = ALIGNED_DIR / source_id / "windows" / window_key
    periodicity_out_dir = PERIODICITY_DIR / source_id / "windows" / window_key
    aligned_out_dir.mkdir(parents=True, exist_ok=True)
    periodicity_out_dir.mkdir(parents=True, exist_ok=True)

    aligned = _load_weekly_light_curve(source.expected_aligned_week_path())
    window_lc = _slice_window(aligned, start_mjd, end_mjd)
    if len(window_lc) < 4:
        raise ValueError(f"{source_id} MJD {start_mjd:g}-{end_mjd:g} has fewer than four usable weekly points.")

    window_aligned_path = aligned_out_dir / "wcda_weekly_aligned.csv"
    window_lc.to_csv(window_aligned_path, index=False)

    t = window_lc["mjd"].to_numpy(dtype=float)
    y = window_lc["wcda_flux_excess"].to_numpy(dtype=float)
    yerr = window_lc["wcda_flux_excess_err"].to_numpy(dtype=float)

    cwt = run_cwt(t, y, period_min=period_min, period_max=period_max)
    wwz = run_wwz(
        t,
        y,
        yerr,
        period_min=period_min,
        period_max=period_max,
        time_divisions=wwz_time_divisions,
        freq_step_factor=wwz_freq_step_factor,
        parallel=wwz_parallel,
    )
    _save_cwt(periodicity_out_dir / "wcda_weekly_window_cwt.npz", cwt)
    _save_wwz(periodicity_out_dir / "wcda_weekly_window_wwz.npz", wwz)

    cwt_row, cwt_refs = _assess_cwt(source_id, source.label, window_lc, cwt, start_mjd, end_mjd)
    cwt_target_row = _assess_cwt_target(
        source_id,
        source.label,
        window_lc,
        cwt,
        cwt_refs,
        start_mjd,
        end_mjd,
        target_period_days=target_period_days,
        target_window_fraction=target_window_fraction,
    )
    wwz_rows, wwz_refs = _assess_wwz(
        source_id,
        source.label,
        window_lc,
        wwz,
        start_mjd,
        end_mjd,
        n_surrogates=n_surrogates,
        seed=seed,
        workers=workers,
        parallel=wwz_parallel,
        target_period_days=target_period_days,
        target_window_fraction=target_window_fraction,
    )
    wwz_row, wwz_target_row = wwz_rows
    _save_wwz_refs(periodicity_out_dir / "wcda_weekly_window_wwz_significance_refs.npz", wwz_refs, n_surrogates)

    summary = _summary_row(
        source_id,
        source.label,
        window_lc,
        cwt_row,
        wwz_row,
        cwt_target_row,
        wwz_target_row,
        start_mjd,
        end_mjd,
        period_min,
        period_max,
        target_period_days,
        target_window_fraction,
    )
    pd.DataFrame([summary]).to_csv(periodicity_out_dir / "wcda_weekly_window_summary.csv", index=False)
    pd.DataFrame([cwt_row, wwz_row, cwt_target_row, wwz_target_row]).to_csv(
        periodicity_out_dir / "wcda_weekly_window_local_significance.csv",
        index=False,
    )

    _plot_periodicity(
        periodicity_out_dir / "wcda_weekly_window_periodicity.png",
        source.label,
        window_lc,
        cwt,
        wwz,
        cwt_row,
        wwz_row,
        cwt_target_row,
        wwz_target_row,
    )
    _plot_cwt_significance(
        periodicity_out_dir / "wcda_weekly_window_cwt_global_significance.png",
        source.label,
        cwt,
        cwt_row,
        cwt_refs,
        cwt_target_row,
    )
    _plot_wwz_significance(
        periodicity_out_dir / "wcda_weekly_window_wwz_local_significance.png",
        source.label,
        wwz,
        wwz_row,
        wwz_refs,
        wwz_target_row,
    )

    print(f"[OK] wrote window aligned CSV -> {window_aligned_path.relative_to(PROJECT_ROOT)}")
    print(f"[OK] wrote window periodicity products -> {periodicity_out_dir.relative_to(PROJECT_ROOT)}")
    print(pd.DataFrame([summary]).to_string(index=False))
    print(pd.DataFrame([cwt_row, wwz_row, cwt_target_row, wwz_target_row]).to_string(index=False))


def _window_key(start_mjd: float, end_mjd: float) -> str:
    return f"{start_mjd:g}_{end_mjd:g}".replace(".", "p")


def _load_weekly_light_curve(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing aligned weekly light curve: {path}")
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


def _slice_window(aligned: pd.DataFrame, start_mjd: float, end_mjd: float) -> pd.DataFrame:
    mask = (aligned["mjd"] >= start_mjd) & (aligned["mjd"] <= end_mjd)
    return aligned.loc[mask].sort_values("mjd").reset_index(drop=True)


def _assess_cwt(
    source_id: str,
    source_label: str,
    aligned: pd.DataFrame,
    cwt: dict,
    start_mjd: float,
    end_mjd: float,
) -> tuple[dict, dict]:
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
    valid = _period_mask(period, gws, float(cwt["period_min"]), float(cwt["period_max"]))
    peak_idx = int(np.nanargmax(np.where(valid, gws, np.nan)))
    t_span = _time_span(aligned)
    peak_period = float(period[peak_idx])
    row = _base_row(source_id, source_label, aligned, start_mjd, end_mjd)
    row.update(
        {
            "method": "CWT",
            "target_type": "window strongest peak",
            "period_days": peak_period,
            "cycles": t_span / peak_period,
            "observed_statistic": float(gws[peak_idx]),
            "statistic_name": "Global wavelet spectrum",
            "null_model": "AR(1) red noise via PyCWT time-averaged significance",
            "local_fap": np.nan,
            "local_confidence": np.nan,
            "reference_95": float(signif_95[peak_idx]),
            "reference_99": float(signif_99[peak_idx]),
            "above_95": bool(gws[peak_idx] >= signif_95[peak_idx]),
            "above_99": bool(gws[peak_idx] >= signif_99[peak_idx]),
            "n_surrogates": 0,
            "exceed_count": 0,
            "local_window_min_days": np.nan,
            "local_window_max_days": np.nan,
            "ar1_alpha": alpha,
            "note": _candidate_note(peak_period, t_span, float(cwt["period_min"]), float(cwt["period_max"])),
        }
    )
    return row, {"period": period, "signif_95": signif_95, "signif_99": signif_99, "alpha": alpha}


def _assess_cwt_target(
    source_id: str,
    source_label: str,
    aligned: pd.DataFrame,
    cwt: dict,
    refs: dict,
    start_mjd: float,
    end_mjd: float,
    *,
    target_period_days: float,
    target_window_fraction: float,
) -> dict:
    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    valid = _period_mask(period, gws, float(cwt["period_min"]), float(cwt["period_max"]))
    target_min, target_max, target_mask = _target_period_mask(
        period,
        valid,
        float(cwt["period_min"]),
        float(cwt["period_max"]),
        target_period_days,
        target_window_fraction,
    )
    target_peak_idx = int(np.nanargmax(np.where(target_mask, gws, np.nan)))
    peak_period = float(period[target_peak_idx])
    t_span = _time_span(aligned)
    signif_95 = np.asarray(refs["signif_95"], dtype=float)
    signif_99 = np.asarray(refs["signif_99"], dtype=float)

    row = _base_row(source_id, source_label, aligned, start_mjd, end_mjd)
    row.update(
        {
            "method": "CWT",
            "target_type": f"pre-specified {target_period_days:g} d band",
            "period_days": peak_period,
            "cycles": t_span / peak_period,
            "observed_statistic": float(gws[target_peak_idx]),
            "statistic_name": "Target-band max global wavelet spectrum",
            "null_model": "AR(1) red noise via PyCWT time-averaged significance",
            "local_fap": np.nan,
            "local_confidence": np.nan,
            "reference_95": float(signif_95[target_peak_idx]),
            "reference_99": float(signif_99[target_peak_idx]),
            "above_95": bool(gws[target_peak_idx] >= signif_95[target_peak_idx]),
            "above_99": bool(gws[target_peak_idx] >= signif_99[target_peak_idx]),
            "n_surrogates": 0,
            "exceed_count": 0,
            "local_window_min_days": float(target_min),
            "local_window_max_days": float(target_max),
            "ar1_alpha": float(refs["alpha"]),
            "note": _candidate_note(peak_period, t_span, float(cwt["period_min"]), float(cwt["period_max"]))
            + f" Targeted check for pre-specified {target_period_days:g} d band.",
        }
    )
    return row


def _assess_wwz(
    source_id: str,
    source_label: str,
    aligned: pd.DataFrame,
    wwz: dict,
    start_mjd: float,
    end_mjd: float,
    *,
    n_surrogates: int,
    seed: int,
    workers: int,
    parallel: bool,
    target_period_days: float,
    target_window_fraction: float,
) -> tuple[tuple[dict, dict], dict]:
    period = np.asarray(wwz["period_axis"], dtype=float)
    global_wwz = np.asarray(wwz["global_wwz"], dtype=float)
    valid = _period_mask(period, global_wwz, float(wwz["period_min"]), float(wwz["period_max"]))
    peak_idx = int(np.nanargmax(np.where(valid, global_wwz, np.nan)))
    peak_period = float(period[peak_idx])
    window_min = max(float(wwz["period_min"]), peak_period * (1.0 - WWZ_LOCAL_WINDOW_FRACTION))
    window_max = min(float(wwz["period_max"]), peak_period * (1.0 + WWZ_LOCAL_WINDOW_FRACTION))
    local_mask = valid & (period >= window_min) & (period <= window_max)
    if not np.any(local_mask):
        local_mask = np.zeros_like(period, dtype=bool)
        local_mask[peak_idx] = True
        window_min = window_max = peak_period
    local_peak_idx = int(np.nanargmax(np.where(local_mask, global_wwz, np.nan)))
    observed_local_max = float(global_wwz[local_peak_idx])

    t = aligned["mjd"].to_numpy(dtype=float)
    y = aligned["wcda_flux_excess"].to_numpy(dtype=float)
    yerr = aligned["wcda_flux_excess_err"].to_numpy(dtype=float)
    y_mean = float(np.nanmean(y))
    y_std = float(np.nanstd(y, ddof=1))
    alpha = float(np.clip(_lag1_autocorr(standardize_flux(y)), -0.95, 0.95))

    rng = np.random.default_rng(seed)
    sim_seeds = rng.integers(0, np.iinfo(np.uint32).max, size=n_surrogates, dtype=np.uint32)
    freq_step_factor = float(wwz.get("freq_step_factor", float(wwz["freq_step"]) * float(wwz["t_span"])))
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
            freq_step_factor,
            parallel,
        )
        for sim_seed in sim_seeds
    ]
    surrogate_global = _run_surrogate_globals(tasks, workers=workers)

    surrogate_local_max = np.nanmax(surrogate_global[:, local_mask], axis=1)
    exceed_count = int(np.count_nonzero(surrogate_local_max >= observed_local_max))
    local_fap = (exceed_count + 1.0) / (n_surrogates + 1.0)

    target_min, target_max, target_mask = _target_period_mask(
        period,
        valid,
        float(wwz["period_min"]),
        float(wwz["period_max"]),
        target_period_days,
        target_window_fraction,
    )
    target_peak_idx = int(np.nanargmax(np.where(target_mask, global_wwz, np.nan)))
    observed_target_max = float(global_wwz[target_peak_idx])
    surrogate_target_max = np.nanmax(surrogate_global[:, target_mask], axis=1)
    target_exceed_count = int(np.count_nonzero(surrogate_target_max >= observed_target_max))
    target_local_fap = (target_exceed_count + 1.0) / (n_surrogates + 1.0)

    q95 = np.nanpercentile(surrogate_global, 95, axis=0)
    q99 = np.nanpercentile(surrogate_global, 99, axis=0)

    t_span = _time_span(aligned)
    row = _base_row(source_id, source_label, aligned, start_mjd, end_mjd)
    row.update(
        {
            "method": "WWZ",
            "target_type": "window strongest peak",
            "period_days": peak_period,
            "cycles": t_span / peak_period,
            "observed_statistic": observed_local_max,
            "statistic_name": "Local-window max global WWZ",
            "null_model": "AR(1) Gaussian surrogate on same weekly sampling",
            "local_fap": float(local_fap),
            "local_confidence": float(1.0 - local_fap),
            "reference_95": float(q95[local_peak_idx]),
            "reference_99": float(q99[local_peak_idx]),
            "above_95": bool(observed_local_max >= q95[local_peak_idx]),
            "above_99": bool(observed_local_max >= q99[local_peak_idx]),
            "n_surrogates": int(n_surrogates),
            "exceed_count": exceed_count,
            "local_window_min_days": float(window_min),
            "local_window_max_days": float(window_max),
            "ar1_alpha": alpha,
            "note": _candidate_note(peak_period, t_span, float(wwz["period_min"]), float(wwz["period_max"])),
        }
    )

    target_row = _base_row(source_id, source_label, aligned, start_mjd, end_mjd)
    target_period = float(period[target_peak_idx])
    target_row.update(
        {
            "method": "WWZ",
            "target_type": f"pre-specified {target_period_days:g} d band",
            "period_days": target_period,
            "cycles": t_span / target_period,
            "observed_statistic": observed_target_max,
            "statistic_name": "Target-band max global WWZ",
            "null_model": "AR(1) Gaussian surrogate on same weekly sampling",
            "local_fap": float(target_local_fap),
            "local_confidence": float(1.0 - target_local_fap),
            "reference_95": float(q95[target_peak_idx]),
            "reference_99": float(q99[target_peak_idx]),
            "above_95": bool(observed_target_max >= q95[target_peak_idx]),
            "above_99": bool(observed_target_max >= q99[target_peak_idx]),
            "n_surrogates": int(n_surrogates),
            "exceed_count": target_exceed_count,
            "local_window_min_days": float(target_min),
            "local_window_max_days": float(target_max),
            "ar1_alpha": alpha,
            "note": _candidate_note(target_period, t_span, float(wwz["period_min"]), float(wwz["period_max"]))
            + f" Targeted check for pre-specified {target_period_days:g} d band.",
        }
    )
    return (
        row,
        target_row,
    ), {
        "period": period,
        "q95": q95,
        "q99": q99,
        "alpha": alpha,
        "surrogate_global": surrogate_global,
    }


def _base_row(
    source_id: str,
    source_label: str,
    aligned: pd.DataFrame,
    start_mjd: float,
    end_mjd: float,
) -> dict:
    t = aligned["mjd"].to_numpy(dtype=float)
    return {
        "source_id": source_id,
        "source": source_label,
        "series": "wcda_weekly_window",
        "requested_start_mjd": float(start_mjd),
        "requested_end_mjd": float(end_mjd),
        "actual_start_mjd": float(np.nanmin(t)),
        "actual_end_mjd": float(np.nanmax(t)),
        "n_points": int(len(aligned)),
        "median_dt_days": float(np.nanmedian(np.diff(t))) if len(t) > 1 else np.nan,
    }


def _summary_row(
    source_id: str,
    source_label: str,
    aligned: pd.DataFrame,
    cwt_row: dict,
    wwz_row: dict,
    cwt_target_row: dict,
    wwz_target_row: dict,
    start_mjd: float,
    end_mjd: float,
    period_min: float,
    period_max: float,
    target_period_days: float,
    target_window_fraction: float,
) -> dict:
    base = _base_row(source_id, source_label, aligned, start_mjd, end_mjd)
    base.update(
        {
            "period_min_days": float(period_min),
            "period_max_days": float(period_max),
            "target_period_days": float(target_period_days),
            "target_window_fraction": float(target_window_fraction),
            "cwt_peak_period_days": float(cwt_row["period_days"]),
            "cwt_peak_gws": float(cwt_row["observed_statistic"]),
            "cwt_reference_95": float(cwt_row["reference_95"]),
            "cwt_reference_99": float(cwt_row["reference_99"]),
            "cwt_above_95": bool(cwt_row["above_95"]),
            "cwt_above_99": bool(cwt_row["above_99"]),
            "cwt_target_period_days": float(cwt_target_row["period_days"]),
            "cwt_target_gws": float(cwt_target_row["observed_statistic"]),
            "cwt_target_reference_95": float(cwt_target_row["reference_95"]),
            "cwt_target_reference_99": float(cwt_target_row["reference_99"]),
            "cwt_target_above_95": bool(cwt_target_row["above_95"]),
            "cwt_target_above_99": bool(cwt_target_row["above_99"]),
            "wwz_peak_period_days": float(wwz_row["period_days"]),
            "wwz_peak_power": float(wwz_row["observed_statistic"]),
            "wwz_local_fap": float(wwz_row["local_fap"]),
            "wwz_reference_95": float(wwz_row["reference_95"]),
            "wwz_reference_99": float(wwz_row["reference_99"]),
            "wwz_above_95": bool(wwz_row["above_95"]),
            "wwz_above_99": bool(wwz_row["above_99"]),
            "wwz_target_period_days": float(wwz_target_row["period_days"]),
            "wwz_target_power": float(wwz_target_row["observed_statistic"]),
            "wwz_target_local_fap": float(wwz_target_row["local_fap"]),
            "wwz_target_reference_95": float(wwz_target_row["reference_95"]),
            "wwz_target_reference_99": float(wwz_target_row["reference_99"]),
            "wwz_target_above_95": bool(wwz_target_row["above_95"]),
            "wwz_target_above_99": bool(wwz_target_row["above_99"]),
            "n_surrogates": int(wwz_row["n_surrogates"]),
            "seed_note": "WWZ AR(1) surrogate seed is stored in the command invocation/log.",
        }
    )
    return base


def _period_mask(period: np.ndarray, power: np.ndarray, period_min: float, period_max: float) -> np.ndarray:
    return np.isfinite(period) & np.isfinite(power) & (period >= period_min) & (period <= period_max)


def _target_period_mask(
    period: np.ndarray,
    valid: np.ndarray,
    period_min: float,
    period_max: float,
    target_period_days: float,
    target_window_fraction: float,
) -> tuple[float, float, np.ndarray]:
    target_min = max(period_min, target_period_days * (1.0 - target_window_fraction))
    target_max = min(period_max, target_period_days * (1.0 + target_window_fraction))
    target_mask = valid & (period >= target_min) & (period <= target_max)
    if not np.any(target_mask):
        nearest_idx = int(np.nanargmin(np.abs(period - target_period_days)))
        target_mask = np.zeros_like(period, dtype=bool)
        target_mask[nearest_idx] = bool(valid[nearest_idx])
        target_min = target_max = float(period[nearest_idx])
    if not np.any(target_mask):
        raise ValueError(
            f"No valid period grid point found in target band {target_min:.3f}-{target_max:.3f} d."
        )
    return float(target_min), float(target_max), target_mask


def _save_cwt(path: Path, result: dict) -> None:
    np.savez_compressed(
        path,
        t_mjd=result["t_mjd"],
        dt=result["dt"],
        dj=result["dj"],
        s0=result["s0"],
        J=result["J"],
        power=result["power"],
        period=result["period"],
        coi=result["coi"],
        gws=result["gws"],
        mask_period=result["mask_period"],
        period_min=result["period_min"],
        period_max=result["period_max"],
    )


def _save_wwz(path: Path, result: dict) -> None:
    np.savez_compressed(
        path,
        t=result["t"],
        y=result["y"],
        yerr=result["yerr"],
        tau_mat=result["tau_mat"],
        freq_mat=result["freq_mat"],
        period_mat=result["period_mat"],
        wwz_mat=result["wwz_mat"],
        amp_mat=result["amp_mat"],
        coef_mat=result["coef_mat"],
        neff_mat=result["neff_mat"],
        ridge_tau=result["ridge_tau"],
        ridge_period=result["ridge_period"],
        ridge_power=result["ridge_power"],
        global_wwz=result["global_wwz"],
        period_axis=result["period_axis"],
        period_min=result["period_min"],
        period_max=result["period_max"],
        freq_low=result["freq_low"],
        freq_high=result["freq_high"],
        freq_step=result["freq_step"],
        time_divisions=result["time_divisions"],
        decay_constant=result["decay_constant"],
        freq_step_factor=result["freq_step"] * result["t_span"],
    )


def _save_wwz_refs(path: Path, refs: dict, n_surrogates: int) -> None:
    np.savez_compressed(
        path,
        period=np.asarray(refs["period"], dtype=float),
        q95=np.asarray(refs["q95"], dtype=float),
        q99=np.asarray(refs["q99"], dtype=float),
        alpha=float(refs["alpha"]),
        surrogate_global=np.asarray(refs["surrogate_global"], dtype=np.float32),
        n_surrogates=int(n_surrogates),
        null_model="AR(1) Gaussian surrogate on same weekly sampling",
    )


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


def _run_surrogate_globals(tasks: list[tuple], *, workers: int) -> np.ndarray:
    n_tasks = len(tasks)
    started = time.monotonic()
    if workers > 1 and n_tasks > 1:
        results = []
        with mp.Pool(processes=int(workers)) as pool:
            for done, result in enumerate(pool.imap_unordered(_run_wwz_surrogate_global, tasks, chunksize=1), start=1):
                results.append(result)
                if done == 1 or done % PROGRESS_EVERY == 0 or done == n_tasks:
                    elapsed = time.monotonic() - started
                    rate = done / elapsed if elapsed > 0 else float("nan")
                    remaining = (n_tasks - done) / rate if rate and np.isfinite(rate) else float("nan")
                    print(
                        f"[progress] WWZ surrogates {done}/{n_tasks} "
                        f"elapsed={elapsed/60:.1f} min eta={remaining/60:.1f} min",
                        flush=True,
                    )
        return np.vstack(results)

    results = []
    for done, task in enumerate(tasks, start=1):
        results.append(_run_wwz_surrogate_global(task))
        if done == 1 or done % PROGRESS_EVERY == 0 or done == n_tasks:
            elapsed = time.monotonic() - started
            rate = done / elapsed if elapsed > 0 else float("nan")
            remaining = (n_tasks - done) / rate if rate and np.isfinite(rate) else float("nan")
            print(
                f"[progress] WWZ surrogates {done}/{n_tasks} "
                f"elapsed={elapsed/60:.1f} min eta={remaining/60:.1f} min",
                flush=True,
            )
    return np.vstack(results)


def _time_span(aligned: pd.DataFrame) -> float:
    t = aligned["mjd"].to_numpy(dtype=float)
    return float(np.nanmax(t) - np.nanmin(t))


def _candidate_note(period: float, t_span: float, period_min: float, period_max: float) -> str:
    notes = ["Fixed-window local-only result; no window-search, source, method, or period-search trial correction."]
    cycles = t_span / period if period > 0 else np.nan
    if np.isfinite(cycles) and cycles < 4.0:
        notes.append("Fewer than four observed cycles; treat as candidate/hint, not robust QPO detection.")
    boundary_fraction = 0.02
    if period <= period_min * (1.0 + boundary_fraction) or period >= period_max * (1.0 - boundary_fraction):
        notes.append("Near search boundary; treat cautiously.")
    return " ".join(notes)


def _plot_periodicity(
    path: Path,
    source_label: str,
    aligned: pd.DataFrame,
    cwt: dict,
    wwz: dict,
    cwt_row: dict,
    wwz_row: dict,
    cwt_target_row: dict,
    wwz_target_row: dict,
) -> None:
    t = aligned["mjd"].to_numpy(dtype=float)
    y = aligned["wcda_flux_excess"].to_numpy(dtype=float)
    yerr = aligned["wcda_flux_excess_err"].to_numpy(dtype=float)
    cwt_period = np.asarray(cwt["period"], dtype=float)
    cwt_mask = np.asarray(cwt["mask_period"], dtype=bool)
    cwt_t_grid, cwt_p_grid = np.meshgrid(t, cwt_period)

    wwz_tau = np.asarray(wwz["tau_mat"][:, 0], dtype=float)
    wwz_period_mat = np.asarray(wwz["period_mat"], dtype=float)
    wwz_sort_idx = np.argsort(wwz_period_mat[0, :])
    wwz_period_axis = wwz_period_mat[0, wwz_sort_idx]
    wwz_power = np.asarray(wwz["wwz_mat"], dtype=float)[:, wwz_sort_idx]

    fig = plt.figure(figsize=(14, 10.4), constrained_layout=True)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.45, 0.85])
    ax_lc = fig.add_subplot(gs[0, :])
    ax_cwt = fig.add_subplot(gs[1, 0])
    ax_wwz = fig.add_subplot(gs[1, 1])
    ax_cwt_global = fig.add_subplot(gs[2, 0])
    ax_wwz_global = fig.add_subplot(gs[2, 1])

    ax_lc.errorbar(t, y, yerr=yerr, fmt="o", ms=3.0, capsize=2, elinewidth=0.8)
    ax_lc.set_title(f"{source_label} WCDA weekly MJD {float(t.min()):.1f}-{float(t.max()):.1f}")
    ax_lc.set_xlabel("MJD")
    ax_lc.set_ylabel("Excess-rate proxy")
    ax_lc.grid(True, alpha=0.25)

    cwt_im = ax_cwt.contourf(
        cwt_t_grid[cwt_mask, :],
        cwt_p_grid[cwt_mask, :],
        np.asarray(cwt["power"], dtype=float)[cwt_mask, :],
        levels=50,
        cmap="magma",
        extend="both",
    )
    cwt_coi_clip = np.clip(np.asarray(cwt["coi"], dtype=float), float(cwt["period_min"]), float(cwt["period_max"]))
    ax_cwt.fill_between(
        t,
        float(cwt["period_max"]),
        cwt_coi_clip,
        where=cwt_coi_clip <= float(cwt["period_max"]),
        color="white",
        alpha=0.5,
        hatch="/",
        edgecolor="0.7",
        linewidth=0.0,
    )
    ax_cwt.plot(t, cwt_coi_clip, color="white", lw=1.2, label="COI")
    ax_cwt.axhline(float(cwt_row["period_days"]), color="cyan", ls="--", lw=1.1, label="CWT peak")
    ax_cwt.axhspan(
        float(cwt_target_row["local_window_min_days"]),
        float(cwt_target_row["local_window_max_days"]),
        color=TARGET_COLOR,
        alpha=0.12,
        label="140 d target band",
    )
    ax_cwt.axhline(
        float(cwt_target_row["period_days"]),
        color=TARGET_COLOR,
        ls="-.",
        lw=1.1,
        label="target-band peak",
    )
    ax_cwt.set_yscale("log")
    ax_cwt.set_ylim(float(cwt["period_min"]), float(cwt["period_max"]))
    ax_cwt.set_xlabel("MJD")
    ax_cwt.set_ylabel("Period (day)")
    ax_cwt.set_title("CWT Power")
    ax_cwt.legend(loc="upper right", fontsize=8)
    fig.colorbar(cwt_im, ax=ax_cwt, pad=0.02, label="Power")

    wwz_mesh = ax_wwz.pcolormesh(wwz_tau, wwz_period_axis, wwz_power.T, shading="auto", cmap="viridis")
    ax_wwz.plot(wwz["ridge_tau"], wwz["ridge_period"], color="black", lw=1.1, alpha=0.9, label="ridge")
    ax_wwz.axhline(float(wwz_row["period_days"]), color="red", ls="--", lw=1.1, label="WWZ peak")
    ax_wwz.axhspan(
        float(wwz_target_row["local_window_min_days"]),
        float(wwz_target_row["local_window_max_days"]),
        color=TARGET_COLOR,
        alpha=0.12,
        label="140 d target band",
    )
    ax_wwz.axhline(
        float(wwz_target_row["period_days"]),
        color=TARGET_COLOR,
        ls="-.",
        lw=1.1,
        label="target-band peak",
    )
    ax_wwz.set_yscale("log")
    ax_wwz.set_ylim(float(wwz["period_min"]), float(wwz["period_max"]))
    ax_wwz.set_xlabel("MJD")
    ax_wwz.set_ylabel("Period (day)")
    ax_wwz.set_title("WWZ Power")
    ax_wwz.legend(loc="upper right", fontsize=8)
    fig.colorbar(wwz_mesh, ax=ax_wwz, pad=0.02, label="WWZ")

    _plot_cwt_global_row(ax_cwt_global, cwt, cwt_row, cwt_target_row)
    _plot_wwz_global_row(ax_wwz_global, wwz, wwz_row, wwz_target_row)

    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def _plot_cwt_significance(
    path: Path,
    source_label: str,
    cwt: dict,
    row: dict,
    refs: dict,
    target_row: dict,
) -> None:
    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    valid = _period_mask(period, gws, float(cwt["period_min"]), float(cwt["period_max"]))
    order = np.argsort(period[valid])
    period_plot = period[valid][order]
    gws_plot = gws[valid][order]
    sig95 = np.asarray(refs["signif_95"], dtype=float)[valid][order]
    sig99 = np.asarray(refs["signif_99"], dtype=float)[valid][order]

    fig, ax = plt.subplots(figsize=(8.8, 4.8), constrained_layout=True)
    ax.plot(period_plot, gws_plot, color="black", lw=1.5, label="Observed GWS")
    ax.plot(period_plot, sig95, color="#255c99", lw=1.1, ls="-.", label="AR(1) 95% local reference")
    ax.plot(period_plot, sig99, color="#7a3e9d", lw=1.1, ls=":", label="AR(1) 99% local reference")
    _draw_target_band(ax, target_row, label="140 d target band")
    _draw_global_peak_markers(ax, period_plot, gws_plot, color="red")
    _draw_single_peak(ax, target_row, color=TARGET_COLOR, show_fap=False)
    ax.set_xscale("log")
    ax.set_xlim(float(cwt["period_min"]), float(cwt["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Global wavelet spectrum")
    ax.set_title(f"{source_label} WCDA weekly fixed-window CWT local reference")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    ax.text(
        0.01,
        0.02,
        f"AR(1) alpha = {float(refs['alpha']):.3f}; fixed window, no trial correction",
        transform=ax.transAxes,
        fontsize=8,
        color="#5f6c7b",
    )
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def _plot_wwz_significance(
    path: Path,
    source_label: str,
    wwz: dict,
    row: dict,
    refs: dict,
    target_row: dict,
) -> None:
    period = np.asarray(wwz["period_axis"], dtype=float)
    global_wwz = np.asarray(wwz["global_wwz"], dtype=float)
    valid = _period_mask(period, global_wwz, float(wwz["period_min"]), float(wwz["period_max"]))
    order = np.argsort(period[valid])
    period_plot = period[valid][order]
    wwz_plot = global_wwz[valid][order]
    q95 = np.asarray(refs["q95"], dtype=float)[valid][order]
    q99 = np.asarray(refs["q99"], dtype=float)[valid][order]

    fig, ax = plt.subplots(figsize=(8.8, 4.8), constrained_layout=True)
    ax.plot(period_plot, wwz_plot, color="black", lw=1.5, label="Observed global WWZ")
    ax.plot(period_plot, q95, color="#255c99", lw=1.1, ls="-.", label="Surrogate 95% pointwise reference")
    ax.plot(period_plot, q99, color="#7a3e9d", lw=1.1, ls=":", label="Surrogate 99% pointwise reference")
    ax.axvspan(
        float(row["local_window_min_days"]),
        float(row["local_window_max_days"]),
        color="red",
        alpha=0.08,
        label="local FAP window",
    )
    _draw_target_band(ax, target_row, label="140 d target FAP window")
    _draw_global_peak_markers(ax, period_plot, wwz_plot, color="red")
    _draw_single_peak(ax, target_row, color=TARGET_COLOR, show_fap=True)
    ax.set_xscale("log")
    ax.set_xlim(float(wwz["period_min"]), float(wwz["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Mean WWZ")
    ax.set_title(f"{source_label} WCDA weekly fixed-window WWZ local significance")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    ax.text(
        0.01,
        0.02,
        f"AR(1) surrogate N = {int(row['n_surrogates'])}; alpha = {float(refs['alpha']):.3f}; fixed-window local FAP only",
        transform=ax.transAxes,
        fontsize=8,
        color="#5f6c7b",
    )
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def _plot_cwt_global_row(ax: plt.Axes, cwt: dict, row: dict, target_row: dict) -> None:
    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    valid = _period_mask(period, gws, float(cwt["period_min"]), float(cwt["period_max"]))
    order = np.argsort(period[valid])
    period_plot = period[valid][order]
    gws_plot = gws[valid][order]
    ax.plot(period_plot, gws_plot, color="black", lw=1.4)
    _draw_global_peak_markers(ax, period_plot, gws_plot, color="red")
    _draw_target_band(ax, target_row, label=None)
    _draw_single_peak(ax, target_row, color=TARGET_COLOR, show_fap=False)
    ax.set_xscale("log")
    ax.set_xlim(float(cwt["period_min"]), float(cwt["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("GWS")
    ax.set_title("CWT Global Spectrum")
    ax.grid(True, alpha=0.25)


def _plot_wwz_global_row(ax: plt.Axes, wwz: dict, row: dict, target_row: dict) -> None:
    period = np.asarray(wwz["period_axis"], dtype=float)
    global_wwz = np.asarray(wwz["global_wwz"], dtype=float)
    valid = _period_mask(period, global_wwz, float(wwz["period_min"]), float(wwz["period_max"]))
    order = np.argsort(period[valid])
    period_plot = period[valid][order]
    global_wwz_plot = global_wwz[valid][order]
    ax.plot(period_plot, global_wwz_plot, color="black", lw=1.4)
    _draw_global_peak_markers(ax, period_plot, global_wwz_plot, color="red")
    _draw_target_band(ax, target_row, label=None)
    _draw_single_peak(ax, target_row, color=TARGET_COLOR, show_fap=True)
    ax.set_xscale("log")
    ax.set_xlim(float(wwz["period_min"]), float(wwz["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Mean WWZ")
    ax.set_title("WWZ Global Spectrum")
    ax.grid(True, alpha=0.25)


def _draw_single_peak(ax: plt.Axes, row: dict, *, color: str, show_fap: bool) -> None:
    period = float(row["period_days"])
    ax.axvline(period, color=color, ls="--", lw=1.1, alpha=0.9)
    y_min, y_max = ax.get_ylim()
    label = f"{period:.1f} d"
    if show_fap and np.isfinite(float(row["local_fap"])):
        label += f"\np={float(row['local_fap']):.3f}"
    ax.text(
        period,
        y_min + 0.90 * (y_max - y_min),
        label,
        color=color,
        fontsize=8,
        rotation=90,
        ha="right",
        va="top",
    )


def _draw_target_band(ax: plt.Axes, row: dict, *, label: str | None) -> None:
    ax.axvspan(
        float(row["local_window_min_days"]),
        float(row["local_window_max_days"]),
        color=TARGET_COLOR,
        alpha=0.12,
        label=label,
    )


def _draw_global_peak_markers(ax: plt.Axes, period: np.ndarray, power: np.ndarray, *, color: str) -> None:
    period = np.asarray(period, dtype=float)
    power = np.asarray(power, dtype=float)
    finite = np.isfinite(period) & np.isfinite(power)
    period = period[finite]
    power = power[finite]
    if len(period) < 3:
        return

    power_range = float(np.nanmax(power) - np.nanmin(power))
    if not np.isfinite(power_range) or power_range <= 0:
        return

    peaks, _ = find_peaks(
        power,
        prominence=GLOBAL_PEAK_PROMINENCE_FRACTION * power_range,
        distance=GLOBAL_PEAK_MIN_DISTANCE_BINS,
    )
    if len(peaks) == 0:
        return

    y_min, y_max = ax.get_ylim()
    for rank, peak_idx in enumerate(sorted(peaks, key=lambda idx: power[idx], reverse=True), start=1):
        peak_period = float(period[peak_idx])
        ax.axvline(peak_period, color=color, ls="--", lw=1.0, alpha=0.85)
        y_text = y_min + (0.92 - 0.13 * ((rank - 1) % 3)) * (y_max - y_min)
        ax.text(
            peak_period,
            y_text,
            f"{peak_period:.1f} d",
            color=color,
            fontsize=8,
            rotation=90,
            ha="right",
            va="top",
        )


if __name__ == "__main__":
    main()
