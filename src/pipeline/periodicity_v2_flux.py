#!/usr/bin/env python3
"""Build the WCDA strict-flux periodicity v2 products and report."""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from astropy.time import Time  # noqa: E402


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import (  # noqa: E402
    align_to_reference_nearest,
    read_wcda_strict_flux_csv,
    run_cwt,
    run_wwz,
    usable_light_curve,
)
from utils.project_paths import (  # noqa: E402
    ALIGNED_DIR,
    FERMI_WEEK_DIR,
    MULTIWAVELENGTH_DIR,
    PERIODICITY_DIR,
    PROJECT_ROOT,
    WCDA_DAY_DIR,
    WCDA_WEEK_DIR,
)


REPORT_MD = PROJECT_ROOT / "reports" / "periodicity_v2_report.md"
REPORT_HTML = PROJECT_ROOT / "reports" / "periodicity_v2_report.html"
ALIGNED_V2_DIR = ALIGNED_DIR / "periodicity_v2"
PERIODICITY_V2_DIR = PERIODICITY_DIR / "periodicity_v2"
ANY_REPORTS_DIR = PROJECT_ROOT.parent / "any-reports"
PUBLISH_SLUG = "qpo-periodicity-v2"
TELAMON_CACHE = MULTIWAVELENGTH_DIR / "mkn421" / "telamon_lhaaso_2022_2026" / "telamon_averaged_bands.csv"
TELAMON_V2_DIR = MULTIWAVELENGTH_DIR / "mkn421" / "telamon_lhaaso_2022_2026_flux_v2"
TELAMON_V2_PNG = TELAMON_V2_DIR / "mkn421_telamon_lhaaso_2022_2025_weekly_flux.png"
FERMI_WEEK_MKN421 = FERMI_WEEK_DIR / "Mrk421_Fermi_weekly_TSge9_MJD.csv"
MKN421_DAY_FLUX = WCDA_DAY_DIR / "LHAASO-WCDA_Mkn421_2021-03-08_2025-07-31_day_flux.csv"
MKN421_WEEK_FLUX = WCDA_WEEK_DIR / "LHAASO-WCDA_Mkn421_2021-03-08_2025-07-27_week_flux.csv"
MKN501_DAY_FLUX = WCDA_DAY_DIR / "LHAASO-WCDA_Mkn501_2021-03-08_2025-07-31_day_flux.csv"
MKN501_WEEK_FLUX = WCDA_WEEK_DIR / "LHAASO-WCDA_Mkn501_2021-03-08_2025-07-27_week_flux.csv"
DEFAULT_WWZ_TIME_DIVISIONS = 80
DEFAULT_WWZ_FREQ_STEP_FACTOR = 0.5
WCDA_N0_ERR_MEDIAN_FACTOR = 5.0
TARGET_PERIOD_DAYS = 140.0
TARGET_WINDOW_FRACTION = 0.10
XGM_WINDOW = (60200.0, 60700.0)
XGM_REFERENCE_PERIOD_DAYS = 51.05
XGM_SIGNIFICANCE_CSV = PERIODICITY_V2_DIR / "xgm_poster_repro" / "mkn421" / "xgm_flux_quicklook_significance.csv"
XGM_SIGNIFICANCE_PNG = PERIODICITY_V2_DIR / "xgm_poster_repro" / "mkn421" / "mkn421_daily_flux_60200_60700_wwz_significance.png"
XGM_CWT_SUMMARY_CSV = PERIODICITY_V2_DIR / "xgm_poster_repro" / "mkn421" / "xgm_flux_cwt_quicklook_summary.csv"
XGM_CWT_QUICKLOOK_PNG = PERIODICITY_V2_DIR / "xgm_poster_repro" / "mkn421" / "mkn421_daily_flux_60200_60700_cwt_quicklook.png"
XGM_CWT_SIGNIFICANCE_CSV = PERIODICITY_V2_DIR / "xgm_poster_repro" / "mkn421" / "xgm_flux_cwt_significance.csv"
XGM_CWT_SIGNIFICANCE_PNG = PERIODICITY_V2_DIR / "xgm_poster_repro" / "mkn421" / "mkn421_daily_flux_60200_60700_cwt_significance.png"
XGM_V1_COUNTS_SIGNIFICANCE_CSV = PERIODICITY_DIR / "xgm_poster_repro" / "mkn421" / "xgm_poster_wwz_local_significance.csv"
XGM_V1_COUNTS_QUICKLOOK_PNG = PERIODICITY_DIR / "xgm_poster_repro" / "mkn421" / "mkn421_daily_60200_60700_wwz_poster_style.png"
XGM_V1_COUNTS_SIGNIFICANCE_PNG = PERIODICITY_DIR / "xgm_poster_repro" / "mkn421" / "mkn421_daily_60200_60700_wwz_local_significance.png"
MIN_XGM_SIGNIFICANCE_SURROGATES = 1000
FIG_DPI = 180


@dataclass(frozen=True)
class SourceFluxConfig:
    source_id: str
    label: str
    day_path: Path
    week_path: Path


@dataclass(frozen=True)
class SeriesSpec:
    source_id: str
    source_label: str
    series: str
    label: str
    cadence: str
    flux_kind: str
    aligned_path: Path
    output_dir: Path
    period_min: float
    period_max: float


@dataclass(frozen=True)
class V2Outputs:
    summary: pd.DataFrame
    qc_summary: pd.DataFrame
    fixed_window: pd.DataFrame
    xgm_summary: pd.DataFrame
    xgm_significance: pd.DataFrame | None
    xgm_cwt_summary: pd.DataFrame | None
    xgm_cwt_significance: pd.DataFrame | None
    xgm_poster_comparison: pd.DataFrame | None
    telamon_summary: dict[str, object]
    figures: dict[str, Path]


