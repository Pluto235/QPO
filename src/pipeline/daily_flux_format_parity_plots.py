#!/usr/bin/env python3
"""Generate the daily-cadence lightcurve-only and WWZ 3-panel plots so the daily
Mrk 421 / Mrk 501 figure set matches the weekly set's exact visual pattern:
lightcurve-alone + CWT 3-panel (already exists as wcda_daily_flux_periodicity.png,
built with the same layout as weekly's CWT plot) + WWZ 3-panel (new here) +
2 significance plots (already exist).

Run: ~/miniconda3/envs/py310/bin/python src/pipeline/daily_flux_format_parity_plots.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402

PERIODICITY_V2_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "periodicity" / "periodicity_v2"
SOURCES = {"mkn421": "Mrk 421", "mkn501": "Mrk 501"}


def load_npz(path):
    with np.load(path, allow_pickle=True) as f:
        return {k: f[k] for k in f.files}


def plot_lightcurve(path, title, t, y, yerr):
    fig, ax = plt.subplots(figsize=(13.5, 4.2), constrained_layout=True)
    ax.errorbar(t, y, yerr=yerr, fmt="o-", ms=2.2, lw=0.6, capsize=1.5,
                color="#255c99", ecolor="#7da0c9")
    ax.axhline(0.0, color="0.4", lw=0.8, alpha=0.8)
    ax.set_title(title)
    ax.set_xlabel("MJD")
    ax.set_ylabel("N0 at 3 TeV\ncm$^{-2}$ s$^{-1}$ TeV$^{-1}$")
    ax.grid(True, alpha=0.25)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_wwz_3panel(path, title, t, y, yerr, wwz):
    period_min, period_max = float(wwz["period_min"]), float(wwz["period_max"])
    tau_plot = wwz["tau_mat"][:, 0]
    period_mat = wwz["period_mat"]
    wwz_mat = wwz["wwz_mat"]
    sort_idx = np.argsort(period_mat[0, :])
    period_axis_map = period_mat[0, sort_idx]
    wwz_plot = wwz_mat[:, sort_idx]
    global_period = wwz["period_axis"]
    global_wwz = wwz["global_wwz"]
    global_sort = np.argsort(global_period)

    fig, axes = plt.subplots(1, 3, figsize=(17, 4.8), gridspec_kw={"width_ratios": [1.45, 2.5, 1.0]},
                              constrained_layout=True)
    ax_lc, ax_map, ax_gwwz = axes
    ax_lc.errorbar(t, y, yerr=yerr, fmt="o", ms=3.2, capsize=2, elinewidth=0.9, color="#255c99", ecolor="#7da0c9")
    ax_lc.set_title(title)
    ax_lc.set_xlabel("MJD")
    ax_lc.set_ylabel("Flux")

    finite = np.isfinite(wwz_plot)
    norm = Normalize(vmin=float(np.nanmin(wwz_plot[finite])), vmax=float(np.nanmax(wwz_plot[finite])))
    mesh = ax_map.pcolormesh(tau_plot, period_axis_map, np.ma.masked_where(~finite, wwz_plot).T,
                              shading="auto", cmap="viridis", norm=norm)
    ax_map.plot(wwz["ridge_tau"], wwz["ridge_period"], color="black", lw=1.2, alpha=0.9, label="ridge")
    ax_map.set_yscale("log")
    ax_map.set_ylim(period_min, period_max)
    ax_map.set_xlabel("MJD")
    ax_map.set_ylabel("Period (day)")
    ax_map.set_title("WWZ Power")
    ax_map.legend(loc="upper right")
    fig.colorbar(mesh, ax=ax_map, pad=0.02, label="WWZ (linear)")

    ax_gwwz.plot(global_wwz[global_sort], global_period[global_sort], color="black", lw=1.5)
    ax_gwwz.set_ylim(period_min, period_max)
    ax_gwwz.set_xlabel("Mean WWZ")
    ax_gwwz.set_title("Global WWZ")
    plt.setp(ax_gwwz.get_yticklabels(), visible=False)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main():
    for sid, label in SOURCES.items():
        src_dir = PERIODICITY_V2_DIR / sid
        wwz = load_npz(src_dir / "wcda_daily_flux_wwz.npz")
        t, y, yerr = wwz["t"], wwz["y"], wwz["yerr"]

        plot_lightcurve(src_dir / "wcda_daily_flux_lightcurve.png",
                         f"{label} — daily N0 flux light curve", t, y, yerr)
        plot_wwz_3panel(src_dir / "wcda_daily_flux_wwz_3panel.png",
                         f"{label} — daily", t, y, yerr, wwz)
        print(f"[{sid}] wrote lightcurve + WWZ 3-panel plots")


if __name__ == "__main__":
    main()
