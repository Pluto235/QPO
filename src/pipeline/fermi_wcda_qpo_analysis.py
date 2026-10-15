#!/usr/bin/env python3
"""Run the official-WCDA CWT/WWZ significance workflow on Fermi light curves."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import run_cwt, run_wwz  # noqa: E402
from pipeline.official_lc_qpo_analysis import (  # noqa: E402
    PERIOD_RANGES,
    SIGNIFICANCE_COLUMNS,
    _assess_cwt,
    _assess_wwz,
    _plot_cwt_significance,
    _plot_wwz_significance,
)
from pipeline.periodicity_v1 import (  # noqa: E402
    _plot_periodicity_summary,
    _save_cwt,
    _save_wwz,
)
from utils.project_paths import (  # noqa: E402
    FERMI_WCDA_ALIGNED_DIR,
    FERMI_WCDA_PERIODICITY_DIR,
    FERMI_WCDA_PROCESSED_DIR,
    PROJECT_ROOT,
)


SOURCE_LABELS = {"mkn421": "Mrk 421", "mkn501": "Mrk 501"}
CADENCES = {"2day": 2, "8day": 8}
EXPECTED_BIN_COUNTS = {"2day": 803, "8day": 200}
MJD_START = 59280.66666667
DEFAULT_N_SURROGATES = 1000
DEFAULT_SEED = 20260825
FLUX_POLICIES = ("all-successful", "detections-only")
EXTRA_SIGNIFICANCE_COLUMNS = (
    "flux_policy",
    "family_curves",
    "bonferroni_4curve_global_fap",
    "passes_4curve_global_0p05",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", nargs="+", choices=sorted(SOURCE_LABELS), default=sorted(SOURCE_LABELS))
    parser.add_argument("--cadences", nargs="+", choices=sorted(CADENCES), default=sorted(CADENCES))
    parser.add_argument("--flux-policy", choices=FLUX_POLICIES, default="all-successful")
    parser.add_argument("--input-root", type=Path, default=FERMI_WCDA_PROCESSED_DIR)
    parser.add_argument("--aligned-dir", type=Path, default=FERMI_WCDA_ALIGNED_DIR)
    parser.add_argument("--periodicity-dir", type=Path, default=FERMI_WCDA_PERIODICITY_DIR)
    parser.add_argument("--n-surrogates", type=int, default=DEFAULT_N_SURROGATES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--wwz-time-divisions", type=int, default=80)
    parser.add_argument("--wwz-freq-step-factor", type=float, default=0.5)
    parser.add_argument("--wwz-color-scale", choices=("linear", "log"), default="linear")
    parser.add_argument("--skip-summary", action="store_true")
    parser.add_argument("--collect-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.n_surrogates < 1:
        raise ValueError("--n-surrogates must be positive.")
    if args.workers < 1:
        raise ValueError("--workers must be positive.")

    input_root = _resolve_path(args.input_root)
    aligned_root = _resolve_path(args.aligned_dir) / args.flux_policy
    periodicity_root = _resolve_path(args.periodicity_dir) / args.flux_policy
    if args.collect_only:
        collect_results(periodicity_root, args.flux_policy)
        return

    all_rows: list[dict[str, object]] = []
    for source_id in args.sources:
        for cadence in args.cadences:
            input_path = input_root / source_id / cadence / "full" / f"{source_id}_fermi_{cadence}_full.csv"
            seed = args.seed + sorted(SOURCE_LABELS).index(source_id) * 1000 + sorted(CADENCES).index(cadence)
            rows = run_source(args, source_id, cadence, input_path, aligned_root, periodicity_root, seed)
            all_rows.extend(rows)

    if not args.skip_summary:
        periodicity_root.mkdir(parents=True, exist_ok=True)
        summary = pd.DataFrame(all_rows, columns=SIGNIFICANCE_COLUMNS + EXTRA_SIGNIFICANCE_COLUMNS)
        summary.to_csv(periodicity_root / "fermi_wcda_qpo_significance_summary.csv", index=False)
        print(f"[OK] wrote {periodicity_root / 'fermi_wcda_qpo_significance_summary.csv'}")


def run_source(
    args: argparse.Namespace,
    source_id: str,
    cadence: str,
    input_path: Path,
    aligned_root: Path,
    periodicity_root: Path,
    seed: int,
) -> list[dict[str, object]]:
    raw, analysis = prepare_light_curve(input_path, source_id, cadence, args.flux_policy)
    aligned_dir = aligned_root / cadence / source_id
    output_dir = periodicity_root / cadence / source_id
    aligned_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"fermi_wcda_{cadence}"
    aligned_path = aligned_dir / f"{stem}_analysis_grid.csv"
    raw.to_csv(aligned_path, index=False)

    t = analysis["mjd"].to_numpy(dtype=float)
    flux = analysis["flux"].to_numpy(dtype=float)
    flux_err = analysis["flux_err"].to_numpy(dtype=float)
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
    _save_cwt(output_dir / f"{stem}_cwt.npz", cwt)
    _save_wwz(output_dir / f"{stem}_wwz.npz", wwz)

    label = f"{SOURCE_LABELS[source_id]} Fermi-LAT {cadence} photon flux (0.1-300 GeV)"
    cwt_rows, cwt_refs = _assess_cwt(source_id, SOURCE_LABELS[source_id], cadence, t, flux, cwt)
    wwz_rows, wwz_refs = _assess_wwz(
        source_id,
        SOURCE_LABELS[source_id],
        cadence,
        t,
        flux,
        flux_err,
        wwz,
        n_surrogates=args.n_surrogates,
        seed=seed,
        workers=args.workers,
    )
    rows = finalize_rows(cwt_rows + wwz_rows, cadence, args.flux_policy)
    pd.DataFrame(rows, columns=SIGNIFICANCE_COLUMNS + EXTRA_SIGNIFICANCE_COLUMNS).to_csv(
        output_dir / f"{stem}_significance.csv", index=False
    )
    save_significance_references(output_dir, stem, cwt_refs, wwz_refs)
    _plot_fermi_light_curve(
        output_dir / f"{stem}_lightcurve.png",
        label,
        raw,
        args.flux_policy,
        cadence_days=CADENCES[cadence],
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
        light_curve_note=f"Analysis policy: {args.flux_policy}",
    )
    write_provenance(
        output_dir / f"{stem}_provenance.json",
        input_path,
        source_id,
        cadence,
        args,
        raw,
        analysis,
        seed,
    )
    print(
        f"[OK] {source_id}/{cadence}: analysis={len(analysis)}/{len(raw)}, "
        f"candidates={len(rows)}, policy={args.flux_policy}"
    )
    return rows


def prepare_light_curve(
    input_path: Path, source_id: str, cadence: str, flux_policy: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if flux_policy not in FLUX_POLICIES:
        raise ValueError(f"Unknown flux policy: {flux_policy}")
    if not input_path.is_file():
        raise FileNotFoundError(f"Fermi light curve not found: {input_path}")
    raw = pd.read_csv(input_path)
    required = {
        "source_id", "cadence_days", "bin_index", "mjd", "flux", "flux_err", "flux_ul95",
        "ts", "fit_success", "is_detection", "is_upper_limit",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"{input_path} is missing required columns: {missing}")
    expected_count = EXPECTED_BIN_COUNTS[cadence]
    if len(raw) != expected_count:
        raise ValueError(f"{source_id}/{cadence} has {len(raw)} rows; expected {expected_count}.")
    if set(raw["source_id"].astype(str)) != {source_id}:
        raise ValueError(f"{input_path} contains a source other than {source_id}.")
    cadence_days = CADENCES[cadence]
    if set(pd.to_numeric(raw["cadence_days"], errors="coerce")) != {cadence_days}:
        raise ValueError(f"{input_path} does not use the expected {cadence_days}-day cadence.")

    raw = raw.sort_values("bin_index").reset_index(drop=True)
    expected_index = np.arange(expected_count)
    if not np.array_equal(raw["bin_index"].to_numpy(), expected_index):
        raise ValueError(f"{source_id}/{cadence} bin indices are not contiguous from zero.")
    expected_mjd = MJD_START + (expected_index + 0.5) * cadence_days
    if not np.allclose(raw["mjd"].to_numpy(dtype=float), expected_mjd, rtol=0.0, atol=1e-6):
        raise ValueError(f"{source_id}/{cadence} MJD centers do not match the frozen WCDA grid.")

    for column in ("mjd", "flux", "flux_err", "flux_ul95", "ts"):
        raw[column] = pd.to_numeric(raw[column], errors="coerce")
    usable = (
        raw["fit_success"].astype(bool)
        & np.isfinite(raw["mjd"])
        & np.isfinite(raw["flux"])
        & np.isfinite(raw["flux_err"])
        & (raw["flux_err"] > 0)
    )
    if flux_policy == "detections-only":
        usable &= np.isfinite(raw["ts"]) & (raw["ts"] >= 9.0)
    raw["flux_policy"] = flux_policy
    raw["is_usable_for_periodicity"] = usable
    analysis = raw.loc[usable].copy().sort_values("mjd").reset_index(drop=True)
    if len(analysis) < 8:
        raise ValueError(f"{source_id}/{cadence} has fewer than eight usable points under {flux_policy}.")
    return raw, analysis


def finalize_rows(
    rows: list[dict[str, object]], cadence: str, flux_policy: str
) -> list[dict[str, object]]:
    for row in rows:
        row["series"] = f"fermi_wcda_{cadence}"
        row["flux_policy"] = flux_policy
        row["family_curves"] = 4
        global_fap = float(row["global_fap"]) if pd.notna(row["global_fap"]) else np.nan
        adjusted = min(1.0, 4.0 * global_fap) if np.isfinite(global_fap) else np.nan
        row["bonferroni_4curve_global_fap"] = adjusted
        row["passes_4curve_global_0p05"] = bool(adjusted < 0.05) if np.isfinite(adjusted) else False
        row["note"] = str(row["note"]).replace("Response-period systematics are not modeled.", "")
        row["note"] += " Four-curve Bonferroni value is reported separately for WWZ global FAP."
    return rows


def save_significance_references(
    output_dir: Path,
    stem: str,
    cwt_refs: dict[str, np.ndarray | float],
    wwz_refs: dict[str, np.ndarray | float],
) -> None:
    np.savez_compressed(
        output_dir / f"{stem}_cwt_significance.npz",
        period=cwt_refs["period"],
        gws=cwt_refs["gws"],
        reference_95=cwt_refs["reference_95"],
        reference_99=cwt_refs["reference_99"],
        alpha=cwt_refs["alpha"],
        period_min=cwt_refs["period_min"],
        period_max=cwt_refs["period_max"],
    )
    np.savez_compressed(
        output_dir / f"{stem}_wwz_significance.npz",
        period=wwz_refs["period"],
        global_wwz=wwz_refs["global_wwz"],
        q95=wwz_refs["q95"],
        q99=wwz_refs["q99"],
        alpha=wwz_refs["alpha"],
        n_surrogates=wwz_refs["n_surrogates"],
        period_min=wwz_refs["period_min"],
        period_max=wwz_refs["period_max"],
    )


def write_provenance(
    path: Path,
    input_path: Path,
    source_id: str,
    cadence: str,
    args: argparse.Namespace,
    raw: pd.DataFrame,
    analysis: pd.DataFrame,
    seed: int,
) -> None:
    payload = {
        "source_id": source_id,
        "cadence": cadence,
        "input_path": str(input_path),
        "input_sha256": _sha256(input_path),
        "input_rows": len(raw),
        "analysis_rows": len(analysis),
        "missing_or_rejected_rows": int(len(raw) - len(analysis)),
        "flux_policy": args.flux_policy,
        "period_range_days": list(PERIOD_RANGES[cadence]),
        "cwt": {"mother": "Morlet(6)", "dj": 1.0 / 12.0, "significance": "PyCWT time-averaged AR(1)"},
        "wwz": {
            "time_divisions": args.wwz_time_divisions,
            "freq_step_factor": args.wwz_freq_step_factor,
            "decay_constant": 0.0125,
            "n_ar1_surrogates": args.n_surrogates,
            "local_window_fraction": 0.10,
        },
        "seed": seed,
        "multiple_testing": "Bonferroni across four source-cadence Fermi curves, applied to WWZ single-curve global FAP",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def collect_results(periodicity_root: Path, flux_policy: str) -> Path:
    paths = [
        periodicity_root / cadence / source_id / f"fermi_wcda_{cadence}_significance.csv"
        for source_id in sorted(SOURCE_LABELS)
        for cadence in sorted(CADENCES)
    ]
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Cannot collect Fermi QPO results; missing: {missing}")
    frames = [pd.read_csv(path) for path in paths]
    output = periodicity_root / "fermi_wcda_qpo_significance_summary.csv"
    pd.concat(frames, ignore_index=True).to_csv(output, index=False)
    print(f"[OK] collected 4/4 {flux_policy} source-cadence products -> {output}")
    return output


def _plot_fermi_light_curve(
    path: Path,
    label: str,
    raw: pd.DataFrame,
    flux_policy: str,
    cadence_days: int,
) -> None:
    fig, axis = plt.subplots(figsize=(12.5, 4.4), constrained_layout=True)
    fit_ok = raw["fit_success"].astype(bool) & np.isfinite(raw["flux"]) & np.isfinite(raw["flux_err"])
    detections = fit_ok & (raw["ts"] >= 9.0)
    upper_limits = fit_ok & (raw["ts"] < 9.0) & np.isfinite(raw["flux_ul95"])
    failed = ~fit_ok
    display_lower, display_upper = fermi_light_curve_display_ylim(raw, detections)
    clipped_upper_limits = upper_limits & (raw["flux_ul95"] > display_upper)
    rolling_bins = max(1, round(32 / cadence_days))
    rolling_median = raw["flux"].where(fit_ok).rolling(rolling_bins, center=True, min_periods=1).median()
    axis.errorbar(
        raw.loc[detections, "mjd"], raw.loc[detections, "flux"], yerr=raw.loc[detections, "flux_err"],
        fmt="o", ms=2.5, capsize=1.3, elinewidth=0.6, color="#0072B2", label=r"Detection ($TS\geq9$)",
    )
    if upper_limits.any():
        in_range_upper_limits = upper_limits & ~clipped_upper_limits
        axis.scatter(
            raw.loc[in_range_upper_limits, "mjd"], raw.loc[in_range_upper_limits, "flux_ul95"], marker="v", s=16,
            facecolors="none", edgecolors="#D55E00", linewidths=0.7, label="95% upper limit (MLE retained in all-successful policy)",
        )
    if clipped_upper_limits.any():
        marker_y = display_upper - 0.035 * (display_upper - display_lower)
        axis.scatter(
            raw.loc[clipped_upper_limits, "mjd"],
            np.full(int(clipped_upper_limits.sum()), marker_y),
            marker="^",
            s=18,
            facecolors="none",
            edgecolors="#D55E00",
            linewidths=0.8,
            label="95% upper limit above display range",
            zorder=5,
        )
    if failed.any():
        baseline = np.zeros(int(failed.sum()))
        axis.scatter(raw.loc[failed, "mjd"], baseline, marker="x", s=18, color="#8A8A8A", label="Failed fit / gap")
    axis.plot(
        raw["mjd"],
        rolling_median,
        color="#B54A3A",
        linewidth=2.0,
        label="32-day rolling median (display only)",
        zorder=4,
    )
    axis.set_xlabel("MJD")
    axis.set_ylabel(r"Photon flux (cm$^{-2}$ s$^{-1}$)")
    axis.set_title(f"{label} - {flux_policy}")
    axis.set_ylim(display_lower, display_upper)
    axis.grid(True, alpha=0.25)
    axis.legend(loc="best", fontsize=8)
    if clipped_upper_limits.any():
        axis.text(
            0.995,
            0.02,
            f"{int(clipped_upper_limits.sum())} upper limit(s) clipped by display y-axis",
            transform=axis.transAxes,
            ha="right",
            va="bottom",
            fontsize=8,
            color="#8A3D35",
        )
    fig.savefig(path, dpi=180)
    plt.close(fig)


def fermi_light_curve_display_ylim(raw: pd.DataFrame, detections: pd.Series) -> tuple[float, float]:
    """Return a display scale that preserves all detections without letting upper limits dominate."""
    detection_high = (raw.loc[detections, "flux"] + raw.loc[detections, "flux_err"]).to_numpy(dtype=float)
    finite_high = detection_high[np.isfinite(detection_high)]
    if len(finite_high):
        reference_upper = float(np.max(finite_high))
    else:
        fallback_flux = raw.loc[np.isfinite(raw["flux"]), "flux"].to_numpy(dtype=float)
        if not len(fallback_flux):
            raise ValueError("Cannot determine a display range without finite Fermi flux values.")
        reference_upper = float(np.max(fallback_flux))
    if reference_upper <= 0:
        raise ValueError("Cannot determine a positive display range from Fermi flux values.")
    display_upper = 1.10 * reference_upper
    detection_low = (raw.loc[detections, "flux"] - raw.loc[detections, "flux_err"]).to_numpy(dtype=float)
    finite_low = detection_low[np.isfinite(detection_low)]
    display_lower = min(0.0, float(np.min(finite_low)) if len(finite_low) else 0.0, -0.05 * display_upper)
    return display_lower, display_upper


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    main()