SOURCE_CONFIGS = (
    SourceFluxConfig("mkn421", "Mrk 421", MKN421_DAY_FLUX, MKN421_WEEK_FLUX),
    SourceFluxConfig("mkn501", "Mrk 501", MKN501_DAY_FLUX, MKN501_WEEK_FLUX),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wwz-time-divisions", type=int, default=DEFAULT_WWZ_TIME_DIVISIONS)
    parser.add_argument("--wwz-freq-step-factor", type=float, default=DEFAULT_WWZ_FREQ_STEP_FACTOR)
    parser.add_argument("--wwz-parallel", action="store_true")
    parser.add_argument("--any-reports-dir", type=Path, default=ANY_REPORTS_DIR)
    parser.add_argument("--skip-publish", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    outputs = run_v2_products(args)
    validate_v2_outputs(outputs)
    write_reports(outputs, REPORT_MD, REPORT_HTML, public_asset_map=None)
    if not args.skip_publish:
        publish_report(outputs, args.any_reports_dir)
    print(f"[OK] v2 report -> {REPORT_HTML.relative_to(PROJECT_ROOT)}")


def run_v2_products(args: argparse.Namespace) -> V2Outputs:
    summary_rows: list[dict[str, object]] = []
    qc_rows: list[dict[str, object]] = []
    figures: dict[str, Path] = {}
    for config in SOURCE_CONFIGS:
        aligned_dir = ALIGNED_V2_DIR / config.source_id
        output_dir = PERIODICITY_V2_DIR / config.source_id
        aligned_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        day_aligned, day_qc = write_wcda_flux_aligned(config.day_path, aligned_dir / "wcda_daily_flux_aligned.csv")
        week_aligned, week_qc = write_wcda_flux_aligned(config.week_path, aligned_dir / "wcda_weekly_flux_aligned.csv")
        qc_rows.extend([day_qc, week_qc])

        for cadence, aligned, period_min, period_max in (
            ("daily", day_aligned, 5.0, 200.0),
            ("weekly", week_aligned, 50.0, 600.0),
        ):
            series = f"wcda_{cadence}_flux"
            spec = SeriesSpec(
                source_id=config.source_id,
                source_label=config.label,
                series=series,
                label=f"{config.label} WCDA {cadence} flux",
                cadence=cadence,
                flux_kind="WCDA N0",
                aligned_path=aligned_dir / f"wcda_{cadence}_flux_aligned.csv",
                output_dir=output_dir,
                period_min=period_min,
                period_max=period_max,
            )
            row, figure = run_periodicity_series(
                spec,
                aligned,
                time_divisions=args.wwz_time_divisions,
                freq_step_factor=args.wwz_freq_step_factor,
                parallel=args.wwz_parallel,
            )
            summary_rows.append(row)
            figures[f"{config.source_id}_{series}"] = figure

        if config.source_id == "mkn421":
            fermi_aligned_path = aligned_dir / "fermi_weekly_on_wcda_weekly_flux_axis.csv"
            fermi_aligned = write_fermi_on_wcda_flux_axis(week_aligned, fermi_aligned_path)
            spec = SeriesSpec(
                source_id=config.source_id,
                source_label=config.label,
                series="fermi_weekly_on_wcda_flux_axis",
                label=f"{config.label} Fermi weekly on WCDA flux axis",
                cadence="weekly",
                flux_kind="Fermi flux",
                aligned_path=fermi_aligned_path,
                output_dir=output_dir,
                period_min=50.0,
                period_max=600.0,
            )
            row, figure = run_periodicity_series(
                spec,
                fermi_aligned.rename(columns={"fermi_flux": "flux", "fermi_flux_err": "flux_err"}),
                time_divisions=args.wwz_time_divisions,
                freq_step_factor=args.wwz_freq_step_factor,
                parallel=args.wwz_parallel,
            )
            summary_rows.append(row)
            figures["mkn421_fermi_weekly_on_wcda_flux_axis"] = figure

    summary = pd.DataFrame(summary_rows)
    qc_summary = pd.DataFrame(qc_rows)
    PERIODICITY_V2_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(PERIODICITY_V2_DIR / "periodicity_v2_summary.csv", index=False)
    qc_summary.to_csv(PERIODICITY_V2_DIR / "periodicity_v2_qc_summary.csv", index=False)

    fixed_window, fixed_fig = run_fixed_window(args)
    figures["mkn421_fixed_window"] = fixed_fig
    xgm_summary, xgm_fig = run_xgm_flux_quicklook(args)
    figures["mkn421_xgm_60200_60700"] = xgm_fig
    xgm_significance = load_xgm_significance()
    if xgm_significance is not None:
        figures["mkn421_xgm_60200_60700_significance"] = XGM_SIGNIFICANCE_PNG
    xgm_cwt_summary = load_xgm_cwt_summary()
    if xgm_cwt_summary is not None:
        figures["mkn421_xgm_60200_60700_cwt"] = XGM_CWT_QUICKLOOK_PNG
    xgm_cwt_significance = load_xgm_cwt_significance()
    if xgm_cwt_significance is not None:
        figures["mkn421_xgm_60200_60700_cwt_significance"] = XGM_CWT_SIGNIFICANCE_PNG
    xgm_poster_comparison = build_xgm_poster_comparison(xgm_significance, xgm_cwt_significance)
    if XGM_V1_COUNTS_QUICKLOOK_PNG.exists():
        figures["mkn421_xgm_60200_60700_counts_quicklook"] = XGM_V1_COUNTS_QUICKLOOK_PNG
    if XGM_V1_COUNTS_SIGNIFICANCE_PNG.exists():
        figures["mkn421_xgm_60200_60700_counts_significance"] = XGM_V1_COUNTS_SIGNIFICANCE_PNG
    telamon_summary = run_telamon_flux_sync()
    figures["mkn421_telamon_flux"] = TELAMON_V2_PNG
    return V2Outputs(
        summary,
        qc_summary,
        fixed_window,
        xgm_summary,
        xgm_significance,
        xgm_cwt_summary,
        xgm_cwt_significance,
        xgm_poster_comparison,
        telamon_summary,
        figures,
    )


def write_wcda_flux_aligned(input_path: Path, output_path: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    lc = read_wcda_strict_flux_csv(input_path)
    err_median = float(lc["wcda_n0_err"].median())
    err_limit = WCDA_N0_ERR_MEDIAN_FACTOR * err_median
    qc_mask = lc["wcda_n0_err"] <= err_limit
    rejected = lc.loc[~qc_mask].copy()
    lc = lc.loc[qc_mask].copy()
    keep = [
        "source",
        "cadence",
        "name",
        "mjd",
        "date1",
        "date2",
        "n_inputs",
        "gamma",
        "E0_TeV",
        "wcda_n0",
        "wcda_n0_err",
        "N0",
        "N0_err",
        "F0",
        "F0_err",
        "F0_order",
        "TS",
        "fit_status",
    ]
    keep = [col for col in keep if col in lc.columns]
    out = lc.loc[:, keep].copy()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False)
    rejected_path = output_path.with_name(f"{output_path.stem}_qc_rejected.csv")
    rejected.loc[:, [col for col in keep if col in rejected.columns]].to_csv(rejected_path, index=False)
    qc_row = {
        "source": str(out["source"].iloc[0]) if "source" in out.columns and not out.empty else input_path.stem,
        "cadence": str(out["cadence"].iloc[0]) if "cadence" in out.columns and not out.empty else "",
        "input_path": _relative_path(input_path, PROJECT_ROOT),
        "aligned_path": _relative_path(output_path, PROJECT_ROOT),
        "rejected_path": _relative_path(rejected_path, PROJECT_ROOT),
        "ok_rows_before_qc": int(len(lc) + len(rejected)),
        "kept_rows": int(len(out)),
        "rejected_rows": int(len(rejected)),
        "n0_err_median": err_median,
        "n0_err_limit": err_limit,
        "n0_err_median_factor": WCDA_N0_ERR_MEDIAN_FACTOR,
    }
    return out.rename(columns={"wcda_n0": "flux", "wcda_n0_err": "flux_err"}), qc_row


def write_fermi_on_wcda_flux_axis(wcda_week: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    if not FERMI_WEEK_MKN421.exists():
        raise FileNotFoundError(f"Missing Fermi weekly input: {FERMI_WEEK_MKN421}")
    fermi = pd.read_csv(FERMI_WEEK_MKN421)
    fermi_lc = usable_light_curve(fermi, "flux", "flux_err")
    aligned = align_to_reference_nearest(
        wcda_week["mjd"].to_numpy(dtype=float),
        fermi_lc,
        tolerance_days=3.6,
        target_prefix="fermi",
    )
    aligned = aligned.loc[
        np.isfinite(pd.to_numeric(aligned["mjd"], errors="coerce"))
        & np.isfinite(pd.to_numeric(aligned["fermi_flux"], errors="coerce"))
        & np.isfinite(pd.to_numeric(aligned["fermi_flux_err"], errors="coerce"))
        & (pd.to_numeric(aligned["fermi_flux_err"], errors="coerce") > 0)
    ].copy()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    aligned.to_csv(output_path, index=False)
    return aligned


def run_periodicity_series(
    spec: SeriesSpec,
    lc: pd.DataFrame,
    *,
    time_divisions: int,
    freq_step_factor: float,
    parallel: bool,
) -> tuple[dict[str, object], Path]:
    clean = _clean_lc(lc)
    t = clean["mjd"].to_numpy(dtype=float)
    y = clean["flux"].to_numpy(dtype=float)
    yerr = clean["flux_err"].to_numpy(dtype=float)
    cwt = run_cwt(t, y, period_min=spec.period_min, period_max=spec.period_max)
    wwz = run_wwz(
        t,
        y,
        yerr,
        period_min=spec.period_min,
        period_max=spec.period_max,
        time_divisions=time_divisions,
        freq_step_factor=freq_step_factor,
        parallel=parallel,
    )

    _save_cwt(spec.output_dir / f"{spec.series}_cwt.npz", cwt)
    _save_wwz(spec.output_dir / f"{spec.series}_wwz.npz", wwz)
    figure = spec.output_dir / f"{spec.series}_periodicity.png"
    plot_periodicity_figure(
        figure,
        spec.label,
        clean,
        cwt,
        wwz,
        y_label=_y_label(spec.flux_kind),
    )
    return summary_row(spec, clean, cwt, wwz), figure


def _clean_lc(lc: pd.DataFrame) -> pd.DataFrame:
    out = lc.loc[:, ["mjd", "flux", "flux_err"]].copy()
    for col in out.columns:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    mask = (
        np.isfinite(out["mjd"])
        & np.isfinite(out["flux"])
        & np.isfinite(out["flux_err"])
        & (out["flux_err"] > 0)
    )
    out = out.loc[mask].sort_values("mjd").reset_index(drop=True)
    if len(out) < 4:
        raise ValueError("Need at least four usable light-curve points.")
    return out


def summary_row(spec: SeriesSpec, lc: pd.DataFrame, cwt: dict, wwz: dict) -> dict[str, object]:
    cwt_period, cwt_power = _masked_global(cwt["period"], cwt["gws"], cwt["period_min"], cwt["period_max"])
    wwz_period, wwz_power = _masked_global(wwz["period_axis"], wwz["global_wwz"], wwz["period_min"], wwz["period_max"])
    cwt_idx = int(np.nanargmax(cwt_power))
    wwz_idx = int(np.nanargmax(wwz_power))
    mjd = lc["mjd"].to_numpy(dtype=float)
    flux = lc["flux"].to_numpy(dtype=float)
    return {
        "source_id": spec.source_id,
        "source": spec.source_label,
        "series": spec.series,
        "series_label": spec.label,
        "flux_kind": spec.flux_kind,
        "n_points": int(len(lc)),
        "mjd_min": float(np.nanmin(mjd)),
        "mjd_max": float(np.nanmax(mjd)),
        "date_min": mjd_to_date(float(np.nanmin(mjd))),
        "date_max": mjd_to_date(float(np.nanmax(mjd))),
        "median_dt_days": float(np.nanmedian(np.diff(mjd))),
        "flux_min": float(np.nanmin(flux)),
        "flux_max": float(np.nanmax(flux)),
        "cwt_peak_period_days": float(cwt_period[cwt_idx]),
        "cwt_peak_gws": float(cwt_power[cwt_idx]),
        "wwz_peak_period_days": float(wwz_period[wwz_idx]),
        "wwz_peak_power": float(wwz_power[wwz_idx]),
    }


def run_fixed_window(args: argparse.Namespace) -> tuple[pd.DataFrame, Path]:
    source_id = "mkn421"
    aligned_dir = ALIGNED_V2_DIR / source_id / "windows" / "59500_60500"
    output_dir = PERIODICITY_V2_DIR / source_id / "windows" / "59500_60500"
    aligned_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    weekly = pd.read_csv(ALIGNED_V2_DIR / source_id / "wcda_weekly_flux_aligned.csv")
    weekly = weekly.rename(columns={"wcda_n0": "flux", "wcda_n0_err": "flux_err"})
    clean = _clean_lc(weekly)
    window = clean[(clean["mjd"] >= 59500.0) & (clean["mjd"] <= 60500.0)].copy().reset_index(drop=True)
    if len(window) < 4:
        raise ValueError("Mrk 421 fixed window has fewer than four usable v2 flux points.")
    window.to_csv(aligned_dir / "wcda_weekly_flux_aligned.csv", index=False)

    t = window["mjd"].to_numpy(dtype=float)
    y = window["flux"].to_numpy(dtype=float)
    yerr = window["flux_err"].to_numpy(dtype=float)
    cwt = run_cwt(t, y, period_min=50.0, period_max=600.0)
    wwz = run_wwz(
        t,
        y,
        yerr,
        period_min=50.0,
        period_max=600.0,
        time_divisions=args.wwz_time_divisions,
        freq_step_factor=args.wwz_freq_step_factor,
        parallel=args.wwz_parallel,
    )
    _save_cwt(output_dir / "wcda_weekly_flux_window_cwt.npz", cwt)
    _save_wwz(output_dir / "wcda_weekly_flux_window_wwz.npz", wwz)

    cwt_peak = _strongest_peak(cwt["period"], cwt["gws"], 50.0, 600.0)
    wwz_peak = _strongest_peak(wwz["period_axis"], wwz["global_wwz"], 50.0, 600.0)
    target_min = TARGET_PERIOD_DAYS * (1 - TARGET_WINDOW_FRACTION)
    target_max = TARGET_PERIOD_DAYS * (1 + TARGET_WINDOW_FRACTION)
    cwt_target = _strongest_peak(cwt["period"], cwt["gws"], target_min, target_max)
    wwz_target = _strongest_peak(wwz["period_axis"], wwz["global_wwz"], target_min, target_max)
    span = float(np.nanmax(t) - np.nanmin(t))
    rows = [
        _window_row("CWT strongest", cwt_peak, span),
        _window_row("WWZ strongest", wwz_peak, span),
        _window_row("CWT targeted 140 d band", cwt_target, span),
        _window_row("WWZ targeted 140 d band", wwz_target, span),
    ]
    summary = pd.DataFrame(rows)
    summary.insert(0, "window", "59500-60500")
    summary.insert(0, "source", "Mrk 421")
    summary.to_csv(output_dir / "wcda_weekly_flux_window_summary.csv", index=False)

    figure = output_dir / "wcda_weekly_flux_window_periodicity.png"
    plot_periodicity_figure(
        figure,
        "Mrk 421 WCDA weekly N0 flux, MJD 59500-60500",
        window,
        cwt,
        wwz,
        y_label=_y_label("WCDA N0"),
        target_period=TARGET_PERIOD_DAYS,
        target_fraction=TARGET_WINDOW_FRACTION,
    )
    return summary, figure


def _window_row(method: str, peak: tuple[float, float], span: float) -> dict[str, object]:
    period, power = peak
    return {
        "method": method,
        "period_days": period,
        "cycles": span / period,
        "observed_power": power,
        "significance": "deferred",
    }


def run_xgm_flux_quicklook(args: argparse.Namespace) -> tuple[pd.DataFrame, Path]:
    aligned = pd.read_csv(ALIGNED_V2_DIR / "mkn421" / "wcda_daily_flux_aligned.csv")
    aligned = aligned.rename(columns={"wcda_n0": "flux", "wcda_n0_err": "flux_err"})
    clean = _clean_lc(aligned)
    sub = clean[(clean["mjd"] >= XGM_WINDOW[0]) & (clean["mjd"] <= XGM_WINDOW[1])].copy().reset_index(drop=True)
    if len(sub) < 4:
        raise ValueError("MJD 60200-60700 has fewer than four usable v2 daily flux points.")

    output_dir = PERIODICITY_V2_DIR / "xgm_poster_repro" / "mkn421"
    output_dir.mkdir(parents=True, exist_ok=True)
    t = sub["mjd"].to_numpy(dtype=float)
    y = sub["flux"].to_numpy(dtype=float)
    yerr = sub["flux_err"].to_numpy(dtype=float)
    wwz = run_wwz(
        t,
        y,
        yerr,
        period_min=2.0,
        period_max=200.0,
        time_divisions=min(len(sub), args.wwz_time_divisions),
        freq_step_factor=args.wwz_freq_step_factor,
        parallel=args.wwz_parallel,
    )
    _save_wwz(output_dir / "mkn421_daily_flux_60200_60700_wwz.npz", wwz)
    figure = output_dir / "mkn421_daily_flux_60200_60700_wwz_quicklook.png"
    plot_xgm_wwz_figure(figure, sub, wwz)

    global_peak = _strongest_peak(wwz["period_axis"], wwz["global_wwz"], 2.0, 200.0)
    nearest_idx = int(np.nanargmin(np.abs(np.asarray(wwz["period_axis"], dtype=float) - XGM_REFERENCE_PERIOD_DAYS)))
    nearest_period = float(np.asarray(wwz["period_axis"], dtype=float)[nearest_idx])
    nearest_power = float(np.asarray(wwz["global_wwz"], dtype=float)[nearest_idx])
    rows = pd.DataFrame(
        [
            {
                "window": "60200-60700",
                "target": "v2 flux global peak",
                "period_days": global_peak[0],
                "wwz_power": global_peak[1],
                "cycles": (float(sub["mjd"].max()) - float(sub["mjd"].min())) / global_peak[0],
                "significance": "deferred",
            },
            {
                "window": "60200-60700",
                "target": "xgm poster reference 51.05 d nearest grid",
                "period_days": nearest_period,
                "wwz_power": nearest_power,
                "cycles": (float(sub["mjd"].max()) - float(sub["mjd"].min())) / nearest_period,
                "significance": "deferred",
            },
        ]
    )
    rows.to_csv(output_dir / "xgm_flux_quicklook_summary.csv", index=False)
    return rows, figure


def load_xgm_significance() -> pd.DataFrame | None:
    if not XGM_SIGNIFICANCE_CSV.exists() or not XGM_SIGNIFICANCE_PNG.exists():
        return None
    sig = pd.read_csv(XGM_SIGNIFICANCE_CSV)
    required = {
        "target",
        "target_period_days",
        "local_window_peak_period_days",
        "local_window_peak_power",
        "local_fap",
        "global_fap",
        "reference_95",
        "reference_99",
        "above_95",
        "above_99",
        "cycles",
        "n_points",
        "n_surrogates",
        "ar1_alpha",
    }
    missing = required - set(sig.columns)
    if missing:
        raise ValueError(f"{XGM_SIGNIFICANCE_CSV} missing columns: {sorted(missing)}")
    n_surrogates = pd.to_numeric(sig["n_surrogates"], errors="coerce")
    if n_surrogates.empty or not np.isfinite(n_surrogates).all() or int(n_surrogates.min()) < MIN_XGM_SIGNIFICANCE_SURROGATES:
        return None
    return sig


def load_xgm_cwt_summary() -> pd.DataFrame | None:
    if not XGM_CWT_SUMMARY_CSV.exists() or not XGM_CWT_QUICKLOOK_PNG.exists():
        return None
    summary = pd.read_csv(XGM_CWT_SUMMARY_CSV)
    required = {"target", "period_days", "cwt_power", "cycles"}
    missing = required - set(summary.columns)
    if missing:
        raise ValueError(f"{XGM_CWT_SUMMARY_CSV} missing columns: {sorted(missing)}")
    return summary


def load_xgm_cwt_significance() -> pd.DataFrame | None:
    if not XGM_CWT_SIGNIFICANCE_CSV.exists() or not XGM_CWT_SIGNIFICANCE_PNG.exists():
        return None
    sig = pd.read_csv(XGM_CWT_SIGNIFICANCE_CSV)
    required = {
        "target",
        "target_period_days",
        "local_window_peak_period_days",
        "local_window_peak_power",
        "local_fap",
        "global_fap",
        "reference_95",
        "reference_99",
        "above_95",
        "above_99",
        "cycles",
        "n_points",
        "n_surrogates",
        "ar1_alpha",
    }
    missing = required - set(sig.columns)
    if missing:
        raise ValueError(f"{XGM_CWT_SIGNIFICANCE_CSV} missing columns: {sorted(missing)}")
    n_surrogates = pd.to_numeric(sig["n_surrogates"], errors="coerce")
    if n_surrogates.empty or not np.isfinite(n_surrogates).all() or int(n_surrogates.min()) < MIN_XGM_SIGNIFICANCE_SURROGATES:
        return None
    return sig


def build_xgm_poster_comparison(
    wwz_sig: pd.DataFrame | None,
    cwt_sig: pd.DataFrame | None,
) -> pd.DataFrame | None:
    rows: list[dict[str, object]] = [
        {
            "case": "xgm poster page 5",
            "input": "WCDA counts",
            "method": "WWZ/PSD visual reference",
            "n_points": np.nan,
            "ar1_alpha": np.nan,
            "period_days": XGM_REFERENCE_PERIOD_DAYS,
            "local_peak_days": np.nan,
            "power": np.nan,
            "local_fap": np.nan,
            "global_fap": np.nan,
            "above_99": "claimed on poster",
            "note": "Poster panel uses counts and a PSD reference-curve display; exact null model and trial definition are not encoded in the v2 flux products.",
        }
    ]

    if XGM_V1_COUNTS_SIGNIFICANCE_CSV.exists():
        v1 = pd.read_csv(XGM_V1_COUNTS_SIGNIFICANCE_CSV)
        mask = (
            (v1.get("window", pd.Series(dtype=str)).astype(str) == "60200_60700")
            & (v1.get("target_type", pd.Series(dtype=str)).astype(str) == "xgm poster reference")
            & np.isclose(pd.to_numeric(v1.get("target_period_days", np.nan), errors="coerce"), XGM_REFERENCE_PERIOD_DAYS)
        )
        if mask.any():
            row = v1.loc[mask].iloc[0]
            rows.append(
                {
                    "case": "local v1 counts/proxy reproduction",
                    "input": "excess counts proxy",
                    "method": "WWZ AR(1) local-window",
                    "n_points": int(row["n_points"]),
                    "ar1_alpha": float(row["ar1_alpha"]),
                    "period_days": float(row["target_period_days"]),
                    "local_peak_days": float(row["local_window_peak_period_days"]),
                    "power": float(row["local_window_peak_power"]),
                    "local_fap": float(row["local_fap"]),
                    "global_fap": np.nan,
                    "above_99": "yes" if bool(row["above_99"]) else "no",
                    "note": "Same MJD window and nominal 51.05 d target under the local AR(1) surrogate method; not above the 99% reference.",
                }
            )

    if wwz_sig is not None:
        row = _xgm_reference_row(wwz_sig)
        if row is not None:
            rows.append(_comparison_row_from_sig(row, case="v2 strict-flux WWZ", method="WWZ AR(1) local/global", input_label="daily N0 flux"))
    if cwt_sig is not None:
        row = _xgm_reference_row(cwt_sig)
        if row is not None:
            rows.append(_comparison_row_from_sig(row, case="v2 strict-flux CWT", method="CWT AR(1) local/global", input_label="daily N0 flux"))

    return pd.DataFrame(rows) if rows else None


def _xgm_reference_row(sig: pd.DataFrame) -> pd.Series | None:
    mask = sig["target_type"].astype(str).eq("xgm poster reference")
    if "target_period_days" in sig.columns:
        period = pd.to_numeric(sig["target_period_days"], errors="coerce")
        mask &= np.isclose(period, XGM_REFERENCE_PERIOD_DAYS)
    if not mask.any():
        return None
    return sig.loc[mask].iloc[0]


def _comparison_row_from_sig(row: pd.Series, *, case: str, method: str, input_label: str) -> dict[str, object]:
    return {
        "case": case,
        "input": input_label,
        "method": method,
        "n_points": int(row["n_points"]),
        "ar1_alpha": float(row["ar1_alpha"]),
        "period_days": float(row["target_period_days"]),
        "local_peak_days": float(row["local_window_peak_period_days"]),
        "power": float(row["local_window_peak_power"]),
        "local_fap": float(row["local_fap"]),
        "global_fap": float(row["global_fap"]),
        "above_99": "yes" if bool(row["above_99"]) else "no",
        "note": "Uses strict-batch N0 flux and same-sampling AR(1) surrogates; not source/method/window-search/post-trial corrected.",
    }


def run_telamon_flux_sync() -> dict[str, object]:
    if not TELAMON_CACHE.exists():
        raise FileNotFoundError(f"Missing TELAMON cache: {TELAMON_CACHE}")
    TELAMON_V2_DIR.mkdir(parents=True, exist_ok=True)
    telamon = pd.read_csv(TELAMON_CACHE)
    required = {"mjd", "flux_jy", "flux_err_jy", "band", "series_label"}
    missing = required - set(telamon.columns)
    if missing:
        raise ValueError(f"TELAMON cache missing columns: {sorted(missing)}")

    wcda = pd.read_csv(ALIGNED_V2_DIR / "mkn421" / "wcda_weekly_flux_aligned.csv")
    wcda = wcda.rename(columns={"wcda_n0": "flux", "wcda_n0_err": "flux_err"})
    wcda = _clean_lc(wcda)
    start = max(_date_to_mjd(date(2022, 1, 1)), float(telamon["mjd"].min()), float(wcda["mjd"].min()))
    end = min(float(telamon["mjd"].max()), float(wcda["mjd"].max()))
    telamon_win = telamon[(telamon["mjd"] >= start) & (telamon["mjd"] <= end)].copy()
    wcda_win = wcda[(wcda["mjd"] >= start) & (wcda["mjd"] <= end)].copy()
    if telamon_win.empty or wcda_win.empty:
        raise ValueError("No TELAMON/WCDA v2 flux overlap.")

    plot_telamon_flux(TELAMON_V2_PNG, telamon_win, wcda_win, (start, end))
    summary = {
        "window_mjd_min": start,
        "window_mjd_max": end,
        "wcda_points": int(len(wcda_win)),
        "telamon_14mm_points": int((telamon_win["band"] == "14mm").sum()),
        "telamon_7mm_points": int((telamon_win["band"] == "7mm").sum()),
        "wcda_mjd_min": float(wcda["mjd"].min()),
        "wcda_mjd_max": float(wcda["mjd"].max()),
        "telamon_mjd_min": float(telamon["mjd"].min()),
        "telamon_mjd_max": float(telamon["mjd"].max()),
    }
    pd.DataFrame([summary]).to_csv(TELAMON_V2_DIR / "telamon_lhaaso_flux_v2_summary.csv", index=False)
    return summary


def plot_telamon_flux(path: Path, telamon: pd.DataFrame, wcda: pd.DataFrame, window: tuple[float, float]) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(12.0, 7.8), sharex=True, constrained_layout=True)
    fig.suptitle("Mrk 421 TELAMON-LHAASO weekly alignment, WCDA strict flux v2", fontsize=14)
    ax_wcda = axes[0]
    ax_wcda.errorbar(
        wcda["mjd"],
        wcda["flux"],
        yerr=wcda["flux_err"],
        fmt="o-",
        ms=3.3,
        lw=1.0,
        color="#245c9f",
        ecolor="#7da0c9",
        capsize=2,
        label=f"WCDA weekly N0 ({len(wcda)} points)",
    )
    ax_wcda.set_ylabel("WCDA N0\ncm^-2 s^-1 TeV^-1")
    ax_wcda.grid(True, alpha=0.25)
    ax_wcda.legend(loc="upper left", frameon=False)

    band_styles = {
        "14mm": ("#2f7f6f", "TELAMON Aver 14mm"),
        "7mm": ("#9b2f3f", "TELAMON Aver 7mm"),
    }
    for ax, band in zip(axes[1:], ("14mm", "7mm"), strict=True):
        color, label = band_styles[band]
        sub = telamon[telamon["band"] == band].sort_values("mjd")
        ax.errorbar(
            sub["mjd"],
            sub["flux_jy"],
            yerr=sub["flux_err_jy"],
            fmt="o-",
            ms=4.0,
            lw=1.0,
            color=color,
            ecolor=color,
            capsize=2,
            label=f"{label} ({len(sub)} points)",
        )
        ax.set_ylabel(f"{band} flux density\nJy")
        ax.grid(True, alpha=0.25)
        ax.legend(loc="upper left", frameon=False)
    axes[-1].set_xlabel("MJD")
    axes[-1].set_xlim(window)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def plot_periodicity_figure(
    path: Path,
    title: str,
    lc: pd.DataFrame,
    cwt: dict,
    wwz: dict,
    *,
    y_label: str,
    target_period: float | None = None,
    target_fraction: float = TARGET_WINDOW_FRACTION,
) -> None:
    t = lc["mjd"].to_numpy(dtype=float)
    y = lc["flux"].to_numpy(dtype=float)
    yerr = lc["flux_err"].to_numpy(dtype=float)
    fig = plt.figure(figsize=(14, 10.2), constrained_layout=True)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.45, 0.85])
    ax_lc = fig.add_subplot(gs[0, :])
    ax_cwt = fig.add_subplot(gs[1, 0])
    ax_wwz = fig.add_subplot(gs[1, 1])
    ax_cwt_global = fig.add_subplot(gs[2, 0])
    ax_wwz_global = fig.add_subplot(gs[2, 1])

    ax_lc.errorbar(t, y, yerr=yerr, fmt="o", ms=3.0, capsize=2, elinewidth=0.8)
    ax_lc.set_title(title)
    ax_lc.set_xlabel("MJD")
    ax_lc.set_ylabel(y_label)
    ax_lc.grid(True, alpha=0.25)

    cwt_period = np.asarray(cwt["period"], dtype=float)
    cwt_mask = np.asarray(cwt["mask_period"], dtype=bool)
    cwt_t_grid, cwt_p_grid = np.meshgrid(t, cwt_period)
    cwt_im = ax_cwt.contourf(
        cwt_t_grid[cwt_mask, :],
        cwt_p_grid[cwt_mask, :],
        np.asarray(cwt["power"])[cwt_mask, :],
        levels=50,
        cmap="magma",
        extend="both",
    )
    coi_clip = np.clip(cwt["coi"], cwt["period_min"], cwt["period_max"])
    ax_cwt.fill_between(
        t,
        cwt["period_max"],
        coi_clip,
        where=coi_clip <= cwt["period_max"],
        color="white",
        alpha=0.5,
        hatch="/",
        edgecolor="0.7",
        linewidth=0.0,
    )
    ax_cwt.plot(t, coi_clip, color="white", lw=1.1, label="COI")
    _format_period_axis(ax_cwt, cwt["period_min"], cwt["period_max"], "CWT Power")
    fig.colorbar(cwt_im, ax=ax_cwt, pad=0.02, label="Power")

    wwz_tau = wwz["tau_mat"][:, 0]
    wwz_period_mat = wwz["period_mat"]
    wwz_sort_idx = np.argsort(wwz_period_mat[0, :])
    wwz_period_axis = wwz_period_mat[0, wwz_sort_idx]
    wwz_power = wwz["wwz_mat"][:, wwz_sort_idx]
    wwz_norm = Normalize(vmin=float(np.nanmin(wwz_power)), vmax=float(np.nanmax(wwz_power)))
    wwz_mesh = ax_wwz.pcolormesh(
        wwz_tau,
        wwz_period_axis,
        wwz_power.T,
        shading="auto",
        cmap="viridis",
        norm=wwz_norm,
    )
    ax_wwz.plot(wwz["ridge_tau"], wwz["ridge_period"], color="black", lw=1.1, alpha=0.9, label="ridge")
    _format_period_axis(ax_wwz, wwz["period_min"], wwz["period_max"], "WWZ Power")
    fig.colorbar(wwz_mesh, ax=ax_wwz, pad=0.02, label="WWZ")

    _plot_global_axis(ax_cwt_global, cwt["period"], cwt["gws"], cwt["period_min"], cwt["period_max"], "CWT Global Spectrum", "GWS")
    _plot_global_axis(
        ax_wwz_global,
        wwz["period_axis"],
        wwz["global_wwz"],
        wwz["period_min"],
        wwz["period_max"],
        "WWZ Global Spectrum",
        "Mean WWZ",
    )
    if target_period is not None:
        target_min = target_period * (1 - target_fraction)
        target_max = target_period * (1 + target_fraction)
        for ax in (ax_cwt, ax_wwz):
            ax.axhspan(target_min, target_max, color="#f59e0b", alpha=0.16)
        for ax in (ax_cwt_global, ax_wwz_global):
            ax.axvspan(target_min, target_max, color="#f59e0b", alpha=0.16)
        for ax in (ax_cwt_global, ax_wwz_global):
            ax.axvline(target_period, color="#f59e0b", ls="--", lw=1.0, alpha=0.9)

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def plot_xgm_wwz_figure(path: Path, lc: pd.DataFrame, wwz: dict) -> None:
    t = lc["mjd"].to_numpy(dtype=float)
    y = lc["flux"].to_numpy(dtype=float)
    yerr = lc["flux_err"].to_numpy(dtype=float)
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(17, 4.8),
        gridspec_kw={"width_ratios": [1.45, 2.5, 1.0]},
        constrained_layout=True,
    )
    ax_lc, ax_map, ax_global = axes
    ax_lc.errorbar(t, y, yerr=yerr, fmt="o", ms=3.0, capsize=2, elinewidth=0.8)
    ax_lc.set_title("Mrk 421 WCDA daily N0, MJD 60200-60700")
    ax_lc.set_xlabel("MJD")
    ax_lc.set_ylabel(_y_label("WCDA N0"))
    ax_lc.grid(True, alpha=0.25)

    period_mat = wwz["period_mat"]
    sort_idx = np.argsort(period_mat[0, :])
    period_axis = period_mat[0, sort_idx]
    power = wwz["wwz_mat"][:, sort_idx]
    mesh = ax_map.pcolormesh(
        wwz["tau_mat"][:, 0],
        period_axis,
        power.T,
        shading="auto",
        cmap="jet",
        norm=Normalize(vmin=float(np.nanmin(power)), vmax=float(np.nanmax(power))),
    )
    ax_map.axhline(XGM_REFERENCE_PERIOD_DAYS, color="red", ls="--", lw=1.0, alpha=0.75, label="xgm 51.05 d")
    _format_period_axis(ax_map, 2.0, 200.0, "WWZ Power")
    fig.colorbar(mesh, ax=ax_map, pad=0.02, label="WWZ")
    global_period, global_power = _masked_global(wwz["period_axis"], wwz["global_wwz"], 2.0, 200.0)
    ax_global.plot(global_power, global_period, color="black", lw=1.4)
    ax_global.axhline(XGM_REFERENCE_PERIOD_DAYS, color="red", ls="--", lw=1.0, alpha=0.75)
    _format_period_axis(ax_global, 2.0, 200.0, "Global WWZ")
    ax_global.set_xlabel("Mean WWZ")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def _format_period_axis(ax: plt.Axes, period_min: float, period_max: float, title: str) -> None:
    ax.set_yscale("log")
    ax.set_ylim(period_min, period_max)
    ax.set_xlabel("MJD" if "Power" in title else "Period (day)")
    ax.set_ylabel("Period (day)")
    ax.set_title(title)
    ax.grid(True, alpha=0.25)


