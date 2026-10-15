#!/usr/bin/env python3
"""Build the final, uniformly-formatted figure set for the Mrk 421 / Mrk 501 QPO
status report, for both weekly and daily cadence, into one dedicated folder:

    reports/assets/status_report_figures/<source>_<cadence>_<kind>.png

Per (source, cadence) combination, exactly 5 images:
    1. lc_ts        — 2-panel: flux light curve (top), TS per bin (bottom)
    2. cwt_summary  — 2-panel: global wavelet spectrum (left), CWT 2D power map (right)
    3. wwz_summary  — 2-panel: global WWZ (left), WWZ 2D power map (right)
    4. cwt_significance — copied from the already-computed AR(1) theoretical reference plot
    5. wwz_significance — copied from the already-computed AR(1) surrogate reference plot

Run: ~/miniconda3/envs/py310/bin/python src/pipeline/build_status_report_figures.py
"""
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data" / "processed"
OUT_DIR = ROOT / "reports" / "assets" / "status_report_figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SOURCES = {"mkn421": "Mrk 421", "mkn501": "Mrk 501"}


def load_npz(path):
    with np.load(path, allow_pickle=True) as f:
        return {k: f[k] for k in f.files}


def paths_for(source_id, cadence):
    if cadence == "weekly":
        aligned_glob = list((DATA / "aligned" / "agn_wcda_weekly_flux_survey" / source_id).glob("*.csv"))
        aligned = aligned_glob[0]
        cwt = DATA / "periodicity" / "agn_wcda_weekly_flux_survey" / source_id / "wcda_strict_flux_weekly_cwt.npz"
        wwz = DATA / "periodicity" / "agn_wcda_weekly_flux_survey" / source_id / "wcda_strict_flux_weekly_wwz.npz"
        cwt_sig = DATA / "periodicity" / "agn_wcda_weekly_flux_survey" / source_id / "wcda_strict_flux_weekly_cwt_global_significance.png"
        wwz_sig = DATA / "periodicity" / "agn_wcda_weekly_flux_survey" / source_id / "wcda_strict_flux_weekly_wwz_global_significance.png"
        flux_col, err_col = "N0", "N0_err"
    else:
        aligned = DATA / "aligned" / "periodicity_v2" / source_id / "wcda_daily_flux_aligned.csv"
        cwt = DATA / "periodicity" / "periodicity_v2" / source_id / "wcda_daily_flux_cwt.npz"
        wwz = DATA / "periodicity" / "periodicity_v2" / source_id / "wcda_daily_flux_wwz.npz"
        cwt_sig = DATA / "periodicity" / "periodicity_v2" / source_id / "wcda_daily_flux_cwt_global_significance.png"
        wwz_sig = DATA / "periodicity" / "periodicity_v2" / source_id / "wcda_daily_flux_wwz_global_significance.png"
        flux_col, err_col = "N0", "N0_err"
    return aligned, cwt, wwz, cwt_sig, wwz_sig, flux_col, err_col


def plot_lc_ts(path, title, mjd, flux, flux_err, ts, usable):
    fig, axes = plt.subplots(2, 1, figsize=(13.5, 6.4), sharex=True,
                              gridspec_kw={"height_ratios": [1.35, 0.85]}, constrained_layout=True)
    ax_flux, ax_ts = axes
    usable = np.asarray(usable, dtype=bool)
    ax_flux.errorbar(mjd[usable], flux[usable], yerr=flux_err[usable], fmt="o-", ms=3.0, lw=0.8,
                      capsize=2, color="#255c99", ecolor="#7da0c9", label="usable fit")
    if (~usable).any():
        ax_flux.scatter(mjd[~usable], flux[~usable], marker="x", s=32, color="#b65c2a", label="excluded fit")
    ax_flux.axhline(0.0, color="0.4", lw=0.8, alpha=0.8)
    ax_flux.set_title(title)
    ax_flux.set_ylabel("N0 at 3 TeV\ncm$^{-2}$ s$^{-1}$ TeV$^{-1}$")
    ax_flux.grid(True, alpha=0.25)
    ax_flux.legend(loc="upper right", frameon=False, fontsize=8)

    ax_ts.plot(mjd, ts, "o-", ms=2.6, lw=0.7, color="#4d5a6b")
    ax_ts.axhline(9, color="#a6362c", ls="--", lw=1, label="TS=9")
    ax_ts.set_xlabel("MJD")
    ax_ts.set_ylabel("TS")
    ax_ts.grid(True, alpha=0.25)
    ax_ts.legend(loc="upper right", frameon=False, fontsize=8)

    fig.savefig(path, dpi=170)
    plt.close(fig)


