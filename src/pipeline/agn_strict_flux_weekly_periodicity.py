#!/usr/bin/env python3
"""Run CWT/WWZ quick-look products for the strict WCDA weekly flux AGN survey."""

from __future__ import annotations

import argparse
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
from pipeline.periodicity_v1 import (  # noqa: E402
    _plot_cwt,
    _plot_periodicity_summary,
    _plot_wwz,
    _save_cwt,
    _save_wwz,
)
from utils.project_paths import ALIGNED_DIR, PERIODICITY_DIR, PROJECT_ROOT, RESULTS_DIR, WCDA_WEEK_DIR  # noqa: E402
from utils.source_registry import SOURCE_REGISTRY, WCDA_STRICT_FLUX_SOURCE_IDS, get_source  # noqa: E402


FLUX_INPUT_DIR = RESULTS_DIR / "flux_strict_agn_week"
SURVEY_ALIGNED_DIR = ALIGNED_DIR / "agn_wcda_weekly_flux_survey"
SURVEY_PERIODICITY_DIR = PERIODICITY_DIR / "agn_wcda_weekly_flux_survey"
SUMMARY_CSV = SURVEY_PERIODICITY_DIR / "agn_wcda_weekly_flux_survey_summary.csv"
STRICT_FLUX_START = "2021-03-08"
STRICT_FLUX_END = "2025-07-27"
EXPECTED_ROWS = 229
REQUIRED_COLUMNS = {
    "source",
    "mjd",
    "date1",
    "date2",
    "F0",
    "F0_err",
    "F0_order",
    "N0",
    "N0_err",
    "TS",
    "fit_status",
    "fit_log_status",
}
NUMERIC_COLUMNS = ("mjd", "F0", "F0_err", "F0_order", "N0", "N0_err", "TS", "gamma", "E0_TeV", "n_inputs")
ALIGNED_COLUMNS = (
    "source_id",
    "source",
    "name",
    "cadence",
    "mjd",
    "date1",
    "date2",
    "N0",
    "N0_err",
    "F0",
    "F0_err",
    "F0_order",
    "TS",
    "gamma",
    "E0_TeV",
    "n_inputs",
    "fit_status",
    "fit_log_status",
    "is_usable_for_periodicity",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=sorted(SOURCE_REGISTRY),
        help="Strict-flux source ids to run. Defaults to all strict-flux sources when --all-strict-flux-sources is set.",
    )
    parser.add_argument(
        "--all-strict-flux-sources",
        action="store_true",
        help="Run the fixed 10-source strict WCDA weekly flux survey.",
    )
    parser.add_argument("--input-dir", type=Path, default=FLUX_INPUT_DIR)
    parser.add_argument("--aligned-dir", type=Path, default=SURVEY_ALIGNED_DIR)
    parser.add_argument("--periodicity-dir", type=Path, default=SURVEY_PERIODICITY_DIR)
    parser.add_argument("--wwz-time-divisions", type=int, default=80)
    parser.add_argument("--wwz-freq-step-factor", type=float, default=0.5)
    parser.add_argument("--wwz-parallel", action="store_true")
    parser.add_argument("--wwz-color-scale", choices=("linear", "log"), default="linear")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    source_ids = _resolve_source_ids(args)
    aligned_base = _resolve_path(args.aligned_dir)
    periodicity_base = _resolve_path(args.periodicity_dir)
    input_dir = _resolve_path(args.input_dir)

    rows = []
    for source_id in source_ids:
        rows.append(run_for_source(args, source_id, input_dir, aligned_base, periodicity_base))

    summary = pd.DataFrame(rows)
    periodicity_base.mkdir(parents=True, exist_ok=True)
    summary.to_csv(periodicity_base / "agn_wcda_weekly_flux_survey_summary.csv", index=False)
    print(f"[OK] wrote strict flux survey summary -> {(periodicity_base / 'agn_wcda_weekly_flux_survey_summary.csv').relative_to(PROJECT_ROOT)}")