def _plot_global_axis(
    ax: plt.Axes,
    period: np.ndarray,
    power: np.ndarray,
    period_min: float,
    period_max: float,
    title: str,
    x_label: str,
) -> None:
    period_plot, power_plot = _masked_global(period, power, period_min, period_max)
    order = np.argsort(period_plot)
    period_plot = period_plot[order]
    power_plot = power_plot[order]
    ax.plot(period_plot, power_plot, color="black", lw=1.4)
    peak_period, _peak_power = _strongest_peak(period_plot, power_plot, period_min, period_max)
    ax.axvline(peak_period, color="red", ls="--", lw=1.0, alpha=0.85)
    ax.set_xscale("log")
    ax.set_xlim(period_min, period_max)
    ax.set_xlabel("Period (day)")
    ax.set_ylabel(x_label)
    ax.set_title(title)
    ax.grid(True, alpha=0.25)


def _masked_global(period: np.ndarray, power: np.ndarray, period_min: float, period_max: float) -> tuple[np.ndarray, np.ndarray]:
    period = np.asarray(period, dtype=float)
    power = np.asarray(power, dtype=float)
    mask = np.isfinite(period) & np.isfinite(power) & (period >= float(period_min)) & (period <= float(period_max))
    if not np.any(mask):
        raise ValueError("No finite global-spectrum values in requested period range.")
    return period[mask], power[mask]


