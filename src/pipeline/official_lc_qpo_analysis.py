#!/usr/bin/env python3
"""Run CWT, WWZ, and AR(1) significance checks for official WCDA light curves."""

from __future__ import annotations

import argparse
import contextlib
import io
import multiprocessing as mp
import os
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pycwt as wavelet  # noqa: E402
from scipy.signal import find_peaks  # noqa: E402


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import run_cwt, run_wwz, standardize_flux  # noqa: E402
from pipeline.periodicity_v1 import _plot_cwt, _plot_periodicity_summary, _plot_wwz, _save_cwt, _save_wwz  # noqa: E402
from utils.project_paths import (  # noqa: E402
    ALIGNED_DIR,
    PERIODICITY_DIR,
    PROCESSED_DATA_DIR,
    PROJECT_ROOT,
)


WCDA_2DAY_DIR = PROCESSED_DATA_DIR / "wcda_2day"
WCDA_8DAY_DIR = PROCESSED_DATA_DIR / "wcda_8day"
INPUT_DIRS = {
    "2day": WCDA_2DAY_DIR / "official_20260817",
    "8day": WCDA_8DAY_DIR / "official_20260817",
}
PERIOD_RANGES = {"2day": (10.0, 600.0), "8day": (32.0, 600.0)}
DEFAULT_N_SURROGATES = 1000
DEFAULT_SEED = 20260817
PEAK_PROMINENCE_FRACTION = 0.10
PEAK_MIN_DISTANCE_BINS = 2
LOCAL_WINDOW_FRACTION = 0.10
FIG_DPI = 180
SIGNIFICANCE_COLUMNS = (
    "source_id",
    "source",
    "series",
    "method",
    "period_days",
    "cycles",
    "observed_statistic",
    "statistic_name",
    "ar1_alpha",
    "note",
    "null_model",
    "reference_95",
    "reference_99",
    "above_95",
    "above_99",
    "n_surrogates",
    "local_fap",
    "global_fap",
    "local_confidence",
    "global_confidence",
    "exceed_count",
    "global_exceed_count",
    "local_window_min_days",
    "local_window_max_days",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cadences", nargs="+", choices=sorted(INPUT_DIRS), default=sorted(INPUT_DIRS))
    parser.add_argument("--sources", nargs="+", help="Source tokens from the official CSV filenames, e.g. Mkn421.")
    parser.add_argument("--input-root", type=Path, default=PROCESSED_DATA_DIR)
    parser.add_argument("--aligned-dir", type=Path, default=ALIGNED_DIR / "official_lc_20260817")
    parser.add_argument("--periodicity-dir", type=Path, default=PERIODICITY_DIR / "official_lc_20260817")
    parser.add_argument("--n-surrogates", type=int, default=DEFAULT_N_SURROGATES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--wwz-time-divisions", type=int, default=80)
    parser.add_argument("--wwz-freq-step-factor", type=float, default=0.5)
    parser.add_argument("--wwz-color-scale", choices=("linear", "log"), default="linear")
    parser.add_argument("--skip-summary", action="store_true", help="Do not write the cross-source summary CSV.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.n_surrogates < 1:
        raise ValueError("--n-surrogates must be positive.")
    if args.workers < 1:
        raise ValueError("--workers must be positive.")

    input_root = _resolve_path(args.input_root)
    aligned_root = _resolve_path(args.aligned_dir)
    periodicity_root = _resolve_path(args.periodicity_dir)
    all_rows: list[dict[str, object]] = []

    for cadence_index, cadence in enumerate(args.cadences):
        input_dir = input_root / f"wcda_{cadence}" / "official_20260817"
        source_paths = _resolve_source_paths(input_dir, cadence, args.sources)
        for source_index, (source_token, input_path) in enumerate(source_paths):
            seed = args.seed + cadence_index * 1000 + source_index
            rows = run_source(args, cadence, source_token, input_path, aligned_root, periodicity_root, seed)
            all_rows.extend(rows)

    if not args.skip_summary:
        periodicity_root.mkdir(parents=True, exist_ok=True)
        summary_path = periodicity_root / "official_lc_qpo_significance_summary.csv"
        pd.DataFrame(all_rows, columns=SIGNIFICANCE_COLUMNS).to_csv(summary_path, index=False)
        print(f"[OK] wrote significance summary -> {summary_path.relative_to(PROJECT_ROOT)}")


def run_source(
    args: argparse.Namespace,
    cadence: str,
    source_token: str,
    input_path: Path,
    aligned_root: Path,
    periodicity_root: Path,
    seed: int,
) -> list[dict[str, object]]:
    raw = pd.read_csv(input_path)
    aligned = _clean_light_curve(raw, cadence, source_token, input_path)
    source_id = _source_id(source_token)
    aligned_dir = aligned_root / cadence / source_id
    output_dir = periodicity_root / cadence / source_id
    aligned_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    aligned_path = aligned_dir / f"wcda_official_{cadence}_aligned.csv"
    aligned.to_csv(aligned_path, index=False)

    t = aligned["mjd"].to_numpy(dtype=float)
    flux = aligned["N0"].to_numpy(dtype=float)
    flux_err = aligned["N0_err"].to_numpy(dtype=float)
    period_min, period_max = PERIOD_RANGES[cadence]
    cwt = run_cwt(t, flux, period_min=period_min, period_max=period_max)
    wwz = run_wwz(
        t,
        flux,
        flux_err,
        period_min=period_min,
        period_max=period_max,
        time_divisions=args.wwz_time_divisions,
        freq_step_factor=args.wwz_freq_step_factor,
        parallel=False,
    )
    stem = f"wcda_official_{cadence}"
    _save_cwt(output_dir / f"{stem}_cwt.npz", cwt)
    _save_wwz(output_dir / f"{stem}_wwz.npz", wwz)
    label = f"{source_token} official WCDA {cadence} flux"
    _plot_light_curve(output_dir / f"{stem}_lightcurve.png", label, raw, aligned)
    _plot_cwt(output_dir / f"{stem}_cwt.png", label, t, flux, flux_err, cwt)
    _plot_wwz(output_dir / f"{stem}_wwz.png", label, wwz, color_scale=args.wwz_color_scale)

    cwt_rows, cwt_refs = _assess_cwt(source_id, source_token, cadence, t, flux, cwt)
    wwz_rows, wwz_refs = _assess_wwz(
        source_id,
        source_token,
        cadence,
        t,
        flux,
        flux_err,
        wwz,
        n_surrogates=args.n_surrogates,
        seed=seed,
        workers=args.workers,
    )
    rows = cwt_rows + wwz_rows
    pd.DataFrame(rows, columns=SIGNIFICANCE_COLUMNS).to_csv(
        output_dir / f"{stem}_significance.csv", index=False
    )
    _plot_cwt_significance(output_dir / f"{stem}_cwt_significance.png", label, cwt_refs, cwt_rows)
    _plot_wwz_significance(
        output_dir / f"{stem}_wwz_significance.png", label, wwz_refs, wwz_rows, args.n_surrogates
    )
    _plot_periodicity_summary(
        output_dir / f"{stem}_periodicity.png",
        label,
        t,
        flux,
        flux_err,
        cwt,
        wwz,
        color_scale=args.wwz_color_scale,
        include_global_row=True,
        cwt_significance=cwt_refs,
        wwz_significance=wwz_refs,
    )
    print(f"[OK] {cadence}/{source_token}: usable={len(aligned)}/{len(raw)}, candidates={len(rows)}")
    return rows


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _resolve_source_paths(input_dir: Path, cadence: str, sources: list[str] | None) -> list[tuple[str, Path]]:
    paths = sorted(input_dir.glob(f"LHAASO-WCDA_*_*_{cadence}_flux.csv"))
    if not paths:
        raise FileNotFoundError(f"No official {cadence} CSV files found in {input_dir}")
    resolved = [(_source_token(path, cadence), path) for path in paths]
    if sources is None:
        return resolved
    requested = {item.strip().lower() for item in sources}
    selected = [(token, path) for token, path in resolved if token.lower() in requested]
    found = {token.lower() for token, _path in selected}
    missing = sorted(requested - found)
    if missing:
        raise ValueError(f"Requested source tokens absent from {cadence}: {missing}")
    return selected


def _source_token(path: Path, cadence: str) -> str:
    prefix = "LHAASO-WCDA_"
    suffix = f"_{cadence}_flux.csv"
    name = path.name
    if not name.startswith(prefix) or not name.endswith(suffix):
        raise ValueError(f"Unexpected official light-curve filename: {path}")
    stem = name[len(prefix) : -len(suffix)]
    match = re.fullmatch(r"(?P<source>.+)_\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2}", stem)
    if match is None:
        raise ValueError(f"Unexpected official light-curve filename: {path}")
    return str(match.group("source"))


def _source_id(source_token: str) -> str:
    return source_token.lower().replace("+", "p").replace("-", "m").replace(" ", "_")


def _clean_light_curve(raw: pd.DataFrame, cadence: str, source_token: str, path: Path) -> pd.DataFrame:
    required = {"source", "cadence", "mjd", "N0", "N0_err", "fit_status", "response_period"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    out = raw.copy()
    for column in ("mjd", "N0", "N0_err", "TS"):
        if column in out:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    mask = (
        out["fit_status"].astype(str).str.strip().eq("OK")
        & np.isfinite(out["mjd"])
        & np.isfinite(out["N0"])
        & np.isfinite(out["N0_err"])
        & (out["N0_err"] > 0)
    )
    clean = out.loc[mask].copy().sort_values("mjd").reset_index(drop=True)
    if len(clean) < 8:
        raise ValueError(f"{cadence}/{source_token} has fewer than eight usable flux measurements.")
    clean.insert(0, "source_id", _source_id(source_token))
    clean.insert(1, "input_path", str(path.relative_to(PROJECT_ROOT)))
    clean["is_usable_for_periodicity"] = True
    return clean


def _candidate_peaks(period: np.ndarray, power: np.ndarray, period_min: float, period_max: float) -> tuple[np.ndarray, np.ndarray]:
    mask = np.isfinite(period) & np.isfinite(power) & (period >= period_min) & (period <= period_max)
    period_plot = np.asarray(period[mask], dtype=float)
    power_plot = np.asarray(power[mask], dtype=float)
    order = np.argsort(period_plot)
    period_plot, power_plot = period_plot[order], power_plot[order]
    if len(period_plot) < 3:
        return period_plot, np.array([], dtype=int)
    power_range = float(np.nanmax(power_plot) - np.nanmin(power_plot))
    if not np.isfinite(power_range) or power_range <= 0:
        return period_plot, np.array([], dtype=int)
    peaks, _ = find_peaks(
        power_plot,
        prominence=PEAK_PROMINENCE_FRACTION * power_range,
        distance=PEAK_MIN_DISTANCE_BINS,
    )
    return period_plot, peaks


def _lag1_autocorr(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 3:
        return 0.0
    left, right = values[:-1] - np.mean(values[:-1]), values[1:] - np.mean(values[1:])
    denominator = float(np.sqrt(np.sum(left * left) * np.sum(right * right)))
    if denominator <= 0 or not np.isfinite(denominator):
        return 0.0
    return float(np.clip(np.sum(left * right) / denominator, -0.95, 0.95))


def _assess_cwt(
    source_id: str, source_token: str, cadence: str, t: np.ndarray, flux: np.ndarray, cwt: dict,
    *, alpha_override: float | None = None,
) -> tuple[list[dict[str, object]], dict[str, np.ndarray | float]]:
    standardized = standardize_flux(flux)
    alpha = _lag1_autocorr(standardized) if alpha_override is None else float(alpha_override)
    scales = float(cwt["s0"]) * 2 ** (np.arange(int(cwt["J"]) + 1) * float(cwt["dj"]))
    dof = np.full_like(scales, fill_value=len(standardized), dtype=float)
    mother = wavelet.Morlet(6)
    reference_95, _ = wavelet.significance(
        standardized, float(cwt["dt"]), scales, sigma_test=1, alpha=alpha, significance_level=0.95, dof=dof, wavelet=mother
    )
    reference_99, _ = wavelet.significance(
        standardized, float(cwt["dt"]), scales, sigma_test=1, alpha=alpha, significance_level=0.99, dof=dof, wavelet=mother
    )
    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    period_min, period_max = float(cwt["period_min"]), float(cwt["period_max"])
    period_plot, peaks = _candidate_peaks(period, gws, period_min, period_max)
    span = float(np.nanmax(t) - np.nanmin(t))
    rows: list[dict[str, object]] = []
    for peak in peaks:
        peak_period = float(period_plot[peak])
        index = int(np.nanargmin(np.abs(period - peak_period)))
        rows.append(
            _base_row(source_id, source_token, cadence, "CWT", peak_period, span, float(gws[index]), "Global wavelet spectrum", alpha)
            | {
                "null_model": "AR(1) red noise via PyCWT time-averaged significance",
                "reference_95": float(reference_95[index]),
                "reference_99": float(reference_99[index]),
                "above_95": bool(gws[index] >= reference_95[index]),
                "above_99": bool(gws[index] >= reference_99[index]),
                "n_surrogates": 0,
                "local_fap": np.nan,
                "global_fap": np.nan,
                "local_confidence": np.nan,
                "global_confidence": np.nan,
                "exceed_count": 0,
                "global_exceed_count": 0,
                "local_window_min_days": np.nan,
                "local_window_max_days": np.nan,
            }
        )
    refs: dict[str, np.ndarray | float] = {
        "period": period,
        "gws": gws,
        "reference_95": reference_95,
        "reference_99": reference_99,
        "signif_95": reference_95,
        "signif_99": reference_99,
        "period_min": period_min,
        "period_max": period_max,
        "alpha": alpha,
    }
    return rows, refs


def _assess_wwz(
    source_id: str,
    source_token: str,
    cadence: str,
    t: np.ndarray,
    flux: np.ndarray,
    flux_err: np.ndarray,
    wwz: dict,
    *,
    n_surrogates: int,
    seed: int,
    workers: int,
) -> tuple[list[dict[str, object]], dict[str, np.ndarray | float]]:
    period = np.asarray(wwz["period_axis"], dtype=float)
    global_wwz = np.asarray(wwz["global_wwz"], dtype=float)
    period_min, period_max = float(wwz["period_min"]), float(wwz["period_max"])
    period_plot, peaks = _candidate_peaks(period, global_wwz, period_min, period_max)
    alpha = _lag1_autocorr(standardize_flux(flux))
    candidate_periods = [float(period_plot[index]) for index in peaks]
    windows: list[tuple[float, float, np.ndarray]] = []
    observed: list[float] = []
    for peak_period in candidate_periods:
        lower, upper = peak_period * (1 - LOCAL_WINDOW_FRACTION), peak_period * (1 + LOCAL_WINDOW_FRACTION)
        mask = np.isfinite(period) & (period >= lower) & (period <= upper)
        if not np.any(mask):
            mask = np.zeros_like(period, dtype=bool)
            mask[int(np.nanargmin(np.abs(period - peak_period)))] = True
        windows.append((lower, upper, mask))
        observed.append(float(np.nanmax(global_wwz[mask])))

    seeds = np.random.default_rng(seed).integers(0, np.iinfo(np.uint32).max, size=n_surrogates, dtype=np.uint32)
    tasks = [
        (
            int(sim_seed), t, flux_err, len(flux), alpha, float(np.nanmean(flux)), float(np.nanstd(flux, ddof=1)),
            period_min, period_max, int(wwz["time_divisions"]), float(wwz["decay_constant"]),
            float(wwz["freq_step"]) * float(wwz["t_span"]),
        )
        for sim_seed in seeds
    ]
    print(f"  [{cadence}/{source_token}] WWZ AR(1) surrogates: {n_surrogates} across {workers} workers")
    if workers > 1 and n_surrogates > 1:
        with mp.Pool(processes=workers) as pool:
            simulated = np.vstack(pool.map(_run_wwz_surrogate, tasks))
    else:
        simulated = np.vstack([_run_wwz_surrogate(task) for task in tasks])
    q95, q99 = np.nanpercentile(simulated, (95, 99), axis=0)
    global_max = np.nanmax(simulated, axis=1)
    span = float(np.nanmax(t) - np.nanmin(t))
    rows: list[dict[str, object]] = []
    for index, peak_period in enumerate(candidate_periods):
        lower, upper, mask = windows[index]
        local_max = np.nanmax(simulated[:, mask], axis=1)
        exceed = int(np.count_nonzero(local_max >= observed[index]))
        global_exceed = int(np.count_nonzero(global_max >= observed[index]))
        nearest = int(np.nanargmin(np.abs(period - peak_period)))
        rows.append(
            _base_row(source_id, source_token, cadence, "WWZ", peak_period, span, observed[index], "Mean WWZ", alpha)
            | {
                "null_model": "AR(1) Gaussian surrogate on identical sampling",
                "reference_95": float(q95[nearest]),
                "reference_99": float(q99[nearest]),
                "above_95": bool(observed[index] >= q95[nearest]),
                "above_99": bool(observed[index] >= q99[nearest]),
                "n_surrogates": n_surrogates,
                "local_fap": (exceed + 1.0) / (n_surrogates + 1.0),
                "global_fap": (global_exceed + 1.0) / (n_surrogates + 1.0),
                "local_confidence": 1.0 - (exceed + 1.0) / (n_surrogates + 1.0),
                "global_confidence": 1.0 - (global_exceed + 1.0) / (n_surrogates + 1.0),
                "exceed_count": exceed,
                "global_exceed_count": global_exceed,
                "local_window_min_days": lower,
                "local_window_max_days": upper,
            }
        )
    refs: dict[str, np.ndarray | float] = {
        "period": period,
        "global_wwz": global_wwz,
        "q95": q95,
        "q99": q99,
        "period_min": period_min,
        "period_max": period_max,
        "alpha": alpha,
        "n_surrogates": n_surrogates,
    }
    return rows, refs


def _base_row(
    source_id: str,
    source_token: str,
    cadence: str,
    method: str,
    period_days: float,
    span: float,
    statistic: float,
    statistic_name: str,
    alpha: float,
) -> dict[str, object]:
    note = "Quick-look candidate; no correction for source, cadence, method, or period trials. Response-period systematics are not modeled."
    if span / period_days < 4:
        note += " Fewer than four observed cycles."
    return {
        "source_id": source_id,
        "source": source_token,
        "series": f"wcda_official_{cadence}",
        "method": method,
        "period_days": period_days,
        "cycles": span / period_days,
        "observed_statistic": statistic,
        "statistic_name": statistic_name,
        "ar1_alpha": alpha,
        "note": note,
    }


def _simulate_ar1(n: int, alpha: float, mean: float, std: float, rng: np.random.Generator) -> np.ndarray:
    innovation_std = np.sqrt(max(1.0 - alpha**2, 1e-8))
    values = np.empty(n, dtype=float)
    values[0] = rng.normal()
    for index in range(1, n):
        values[index] = alpha * values[index - 1] + innovation_std * rng.normal()
    values = (values - np.mean(values)) / np.std(values, ddof=1)
    return mean + std * values


def _run_wwz_surrogate(task: tuple) -> np.ndarray:
    seed, t, flux_err, n, alpha, mean, std, period_min, period_max, time_divisions, decay_constant, freq_step_factor = task
    flux = _simulate_ar1(n, alpha, mean, std, np.random.default_rng(seed))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = run_wwz(
            t,
            flux,
            flux_err,
            period_min=period_min,
            period_max=period_max,
            time_divisions=time_divisions,
            decay_constant=decay_constant,
            freq_step_factor=freq_step_factor,
            parallel=False,
        )
    return np.asarray(result["global_wwz"], dtype=float)


def _plot_light_curve(path: Path, label: str, raw: pd.DataFrame, aligned: pd.DataFrame) -> None:
    fig, axis = plt.subplots(figsize=(12.5, 4.4), constrained_layout=True)
    rejected = raw.loc[~raw["fit_status"].astype(str).str.strip().eq("OK")].copy()
    if not rejected.empty:
        rejected["mjd"] = pd.to_numeric(rejected["mjd"], errors="coerce")
        axis.scatter(rejected["mjd"], np.zeros(len(rejected)), marker="x", color="#a33a3a", label="Rejected fit-status row")
    axis.errorbar(aligned["mjd"], aligned["N0"], yerr=aligned["N0_err"], fmt="o", ms=2.4, capsize=1.5, elinewidth=0.6, label="fit_status = OK")
    axis.set_xlabel("MJD")
    axis.set_ylabel(r"$N_0$ (TeV$^{-1}$ cm$^{-2}$ s$^{-1}$)")
    axis.set_title(label)
    axis.grid(True, alpha=0.25)
    axis.legend(loc="best", fontsize=8)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def _plot_cwt_significance(path: Path, label: str, refs: dict[str, np.ndarray | float], rows: list[dict[str, object]]) -> None:
    fig, axis = plt.subplots(figsize=(8.5, 4.4), constrained_layout=True)
    axis.plot(refs["period"], refs["gws"], color="black", lw=1.5, label="Observed GWS")
    axis.plot(refs["period"], refs["reference_95"], color="#255c99", lw=1.1, ls="-.", label="AR(1) 95%")
    axis.plot(refs["period"], refs["reference_99"], color="#7a3e9d", lw=1.1, ls=":", label="AR(1) 99%")
    for row in rows:
        axis.axvline(float(row["period_days"]), color="#8a95a5", lw=0.6, alpha=0.6)
    axis.set_xscale("log")
    axis.set_xlim(float(refs["period_min"]), float(refs["period_max"]))
    axis.set_xlabel("Period (day)")
    axis.set_ylabel("Global wavelet spectrum")
    axis.set_title(f"{label}: CWT AR(1) reference")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="best", fontsize=8)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def _plot_wwz_significance(
    path: Path, label: str, refs: dict[str, np.ndarray | float], rows: list[dict[str, object]], n_surrogates: int
) -> None:
    fig, axis = plt.subplots(figsize=(8.5, 4.4), constrained_layout=True)
    axis.plot(refs["period"], refs["global_wwz"], color="black", lw=1.5, label="Observed mean WWZ")
    axis.plot(refs["period"], refs["q95"], color="#255c99", lw=1.1, ls="-.", label="AR(1) surrogate 95%")
    axis.plot(refs["period"], refs["q99"], color="#7a3e9d", lw=1.1, ls=":", label="AR(1) surrogate 99%")
    for row in rows:
        axis.axvline(float(row["period_days"]), color="#8a95a5", lw=0.6, alpha=0.6)
    axis.set_xscale("log")
    axis.set_xlim(float(refs["period_min"]), float(refs["period_max"]))
    axis.set_xlabel("Period (day)")
    axis.set_ylabel("Mean WWZ")
    axis.set_title(f"{label}: WWZ AR(1) surrogates (N={n_surrogates})")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="best", fontsize=8)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


if __name__ == "__main__":
    main()
