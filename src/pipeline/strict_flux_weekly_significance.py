#!/usr/bin/env python3
"""Assess AR(1) quick-look significance for strict WCDA weekly flux products."""

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
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pycwt as wavelet  # noqa: E402


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import run_wwz, standardize_flux  # noqa: E402
from pipeline.weekly_qpo_local_significance import (  # noqa: E402
    DEFAULT_N_SURROGATES,
    DEFAULT_SEED,
    FIG_DPI,
    WWZ_LOCAL_WINDOW_FRACTION,
    _candidate_note,
    _candidate_peaks,
    _draw_peak_markers,
    _lag1_autocorr,
    _simulate_ar1,
    _time_span,
)
from utils.project_paths import ALIGNED_DIR, PERIODICITY_DIR, PROJECT_ROOT  # noqa: E402
from utils.source_registry import SOURCE_REGISTRY, WCDA_STRICT_FLUX_SOURCE_IDS, get_source  # noqa: E402


FLUX_SURVEY_ALIGNED_DIR = ALIGNED_DIR / "agn_wcda_weekly_flux_survey"
FLUX_SURVEY_PERIODICITY_DIR = PERIODICITY_DIR / "agn_wcda_weekly_flux_survey"
FLUX_SIGNIFICANCE_SUMMARY = FLUX_SURVEY_PERIODICITY_DIR / "agn_wcda_weekly_flux_significance_summary.csv"
SERIES_NAME = "wcda_strict_flux_weekly"
SIGNIFICANCE_COLUMNS = (
    "source_id",
    "source",
    "series",
    "method",
    "period_days",
    "cycles",
    "observed_statistic",
    "statistic_name",
    "null_model",
    "local_fap",
    "global_fap",
    "local_confidence",
    "global_confidence",
    "reference_95",
    "reference_99",
    "above_95",
    "above_99",
    "n_surrogates",
    "exceed_count",
    "global_exceed_count",
    "local_window_min_days",
    "local_window_max_days",
    "ar1_alpha",
    "note",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=sorted(SOURCE_REGISTRY),
        default=None,
        help="Source ids to process. Defaults to all strict-flux survey sources with --all-strict-flux-sources.",
    )
    parser.add_argument(
        "--all-strict-flux-sources",
        action="store_true",
        help="Process all 10 strict-flux survey sources.",
    )
    parser.add_argument(
        "--collect-summary-only",
        action="store_true",
        help="Only collect existing per-source strict-flux significance CSVs into the survey summary.",
    )
    parser.add_argument(
        "--write-summary",
        action="store_true",
        help="Write the 10-source strict-flux significance summary after processing or collecting.",
    )
    parser.add_argument("--n-surrogates", type=int, default=DEFAULT_N_SURROGATES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--wwz-parallel", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    source_ids = _resolve_source_ids(args)
    if args.collect_summary_only:
        _write_summary(source_ids)
        return
    if args.n_surrogates < 1:
        raise ValueError("--n-surrogates must be positive.")

    all_rows = []
    for source_index, source_id in enumerate(source_ids):
        rng = np.random.default_rng(args.seed + source_index)
        rows = assess_source(
            source_id,
            n_surrogates=args.n_surrogates,
            rng=rng,
            wwz_parallel=args.wwz_parallel,
            workers=args.workers,
        )
        output_csv = FLUX_SURVEY_PERIODICITY_DIR / source_id / "wcda_strict_flux_weekly_local_significance.csv"
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        _rows_to_frame(rows).to_csv(output_csv, index=False)
        all_rows.extend(rows)
        print(f"[OK] wrote {output_csv.relative_to(PROJECT_ROOT)}")

    if args.write_summary:
        if set(source_ids) == set(WCDA_STRICT_FLUX_SOURCE_IDS):
            _rows_to_frame(all_rows).to_csv(FLUX_SIGNIFICANCE_SUMMARY, index=False)
            print(f"[OK] wrote {FLUX_SIGNIFICANCE_SUMMARY.relative_to(PROJECT_ROOT)}")
        else:
            _write_summary(list(WCDA_STRICT_FLUX_SOURCE_IDS))


def _resolve_source_ids(args: argparse.Namespace) -> list[str]:
    if args.all_strict_flux_sources:
        return list(WCDA_STRICT_FLUX_SOURCE_IDS)
    if args.sources:
        invalid = sorted(set(args.sources) - set(WCDA_STRICT_FLUX_SOURCE_IDS))
        if invalid:
            raise ValueError(f"Sources do not have strict-flux survey inputs in this workflow: {invalid}")
        return list(args.sources)
    raise ValueError("Pass --all-strict-flux-sources or --sources.")


def assess_source(
    source_id: str,
    *,
    n_surrogates: int,
    rng: np.random.Generator,
    wwz_parallel: bool,
    workers: int,
) -> list[dict]:
    source_label = get_source(source_id).label
    aligned = _load_strict_flux_light_curve(FLUX_SURVEY_ALIGNED_DIR / source_id / "wcda_strict_flux_weekly_aligned.csv")
    periodicity_dir = FLUX_SURVEY_PERIODICITY_DIR / source_id
    cwt = _load_npz_dict(periodicity_dir / "wcda_strict_flux_weekly_cwt.npz")
    wwz = _load_npz_dict(periodicity_dir / "wcda_strict_flux_weekly_wwz.npz")

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
        periodicity_dir / "wcda_strict_flux_weekly_cwt_global_significance.png",
        source_label,
        cwt,
        cwt_rows,
        cwt_refs,
    )
    _plot_wwz_global_significance(
        periodicity_dir / "wcda_strict_flux_weekly_wwz_global_significance.png",
        source_label,
        wwz,
        wwz_rows,
        wwz_refs,
    )
    return cwt_rows + wwz_rows