def plot_cwt_summary(path, title, cwt):
    period = np.asarray(cwt["period"], dtype=float)
    mask = np.asarray(cwt["mask_period"], dtype=bool)
    power = np.asarray(cwt["power"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    coi = np.asarray(cwt["coi"], dtype=float)
    t_mjd = np.asarray(cwt["t_mjd"], dtype=float)
    period_min, period_max = float(cwt["period_min"]), float(cwt["period_max"])

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [2.3, 1.0]},
                              constrained_layout=True)
    ax_map, ax_gws = axes
    ax_gws.plot(gws[mask], period[mask], color="black", lw=1.6)
    ax_gws.set_xscale("log")
    ax_gws.set_yscale("log")
    ax_gws.set_ylim(period_min, period_max)
    ax_gws.set_xlabel("Global Wavelet Power")
    ax_gws.set_ylabel("Period (day)")
    ax_gws.set_title("Global Spectrum")

    t_grid, p_grid = np.meshgrid(t_mjd, period)
    im = ax_map.contourf(t_grid[mask, :], p_grid[mask, :], power[mask, :], levels=50, cmap="magma", extend="both")
    coi_clip = np.clip(coi, period_min, period_max)
    ax_map.fill_between(t_mjd, period_max, coi_clip, where=coi_clip <= period_max, color="white", alpha=0.5,
                         hatch="/", edgecolor="0.7", linewidth=0.0)
    ax_map.plot(t_mjd, coi_clip, color="white", lw=1.3, label="COI")
    ax_map.set_yscale("log")
    ax_map.set_ylim(period_min, period_max)
    ax_map.set_xlabel("MJD")
    ax_map.set_ylabel("Period (day)")
    ax_map.set_title(f"{title} — CWT 2D Power")
    ax_map.legend(loc="upper right", fontsize=8)
    fig.colorbar(im, ax=ax_map, pad=0.02, label="Power")
    plt.setp(ax_gws.get_yticklabels(), visible=False)
    ax_gws.set_ylabel("")

    fig.savefig(path, dpi=170)
    plt.close(fig)


def plot_wwz_summary(path, title, wwz):
    period_min, period_max = float(wwz["period_min"]), float(wwz["period_max"])
    tau_plot = wwz["tau_mat"][:, 0]
    period_mat = wwz["period_mat"]
    wwz_mat = np.asarray(wwz["wwz_mat"], dtype=float)
    sort_idx = np.argsort(period_mat[0, :])
    period_axis_map = period_mat[0, sort_idx]
    wwz_plot = wwz_mat[:, sort_idx]
    global_period = np.asarray(wwz["period_axis"], dtype=float)
    global_wwz = np.asarray(wwz["global_wwz"], dtype=float)
    global_sort = np.argsort(global_period)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [2.3, 1.0]},
                              constrained_layout=True)
    ax_map, ax_gwwz = axes
    ax_gwwz.plot(global_wwz[global_sort], global_period[global_sort], color="black", lw=1.6)
    ax_gwwz.set_yscale("log")
    ax_gwwz.set_ylim(period_min, period_max)
    ax_gwwz.set_xlabel("Mean WWZ Power")
    ax_gwwz.set_title("Global WWZ")

    finite = np.isfinite(wwz_plot)
    norm = Normalize(vmin=float(np.nanmin(wwz_plot[finite])), vmax=float(np.nanmax(wwz_plot[finite])))
    mesh = ax_map.pcolormesh(tau_plot, period_axis_map, np.ma.masked_where(~finite, wwz_plot).T,
                              shading="auto", cmap="viridis", norm=norm)
    ax_map.plot(wwz["ridge_tau"], wwz["ridge_period"], color="black", lw=1.1, alpha=0.9, label="ridge")
    ax_map.set_yscale("log")
    ax_map.set_ylim(period_min, period_max)
    ax_map.set_xlabel("MJD")
    ax_map.set_ylabel("Period (day)")
    ax_map.set_title(f"{title} — WWZ 2D Power")
    ax_map.legend(loc="upper right", fontsize=8)
    fig.colorbar(mesh, ax=ax_map, pad=0.02, label="WWZ power")
    plt.setp(ax_gwwz.get_yticklabels(), visible=False)

    fig.savefig(path, dpi=170)
    plt.close(fig)


def main():
    for source_id, label in SOURCES.items():
        for cadence in ("weekly", "daily"):
            aligned_path, cwt_path, wwz_path, cwt_sig_src, wwz_sig_src, flux_col, err_col = paths_for(source_id, cadence)
            df = pd.read_csv(aligned_path)
            df = df.sort_values("mjd").reset_index(drop=True)
            mjd = df["mjd"].to_numpy(dtype=float)
            flux = pd.to_numeric(df[flux_col], errors="coerce").to_numpy(dtype=float)
            flux_err = pd.to_numeric(df[err_col], errors="coerce").to_numpy(dtype=float)
            ts = pd.to_numeric(df["TS"], errors="coerce").to_numpy(dtype=float)
            if "is_usable_for_periodicity" in df.columns:
                usable = df["is_usable_for_periodicity"].astype(bool).to_numpy()
            else:
                usable = (df["fit_status"].astype(str) == "OK").to_numpy()

            cwt = load_npz(cwt_path)
            wwz = load_npz(wwz_path)

            prefix = f"{source_id}_{cadence}"
            title = f"{label} — {cadence}"
            plot_lc_ts(OUT_DIR / f"{prefix}_lc_ts.png", title, mjd, flux, flux_err, ts, usable)
            plot_cwt_summary(OUT_DIR / f"{prefix}_cwt_summary.png", title, cwt)
            plot_wwz_summary(OUT_DIR / f"{prefix}_wwz_summary.png", title, wwz)
            shutil.copyfile(cwt_sig_src, OUT_DIR / f"{prefix}_cwt_significance.png")
            shutil.copyfile(wwz_sig_src, OUT_DIR / f"{prefix}_wwz_significance.png")
            print(f"[{source_id}/{cadence}] done -> {prefix}_*.png")


if __name__ == "__main__":
    main()