def _strongest_peak(period: np.ndarray, power: np.ndarray, period_min: float, period_max: float) -> tuple[float, float]:
    period_plot, power_plot = _masked_global(period, power, period_min, period_max)
    idx = int(np.nanargmax(power_plot))
    return float(period_plot[idx]), float(power_plot[idx])


def _save_cwt(path: Path, result: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    path.parent.mkdir(parents=True, exist_ok=True)
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


def validate_v2_outputs(outputs: V2Outputs) -> None:
    expected = [
        ALIGNED_V2_DIR / "mkn421" / "wcda_daily_flux_aligned.csv",
        ALIGNED_V2_DIR / "mkn421" / "wcda_weekly_flux_aligned.csv",
        ALIGNED_V2_DIR / "mkn421" / "fermi_weekly_on_wcda_weekly_flux_axis.csv",
        ALIGNED_V2_DIR / "mkn501" / "wcda_daily_flux_aligned.csv",
        ALIGNED_V2_DIR / "mkn501" / "wcda_weekly_flux_aligned.csv",
    ]
    for path in expected:
        if not path.exists():
            raise FileNotFoundError(f"Missing v2 aligned output: {path}")
        df = pd.read_csv(path)
        if "fermi" in path.name:
            required = {"mjd", "fermi_flux", "fermi_flux_err"}
            flux_col, err_col = "fermi_flux", "fermi_flux_err"
        else:
            required = {"mjd", "wcda_n0", "wcda_n0_err", "fit_status"}
            flux_col, err_col = "wcda_n0", "wcda_n0_err"
            if set(df["fit_status"].astype(str)) != {"OK"}:
                raise ValueError(f"{path} contains non-OK WCDA flux rows.")
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"{path} missing columns: {sorted(missing)}")
        mjd = pd.to_numeric(df["mjd"], errors="coerce")
        flux = pd.to_numeric(df[flux_col], errors="coerce")
        err = pd.to_numeric(df[err_col], errors="coerce")
        if not mjd.is_monotonic_increasing:
            raise ValueError(f"{path} MJD is not sorted.")
        if not (np.isfinite(mjd).all() and np.isfinite(flux).all() and np.isfinite(err).all() and (err > 0).all()):
            raise ValueError(f"{path} contains non-finite values or non-positive errors.")
    for label, path in outputs.figures.items():
        if not path.exists() or path.stat().st_size <= 0:
            raise ValueError(f"Missing or empty figure for {label}: {path}")


