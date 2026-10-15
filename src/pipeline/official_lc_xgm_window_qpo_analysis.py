#!/usr/bin/env python3
"""Run official WCDA 2-day QPO analyses in configurable MJD windows."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import run_cwt, run_wwz  # noqa: E402
from pipeline.official_lc_qpo_analysis import (  # noqa: E402
    SIGNIFICANCE_COLUMNS,
    _assess_cwt,
    _assess_wwz,
    _clean_light_curve,
    _plot_cwt_significance,
    _plot_light_curve,
    _plot_wwz_significance,
    _resolve_source_paths,
    _source_id,
)
from pipeline.periodicity_v1 import (  # noqa: E402
    _plot_cwt,
    _plot_periodicity_summary,
    _plot_wwz,
    _save_cwt,
    _save_wwz,
)
from utils.project_paths import ALIGNED_DIR, PERIODICITY_DIR, PROCESSED_DATA_DIR, PROJECT_ROOT  # noqa: E402


CADENCE = "2day"
WINDOW_MIN = 60200.0
WINDOW_MAX = 60700.0
PERIOD_MIN = 10.0
PERIOD_MAX = 200.0
XGM_REFERENCE_PERIOD = 51.05
DEFAULT_N_SURROGATES = 200
DEFAULT_SEED = 20260817
DEFAULT_SOURCES = ("Mkn421", "Mkn501")
OUTPUT_KEY = "xgm_window_60200_60700"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", nargs="+", default=list(DEFAULT_SOURCES))
    parser.add_argument("--n-surrogates", type=int, default=DEFAULT_N_SURROGATES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--wwz-time-divisions", type=int, default=80)
    parser.add_argument("--wwz-freq-step-factor", type=float, default=0.5)
    parser.add_argument("--window-min", type=float, default=WINDOW_MIN)
    parser.add_argument("--window-max", type=float, default=WINDOW_MAX)
    parser.add_argument("--period-min", type=float, default=PERIOD_MIN)
    parser.add_argument("--period-max", type=float, default=PERIOD_MAX)
    parser.add_argument("--output-key", default=OUTPUT_KEY)
    parser.add_argument("--target-period", type=float, default=XGM_REFERENCE_PERIOD)
    parser.add_argument("--skip-target-summary", action="store_true")
    parser.add_argument(
        "--mark-global-peaks-on-maps",
        action="store_true",
        help="Draw horizontal guides for global-spectrum candidate peaks on the CWT and WWZ maps.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.n_surrogates < 1:
        raise ValueError("--n-surrogates must be positive.")
    if args.workers < 1:
        raise ValueError("--workers must be positive.")
    if args.window_max <= args.window_min:
        raise ValueError("--window-max must exceed --window-min.")
    if args.period_min <= 0 or args.period_max <= args.period_min:
        raise ValueError("Require 0 < --period-min < --period-max.")
    if not args.output_key.replace("_", "").isalnum():
        raise ValueError("--output-key may contain only letters, digits, and underscores.")

    input_dir = PROCESSED_DATA_DIR / "wcda_2day" / "official_20260817"
    aligned_root = ALIGNED_DIR / "official_lc_20260817" / args.output_key
    periodicity_root = PERIODICITY_DIR / "official_lc_20260817" / args.output_key
    candidate_rows: list[dict[str, object]] = []
    target_rows: list[dict[str, object]] = []

    for source_index, (source_token, input_path) in enumerate(
        _resolve_source_paths(input_dir, CADENCE, args.sources)
    ):
        source_candidates, source_targets = run_source(
            args,
            source_token,
            input_path,
            aligned_root,
            periodicity_root,
            args.seed + source_index,
        )
        candidate_rows.extend(source_candidates)
        target_rows.extend(source_targets)

    periodicity_root.mkdir(parents=True, exist_ok=True)
    analysis_stem = f"official_2day_{args.output_key}"
    pd.DataFrame(candidate_rows, columns=SIGNIFICANCE_COLUMNS).to_csv(
        periodicity_root / f"{analysis_stem}_candidate_significance.csv", index=False
    )
    if not args.skip_target_summary:
        pd.DataFrame(target_rows).to_csv(
            periodicity_root / f"{analysis_stem}_target_summary.csv", index=False
        )
    print(f"[OK] wrote window summaries -> {periodicity_root.relative_to(PROJECT_ROOT)}")


def run_source(
    args: argparse.Namespace,
    source_token: str,
    input_path: Path,
    aligned_root: Path,
    periodicity_root: Path,
    seed: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    raw = pd.read_csv(input_path)
    aligned = _clean_light_curve(raw, CADENCE, source_token, input_path)
    aligned = aligned.loc[
        (aligned["mjd"] >= args.window_min) & (aligned["mjd"] <= args.window_max)
    ].reset_index(drop=True)
    if len(aligned) < 8:
        raise ValueError(f"{source_token} has fewer than eight usable rows in the requested window.")

    source_id = _source_id(source_token)
    aligned_dir = aligned_root / source_id
    output_dir = periodicity_root / source_id
    aligned_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"wcda_official_2day_{args.output_key}"
    aligned.to_csv(aligned_dir / f"{stem}_aligned.csv", index=False)

    t = aligned["mjd"].to_numpy(dtype=float)
    flux = aligned["N0"].to_numpy(dtype=float)
    flux_err = aligned["N0_err"].to_numpy(dtype=float)
    cwt = run_cwt(t, flux, period_min=args.period_min, period_max=args.period_max)
    wwz = run_wwz(
        t,
        flux,
        flux_err,
        period_min=args.period_min,
        period_max=args.period_max,
        time_divisions=args.wwz_time_divisions,
        freq_step_factor=args.wwz_freq_step_factor,
        parallel=False,
    )
    _save_cwt(output_dir / f"{stem}_cwt.npz", cwt)
    _save_wwz(output_dir / f"{stem}_wwz.npz", wwz)

    cwt_rows, cwt_refs = _assess_cwt(source_id, source_token, CADENCE, t, flux, cwt)
    wwz_rows, wwz_refs = _assess_wwz(
        source_id,
        source_token,
        CADENCE,
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
        output_dir / f"{stem}_candidate_significance.csv", index=False
    )
    save_significance_refs(output_dir / f"{stem}_significance_refs.npz", cwt_refs, wwz_refs)
    target_rows = []
    if not args.skip_target_summary:
        target_rows = target_summaries(
            source_id, source_token, cwt_refs, wwz_refs, args.target_period, args.window_min, args.window_max
        )
        pd.DataFrame(target_rows).to_csv(output_dir / f"{stem}_target.csv", index=False)

    raw_window = raw.loc[(raw["mjd"] >= args.window_min) & (raw["mjd"] <= args.window_max)].copy()
    label = f"{source_token} official WCDA 2-day flux · MJD {args.window_min:.0f}–{args.window_max:.0f}"
    _plot_light_curve(output_dir / f"{stem}_lightcurve.png", label, raw_window, aligned)
    _plot_cwt(output_dir / f"{stem}_cwt.png", label, t, flux, flux_err, cwt)
    _plot_wwz(output_dir / f"{stem}_wwz.png", label, wwz, color_scale="linear")
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
        color_scale="linear",
        include_global_row=True,
        cwt_significance=cwt_refs,
        wwz_significance=wwz_refs,
        light_curve_ylim=presentation_flux_limits(flux, flux_err),
        light_curve_note="Flux-axis clipping is display-only; timing uses all retained values.",
        mark_global_peaks_on_maps=args.mark_global_peaks_on_maps,
    )
    print(
        f"[OK] {source_token}: window rows={len(aligned)}, "
        f"candidate rows={len(rows)}"
    )
    return rows, target_rows


def presentation_flux_limits(flux: np.ndarray, flux_err: np.ndarray) -> tuple[float, float]:
    finite_flux = np.asarray(flux, dtype=float)
    finite_flux = finite_flux[np.isfinite(finite_flux)]
    finite_error = np.asarray(flux_err, dtype=float)
    finite_error = finite_error[np.isfinite(finite_error) & (finite_error > 0)]
    if len(finite_flux) == 0:
        raise ValueError("Cannot derive presentation limits without finite flux values.")

    lower = float(np.nanmin(finite_flux))
    upper = float(np.nanmax(finite_flux))
    span = max(upper - lower, np.finfo(float).eps)
    typical_error = float(np.nanquantile(finite_error, 0.75)) if len(finite_error) else 0.0
    padding = max(0.05 * span, 2.0 * typical_error)
    return lower - padding, upper + padding


def save_significance_refs(path: Path, cwt_refs: dict, wwz_refs: dict) -> None:
    np.savez_compressed(
        path,
        cwt_period=np.asarray(cwt_refs["period"], dtype=float),
        cwt_gws=np.asarray(cwt_refs["gws"], dtype=float),
        cwt_reference_95=np.asarray(cwt_refs["reference_95"], dtype=float),
        cwt_reference_99=np.asarray(cwt_refs["reference_99"], dtype=float),
        wwz_period=np.asarray(wwz_refs["period"], dtype=float),
        wwz_global=np.asarray(wwz_refs["global_wwz"], dtype=float),
        wwz_q95=np.asarray(wwz_refs["q95"], dtype=float),
        wwz_q99=np.asarray(wwz_refs["q99"], dtype=float),
        wwz_n_surrogates=int(wwz_refs["n_surrogates"]),
    )


def target_summaries(
    source_id: str,
    source_token: str,
    cwt_refs: dict,
    wwz_refs: dict,
    target_period: float,
    window_min: float,
    window_max: float,
) -> list[dict[str, object]]:
    rows = []
    for method, refs, observed_key, reference_95_key, reference_99_key in (
        ("CWT", cwt_refs, "gws", "reference_95", "reference_99"),
        ("WWZ", wwz_refs, "global_wwz", "q95", "q99"),
    ):
        period = np.asarray(refs["period"], dtype=float)
        nearest = int(np.nanargmin(np.abs(period - target_period)))
        observed = float(np.asarray(refs[observed_key], dtype=float)[nearest])
        reference_95 = float(np.asarray(refs[reference_95_key], dtype=float)[nearest])
        reference_99 = float(np.asarray(refs[reference_99_key], dtype=float)[nearest])
        rows.append(
            {
                "source_id": source_id,
                "source": source_token,
                "cadence": CADENCE,
                "window_mjd_min": window_min,
                "window_mjd_max": window_max,
                "method": method,
                "target_period_days": target_period,
                "nearest_grid_period_days": float(period[nearest]),
                "observed_statistic": observed,
                "reference_95": reference_95,
                "reference_99": reference_99,
                "above_95": bool(observed >= reference_95),
                "above_99": bool(observed >= reference_99),
                "n_surrogates": int(wwz_refs["n_surrogates"]) if method == "WWZ" else 0,
            }
        )
    return rows


if __name__ == "__main__":
    main()