def run_for_source(
    args: argparse.Namespace,
    source_id: str,
    input_dir: Path,
    aligned_base: Path,
    periodicity_base: Path,
) -> dict[str, object]:
    source = get_source(source_id)
    input_path = _strict_flux_path(input_dir, source_id)
    raw = _read_and_validate_flux_csv(input_path, source_id)
    aligned = _build_aligned_flux(raw, source_id)

    aligned_dir = aligned_base / source_id
    periodicity_dir = periodicity_base / source_id
    aligned_dir.mkdir(parents=True, exist_ok=True)
    periodicity_dir.mkdir(parents=True, exist_ok=True)

    aligned_path = aligned_dir / "wcda_strict_flux_weekly_aligned.csv"
    aligned.to_csv(aligned_path, index=False)

    usable = _usable_flux_rows(aligned, source_id)
    t = usable["mjd"].to_numpy(dtype=float)
    flux = usable["N0"].to_numpy(dtype=float)
    flux_err = usable["N0_err"].to_numpy(dtype=float)

    cwt = run_cwt(t, flux, period_min=50.0, period_max=600.0)
    wwz = run_wwz(
        t,
        flux,
        flux_err,
        period_min=50.0,
        period_max=600.0,
        time_divisions=args.wwz_time_divisions,
        freq_step_factor=args.wwz_freq_step_factor,
        parallel=args.wwz_parallel,
    )

    _save_cwt(periodicity_dir / "wcda_strict_flux_weekly_cwt.npz", cwt)
    _save_wwz(periodicity_dir / "wcda_strict_flux_weekly_wwz.npz", wwz)
    plot_label = f"{source.label} WCDA strict weekly flux"
    _plot_flux_lightcurve(periodicity_dir / "wcda_strict_flux_weekly_lightcurve.png", plot_label, aligned)
    _plot_cwt(periodicity_dir / "wcda_strict_flux_weekly_cwt.png", plot_label, t, flux, flux_err, cwt)
    _plot_wwz(periodicity_dir / "wcda_strict_flux_weekly_wwz.png", plot_label, wwz, color_scale=args.wwz_color_scale)
    _plot_periodicity_summary(
        periodicity_dir / "wcda_strict_flux_weekly_periodicity.png",
        plot_label,
        t,
        flux,
        flux_err,
        cwt,
        wwz,
        color_scale=args.wwz_color_scale,
        include_global_row=True,
    )

    row = _summary_row(source_id, source.label, aligned, usable, cwt, wwz)
    pd.DataFrame([row]).to_csv(periodicity_dir / "periodicity_flux_summary.csv", index=False)
    print(
        f"[OK] {source_id}: usable={len(usable)}/{len(aligned)} "
        f"-> {periodicity_dir.relative_to(PROJECT_ROOT)}"
    )
    return row


def _resolve_source_ids(args: argparse.Namespace) -> list[str]:
    if args.all_strict_flux_sources:
        return list(WCDA_STRICT_FLUX_SOURCE_IDS)
    if args.sources:
        invalid = sorted(set(args.sources) - set(WCDA_STRICT_FLUX_SOURCE_IDS))
        if invalid:
            raise ValueError(f"Sources do not have strict-flux survey inputs in this workflow: {invalid}")
        return list(args.sources)
    raise ValueError("Pass --all-strict-flux-sources or --sources.")


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def _strict_flux_path(input_dir: Path, source_id: str) -> Path:
    source = get_source(source_id)
    if source_id in {"mkn421", "mkn501"}:
        return WCDA_WEEK_DIR / f"LHAASO-WCDA_{source.lhaaso_token}_{STRICT_FLUX_START}_{STRICT_FLUX_END}_week_flux.csv"
    return input_dir / f"LHAASO-WCDA_{source.lhaaso_token}_{STRICT_FLUX_START}_{STRICT_FLUX_END}_week_flux.csv"