def _load_strict_flux_light_curve(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"mjd", "N0", "N0_err", "is_usable_for_periodicity"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required strict-flux columns: {sorted(missing)}")
    out = df.loc[:, ["mjd", "N0", "N0_err", "is_usable_for_periodicity"]].copy()
    for col in ("mjd", "N0", "N0_err"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    usable = out["is_usable_for_periodicity"].astype(bool)
    mask = usable & np.isfinite(out["mjd"]) & np.isfinite(out["N0"]) & np.isfinite(out["N0_err"]) & (out["N0_err"] > 0)
    out = out.loc[mask, ["mjd", "N0", "N0_err"]].sort_values("mjd").reset_index(drop=True)
    if len(out) < 4:
        raise ValueError(f"{path} has fewer than four usable strict-flux rows.")
    return out


def _load_npz_dict(path: Path) -> dict:
    with np.load(path) as data:
        return {key: data[key] for key in data.files}


def _assess_cwt(source_id: str, source_label: str, aligned: pd.DataFrame, cwt: dict) -> tuple[list[dict], dict]:
    flux = aligned["N0"].to_numpy(dtype=float)
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
                "series": SERIES_NAME,
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
    y = aligned["N0"].to_numpy(dtype=float)
    yerr = aligned["N0_err"].to_numpy(dtype=float)
    y_mean = float(np.nanmean(y))
    y_std = float(np.nanstd(y, ddof=1))
    alpha = float(np.clip(_lag1_autocorr(standardize_flux(y)), -0.95, 0.95))

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
                "series": SERIES_NAME,
                "method": "WWZ",
                "period_days": peak_period,
                "cycles": t_span / peak_period,
                "observed_statistic": observed_local_max[peak_idx],
                "statistic_name": "Local-window max global WWZ",
                "null_model": "AR(1) Gaussian surrogate on same strict-flux weekly sampling",
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
    ax.plot(period_plot, gws_plot, color="black", lw=1.5, label="Observed strict-flux GWS")
    ax.plot(period_plot, sig95, color="#255c99", lw=1.1, ls="-.", label="AR(1) 95% local reference")
    ax.plot(period_plot, sig99, color="#7a3e9d", lw=1.1, ls=":", label="AR(1) 99% local reference")
    _draw_peak_markers(ax, rows)
    ax.set_xscale("log")
    ax.set_xlim(float(cwt["period_min"]), float(cwt["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Global wavelet spectrum")
    ax.set_title(f"{source_label} strict flux CWT local significance")
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
    ax.plot(period_plot, wwz_plot, color="black", lw=1.5, label="Observed strict-flux global WWZ")
    ax.plot(period_plot, q95, color="#255c99", lw=1.1, ls="-.", label="Surrogate 95% pointwise reference")
    ax.plot(period_plot, q99, color="#7a3e9d", lw=1.1, ls=":", label="Surrogate 99% pointwise reference")
    _draw_peak_markers(ax, rows, show_fap=True)
    ax.set_xscale("log")
    ax.set_xlim(float(wwz["period_min"]), float(wwz["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Mean WWZ")
    ax.set_title(f"{source_label} strict flux WWZ local significance")
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


def _write_summary(source_ids: list[str]) -> None:
    frames = []
    missing = []
    for source_id in source_ids:
        path = FLUX_SURVEY_PERIODICITY_DIR / source_id / "wcda_strict_flux_weekly_local_significance.csv"
        if not path.exists():
            missing.append(path)
            continue
        frames.append(pd.read_csv(path))
    if missing:
        raise FileNotFoundError(f"Missing strict-flux per-source significance CSVs: {missing}")
    summary = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=SIGNIFICANCE_COLUMNS)
    for col in SIGNIFICANCE_COLUMNS:
        if col not in summary.columns:
            summary[col] = pd.NA
    summary = summary.loc[:, list(SIGNIFICANCE_COLUMNS)]
    observed = set(summary["source_id"]) if "source_id" in summary.columns else set()
    source_ids_with_csv = {
        source_id
        for source_id in source_ids
        if (FLUX_SURVEY_PERIODICITY_DIR / source_id / "wcda_strict_flux_weekly_local_significance.csv").exists()
    }
    if not observed.issubset(source_ids_with_csv):
        raise ValueError(f"Unexpected strict-flux significance source ids: extra={sorted(observed-source_ids_with_csv)}")
    FLUX_SURVEY_PERIODICITY_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(FLUX_SIGNIFICANCE_SUMMARY, index=False)
    print(f"[OK] wrote {FLUX_SIGNIFICANCE_SUMMARY.relative_to(PROJECT_ROOT)}")


def _rows_to_frame(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    for col in SIGNIFICANCE_COLUMNS:
        if col not in frame.columns:
            frame[col] = pd.NA
    return frame.loc[:, list(SIGNIFICANCE_COLUMNS)]


if __name__ == "__main__":
    main()