def write_reports(
    outputs: V2Outputs,
    report_md: Path,
    report_html: Path,
    *,
    public_asset_map: dict[Path, str] | None,
) -> tuple[str, str]:
    report_md.parent.mkdir(parents=True, exist_ok=True)
    image_url = _image_url_factory(report_md.parent, public_asset_map)
    md = build_markdown(outputs, image_url)
    html_text = build_html(outputs, image_url)
    report_md.write_text(md, encoding="utf-8")
    report_html.write_text(html_text, encoding="utf-8")
    return md, html_text


def build_markdown(outputs: V2Outputs, image_url) -> str:
    summary = outputs.summary
    lines = [
        "# Mrk 421 / Mrk 501 WCDA Flux Periodicity Analysis v2",
        "",
        f"Generated on {date.today().isoformat()} from strict-batch WCDA flux products.",
        "",
        "This v2 report replaces the v1 WCDA photon-count/excess-rate proxy with the strict-batch forward-folded `N0` flux normalization at `E0=3 TeV` with fixed `gamma=2.6`. The Fermi comparison is realigned to the v2 WCDA weekly flux axis.",
        "",
        "**Significance scope.** The main v2 CWT/WWZ maps and global spectra remain quick-look periodicity products only. The user-requested xgm MJD 60200-60700 CWT/WWZ targets are assessed with AR(1) surrogates in this pass; no source/method/window-search/post-trial correction is applied.",
        "",
        "## Peak Summary",
        "",
        _markdown_summary_table(summary),
        "",
        "## Coverage Notes",
        "",
        "- WCDA daily flux products currently cover 2021-03-08 to 2025-07-31.",
        "- WCDA weekly flux products currently cover 2021-03-08 to 2025-07-27.",
        "- This is shorter than the v1 counts/proxy products, so v2 does not reproduce late-2025/2026 WCDA-only sections.",
        f"- WCDA v2 aligned products apply an uncertainty-outlier QC filter after the `fit_status=OK` strict-flux filter: rows with `N0_err > {WCDA_N0_ERR_MEDIAN_FACTOR:g} x median(N0_err)` are excluded per source/cadence, and rejected rows are saved beside each aligned CSV.",
        "",
        "## WCDA Flux QC Summary",
        "",
        _markdown_qc_table(outputs.qc_summary),
        "",
        "## Main Figures",
        "",
    ]
    for row in summary.itertuples(index=False):
        key = _figure_key(row.source_id, row.series)
        lines.extend(
            [
                f"### {row.series_label}",
                "",
                f"- N={row.n_points}; MJD {row.mjd_min:.3f}-{row.mjd_max:.3f}; median dt={row.median_dt_days:.3f} d.",
                f"- CWT peak={row.cwt_peak_period_days:.2f} d; WWZ peak={row.wwz_peak_period_days:.2f} d.",
                f"![{row.series_label}]({image_url(outputs.figures[key])})",
                "",
            ]
        )

    lines.extend(
        [
            "## Mrk 421 Fixed Window, MJD 59500-60500",
            "",
            "This v2 fixed-window check uses weekly `N0` flux and keeps the v1 140 d target-band localization, but does not run surrogate significance.",
            "",
            _markdown_fixed_table(outputs.fixed_window),
            "",
            f"![Mrk 421 fixed-window flux quick-look]({image_url(outputs.figures['mkn421_fixed_window'])})",
            "",
            "## xgm Poster Flux Quick-Look",
            "",
            "Only MJD 60200-60700 is rerun with daily `N0` flux. The v1 MJD 61020-61098 poster window is outside the current strict-batch flux coverage and is marked pending.",
            "",
            _markdown_xgm_poster_comparison(outputs),
            "",
            _markdown_xgm_table(outputs.xgm_summary, sig_available=outputs.xgm_significance is not None),
            "",
            f"![Mrk 421 xgm 60200-60700 flux WWZ quick-look]({image_url(outputs.figures['mkn421_xgm_60200_60700'])})",
            "",
            _markdown_xgm_counts_foldout(outputs, image_url),
            "",
            _markdown_xgm_significance_section(outputs, image_url),
            "",
            _markdown_xgm_cwt_section(outputs, image_url),
            "",
            "## TELAMON-LHAASO Flux Alignment",
            "",
            f"The TELAMON overlap with v2 WCDA weekly flux covers MJD {outputs.telamon_summary['window_mjd_min']:.3f}-{outputs.telamon_summary['window_mjd_max']:.3f}. This figure is visual timing context only; no DCF, correlation, lag, FAP, or QPO significance is reported.",
            "",
            f"![Mrk 421 TELAMON-LHAASO weekly flux alignment]({image_url(outputs.figures['mkn421_telamon_flux'])})",
            "",
        ]
    )
    return "\n".join(lines)