def _read_and_validate_flux_csv(path: Path, source_id: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing strict flux CSV for {source_id}: {path}")
    df = pd.read_csv(path)
    df.columns = [str(col).strip() for col in df.columns]
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    if len(df) != EXPECTED_ROWS:
        raise ValueError(f"{path} should have {EXPECTED_ROWS} rows, found {len(df)}.")
    if str(df["date1"].iloc[0]) != STRICT_FLUX_START or str(df["date2"].iloc[-1]) != STRICT_FLUX_END:
        raise ValueError(
            f"{path} has unexpected date range: date1[0]={df['date1'].iloc[0]}, date2[-1]={df['date2'].iloc[-1]}"
        )
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if not np.all(np.isfinite(df["N0_err"])) or not np.all(df["N0_err"] > 0):
        raise ValueError(f"{path} has non-finite or non-positive N0_err values.")
    return df.sort_values("mjd").reset_index(drop=True)


def _build_aligned_flux(df: pd.DataFrame, source_id: str) -> pd.DataFrame:
    out = df.copy()
    out.insert(0, "source_id", source_id)
    fit_status = out["fit_status"].astype(str).str.strip()
    fit_log_status = out["fit_log_status"].astype(str).str.strip()
    out["is_usable_for_periodicity"] = (
        (fit_status == "OK")
        & (fit_log_status == "OK")
        & np.isfinite(out["mjd"])
        & np.isfinite(out["N0"])
        & np.isfinite(out["N0_err"])
        & (out["N0_err"] > 0)
    )
    keep = [col for col in ALIGNED_COLUMNS if col in out.columns]
    return out.loc[:, keep].sort_values("mjd").reset_index(drop=True)


def _usable_flux_rows(aligned: pd.DataFrame, source_id: str) -> pd.DataFrame:
    usable = aligned.loc[aligned["is_usable_for_periodicity"].astype(bool)].copy()
    if len(usable) < 4:
        raise ValueError(f"{source_id} has fewer than four usable strict-flux weekly rows.")
    return usable.sort_values("mjd").reset_index(drop=True)


def _summary_row(
    source_id: str,
    source_label: str,
    aligned: pd.DataFrame,
    usable: pd.DataFrame,
    cwt: dict,
    wwz: dict,
) -> dict[str, object]:
    cwt_period = np.asarray(cwt["period"], dtype=float)
    cwt_power = np.asarray(cwt["gws"], dtype=float)
    cwt_mask = np.asarray(cwt["mask_period"], dtype=bool) & np.isfinite(cwt_power)
    cwt_peak_idx = int(np.nanargmax(np.where(cwt_mask, cwt_power, np.nan)))

    wwz_period = np.asarray(wwz["period_axis"], dtype=float)
    wwz_power = np.asarray(wwz["global_wwz"], dtype=float)
    wwz_mask = (
        np.isfinite(wwz_period)
        & np.isfinite(wwz_power)
        & (wwz_period >= float(wwz["period_min"]))
        & (wwz_period <= float(wwz["period_max"]))
    )
    wwz_peak_idx = int(np.nanargmax(np.where(wwz_mask, wwz_power, np.nan)))

    t = usable["mjd"].to_numpy(dtype=float)
    flux = usable["N0"].to_numpy(dtype=float)
    flux_err = usable["N0_err"].to_numpy(dtype=float)
    return {
        "source_id": source_id,
        "source": source_label,
        "series": "wcda_strict_flux_weekly",
        "n_rows": int(len(aligned)),
        "n_points": int(len(usable)),
        "n_bad_fit_rows": int(len(aligned) - len(usable)),
        "mjd_min": float(np.nanmin(t)),
        "mjd_max": float(np.nanmax(t)),
        "date_min": str(usable["date1"].iloc[0]) if "date1" in usable else "",
        "date_max": str(usable["date2"].iloc[-1]) if "date2" in usable else "",
        "median_dt_days": float(np.nanmedian(np.diff(t))),
        "flux_min": float(np.nanmin(flux)),
        "flux_max": float(np.nanmax(flux)),
        "median_flux_err": float(np.nanmedian(flux_err)),
        "cwt_peak_period_days": float(cwt_period[cwt_peak_idx]),
        "cwt_peak_gws": float(cwt_power[cwt_peak_idx]),
        "wwz_peak_period_days": float(wwz_period[wwz_peak_idx]),
        "wwz_peak_power": float(wwz_power[wwz_peak_idx]),
    }


def _plot_flux_lightcurve(path: Path, title: str, aligned: pd.DataFrame) -> None:
    plot_df = aligned.copy()
    for col in ("mjd", "N0", "N0_err", "TS"):
        if col in plot_df.columns:
            plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce")
    usable = plot_df["is_usable_for_periodicity"].astype(bool)
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(13.5, 6.4),
        sharex=True,
        gridspec_kw={"height_ratios": [1.35, 0.85]},
        constrained_layout=True,
    )
    ax_flux, ax_ts = axes
    ax_flux.errorbar(
        plot_df.loc[usable, "mjd"],
        plot_df.loc[usable, "N0"],
        yerr=plot_df.loc[usable, "N0_err"],
        fmt="o-",
        ms=3.1,
        lw=0.9,
        capsize=2,
        color="#255c99",
        ecolor="#7da0c9",
        label="usable fit",
    )
    if (~usable).any():
        ax_flux.scatter(
            plot_df.loc[~usable, "mjd"],
            plot_df.loc[~usable, "N0"],
            marker="x",
            s=36,
            color="#b65c2a",
            label="excluded fit",
        )
    ax_flux.axhline(0.0, color="0.4", lw=0.8, alpha=0.8)
    ax_flux.set_title(title)
    ax_flux.set_ylabel("N0 at 3 TeV\ncm$^{-2}$ s$^{-1}$ TeV$^{-1}$")
    ax_flux.grid(True, alpha=0.25)
    ax_flux.legend(loc="upper right", frameon=False)

    ax_ts.plot(plot_df["mjd"], plot_df["TS"], color="#1b7f5c", lw=1.0, marker="o", ms=2.6)
    ax_ts.set_xlabel("MJD")
    ax_ts.set_ylabel("TS")
    ax_ts.grid(True, alpha=0.25)
    fig.savefig(path, dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
