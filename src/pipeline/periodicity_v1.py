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
from matplotlib.colors import LogNorm  # noqa: E402


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
from utils.project_paths import PROCESSED_DATA_DIR, PROJECT_ROOT  # noqa: E402


WCDA_DAY_CSV = PROCESSED_DATA_DIR / "wcda_day" / "LHAASO-WCDA_Mkn421_2025-03-29_2026-03-29_day.csv"
WCDA_WEEK_CSV = PROCESSED_DATA_DIR / "wcda_week" / "LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv"
FERMI_WEEK_CSV = PROCESSED_DATA_DIR / "fermi_week" / "Mrk421_Fermi_weekly_TSge9_MJD.csv"
ALIGNED_DIR = PROCESSED_DATA_DIR / "aligned"
PERIODICITY_DIR = PROCESSED_DATA_DIR / "periodicity"
SOURCE_WITH_DEFAULT_AUX = "mkn421"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", default=SOURCE_WITH_DEFAULT_AUX, help="Short source key used for output directories.")
    parser.add_argument("--source-label", default="Mrk 421", help="Human-readable source name used in plots.")
    parser.add_argument("--wcda-day", type=Path, default=WCDA_DAY_CSV)
    parser.add_argument("--wcda-week", type=Path, default=WCDA_WEEK_CSV)
    parser.add_argument("--fermi-week", type=Path, default=FERMI_WEEK_CSV)
    parser.add_argument("--aligned-dir", type=Path, default=ALIGNED_DIR)
    parser.add_argument("--periodicity-dir", type=Path, default=PERIODICITY_DIR)
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    source_id = _clean_source_id(args.source_id)
    include_wcda_day = _resolve_optional_channel(args.include_wcda_day, source_id)
    include_fermi_week = _resolve_optional_channel(args.include_fermi_week, source_id)
    aligned_dir = args.aligned_dir / source_id
    periodicity_dir = args.periodicity_dir / source_id
    aligned_dir.mkdir(parents=True, exist_ok=True)
    periodicity_dir.mkdir(parents=True, exist_ok=True)

    wcda_week = read_wcda_counts_csv(args.wcda_week)
    wcda_week_lc = usable_light_curve(wcda_week, "flux_excess", "flux_excess_err")

    wcda_week_out = wcda_week_lc.rename(
        columns={"flux_excess": "wcda_flux_excess", "flux_excess_err": "wcda_flux_excess_err"}
    )

    wcda_week_out.to_csv(aligned_dir / "wcda_weekly_aligned.csv", index=False)

    jobs = []
    if include_wcda_day:
        wcda_day = read_wcda_counts_csv(args.wcda_day)
        wcda_day_lc = usable_light_curve(wcda_day, "flux_excess", "flux_excess_err")
        wcda_day_out = wcda_day_lc.rename(
            columns={"flux_excess": "wcda_flux_excess", "flux_excess_err": "wcda_flux_excess_err"}
        )
        wcda_day_out.to_csv(aligned_dir / "wcda_daily_aligned.csv", index=False)
        jobs.append(
            (
                "wcda_daily",
                f"{args.source_label} WCDA daily",
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
            f"{args.source_label} WCDA weekly",
            wcda_week_out["mjd"].to_numpy(dtype=float),
            wcda_week_out["wcda_flux_excess"].to_numpy(dtype=float),
            wcda_week_out["wcda_flux_excess_err"].to_numpy(dtype=float),
            50.0,
            600.0,
        )
    )

    if include_fermi_week:
        fermi_week = pd.read_csv(args.fermi_week)
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
                f"{args.source_label} Fermi weekly on WCDA axis",
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
        _plot_wwz(periodicity_dir / f"{name}_wwz.png", plot_label, wwz)
        _plot_periodicity_summary(
            periodicity_dir / f"{name}_periodicity.png",
            plot_label,
            t_use,
            flux_use,
            err_use,
            cwt,
            wwz,
        )
        summary_rows.append(_summary_row(source_id, args.source_label, name, t_use, cwt, wwz))

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(periodicity_dir / "periodicity_v1_summary.csv", index=False)
    print(f"[OK] wrote aligned CSVs -> {aligned_dir.relative_to(PROJECT_ROOT)}")
    print(f"[OK] wrote CWT/WWZ npz files -> {periodicity_dir.relative_to(PROJECT_ROOT)}")
    print(summary.to_string(index=False))


def _clean_source_id(source_id: str) -> str:
    cleaned = str(source_id).strip().lower().replace(" ", "_")
    if not cleaned:
        raise ValueError("--source-id cannot be empty.")
    return cleaned


def _resolve_optional_channel(flag: bool | None, source_id: str) -> bool:
    if flag is not None:
        return bool(flag)
    return source_id == SOURCE_WITH_DEFAULT_AUX


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


def _plot_wwz(path: Path, name: str, result: dict) -> None:
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

    wwz_plot_masked, wwz_norm = _positive_log_power(wwz_plot)
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
    fig.colorbar(mesh, ax=ax_map, pad=0.02, label="WWZ")

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

    fig = plt.figure(figsize=(14, 8.2), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.45])
    ax_lc = fig.add_subplot(gs[0, :])
    ax_cwt = fig.add_subplot(gs[1, 0])
    ax_wwz = fig.add_subplot(gs[1, 1])

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

    wwz_power_masked, wwz_norm = _positive_log_power(wwz_power)
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
    fig.colorbar(wwz_mesh, ax=ax_wwz, pad=0.02, label="WWZ")

    fig.savefig(path, dpi=180)
    plt.close(fig)


def _positive_log_power(power: np.ndarray) -> tuple[np.ma.MaskedArray, LogNorm]:
    power = np.asarray(power, dtype=float)
    positive = np.isfinite(power) & (power > 0)
    if not np.any(positive):
        raise ValueError("WWZ log heatmap requires at least one positive finite power value.")
    masked = np.ma.masked_where(~positive, power)
    return masked, LogNorm(vmin=float(np.nanmin(power[positive])), vmax=float(np.nanmax(power[positive])))


if __name__ == "__main__":
    main()