def build_html(outputs: V2Outputs, image_url) -> str:
    title = "Mrk 421 / Mrk 501 WCDA Flux Periodicity Analysis v2"
    zh_summary = _html_summary_table(outputs.summary, zh=True)
    en_summary = _html_summary_table(outputs.summary, zh=False)
    zh_qc = _html_qc_table(outputs.qc_summary, zh=True)
    en_qc = _html_qc_table(outputs.qc_summary, zh=False)
    zh_figures = _html_main_figures(outputs, image_url, zh=True)
    en_figures = _html_main_figures(outputs, image_url, zh=False)
    zh_fixed = _html_fixed_table(outputs.fixed_window, zh=True)
    en_fixed = _html_fixed_table(outputs.fixed_window, zh=False)
    zh_xgm = _html_xgm_table(outputs.xgm_summary, zh=True, sig_available=outputs.xgm_significance is not None)
    en_xgm = _html_xgm_table(outputs.xgm_summary, zh=False, sig_available=outputs.xgm_significance is not None)
    zh_xgm_compare = _html_xgm_poster_comparison(outputs, zh=True)
    en_xgm_compare = _html_xgm_poster_comparison(outputs, zh=False)
    zh_xgm_sig = _html_xgm_significance_section(outputs, image_url, zh=True)
    en_xgm_sig = _html_xgm_significance_section(outputs, image_url, zh=False)
    zh_xgm_cwt = _html_xgm_cwt_section(outputs, image_url, zh=True)
    en_xgm_cwt = _html_xgm_cwt_section(outputs, image_url, zh=False)
    tel = outputs.telamon_summary
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{ --ink:#1f2933; --muted:#5f6c7b; --line:#d7dee8; --panel:#f7f9fc; --accent:#255c99; }}
    body {{ margin:0; font-family:Arial, Helvetica, sans-serif; color:var(--ink); background:#fff; line-height:1.55; }}
    main {{ max-width:1180px; margin:0 auto; padding:32px 24px 56px; }}
    h1 {{ margin:0 0 8px; font-size:30px; letter-spacing:0; }}
    h2 {{ margin-top:34px; border-bottom:1px solid var(--line); padding-bottom:6px; font-size:22px; }}
    h3 {{ margin-top:22px; font-size:18px; }}
    a {{ color:var(--accent); }}
    .meta,.note {{ color:var(--muted); }}
    .topline {{ display:flex; justify-content:space-between; align-items:flex-start; gap:16px; margin-bottom:18px; }}
    .language-toggle {{ display:inline-flex; border:1px solid var(--line); border-radius:8px; overflow:hidden; flex:0 0 auto; background:#fff; }}
    .language-toggle button {{ border:0; background:transparent; color:var(--muted); padding:8px 12px; cursor:pointer; font:inherit; }}
    .language-toggle button.active {{ background:var(--accent); color:#fff; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px 18px; margin:18px 0; }}
    code {{ background:#eef2f7; padding:2px 4px; border-radius:4px; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; margin:12px 0 20px; }}
    th,td {{ border:1px solid var(--line); padding:8px 9px; text-align:right; vertical-align:top; }}
    th:first-child,td:first-child,th:nth-child(2),td:nth-child(2) {{ text-align:left; }}
    th {{ background:#eef3f9; }}
    figure {{ margin:18px 0 26px; }}
    img {{ width:100%; height:auto; border:1px solid var(--line); border-radius:6px; background:#fff; }}
    figcaption {{ color:var(--muted); font-size:13px; margin-top:6px; }}
    .result-note {{ background:var(--panel); border-left:4px solid var(--accent); padding:10px 12px; margin:10px 0 26px; font-size:14px; }}
    details.foldout {{ border:1px solid var(--line); border-radius:8px; background:#fff; margin:14px 0 24px; padding:0; }}
    details.foldout summary {{ cursor:pointer; padding:12px 14px; font-weight:700; background:var(--panel); border-radius:8px; }}
    details.foldout[open] summary {{ border-bottom:1px solid var(--line); border-radius:8px 8px 0 0; }}
    details.foldout .foldout-body {{ padding:14px 14px 2px; }}
    details.foldout figure {{ margin:10px 0 18px; }}
    [data-lang-panel] {{ display:none; }}
    [data-lang-panel].active {{ display:block; }}
    @media (max-width:820px) {{ .topline {{ display:block; }} .language-toggle {{ margin-top:14px; }} main {{ padding:22px 14px 40px; }} table {{ font-size:12px; }} }}
  </style>
</head>
<body>
<main>
  <div class="topline">
    <div>
      <h1>{html.escape(title)}</h1>
      <p class="meta">Report date: {date.today().isoformat()}.</p>
    </div>
    <div class="language-toggle" aria-label="Language switch">
      <button type="button" data-lang-button="zh" class="active">中文</button>
      <button type="button" data-lang-button="en">English</button>
    </div>
  </div>

  <section data-lang-panel="zh" class="active">
    <section class="panel"><strong>范围。</strong>v2 将 v1 中 WCDA photon-count / excess-rate proxy 全面替换为 strict-batch forward-folded <code>N0</code> flux；<code>E0=3 TeV</code>，固定 <code>gamma=2.6</code>。本页包括 Mrk 421/501 daily 与 weekly WCDA flux、Mrk 421 Fermi weekly 重新对齐到 v2 WCDA weekly flux 轴、TELAMON-LHAASO flux 对齐，以及 Mrk 421 MJD 59500-60500 fixed-window quick-look。</section>
    <h2>数据与方法</h2>
    <p>WCDA 主序列使用 <code>N0/N0_err</code>，先保留 <code>fit_status=OK</code>、有限 <code>N0</code>、有限且正的 <code>N0_err</code>。随后按源和时间尺度应用不确定度离群点 QC：排除 <code>N0_err &gt; {WCDA_N0_ERR_MEDIAN_FACTOR:g} × median(N0_err)</code> 的行；被排除行保存到 aligned CSV 旁边的 <code>qc_rejected</code> 表。</p>
    <p>CWT 使用 Morlet wavelet，WWZ 使用 <code>libwwz</code>；周期图为 quick-look 产品。</p>
    <p class="result-note"><strong>显著性范围。</strong>主序列 CWT/WWZ 峰值仍是 quick-look 候选；本版只对用户指定的 xgm MJD 60200-60700 CWT/WWZ 目标运行 AR(1) surrogate 检验，且不做 source/method/window-search/post-trial correction。</p>
    <h2>峰值摘要</h2>
    {zh_summary}
    <h2>覆盖范围说明</h2>
    <ul><li>WCDA daily flux 覆盖到 2025-07-31。</li><li>WCDA weekly flux 覆盖到 2025-07-27。</li><li>因此 v2 比 v1 counts/proxy 覆盖短，不复现晚 2025/2026 的 WCDA-only 结果。</li></ul>
    <h2>WCDA flux QC 摘要</h2>
    {zh_qc}
    <h2>主图</h2>
    {zh_figures}
    <h2>Mrk 421 MJD 59500-60500 fixed-window quick-look</h2>
    <p>使用 weekly <code>N0</code> flux 重算窗口 CWT/WWZ，并保留 140 d ±10% target-band 峰值定位；不计算 FAP 或显著性参考线。</p>
    {zh_fixed}
    <figure><img src="{html.escape(image_url(outputs.figures['mkn421_fixed_window']))}" alt="Mrk 421 fixed-window flux quick-look"><figcaption>Mrk 421 WCDA weekly N0 fixed-window quick-look；橙色带标出 140 d ±10%。</figcaption></figure>
    <h2>xgm poster flux quick-look</h2>
    <p>只用 daily <code>N0</code> flux 重算 MJD 60200-60700。MJD 61020-61098 超出当前 flux 覆盖范围，标为待更新。</p>
    {zh_xgm_compare}
    {zh_xgm}
    <figure><img src="{html.escape(image_url(outputs.figures['mkn421_xgm_60200_60700']))}" alt="Mrk 421 xgm 60200-60700 flux WWZ quick-look"><figcaption>MJD 60200-60700 daily N0 WWZ quick-look；红线为 xgm poster 51.05 d reference。</figcaption></figure>
    {_html_xgm_counts_foldout(outputs, image_url, zh=True)}
    {zh_xgm_sig}
    {zh_xgm_cwt}
    <h2>TELAMON-LHAASO flux 对齐</h2>
    <p>v2 使用 WCDA weekly <code>N0</code> 重画 gamma-ray 面板。重叠窗口为 MJD {tel['window_mjd_min']:.3f}-{tel['window_mjd_max']:.3f}；WCDA {tel['wcda_points']} 点，TELAMON 14 mm {tel['telamon_14mm_points']} 点，7 mm {tel['telamon_7mm_points']} 点。此图只作视觉同步上下文，不给出相关、时延或 QPO 显著性。</p>
    <figure><img src="{html.escape(image_url(outputs.figures['mkn421_telamon_flux']))}" alt="Mrk 421 TELAMON-LHAASO weekly flux alignment"><figcaption>Mrk 421 TELAMON 14 mm / 7 mm 与 LHAASO-WCDA weekly N0 flux 对齐。</figcaption></figure>
  </section>

  <section data-lang-panel="en">
    <section class="panel"><strong>Scope.</strong> v2 replaces the WCDA photon-count / excess-rate proxy used in v1 with strict-batch forward-folded <code>N0</code> flux at <code>E0=3 TeV</code> with fixed <code>gamma=2.6</code>. It includes Mrk 421/501 daily and weekly WCDA flux, Mrk 421 Fermi weekly realigned to the v2 WCDA weekly flux axis, TELAMON-LHAASO flux alignment, and a Mrk 421 MJD 59500-60500 fixed-window quick-look.</section>
    <h2>Data and Methods</h2>
    <p>The WCDA series uses <code>N0/N0_err</code>. It first keeps rows with <code>fit_status=OK</code>, finite <code>N0</code>, and finite positive <code>N0_err</code>. It then applies a per-source/per-cadence uncertainty-outlier QC cut: rows with <code>N0_err &gt; {WCDA_N0_ERR_MEDIAN_FACTOR:g} × median(N0_err)</code> are excluded, and rejected rows are written beside the aligned CSVs as <code>qc_rejected</code> tables.</p>
    <p>CWT uses a Morlet wavelet and WWZ uses <code>libwwz</code>; these are quick-look products.</p>
    <p class="result-note"><strong>Significance scope.</strong> The main CWT/WWZ peaks remain quick-look candidates. This pass runs AR(1) surrogate significance only for the user-requested xgm MJD 60200-60700 CWT/WWZ targets, with no source/method/window-search/post-trial correction.</p>
    <h2>Peak Summary</h2>
    {en_summary}
    <h2>Coverage Notes</h2>
    <ul><li>WCDA daily flux currently reaches 2025-07-31.</li><li>WCDA weekly flux currently reaches 2025-07-27.</li><li>v2 is therefore shorter than the v1 counts/proxy coverage and does not reproduce late-2025/2026 WCDA-only sections.</li></ul>
    <h2>WCDA Flux QC Summary</h2>
    {en_qc}
    <h2>Main Figures</h2>
    {en_figures}
    <h2>Mrk 421 MJD 59500-60500 Fixed-Window Quick-Look</h2>
    <p>This section reruns the fixed window with weekly <code>N0</code> flux and preserves the 140 d ±10% target-band peak localization. It does not compute FAP or significance references.</p>
    {en_fixed}
    <figure><img src="{html.escape(image_url(outputs.figures['mkn421_fixed_window']))}" alt="Mrk 421 fixed-window flux quick-look"><figcaption>Mrk 421 WCDA weekly N0 fixed-window quick-look; the orange band marks 140 d ±10%.</figcaption></figure>
    <h2>xgm Poster Flux Quick-Look</h2>
    <p>Only MJD 60200-60700 is rerun with daily <code>N0</code> flux. MJD 61020-61098 is outside the current flux coverage and remains pending.</p>
    {en_xgm_compare}
    {en_xgm}
    <figure><img src="{html.escape(image_url(outputs.figures['mkn421_xgm_60200_60700']))}" alt="Mrk 421 xgm 60200-60700 flux WWZ quick-look"><figcaption>MJD 60200-60700 daily N0 WWZ quick-look; the red line marks the xgm poster 51.05 d reference.</figcaption></figure>
    {_html_xgm_counts_foldout(outputs, image_url, zh=False)}
    {en_xgm_sig}
    {en_xgm_cwt}
    <h2>TELAMON-LHAASO Flux Alignment</h2>
    <p>The gamma-ray panel is redrawn with WCDA weekly <code>N0</code>. The overlap window is MJD {tel['window_mjd_min']:.3f}-{tel['window_mjd_max']:.3f}: WCDA {tel['wcda_points']} points, TELAMON 14 mm {tel['telamon_14mm_points']} points, and 7 mm {tel['telamon_7mm_points']} points. This is visual timing context only; no correlation, lag, FAP, or QPO significance is reported.</p>
    <figure><img src="{html.escape(image_url(outputs.figures['mkn421_telamon_flux']))}" alt="Mrk 421 TELAMON-LHAASO weekly flux alignment"><figcaption>Mrk 421 TELAMON 14 mm / 7 mm aligned with LHAASO-WCDA weekly N0 flux.</figcaption></figure>
  </section>
</main>
<script>
  (function () {{
    const buttons = document.querySelectorAll("[data-lang-button]");
    const panels = document.querySelectorAll("[data-lang-panel]");
    function setLang(lang) {{
      document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
      buttons.forEach((button) => button.classList.toggle("active", button.dataset.langButton === lang));
      panels.forEach((panel) => panel.classList.toggle("active", panel.dataset.langPanel === lang));
      try {{ localStorage.setItem("qpo-periodicity-v2-lang", lang); }} catch (_err) {{}}
    }}
    buttons.forEach((button) => button.addEventListener("click", () => setLang(button.dataset.langButton)));
    let preferred = "zh";
    try {{ preferred = localStorage.getItem("qpo-periodicity-v2-lang") || preferred; }} catch (_err) {{}}
    if (!["zh", "en"].includes(preferred)) preferred = "zh";
    setLang(preferred);
  }})();
</script>
</body>
</html>
"""


def publish_report(outputs: V2Outputs, any_reports_dir: Path) -> None:
    if not any_reports_dir.exists():
        raise FileNotFoundError(f"Missing any-reports checkout: {any_reports_dir}")
    publish_dir = any_reports_dir / PUBLISH_SLUG
    assets_dir = publish_dir / "assets"
    publish_dir.mkdir(parents=True, exist_ok=True)
    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)

    public_asset_map: dict[Path, str] = {}
    for key, source_path in outputs.figures.items():
        source_path = source_path.resolve()
        target_name = f"{key}{source_path.suffix}"
        target = assets_dir / target_name
        shutil.copy2(source_path, target)
        public_asset_map[source_path] = f"assets/{target_name}"

    _md, html_text = write_reports(
        outputs,
        publish_dir / "periodicity_v2_report.md",
        publish_dir / "index.html",
        public_asset_map=public_asset_map,
    )
    update_any_reports_index(any_reports_dir / "index.html")
    print(f"[OK] published local any-reports copy -> {publish_dir}")


def update_any_reports_index(index_path: Path) -> None:
    content = index_path.read_text(encoding="utf-8")
    card = f"""
    <li>
      <a class="report-card" href="{PUBLISH_SLUG}/">
        <span class="title">Mrk 421 / Mrk 501 WCDA Flux 周期性分析 v2</span>
        <p class="desc">
          用 IHEP strict-batch forward-folded WCDA N0 flux 全面替换 v1 的 photon-count / excess-rate proxy：
          覆盖 Mrk 421 与 Mrk 501 daily/weekly flux、Mrk 421 Fermi weekly 重新对齐、
          TELAMON-LHAASO flux 对齐、xgm MJD 60200-60700 flux quick-look，以及
          MJD 59500-60500 fixed-window quick-look；xgm 窗口加入 targeted AR(1) WWZ 显著性检验。
        </p>
        <span class="meta">
          <time datetime="{date.today().isoformat()}">{date.today().isoformat()}</time>
          <span class="tag">QPO</span>
          <span class="tag">WCDA flux</span>
          <span class="tag">Fermi</span>
          <span class="tag">双语</span>
          <span class="tag">WWZ</span>
        </span>
      </a>
    </li>
"""
    pattern = rf"\n\s*<li>\s*<a class=\"report-card\" href=\"{re.escape(PUBLISH_SLUG)}/\">.*?</li>\s*"
    content = re.sub(pattern, "\n", content, flags=re.S)
    marker = '<li>\n      <a class="report-card" href="qpo-periodicity-v1/">'
    idx = content.find(marker)
    if idx >= 0:
        content = content[:idx] + card + "\n" + content[idx:]
    else:
        content = content.replace("  </ul>", card + "\n  </ul>")
    index_path.write_text(content, encoding="utf-8")


def _html_summary_table(summary: pd.DataFrame, *, zh: bool) -> str:
    headers = ["源" if zh else "Source", "序列" if zh else "Series", "N", "MJD min", "MJD max", "dt [d]", "CWT [d]", "WWZ [d]"]
    rows = []
    for row in summary.itertuples(index=False):
        rows.append(
            [
                row.source,
                _series_label(row.series, zh=zh),
                f"{row.n_points:d}",
                f"{row.mjd_min:.3f}",
                f"{row.mjd_max:.3f}",
                f"{row.median_dt_days:.3f}",
                f"{row.cwt_peak_period_days:.2f}",
                f"{row.wwz_peak_period_days:.2f}",
            ]
        )
    return _html_table(headers, rows)


def _html_qc_table(qc: pd.DataFrame, *, zh: bool) -> str:
    headers = [
        "源" if zh else "Source",
        "尺度" if zh else "Cadence",
        "OK行" if zh else "OK rows",
        "保留" if zh else "Kept",
        "排除" if zh else "Rejected",
        "N0_err上限" if zh else "N0_err limit",
    ]
    rows = []
    for row in qc.itertuples(index=False):
        rows.append(
            [
                row.source,
                row.cadence,
                f"{row.ok_rows_before_qc:d}",
                f"{row.kept_rows:d}",
                f"{row.rejected_rows:d}",
                f"{row.n0_err_limit:.3e}",
            ]
        )
    return _html_table(headers, rows)


def _html_main_figures(outputs: V2Outputs, image_url, *, zh: bool) -> str:
    parts: list[str] = []
    for row in outputs.summary.itertuples(index=False):
        key = _figure_key(row.source_id, row.series)
        caption = (
            f"N={row.n_points}, MJD {row.mjd_min:.3f}-{row.mjd_max:.3f}; CWT peak {row.cwt_peak_period_days:.2f} d, WWZ peak {row.wwz_peak_period_days:.2f} d. 显著性暂缓。"
            if zh
            else f"N={row.n_points}, MJD {row.mjd_min:.3f}-{row.mjd_max:.3f}; CWT peak {row.cwt_peak_period_days:.2f} d, WWZ peak {row.wwz_peak_period_days:.2f} d. Significance deferred."
        )
        parts.append(
            f"<h3>{html.escape(_series_label(row.series, zh=zh, source=row.source))}</h3>"
            f"<figure><img src=\"{html.escape(image_url(outputs.figures[key]))}\" alt=\"{html.escape(row.series_label)}\">"
            f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        )
    return "\n".join(parts)


def _html_fixed_table(fixed: pd.DataFrame, *, zh: bool) -> str:
    headers = ["方法" if zh else "Method", "周期 [d]" if zh else "Period [d]", "Cycles", "Observed", "显著性" if zh else "Significance"]
    rows = [
        [row.method, f"{row.period_days:.2f}", f"{row.cycles:.2f}", f"{row.observed_power:.3f}", "暂缓" if zh else "deferred"]
        for row in fixed.itertuples(index=False)
    ]
    return _html_table(headers, rows)


def _html_xgm_table(xgm: pd.DataFrame, *, zh: bool, sig_available: bool) -> str:
    headers = ["目标" if zh else "Target", "周期 [d]" if zh else "Period [d]", "WWZ power", "Cycles", "显著性" if zh else "Significance"]
    significance = ("见下方 targeted AR(1)" if zh else "see targeted AR(1) below") if sig_available else ("暂缓" if zh else "deferred")
    rows = [
        [row.target, f"{row.period_days:.2f}", f"{row.wwz_power:.3f}", f"{row.cycles:.2f}", significance]
        for row in xgm.itertuples(index=False)
    ]
    return _html_table(headers, rows)


def _html_xgm_poster_comparison(outputs: V2Outputs, *, zh: bool) -> str:
    comparison = outputs.xgm_poster_comparison
    if comparison is None or comparison.empty:
        return ""
    if zh:
        intro = (
            "与 xgm poster 第 5 页的 51.05 d 结果不是同一口径：poster 面板使用 WCDA counts，并在 PSD 面板上显示参考线；"
            "v2 表格使用 strict-batch daily <code>N0</code> flux，并报告同一采样下 AR(1) surrogate 的 local/global FAP。"
            "因此 poster 上读到的 &gt;99% 不能直接等价为 v2 flux 的 &gt;99%。"
        )
        headers = ["口径", "输入", "方法", "N", "alpha", "局部峰 [d]", "power", "local FAP", "global FAP", "99%"]
    else:
        intro = (
            "This is not an apples-to-apples comparison with xgm poster page 5: the poster panel uses WCDA counts and a PSD reference-curve display, "
            "whereas v2 uses strict-batch daily <code>N0</code> flux and reports AR(1) surrogate local/global FAP on the same sampling. "
            "The poster's visual &gt;99% reading is therefore not equivalent to a v2 flux &gt;99% claim."
        )
        headers = ["Case", "Input", "Method", "N", "alpha", "Local peak [d]", "Power", "Local FAP", "Global FAP", "99%"]
    rows = []
    for row in comparison.itertuples(index=False):
        rows.append(
            [
                row.case,
                row.input,
                row.method,
                _format_optional_int(row.n_points),
                _format_optional_float(row.ar1_alpha, digits=3),
                _format_optional_float(row.local_peak_days, digits=2),
                _format_optional_float(row.power, digits=3),
                _format_optional_float(row.local_fap, digits=4),
                _format_optional_float(row.global_fap, digits=4),
                row.above_99,
            ]
        )
    return f"<p class=\"result-note\">{intro}</p>{_html_table(headers, rows)}"


def _html_xgm_counts_foldout(outputs: V2Outputs, image_url, *, zh: bool) -> str:
    quicklook = outputs.figures.get("mkn421_xgm_60200_60700_counts_quicklook")
    significance = outputs.figures.get("mkn421_xgm_60200_60700_counts_significance")
    if quicklook is None and significance is None:
        return ""
    title = "展开查看之前的 counts/proxy 版本" if zh else "Show previous counts/proxy version"
    intro = (
        "以下是 v1 counts/proxy 的同一 MJD 60200-60700 窗口，仅作输入数据和显著性口径对照；不属于 v2 strict-flux 结果。"
        if zh
        else "These are the v1 counts/proxy products for the same MJD 60200-60700 window. They are included only for input/method comparison and are not v2 strict-flux results."
    )
    parts = [f"<details class=\"foldout\"><summary>{html.escape(title)}</summary><div class=\"foldout-body\"><p>{html.escape(intro)}</p>"]
    if quicklook is not None:
        caption = (
            "v1 counts/proxy WWZ poster-style quick-look。"
            if zh
            else "v1 counts/proxy WWZ poster-style quick-look."
        )
        parts.append(
            f"<figure><img src=\"{html.escape(image_url(quicklook))}\" alt=\"Mrk 421 xgm counts/proxy WWZ quick-look\">"
            f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        )
    if significance is not None:
        caption = (
            "v1 counts/proxy AR(1) local-window WWZ 显著性对照。"
            if zh
            else "v1 counts/proxy AR(1) local-window WWZ significance comparison."
        )
        parts.append(
            f"<figure><img src=\"{html.escape(image_url(significance))}\" alt=\"Mrk 421 xgm counts/proxy WWZ significance\">"
            f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        )
    parts.append("</div></details>")
    return "".join(parts)


def _html_xgm_significance_section(outputs: V2Outputs, image_url, *, zh: bool) -> str:
    sig = outputs.xgm_significance
    if sig is None:
        return (
            "<p class=\"result-note\">该窗口的 AR(1) surrogate 显著性正在等待正式产物。</p>"
            if zh
            else "<p class=\"result-note\">AR(1) surrogate significance for this window is pending.</p>"
        )
    headers = [
        "目标" if zh else "Target",
        "目标周期 [d]" if zh else "Target period [d]",
        "局部峰 [d]" if zh else "Local peak [d]",
        "WWZ",
        "local FAP",
        "global FAP",
        "99%" if zh else "Above 99%",
        "Nsim",
    ]
    rows = []
    for row in sig.itertuples(index=False):
        rows.append(
            [
                row.target,
                f"{row.target_period_days:.2f}",
                f"{row.local_window_peak_period_days:.2f}",
                f"{row.local_window_peak_power:.3f}",
                f"{row.local_fap:.4f}",
                f"{row.global_fap:.4f}",
                _yes_no(bool(row.above_99), zh=zh),
                f"{row.n_surrogates:d}",
            ]
        )
    note = (
        "AR(1) Gaussian surrogate 使用同一 v2 daily flux 采样；local FAP 是目标周期 ±10% 窗口内最大 global-WWZ 的检验，global FAP 是同一 2-200 d 搜索范围内最大值参考；不包含 source/method/window-search/post-trial correction。"
        if zh
        else "AR(1) Gaussian surrogates use the same v2 daily flux sampling. Local FAP tests the maximum global WWZ inside target period ±10%; global FAP references the maximum across the same 2-200 d search range. No source/method/window-search/post-trial correction is included."
    )
    fig = outputs.figures.get("mkn421_xgm_60200_60700_significance")
    figure = ""
    if fig is not None:
        caption = (
            "MJD 60200-60700 daily N0 WWZ 显著性；虚线为 AR(1) surrogate pointwise 95%/99% 参考。"
            if zh
            else "MJD 60200-60700 daily N0 WWZ significance; dashed curves are AR(1) surrogate pointwise 95%/99% references."
        )
        figure = (
            f"<figure><img src=\"{html.escape(image_url(fig))}\" alt=\"Mrk 421 xgm flux WWZ significance\">"
            f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        )
    title = "<h3>xgm 窗口 WWZ 显著性</h3>" if zh else "<h3>xgm Window WWZ Significance</h3>"
    return f"{title}<p>{html.escape(note)}</p>{_html_table(headers, rows)}{figure}"


def _html_xgm_cwt_section(outputs: V2Outputs, image_url, *, zh: bool) -> str:
    summary = outputs.xgm_cwt_summary
    sig = outputs.xgm_cwt_significance
    if summary is None:
        return ""
    significance = ("见下方 CWT AR(1)" if zh and sig is not None else "see CWT AR(1) below" if sig is not None else "暂缓" if zh else "deferred")
    summary_headers = ["目标" if zh else "Target", "周期 [d]" if zh else "Period [d]", "CWT power", "Cycles", "显著性" if zh else "Significance"]
    summary_rows = [
        [row.target, f"{row.period_days:.2f}", f"{row.cwt_power:.3f}", f"{row.cycles:.2f}", significance]
        for row in summary.itertuples(index=False)
    ]
    title = "<h3>xgm 窗口 CWT quick-look</h3>" if zh else "<h3>xgm Window CWT Quick-Look</h3>"
    fig = outputs.figures.get("mkn421_xgm_60200_60700_cwt")
    figure = ""
    if fig is not None:
        caption = (
            "MJD 60200-60700 daily N0 CWT quick-look；红线为 xgm poster 51.05 d reference。"
            if zh
            else "MJD 60200-60700 daily N0 CWT quick-look; the red line marks the xgm poster 51.05 d reference."
        )
        figure = (
            f"<figure><img src=\"{html.escape(image_url(fig))}\" alt=\"Mrk 421 xgm flux CWT quick-look\">"
            f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        )
    if sig is None:
        return f"{title}{_html_table(summary_headers, summary_rows)}{figure}<p class=\"result-note\">CWT AR(1) surrogate 显著性正在等待正式产物。</p>"

    sig_headers = [
        "目标" if zh else "Target",
        "目标周期 [d]" if zh else "Target period [d]",
        "局部峰 [d]" if zh else "Local peak [d]",
        "CWT",
        "local FAP",
        "global FAP",
        "99%" if zh else "Above 99%",
        "Nsim",
    ]
    sig_rows = []
    for row in sig.itertuples(index=False):
        sig_rows.append(
            [
                row.target,
                f"{row.target_period_days:.2f}",
                f"{row.local_window_peak_period_days:.2f}",
                f"{row.local_window_peak_power:.3f}",
                f"{row.local_fap:.4f}",
                f"{row.global_fap:.4f}",
                _yes_no(bool(row.above_99), zh=zh),
                f"{row.n_surrogates:d}",
            ]
        )
    note = (
        "CWT 使用同一 v2 daily flux 采样的 AR(1) Gaussian surrogate；local FAP 是目标周期 ±10% 窗口内最大 global-CWT 的检验，global FAP 是同一 2-200 d 搜索范围内最大值参考；不包含 source/method/window-search/post-trial correction。"
        if zh
        else "CWT uses AR(1) Gaussian surrogates on the same v2 daily flux sampling. Local FAP tests the maximum global CWT inside target period ±10%; global FAP references the maximum across the same 2-200 d search range. No source/method/window-search/post-trial correction is included."
    )
    sig_fig = outputs.figures.get("mkn421_xgm_60200_60700_cwt_significance")
    sig_figure = ""
    if sig_fig is not None:
        caption = (
            "MJD 60200-60700 daily N0 CWT 显著性；虚线为 AR(1) surrogate pointwise 95%/99% 参考。"
            if zh
            else "MJD 60200-60700 daily N0 CWT significance; dashed curves are AR(1) surrogate pointwise 95%/99% references."
        )
        sig_figure = (
            f"<figure><img src=\"{html.escape(image_url(sig_fig))}\" alt=\"Mrk 421 xgm flux CWT significance\">"
            f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        )
    sig_title = "<h3>xgm 窗口 CWT 显著性</h3>" if zh else "<h3>xgm Window CWT Significance</h3>"
    return f"{title}{_html_table(summary_headers, summary_rows)}{figure}{sig_title}<p>{html.escape(note)}</p>{_html_table(sig_headers, sig_rows)}{sig_figure}"


def _html_table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{html.escape(str(item))}</th>" for item in headers)
    body = "\n".join(
        "<tr>" + "".join(f"<td>{html.escape(str(item))}</td>" for item in row) + "</tr>" for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _markdown_summary_table(summary: pd.DataFrame) -> str:
    lines = [
        "| Source | Series | N | MJD min | MJD max | dt [d] | CWT peak [d] | WWZ peak [d] |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary.itertuples(index=False):
        lines.append(
            f"| {row.source} | {_series_label(row.series, zh=False)} | {row.n_points} | "
            f"{row.mjd_min:.3f} | {row.mjd_max:.3f} | {row.median_dt_days:.3f} | "
            f"{row.cwt_peak_period_days:.2f} | {row.wwz_peak_period_days:.2f} |"
        )
    return "\n".join(lines)


def _markdown_qc_table(qc: pd.DataFrame) -> str:
    lines = [
        "| Source | Cadence | OK rows | Kept | Rejected | N0_err limit |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in qc.itertuples(index=False):
        lines.append(
            f"| {row.source} | {row.cadence} | {row.ok_rows_before_qc} | "
            f"{row.kept_rows} | {row.rejected_rows} | {row.n0_err_limit:.3e} |"
        )
    return "\n".join(lines)


def _markdown_fixed_table(fixed: pd.DataFrame) -> str:
    lines = [
        "| Method | Period [d] | Cycles | Observed power | Significance |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in fixed.itertuples(index=False):
        lines.append(f"| {row.method} | {row.period_days:.2f} | {row.cycles:.2f} | {row.observed_power:.3f} | deferred |")
    return "\n".join(lines)


def _markdown_xgm_table(xgm: pd.DataFrame, *, sig_available: bool) -> str:
    lines = [
        "| Target | Period [d] | WWZ power | Cycles | Significance |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    significance = "see targeted AR(1) below" if sig_available else "deferred"
    for row in xgm.itertuples(index=False):
        lines.append(f"| {row.target} | {row.period_days:.2f} | {row.wwz_power:.3f} | {row.cycles:.2f} | {significance} |")
    return "\n".join(lines)


def _markdown_xgm_poster_comparison(outputs: V2Outputs) -> str:
    comparison = outputs.xgm_poster_comparison
    if comparison is None or comparison.empty:
        return ""
    lines = [
        "### xgm Poster Comparison Note",
        "",
        "This is not an apples-to-apples comparison with xgm poster page 5: the poster panel uses WCDA counts and a PSD reference-curve display, whereas v2 uses strict-batch daily `N0` flux and reports AR(1) surrogate local/global FAP on the same sampling. The poster's visual >99% reading is therefore not equivalent to a v2 flux >99% claim.",
        "",
        "| Case | Input | Method | N | alpha | Local peak [d] | Power | Local FAP | Global FAP | 99% |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in comparison.itertuples(index=False):
        lines.append(
            f"| {row.case} | {row.input} | {row.method} | {_format_optional_int(row.n_points)} | "
            f"{_format_optional_float(row.ar1_alpha, digits=3)} | {_format_optional_float(row.local_peak_days, digits=2)} | "
            f"{_format_optional_float(row.power, digits=3)} | {_format_optional_float(row.local_fap, digits=4)} | "
            f"{_format_optional_float(row.global_fap, digits=4)} | {row.above_99} |"
        )
    return "\n".join(lines)


def _markdown_xgm_counts_foldout(outputs: V2Outputs, image_url) -> str:
    quicklook = outputs.figures.get("mkn421_xgm_60200_60700_counts_quicklook")
    significance = outputs.figures.get("mkn421_xgm_60200_60700_counts_significance")
    if quicklook is None and significance is None:
        return ""
    lines = [
        "<details>",
        "<summary>Show previous counts/proxy version</summary>",
        "",
        "These are the v1 counts/proxy products for the same MJD 60200-60700 window. They are included only for input/method comparison and are not v2 strict-flux results.",
        "",
    ]
    if quicklook is not None:
        lines.extend(
            [
                f"![Mrk 421 xgm counts/proxy WWZ quick-look]({image_url(quicklook)})",
                "",
            ]
        )
    if significance is not None:
        lines.extend(
            [
                f"![Mrk 421 xgm counts/proxy WWZ significance]({image_url(significance)})",
                "",
            ]
        )
    lines.append("</details>")
    return "\n".join(lines)


def _markdown_xgm_significance_section(outputs: V2Outputs, image_url) -> str:
    sig = outputs.xgm_significance
    if sig is None:
        return "### xgm Window WWZ Significance\n\nAR(1) surrogate significance for this window is pending."
    lines = [
        "### xgm Window WWZ Significance",
        "",
        "AR(1) Gaussian surrogates use the same v2 daily flux sampling. Local FAP tests the maximum global WWZ inside target period ±10%; global FAP references the maximum across the same 2-200 d search range. No source/method/window-search/post-trial correction is included.",
        "",
        "| Target | Target period [d] | Local peak [d] | WWZ | Local FAP | Global FAP | Above 99% | Nsim |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in sig.itertuples(index=False):
        lines.append(
            f"| {row.target} | {row.target_period_days:.2f} | {row.local_window_peak_period_days:.2f} | "
            f"{row.local_window_peak_power:.3f} | {row.local_fap:.4f} | {row.global_fap:.4f} | "
            f"{_yes_no(bool(row.above_99), zh=False)} | {row.n_surrogates} |"
        )
    fig = outputs.figures.get("mkn421_xgm_60200_60700_significance")
    if fig is not None:
        lines.extend(
            [
                "",
                f"![Mrk 421 xgm flux WWZ significance]({image_url(fig)})",
            ]
        )
    return "\n".join(lines)


def _markdown_xgm_cwt_section(outputs: V2Outputs, image_url) -> str:
    summary = outputs.xgm_cwt_summary
    sig = outputs.xgm_cwt_significance
    if summary is None:
        return ""
    significance = "see CWT AR(1) below" if sig is not None else "deferred"
    lines = [
        "### xgm Window CWT Quick-Look",
        "",
        "| Target | Period [d] | CWT power | Cycles | Significance |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in summary.itertuples(index=False):
        lines.append(f"| {row.target} | {row.period_days:.2f} | {row.cwt_power:.3f} | {row.cycles:.2f} | {significance} |")
    fig = outputs.figures.get("mkn421_xgm_60200_60700_cwt")
    if fig is not None:
        lines.extend(
            [
                "",
                f"![Mrk 421 xgm flux CWT quick-look]({image_url(fig)})",
                "",
            ]
        )
    if sig is None:
        lines.extend(["", "CWT AR(1) surrogate significance for this window is pending."])
        return "\n".join(lines)

    lines.extend(
        [
            "### xgm Window CWT Significance",
            "",
            "CWT uses AR(1) Gaussian surrogates on the same v2 daily flux sampling. Local FAP tests the maximum global CWT inside target period ±10%; global FAP references the maximum across the same 2-200 d search range. No source/method/window-search/post-trial correction is included.",
            "",
            "| Target | Target period [d] | Local peak [d] | CWT | Local FAP | Global FAP | Above 99% | Nsim |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    for row in sig.itertuples(index=False):
        lines.append(
            f"| {row.target} | {row.target_period_days:.2f} | {row.local_window_peak_period_days:.2f} | "
            f"{row.local_window_peak_power:.3f} | {row.local_fap:.4f} | {row.global_fap:.4f} | "
            f"{_yes_no(bool(row.above_99), zh=False)} | {row.n_surrogates} |"
        )
    sig_fig = outputs.figures.get("mkn421_xgm_60200_60700_cwt_significance")
    if sig_fig is not None:
        lines.extend(
            [
                "",
                f"![Mrk 421 xgm flux CWT significance]({image_url(sig_fig)})",
            ]
        )
    return "\n".join(lines)


def _yes_no(value: bool, *, zh: bool) -> str:
    if zh:
        return "是" if value else "否"
    return "yes" if value else "no"


def _format_optional_float(value: object, *, digits: int) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if not np.isfinite(number):
        return "-"
    return f"{number:.{digits}f}"


def _format_optional_int(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    if not np.isfinite(number):
        return "-"
    return f"{int(number):d}"


def _series_label(series: str, *, zh: bool, source: str | None = None) -> str:
    labels = {
        "wcda_daily_flux": ("WCDA daily N0 flux", "WCDA daily N0 flux"),
        "wcda_weekly_flux": ("WCDA weekly N0 flux", "WCDA weekly N0 flux"),
        "fermi_weekly_on_wcda_flux_axis": ("Fermi weekly on WCDA flux axis", "Fermi weekly on WCDA flux axis"),
    }
    label = labels.get(series, (series, series))[0 if zh else 1]
    return f"{source} {label}" if source else label


def _figure_key(source_id: str, series: str) -> str:
    if source_id == "mkn421" and series == "fermi_weekly_on_wcda_flux_axis":
        return "mkn421_fermi_weekly_on_wcda_flux_axis"
    return f"{source_id}_{series}"


def _image_url_factory(base_dir: Path, public_asset_map: dict[Path, str] | None):
    def image_url(path: Path) -> str:
        resolved = path.resolve()
        if public_asset_map is not None:
            return public_asset_map[resolved]
        return _relative_path(path, base_dir)

    return image_url


def _relative_path(path: Path, base_dir: Path) -> str:
    return Path(os.path.relpath(Path(path).resolve(), base_dir.resolve())).as_posix()


def _y_label(kind: str) -> str:
    if kind == "WCDA N0":
        return "N0 [cm^-2 s^-1 TeV^-1]"
    return "Flux"


def mjd_to_date(mjd: float) -> str:
    return Time(float(mjd), format="mjd").to_datetime().date().isoformat()


def _date_to_mjd(value: date) -> float:
    return float(Time(f"{value.isoformat()}T00:00:00", format="isot", scale="utc").mjd)


if __name__ == "__main__":
    main()
