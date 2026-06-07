#!/usr/bin/env python3
"""Prepare aligned WCDA/Fermi light curves and run CWT/WWZ v1 checks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LogNorm, Normalize  # noqa: E402
from scipy.signal import find_peaks  # noqa: E402


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import (  # noqa: E402
    align_to_reference_nearest,
    read_wcda_counts_csv,
    run_cwt,
    run_wwz,
    usable_light_curve,
)
from utils.project_paths import ALIGNED_DIR, PERIODICITY_DIR, PROJECT_ROOT  # noqa: E402
from utils.source_registry import (  # noqa: E402
    DEFAULT_SURVEY_SOURCE_IDS,
    SOURCE_REGISTRY,
    WCDA_WEEK_SURVEY_SOURCE_IDS,
    get_source,
)


SOURCE_WITH_DEFAULT_AUX = "mkn421"
GLOBAL_PEAK_PROMINENCE_FRACTION = 0.10
GLOBAL_PEAK_MIN_DISTANCE_BINS = 2
RENDER_EXISTING_SERIES = (
    "wcda_daily",
    "wcda_weekly",
    "fermi_weekly_on_wcda_axis",
)
RENDER_SERIES_CONFIG = {
    "wcda_daily": {
        "aligned": "wcda_daily_aligned.csv",
        "flux": "wcda_flux_excess",
        "flux_err": "wcda_flux_excess_err",
        "label": "WCDA daily",
    },
    "wcda_weekly": {
        "aligned": "wcda_weekly_aligned.csv",
        "flux": "wcda_flux_excess",
        "flux_err": "wcda_flux_excess_err",
        "label": "WCDA weekly",
    },
    "fermi_weekly_on_wcda_axis": {
        "aligned": "fermi_weekly_on_wcda_weekly_axis.csv",
        "flux": "fermi_flux",
        "flux_err": "fermi_flux_err",
        "label": "Fermi weekly on WCDA axis",
    },
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", default=SOURCE_WITH_DEFAULT_AUX, help="Short source key used for output directories.")
    parser.add_argument("--source-label", default=None, help="Human-readable source name used in plots.")
    parser.add_argument("--wcda-day", type=Path, default=None)
    parser.add_argument("--wcda-week", type=Path, default=None)
    parser.add_argument("--fermi-week", type=Path, default=None)
    parser.add_argument("--aligned-dir", type=Path, default=ALIGNED_DIR)
    parser.add_argument("--periodicity-dir", type=Path, default=PERIODICITY_DIR)
    parser.add_argument(
        "--source-ids",
        nargs="+",
        choices=sorted(SOURCE_REGISTRY),
        help="Run the same periodicity workflow over multiple registry sources.",
    )
    parser.add_argument(
        "--survey-shortlist",
        action="store_true",
        help="Run the workflow over the default registry shortlist defined for the survey.",
    )
    parser.add_argument(
        "--wcda-week-survey",
        action="store_true",
        help="Run the fixed 10-source AGN WCDA weekly-only survey.",
    )
    parser.add_argument(
        "--include-wcda-day",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include WCDA daily analysis. Defaults on only for mkn421.",
    )
    parser.add_argument(
        "--include-fermi-week",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include Fermi weekly analysis aligned to the WCDA weekly axis. Defaults on only for mkn421.",
    )
    parser.add_argument("--wwz-time-divisions", type=int, default=80)
    parser.add_argument("--wwz-freq-step-factor", type=float, default=0.5)
    parser.add_argument("--wwz-parallel", action="store_true")
    parser.add_argument(
        "--wwz-color-scale",
        choices=("linear", "log"),
        default="linear",
        help="Color normalization for WWZ heatmaps. Period axes remain log-scaled.",
    )
    parser.add_argument(
        "--render-existing-weekly-only",
        action="store_true",
        help="Re-render only wcda_weekly PNGs from existing aligned CSV and CWT/WWZ NPZ files.",
    )
    parser.add_argument(
        "--render-existing-series",
        nargs="+",
        choices=RENDER_EXISTING_SERIES,
        help="Re-render selected PNGs from existing aligned CSV and CWT/WWZ NPZ files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    source_ids = _resolve_source_ids(args)
    summary_frames = []
    for source_id in source_ids:
        summary = run_for_source(args, source_id)
        if summary is not None:
            summary_frames.append(summary)

    if args.wcda_week_survey and summary_frames:
        survey_summary = pd.concat(summary_frames, ignore_index=True)
        survey_periodicity_dir = _resolve_output_base(args.periodicity_dir)
        survey_summary_path = survey_periodicity_dir / "agn_wcda_weekly_survey_summary.csv"
        survey_periodicity_dir.mkdir(parents=True, exist_ok=True)
        survey_summary.to_csv(survey_summary_path, index=False)
        print(f"[OK] wrote survey summary -> {survey_summary_path.relative_to(PROJECT_ROOT)}")


def run_for_source(args: argparse.Namespace, source_id: str) -> pd.DataFrame | None:
    source_id = _clean_source_id(source_id)
    source = get_source(source_id)
    source_label = source.label if args.wcda_week_survey else (args.source_label or source.label)
    wcda_day_path = source.expected_wcda_day_path() if args.wcda_week_survey else (args.wcda_day or source.expected_wcda_day_path())
    wcda_week_path = source.expected_wcda_week_path() if args.wcda_week_survey else (args.wcda_week or source.expected_wcda_week_path())
    fermi_week_path = source.expected_fermi_week_path() if args.wcda_week_survey else (args.fermi_week or source.expected_fermi_week_path())
    if args.wcda_week_survey:
        include_wcda_day = False
        include_fermi_week = False
    else:
        include_wcda_day = _resolve_optional_channel(args.include_wcda_day, source.default_wcda_day)
        include_fermi_week = _resolve_optional_channel(args.include_fermi_week, source.default_fermi_week)
    aligned_base = _resolve_output_base(args.aligned_dir)
    periodicity_base = _resolve_output_base(args.periodicity_dir)
    aligned_dir = aligned_base / source_id
    periodicity_dir = periodicity_base / source_id
    aligned_dir.mkdir(parents=True, exist_ok=True)
    periodicity_dir.mkdir(parents=True, exist_ok=True)

    render_existing_series = args.render_existing_series
    if args.render_existing_weekly_only:
        render_existing_series = ["wcda_weekly"]
    if render_existing_series:
        _render_existing_series(
            aligned_dir,
            periodicity_dir,
            source_label,
            args.wwz_color_scale,
            render_existing_series,
        )
        return None

    if wcda_week_path is None:
        raise ValueError(f"No WCDA weekly path resolved for source {source_id}.")

    wcda_week = read_wcda_counts_csv(wcda_week_path)
    _plot_wcda_counts(periodicity_dir / "wcda_weekly_counts.png", f"{source_label} WCDA weekly", wcda_week)
    wcda_week_lc = usable_light_curve(wcda_week, "flux_excess", "flux_excess_err")
    wcda_week_out = wcda_week_lc.rename(
        columns={"flux_excess": "wcda_flux_excess", "flux_excess_err": "wcda_flux_excess_err"}
    )
    wcda_week_out.to_csv(aligned_dir / "wcda_weekly_aligned.csv", index=False)

    jobs = []
    if include_wcda_day:
        if wcda_day_path is None or not wcda_day_path.exists():
            raise FileNotFoundError(f"WCDA daily input not found for source {source_id}: {wcda_day_path}")
        wcda_day = read_wcda_counts_csv(wcda_day_path)
        wcda_day_lc = usable_light_curve(wcda_day, "flux_excess", "flux_excess_err")
        wcda_day_out = wcda_day_lc.rename(
            columns={"flux_excess": "wcda_flux_excess", "flux_excess_err": "wcda_flux_excess_err"}
        )
        wcda_day_out.to_csv(aligned_dir / "wcda_daily_aligned.csv", index=False)
        jobs.append(
            (
                "wcda_daily",
                f"{source_label} WCDA daily",
                wcda_day_out["mjd"].to_numpy(dtype=float),
                wcda_day_out["wcda_flux_excess"].to_numpy(dtype=float),
                wcda_day_out["wcda_flux_excess_err"].to_numpy(dtype=float),
                5.0,
                200.0,
            )
        )

    jobs.append(
        (
            "wcda_weekly",
            f"{source_label} WCDA weekly",
            wcda_week_out["mjd"].to_numpy(dtype=float),
            wcda_week_out["wcda_flux_excess"].to_numpy(dtype=float),
            wcda_week_out["wcda_flux_excess_err"].to_numpy(dtype=float),
            50.0,
            600.0,
        )
    )

    if include_fermi_week:
        if fermi_week_path is None or not fermi_week_path.exists():
            raise FileNotFoundError(f"Fermi weekly input not found for source {source_id}: {fermi_week_path}")
        fermi_week = pd.read_csv(fermi_week_path)
        fermi_week_lc = usable_light_curve(fermi_week, "flux", "flux_err")
        fermi_on_wcda_week = align_to_reference_nearest(
            wcda_week_lc["mjd"].to_numpy(dtype=float),
            fermi_week_lc,
            tolerance_days=3.6,
            target_prefix="fermi",
        )
        fermi_on_wcda_week.to_csv(aligned_dir / "fermi_weekly_on_wcda_weekly_axis.csv", index=False)
        jobs.append(
            (
                "fermi_weekly_on_wcda_axis",
                f"{source_label} Fermi weekly on WCDA axis",
                fermi_on_wcda_week["mjd"].to_numpy(dtype=float),
                fermi_on_wcda_week["fermi_flux"].to_numpy(dtype=float),
                fermi_on_wcda_week["fermi_flux_err"].to_numpy(dtype=float),
                50.0,
                600.0,
            )
        )

    summary_rows = []
    for name, plot_label, t_mjd, flux, flux_err, period_min, period_max in jobs:
        finite = np.isfinite(t_mjd) & np.isfinite(flux) & np.isfinite(flux_err) & (flux_err > 0)
        t_use, flux_use, err_use = t_mjd[finite], flux[finite], flux_err[finite]
        cwt = run_cwt(t_use, flux_use, period_min=period_min, period_max=period_max)
        wwz = run_wwz(
            t_use,
            flux_use,
            err_use,
            period_min=period_min,
            period_max=period_max,
            time_divisions=args.wwz_time_divisions,
            freq_step_factor=args.wwz_freq_step_factor,
            parallel=args.wwz_parallel,
        )
        _save_cwt(periodicity_dir / f"{name}_cwt.npz", cwt)
        _save_wwz(periodicity_dir / f"{name}_wwz.npz", wwz)
        _plot_cwt(periodicity_dir / f"{name}_cwt.png", plot_label, t_use, flux_use, err_use, cwt)
        _plot_wwz(periodicity_dir / f"{name}_wwz.png", plot_label, wwz, color_scale=args.wwz_color_scale)
        _plot_periodicity_summary(
            periodicity_dir / f"{name}_periodicity.png",
            plot_label,
            t_use,
            flux_use,
            err_use,
            cwt,
            wwz,
            color_scale=args.wwz_color_scale,
            include_global_row=name == "wcda_weekly",
        )
        summary_rows.append(_summary_row(source_id, source_label, name, t_use, cwt, wwz))

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(periodicity_dir / "periodicity_v1_summary.csv", index=False)
    print(f"[OK] {source_id}: wrote aligned CSVs -> {aligned_dir.relative_to(PROJECT_ROOT)}")
    print(f"[OK] {source_id}: wrote CWT/WWZ npz files -> {periodicity_dir.relative_to(PROJECT_ROOT)}")
    print(summary.to_string(index=False))
    return summary


def _clean_source_id(source_id: str) -> str:
    cleaned = str(source_id).strip().lower().replace(" ", "_")
    if not cleaned:
        raise ValueError("--source-id cannot be empty.")
    return cleaned


def _resolve_source_ids(args: argparse.Namespace) -> list[str]:
    if args.wcda_week_survey:
        return list(WCDA_WEEK_SURVEY_SOURCE_IDS)
    if args.survey_shortlist:
        return list(DEFAULT_SURVEY_SOURCE_IDS)
    if args.source_ids:
        return [_clean_source_id(source_id) for source_id in args.source_ids]
    return [_clean_source_id(args.source_id)]


def _resolve_output_base(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _resolve_optional_channel(flag: bool | None, default_value: bool) -> bool:
    if flag is not None:
        return bool(flag)
    return bool(default_value)


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


def _summary_row(source_id: str, source_label: str, name: str, t_mjd: np.ndarray, cwt: dict, wwz: dict) -> dict:
    cwt_mask = cwt["mask_period"]
    cwt_peak_idx = np.nanargmax(np.where(cwt_mask, cwt["gws"], np.nan))
    wwz_period = wwz["period_axis"]
    wwz_mask = (wwz_period >= wwz["period_min"]) & (wwz_period <= wwz["period_max"])
    wwz_peak_idx = np.nanargmax(np.where(wwz_mask, wwz["global_wwz"], np.nan))
    return {
        "source_id": source_id,
        "source": source_label,
        "series": name,
        "n_points": int(len(t_mjd)),
        "mjd_min": float(np.nanmin(t_mjd)),
        "mjd_max": float(np.nanmax(t_mjd)),
        "median_dt_days": float(np.nanmedian(np.diff(t_mjd))),
        "cwt_peak_period_days": float(cwt["period"][cwt_peak_idx]),
        "cwt_peak_gws": float(cwt["gws"][cwt_peak_idx]),
        "wwz_peak_period_days": float(wwz_period[wwz_peak_idx]),
        "wwz_peak_power": float(wwz["global_wwz"][wwz_peak_idx]),
    }


def _render_existing_series(
    aligned_dir: Path,
    periodicity_dir: Path,
    source_label: str,
    color_scale: str,
    series_names: list[str],
) -> None:
    """Re-render selected figures from saved aligned CSV and CWT/WWZ arrays."""
    for series_name in series_names:
        config = RENDER_SERIES_CONFIG[series_name]
        aligned_path = aligned_dir / config["aligned"]
        cwt_path = periodicity_dir / f"{series_name}_cwt.npz"
        wwz_path = periodicity_dir / f"{series_name}_wwz.npz"
        missing = [path for path in (aligned_path, cwt_path, wwz_path) if not path.exists()]
        if missing:
            raise FileNotFoundError(f"Missing inputs for render-only mode ({series_name}): {missing}")

        aligned = pd.read_csv(aligned_path)
        t = aligned["mjd"].to_numpy(dtype=float)
        flux = aligned[config["flux"]].to_numpy(dtype=float)
        flux_err = aligned[config["flux_err"]].to_numpy(dtype=float)
        finite = np.isfinite(t) & np.isfinite(flux) & np.isfinite(flux_err) & (flux_err > 0)
        t, flux, flux_err = t[finite], flux[finite], flux_err[finite]

        cwt = _load_npz_dict(cwt_path)
        wwz = _load_npz_dict(wwz_path)
        plot_label = f"{source_label} {config['label']}"
        _plot_wwz(periodicity_dir / f"{series_name}_wwz.png", plot_label, wwz, color_scale=color_scale)
        _plot_periodicity_summary(
            periodicity_dir / f"{series_name}_periodicity.png",
            plot_label,
            t,
            flux,
            flux_err,
            cwt,
            wwz,
            color_scale=color_scale,
            include_global_row=series_name == "wcda_weekly",
        )
        print(
            f"[OK] re-rendered {series_name} figures with {color_scale} WWZ color scale "
            f"-> {periodicity_dir.relative_to(PROJECT_ROOT)}"
        )


def _load_npz_dict(path: Path) -> dict:
    with np.load(path) as data:
        return {key: data[key] for key in data.files}


def _plot_wcda_counts(path: Path, name: str, wcda_counts: pd.DataFrame) -> None:
    """Plot weekly photon-count diagnostics from the raw WCDA count columns."""
    required = {"mjd", "excess_counts", "n_on_tot", "n_bkg_tot"}
    missing = required - set(wcda_counts.columns)
    if missing:
        raise ValueError(f"Cannot plot WCDA counts; missing columns: {sorted(missing)}")

    plot_df = wcda_counts.loc[:, ["mjd", "excess_counts", "n_on_tot", "n_bkg_tot"]].copy()
    for col in plot_df.columns:
        plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce")
    plot_df = plot_df.replace([np.inf, -np.inf], np.nan).dropna(subset=["mjd", "excess_counts"])
    if plot_df.empty:
        raise ValueError(f"Cannot plot WCDA counts for {name}; no finite excess count rows.")

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(13.5, 6.2),
        sharex=True,
        gridspec_kw={"height_ratios": [1.35, 1.0]},
        constrained_layout=True,
    )
    ax_excess, ax_totals = axes
    ax_excess.axhline(0.0, color="0.35", lw=0.9, alpha=0.8)
    ax_excess.plot(plot_df["mjd"], plot_df["excess_counts"], marker="o", ms=3.0, lw=1.0, color="#255c99")
    ax_excess.set_title(f"{name} photon-count diagnostic")
    ax_excess.set_ylabel("Excess counts")
    ax_excess.grid(True, alpha=0.25)

    finite_totals = plot_df.dropna(subset=["n_on_tot", "n_bkg_tot"])
    if not finite_totals.empty:
        ax_totals.plot(finite_totals["mjd"], finite_totals["n_on_tot"], lw=1.0, color="#1b7f5c", label="n_on total")
        ax_totals.plot(finite_totals["mjd"], finite_totals["n_bkg_tot"], lw=1.0, color="#b65c2a", label="n_bkg total")
        ax_totals.legend(loc="upper right")
    ax_totals.set_xlabel("MJD")
    ax_totals.set_ylabel("Counts")
    ax_totals.grid(True, alpha=0.25)

    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_cwt(path: Path, name: str, t_mjd: np.ndarray, flux: np.ndarray, flux_err: np.ndarray, result: dict) -> None:
    period = result["period"]
    mask_period = result["mask_period"]
    power = result["power"]
    coi = result["coi"]
    gws = result["gws"]
    period_min = result["period_min"]
    period_max = result["period_max"]
    t_grid, p_grid = np.meshgrid(t_mjd, period)

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(17, 4.8),
        gridspec_kw={"width_ratios": [1.45, 2.5, 1.0]},
        constrained_layout=True,
    )
    ax_lc, ax_map, ax_gws = axes
    ax_lc.errorbar(t_mjd, flux, yerr=flux_err, fmt="o", ms=3.2, capsize=2, elinewidth=0.9)
    ax_lc.set_title(name)
    ax_lc.set_xlabel("MJD")
    ax_lc.set_ylabel("Flux")

    im = ax_map.contourf(
        t_grid[mask_period, :],
        p_grid[mask_period, :],
        power[mask_period, :],
        levels=50,
        cmap="magma",
        extend="both",
    )
    coi_clip = np.clip(coi, period_min, period_max)
    ax_map.fill_between(
        t_mjd,
        period_max,
        coi_clip,
        where=coi_clip <= period_max,
        color="white",
        alpha=0.5,
        hatch="/",
        edgecolor="0.7",
        linewidth=0.0,
    )
    ax_map.plot(t_mjd, coi_clip, color="white", lw=1.3, label="COI")
    ax_map.set_yscale("log")
    ax_map.set_ylim(period_min, period_max)
    ax_map.set_xlabel("MJD")
    ax_map.set_ylabel("Period (day)")
    ax_map.set_title("CWT Power")
    ax_map.legend(loc="upper right")
    fig.colorbar(im, ax=ax_map, pad=0.02, label="Power")

    ax_gws.plot(gws[mask_period], period[mask_period], color="black", lw=1.5)
    ax_gws.set_xscale("log")
    ax_gws.set_yscale("log")
    ax_gws.set_ylim(period_min, period_max)
    ax_gws.set_xlabel("GWS")
    ax_gws.set_title("Global Spectrum")
    plt.setp(ax_gws.get_yticklabels(), visible=False)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_wwz(path: Path, name: str, result: dict, *, color_scale: str = "linear") -> None:
    t = result["t"]
    y = result["y"]
    yerr = result["yerr"]
    period_min = result["period_min"]
    period_max = result["period_max"]
    tau_plot = result["tau_mat"][:, 0]
    period_mat = result["period_mat"]
    wwz_mat = result["wwz_mat"]
    sort_idx = np.argsort(period_mat[0, :])
    period_axis = period_mat[0, sort_idx]
    wwz_plot = wwz_mat[:, sort_idx]
    global_period = result["period_axis"]
    global_wwz = result["global_wwz"]
    global_sort = np.argsort(global_period)

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(17, 4.8),
        gridspec_kw={"width_ratios": [1.45, 2.5, 1.0]},
        constrained_layout=True,
    )
    ax_lc, ax_map, ax_gwwz = axes
    ax_lc.errorbar(t, y, yerr=yerr, fmt="o", ms=3.2, capsize=2, elinewidth=0.9)
    ax_lc.set_title(name)
    ax_lc.set_xlabel("MJD")
    ax_lc.set_ylabel("Flux")

    wwz_plot_masked, wwz_norm = _wwz_power_for_plot(wwz_plot, color_scale)
    mesh = ax_map.pcolormesh(
        tau_plot,
        period_axis,
        wwz_plot_masked.T,
        shading="auto",
        cmap="viridis",
        norm=wwz_norm,
    )
    ax_map.plot(result["ridge_tau"], result["ridge_period"], color="black", lw=1.2, alpha=0.9, label="ridge")
    ax_map.set_yscale("log")
    ax_map.set_ylim(period_min, period_max)
    ax_map.set_xlabel("MJD")
    ax_map.set_ylabel("Period (day)")
    ax_map.set_title("WWZ Power")
    ax_map.legend(loc="upper right")
    fig.colorbar(mesh, ax=ax_map, pad=0.02, label=f"WWZ ({color_scale})")

    ax_gwwz.plot(global_wwz[global_sort], global_period[global_sort], color="black", lw=1.5)
    ax_gwwz.set_ylim(period_min, period_max)
    ax_gwwz.set_xlabel("Mean WWZ")
    ax_gwwz.set_title("Global WWZ")
    plt.setp(ax_gwwz.get_yticklabels(), visible=False)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_periodicity_summary(
    path: Path,
    name: str,
    t_mjd: np.ndarray,
    flux: np.ndarray,
    flux_err: np.ndarray,
    cwt: dict,
    wwz: dict,
    *,
    color_scale: str = "linear",
    include_global_row: bool = False,
) -> None:
    cwt_period = cwt["period"]
    cwt_mask = cwt["mask_period"]
    cwt_power = cwt["power"]
    cwt_period_min = cwt["period_min"]
    cwt_period_max = cwt["period_max"]
    cwt_t_grid, cwt_p_grid = np.meshgrid(t_mjd, cwt_period)

    wwz_period_min = wwz["period_min"]
    wwz_period_max = wwz["period_max"]
    wwz_tau = wwz["tau_mat"][:, 0]
    wwz_period_mat = wwz["period_mat"]
    wwz_sort_idx = np.argsort(wwz_period_mat[0, :])
    wwz_period_axis = wwz_period_mat[0, wwz_sort_idx]
    wwz_power = wwz["wwz_mat"][:, wwz_sort_idx]

    fig_height = 10.2 if include_global_row else 8.2
    fig = plt.figure(figsize=(14, fig_height), constrained_layout=True)
    if include_global_row:
        gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.45, 0.85])
    else:
        gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.45])
    ax_lc = fig.add_subplot(gs[0, :])
    ax_cwt = fig.add_subplot(gs[1, 0])
    ax_wwz = fig.add_subplot(gs[1, 1])
    ax_cwt_global = fig.add_subplot(gs[2, 0]) if include_global_row else None
    ax_wwz_global = fig.add_subplot(gs[2, 1]) if include_global_row else None

    ax_lc.errorbar(t_mjd, flux, yerr=flux_err, fmt="o", ms=3.0, capsize=2, elinewidth=0.8)
    ax_lc.set_title(name)
    ax_lc.set_xlabel("MJD")
    ax_lc.set_ylabel("Flux")

    cwt_im = ax_cwt.contourf(
        cwt_t_grid[cwt_mask, :],
        cwt_p_grid[cwt_mask, :],
        cwt_power[cwt_mask, :],
        levels=50,
        cmap="magma",
        extend="both",
    )
    cwt_coi_clip = np.clip(cwt["coi"], cwt_period_min, cwt_period_max)
    ax_cwt.fill_between(
        t_mjd,
        cwt_period_max,
        cwt_coi_clip,
        where=cwt_coi_clip <= cwt_period_max,
        color="white",
        alpha=0.5,
        hatch="/",
        edgecolor="0.7",
        linewidth=0.0,
    )
    ax_cwt.plot(t_mjd, cwt_coi_clip, color="white", lw=1.2, label="COI")
    ax_cwt.set_yscale("log")
    ax_cwt.set_ylim(cwt_period_min, cwt_period_max)
    ax_cwt.set_xlabel("MJD")
    ax_cwt.set_ylabel("Period (day)")
    ax_cwt.set_title("CWT Power")
    ax_cwt.legend(loc="upper right")
    fig.colorbar(cwt_im, ax=ax_cwt, pad=0.02, label="Power")

    wwz_power_masked, wwz_norm = _wwz_power_for_plot(wwz_power, color_scale)
    wwz_mesh = ax_wwz.pcolormesh(
        wwz_tau,
        wwz_period_axis,
        wwz_power_masked.T,
        shading="auto",
        cmap="viridis",
        norm=wwz_norm,
    )
    ax_wwz.plot(wwz["ridge_tau"], wwz["ridge_period"], color="black", lw=1.1, alpha=0.9, label="ridge")
    ax_wwz.set_yscale("log")
    ax_wwz.set_ylim(wwz_period_min, wwz_period_max)
    ax_wwz.set_xlabel("MJD")
    ax_wwz.set_ylabel("Period (day)")
    ax_wwz.set_title("WWZ Power")
    ax_wwz.legend(loc="upper right")
    fig.colorbar(wwz_mesh, ax=ax_wwz, pad=0.02, label=f"WWZ ({color_scale})")

    if include_global_row:
        _plot_cwt_global_row(ax_cwt_global, cwt)
        _plot_wwz_global_row(ax_wwz_global, wwz)

    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_cwt_global_row(ax: plt.Axes, cwt: dict) -> None:
    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    mask = np.asarray(cwt["mask_period"], dtype=bool) & np.isfinite(period) & np.isfinite(gws)
    period_plot = period[mask]
    gws_plot = gws[mask]
    order = np.argsort(period_plot)
    period_plot = period_plot[order]
    gws_plot = gws_plot[order]
    ax.plot(period_plot, gws_plot, color="black", lw=1.4)
    ax.set_xscale("log")
    ax.set_xlim(float(cwt["period_min"]), float(cwt["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("GWS")
    ax.set_title("CWT Global Spectrum")
    ax.grid(True, alpha=0.25)
    _mark_global_peaks(ax, period_plot, gws_plot)


def _plot_wwz_global_row(ax: plt.Axes, wwz: dict) -> None:
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
    global_wwz_plot = global_wwz[mask][order]
    ax.plot(period_plot, global_wwz_plot, color="black", lw=1.4)
    ax.set_xscale("log")
    ax.set_xlim(float(wwz["period_min"]), float(wwz["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Mean WWZ")
    ax.set_title("WWZ Global Spectrum")
    ax.grid(True, alpha=0.25)
    _mark_global_peaks(ax, period_plot, global_wwz_plot)


def _mark_global_peaks(ax: plt.Axes, period: np.ndarray, power: np.ndarray) -> None:
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

    peaks, _properties = find_peaks(
        power,
        prominence=GLOBAL_PEAK_PROMINENCE_FRACTION * power_range,
        distance=GLOBAL_PEAK_MIN_DISTANCE_BINS,
    )
    if len(peaks) == 0:
        return

    y_min, y_max = ax.get_ylim()
    y_text = y_min + 0.90 * (y_max - y_min)
    for peak_idx in peaks:
        peak_period = float(period[peak_idx])
        ax.axvline(peak_period, color="red", ls="--", lw=1.0, alpha=0.85)
        ax.text(
            peak_period,
            y_text,
            _format_period_label(peak_period),
            color="red",
            fontsize=8,
            rotation=90,
            ha="right",
            va="top",
        )


def _format_period_label(period: float) -> str:
    if period >= 100:
        return f"{period:.0f} d"
    if period >= 10:
        return f"{period:.1f} d"
    return f"{period:.2f} d"


def _wwz_power_for_plot(power: np.ndarray, color_scale: str) -> tuple[np.ma.MaskedArray, Normalize | LogNorm | None]:
    power = np.asarray(power, dtype=float)
    if color_scale == "linear":
        finite = np.isfinite(power)
        if not np.any(finite):
            raise ValueError("WWZ linear heatmap requires at least one finite power value.")
        return np.ma.masked_where(~finite, power), Normalize(
            vmin=float(np.nanmin(power[finite])),
            vmax=float(np.nanmax(power[finite])),
        )
    if color_scale == "log":
        return _positive_log_power(power)
    raise ValueError(f"Unsupported WWZ color scale: {color_scale}")


def _positive_log_power(power: np.ndarray) -> tuple[np.ma.MaskedArray, LogNorm]:
    power = np.asarray(power, dtype=float)
    positive = np.isfinite(power) & (power > 0)
    if not np.any(positive):
        raise ValueError("WWZ log heatmap requires at least one positive finite power value.")
    masked = np.ma.masked_where(~positive, power)
    return masked, LogNorm(vmin=float(np.nanmin(power[positive])), vmax=float(np.nanmax(power[positive])))


if __name__ == "__main__":
    main()
