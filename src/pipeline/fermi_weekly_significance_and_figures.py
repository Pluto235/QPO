#!/usr/bin/env python3
"""Fermi-LAT weekly (Mrk 421, WCDA-axis-aligned) CWT/WWZ AR(1) significance +
the same unified 5-figure set used for WCDA weekly/daily, into
reports/assets/status_report_figures/mkn421_fermi_*.png.

N=224 here (small, like WCDA weekly) so the WWZ surrogate MC runs fast locally
(~1.6s/realization) — no remote job needed, unlike the WCDA daily case.

Run: ~/miniconda3/envs/py310/bin/python src/pipeline/fermi_weekly_significance_and_figures.py
"""
import multiprocessing as mp
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
from scipy.signal import find_peaks  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
import pycwt as wavelet  # noqa: E402
from methods.periodicity import run_wwz, standardize_flux  # noqa: E402

V2_421 = ROOT / "data" / "processed" / "periodicity" / "periodicity_v2" / "mkn421"
OUT_DIR = ROOT / "reports" / "assets" / "status_report_figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LABEL = "Mrk 421"
N_SURROGATES = 300
SEED = 421501
GLOBAL_PEAK_PROMINENCE_FRACTION = 0.10
GLOBAL_PEAK_MIN_DISTANCE_BINS = 2
WWZ_LOCAL_WINDOW_FRACTION = 0.10


def _draw_peak_markers(ax, rows, *, show_fap=False):
    # Matches weekly_qpo_local_significance.py's _draw_peak_markers exactly: red dashed
    # vertical line per candidate peak, rotated label with period (and pl/pg FAP for WWZ).
    if not rows:
        return
    y_min, y_max = ax.get_ylim()
    y_text = y_min + 0.88 * (y_max - y_min)
    for idx, row in enumerate(rows):
        period = float(row["period_days"])
        ax.axvline(period, color="red", ls="--", lw=1.1, alpha=0.9)
        label = f"{period:.1f} d"
        if show_fap and np.isfinite(row.get("local_fap", np.nan)):
            label += f"\npl={float(row['local_fap']):.3f}"
            if np.isfinite(row.get("global_fap", np.nan)):
                label += f"\npg={float(row['global_fap']):.3f}"
        ax.text(period, y_text, label, color="red", fontsize=8, rotation=90, ha="right", va="top")
        y_text = y_min + (0.88 - 0.10 * ((idx + 1) % 3)) * (y_max - y_min)


def load_npz(path):
    with np.load(path, allow_pickle=True) as f:
        return {k: f[k] for k in f.files}


def candidate_peaks(period, power, period_min, period_max):
    mask = np.isfinite(period) & np.isfinite(power) & (period >= period_min) & (period <= period_max)
    order = np.argsort(period[mask])
    p, s = period[mask][order], power[mask][order]
    if len(p) < 3:
        return p, np.array([], dtype=int)
    rng = float(np.nanmax(s) - np.nanmin(s))
    if not np.isfinite(rng) or rng <= 0:
        return p, np.array([], dtype=int)
    peaks, _ = find_peaks(s, prominence=GLOBAL_PEAK_PROMINENCE_FRACTION * rng, distance=GLOBAL_PEAK_MIN_DISTANCE_BINS)
    return p, peaks


def lag1_autocorr(y):
    y = y[np.isfinite(y)]
    y0, y1 = y[:-1] - np.nanmean(y[:-1]), y[1:] - np.nanmean(y[1:])
    denom = float(np.sqrt(np.sum(y0 * y0) * np.sum(y1 * y1)))
    return float(np.clip(np.sum(y0 * y1) / denom, -0.95, 0.95)) if denom > 0 else 0.0


def simulate_ar1(n, alpha, mean, std, rng):
    innov = np.sqrt(max(1.0 - alpha**2, 1e-8))
    x = np.empty(n)
    x[0] = rng.normal()
    for i in range(1, n):
        x[i] = alpha * x[i - 1] + innov * rng.normal()
    x = (x - np.mean(x)) / np.std(x, ddof=1)
    return mean + std * x


def wwz_surrogate(task):
    seed, t, yerr, n, alpha, mean, std, pmin, pmax, tdiv, decay, fstep = task
    rng = np.random.default_rng(seed)
    sim_y = simulate_ar1(n, alpha, mean, std, rng)
    sim = run_wwz(t, sim_y, yerr, period_min=pmin, period_max=pmax, time_divisions=tdiv,
                  decay_constant=decay, freq_step_factor=fstep, parallel=False)
    return np.asarray(sim["global_wwz"], dtype=float)


def main():
    cwt = load_npz(V2_421 / "fermi_weekly_on_wcda_flux_axis_cwt.npz")
    wwz = load_npz(V2_421 / "fermi_weekly_on_wcda_flux_axis_wwz.npz")
    t, y, yerr = wwz["t"], wwz["y"], wwz["yerr"]
    n = len(t)
    print(f"N={n}, MJD {t.min():.1f}-{t.max():.1f}")

    # ---- CWT: theoretical AR(1) significance (fast, closed-form) ----
    y_std = standardize_flux(y)
    alpha = lag1_autocorr(y_std)
    mother = wavelet.Morlet(6)
    scales = float(cwt["s0"]) * 2 ** (np.arange(int(cwt["J"]) + 1) * float(cwt["dj"]))
    dof = np.full_like(scales, fill_value=len(y_std), dtype=float)
    sig95, _ = wavelet.significance(y_std, float(cwt["dt"]), scales, sigma_test=1, alpha=alpha,
                                     significance_level=0.95, dof=dof, wavelet=mother)
    sig99, _ = wavelet.significance(y_std, float(cwt["dt"]), scales, sigma_test=1, alpha=alpha,
                                     significance_level=0.99, dof=dof, wavelet=mother)
    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    pmin, pmax = float(cwt["period_min"]), float(cwt["period_max"])
    cwt_period_plot, cwt_peaks = candidate_peaks(period, gws, pmin, pmax)
    cwt_candidates = [float(cwt_period_plot[i]) for i in cwt_peaks]
    print("CWT candidates:", cwt_candidates)

    # ---- WWZ: AR(1) Gaussian surrogate MC (fast here, N=224) ----
    wwz_period = np.asarray(wwz["period_axis"], dtype=float)
    global_wwz = np.asarray(wwz["global_wwz"], dtype=float)
    wwz_period_plot, wwz_peaks = candidate_peaks(wwz_period, global_wwz, float(wwz["period_min"]), float(wwz["period_max"]))
    y_mean, y_std_val = float(np.nanmean(y)), float(np.nanstd(y, ddof=1))
    alpha_wwz = float(np.clip(lag1_autocorr(standardize_flux(y)), -0.95, 0.95))

    rng = np.random.default_rng(SEED)
    seeds = rng.integers(0, np.iinfo(np.uint32).max, size=N_SURROGATES, dtype=np.uint32)
    tasks = [(int(s), t, yerr, n, alpha_wwz, y_mean, y_std_val, float(wwz["period_min"]), float(wwz["period_max"]),
              int(wwz["time_divisions"]), float(wwz["decay_constant"]), float(wwz["freq_step_factor"])) for s in seeds]
    print(f"Running {N_SURROGATES} WWZ surrogates across 8 workers ...")
    with mp.Pool(8) as pool:
        surrogate_global = np.vstack(pool.map(wwz_surrogate, tasks))
    q95 = np.nanpercentile(surrogate_global, 95, axis=0)
    q99 = np.nanpercentile(surrogate_global, 99, axis=0)
    print("WWZ candidates:", [float(wwz_period_plot[i]) for i in wwz_peaks])

    # Local/global FAP per WWZ candidate, matching weekly_qpo_local_significance.py's
    # _assess_wwz methodology (local-window max vs. surrogate local-window max distribution).
    cwt_rows = [{"period_days": p} for p in cwt_candidates]
    wwz_rows = []
    for peak_idx in wwz_peaks:
        peak_period = float(wwz_period_plot[peak_idx])
        window_min = peak_period * (1.0 - WWZ_LOCAL_WINDOW_FRACTION)
        window_max = peak_period * (1.0 + WWZ_LOCAL_WINDOW_FRACTION)
        mask = np.isfinite(wwz_period) & (wwz_period >= window_min) & (wwz_period <= window_max)
        if not np.any(mask):
            nearest = int(np.nanargmin(np.abs(wwz_period - peak_period)))
            mask = np.zeros_like(wwz_period, dtype=bool)
            mask[nearest] = True
        observed_local_max = float(np.nanmax(global_wwz[mask]))
        surrogate_local_max = np.nanmax(surrogate_global[:, mask], axis=1)
        surrogate_global_max = np.nanmax(surrogate_global, axis=1)
        exceed = int(np.count_nonzero(surrogate_local_max >= observed_local_max))
        local_fap = (exceed + 1.0) / (N_SURROGATES + 1.0)
        gexceed = int(np.count_nonzero(surrogate_global_max >= observed_local_max))
        global_fap = (gexceed + 1.0) / (N_SURROGATES + 1.0)
        wwz_rows.append({"period_days": peak_period, "local_fap": local_fap, "global_fap": global_fap})
    print("WWZ candidate FAP:", wwz_rows)

    # ---- figures: LC (no TS available for Fermi), CWT summary, WWZ summary, 2 significance plots ----
    fig, ax = plt.subplots(figsize=(13.5, 4.2), constrained_layout=True)
    ax.errorbar(t, y, yerr=yerr, fmt="o-", ms=3.0, lw=0.7, capsize=2, color="#255c99", ecolor="#7da0c9")
    ax.set_title(f"{LABEL} — Fermi-LAT weekly flux (0.1-300 GeV), WCDA-axis-aligned")
    ax.set_xlabel("MJD")
    ax.set_ylabel("Photon flux (cm$^{-2}$ s$^{-1}$)")
    ax.grid(True, alpha=0.25)
    fig.savefig(OUT_DIR / "mkn421_fermi_lc_ts.png", dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [2.3, 1.0]}, constrained_layout=True)
    ax_map, ax_gws = axes
    mask_p = np.asarray(cwt["mask_period"], dtype=bool)
    power = np.asarray(cwt["power"], dtype=float)
    coi = np.asarray(cwt["coi"], dtype=float)
    t_grid, p_grid = np.meshgrid(t, period)
    im = ax_map.contourf(t_grid[mask_p, :], p_grid[mask_p, :], power[mask_p, :], levels=50, cmap="magma", extend="both")
    coi_clip = np.clip(coi, pmin, pmax)
    ax_map.fill_between(t, pmax, coi_clip, where=coi_clip <= pmax, color="white", alpha=0.5, hatch="/",
                         edgecolor="0.7", linewidth=0.0)
    ax_map.plot(t, coi_clip, color="white", lw=1.3, label="COI")
    ax_map.set_yscale("log")
    ax_map.set_ylim(pmin, pmax)
    ax_map.set_xlabel("MJD")
    ax_map.set_ylabel("Period (day)")
    ax_map.set_title(f"{LABEL} — Fermi weekly CWT 2D Power")
    ax_map.legend(loc="upper right", fontsize=8)
    fig.colorbar(im, ax=ax_map, pad=0.02, label="Power")
    ax_gws.plot(gws[mask_p], period[mask_p], color="black", lw=1.6)
    ax_gws.set_xscale("log")
    ax_gws.set_yscale("log")
    ax_gws.set_ylim(pmin, pmax)
    ax_gws.set_xlabel("Global Wavelet Power")
    ax_gws.set_title("Global Spectrum")
    plt.setp(ax_gws.get_yticklabels(), visible=False)
    fig.savefig(OUT_DIR / "mkn421_fermi_cwt_summary.png", dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [2.3, 1.0]}, constrained_layout=True)
    ax_map, ax_gwwz = axes
    tau_plot = wwz["tau_mat"][:, 0]
    period_mat = wwz["period_mat"]
    wwz_mat = np.asarray(wwz["wwz_mat"], dtype=float)
    sort_idx = np.argsort(period_mat[0, :])
    finite = np.isfinite(wwz_mat[:, sort_idx])
    norm = Normalize(vmin=float(np.nanmin(wwz_mat[:, sort_idx][finite])), vmax=float(np.nanmax(wwz_mat[:, sort_idx][finite])))
    mesh = ax_map.pcolormesh(tau_plot, period_mat[0, sort_idx], np.ma.masked_where(~finite, wwz_mat[:, sort_idx]).T,
                              shading="auto", cmap="viridis", norm=norm)
    ax_map.plot(wwz["ridge_tau"], wwz["ridge_period"], color="black", lw=1.1, alpha=0.9, label="ridge")
    ax_map.set_yscale("log")
    ax_map.set_ylim(float(wwz["period_min"]), float(wwz["period_max"]))
    ax_map.set_xlabel("MJD")
    ax_map.set_ylabel("Period (day)")
    ax_map.set_title(f"{LABEL} — Fermi weekly WWZ 2D Power")
    ax_map.legend(loc="upper right", fontsize=8)
    fig.colorbar(mesh, ax=ax_map, pad=0.02, label="WWZ power")
    global_sort = np.argsort(wwz_period)
    ax_gwwz.plot(global_wwz[global_sort], wwz_period[global_sort], color="black", lw=1.6)
    ax_gwwz.set_yscale("log")
    ax_gwwz.set_ylim(float(wwz["period_min"]), float(wwz["period_max"]))
    ax_gwwz.set_xlabel("Mean WWZ Power")
    ax_gwwz.set_title("Global WWZ")
    plt.setp(ax_gwwz.get_yticklabels(), visible=False)
    fig.savefig(OUT_DIR / "mkn421_fermi_wwz_summary.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 4.4), constrained_layout=True)
    ax.plot(period, gws, color="black", lw=1.5, label="Observed GWS")
    ax.plot(period, sig95, color="#255c99", lw=1.1, ls="-.", label="AR(1) 95% reference")
    ax.plot(period, sig99, color="#7a3e9d", lw=1.1, ls=":", label="AR(1) 99% reference")
    ax.set_xscale("log")
    ax.set_xlim(pmin, pmax)
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Global wavelet spectrum")
    ax.set_title(f"{LABEL} — Fermi weekly CWT vs. AR(1) reference")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    _draw_peak_markers(ax, cwt_rows)
    fig.savefig(OUT_DIR / "mkn421_fermi_cwt_significance.png", dpi=170)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 4.4), constrained_layout=True)
    ax.plot(wwz_period, global_wwz, color="black", lw=1.5, label="Observed WWZ")
    ax.plot(wwz_period, q95, color="#255c99", lw=1.1, ls="-.", label="AR(1) surrogate 95%")
    ax.plot(wwz_period, q99, color="#7a3e9d", lw=1.1, ls=":", label="AR(1) surrogate 99%")
    ax.set_xscale("log")
    ax.set_xlim(float(wwz["period_min"]), float(wwz["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Mean WWZ power")
    ax.set_title(f"{LABEL} — Fermi weekly WWZ vs. AR(1) surrogate ({N_SURROGATES} realizations)")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    _draw_peak_markers(ax, wwz_rows, show_fap=True)
    fig.savefig(OUT_DIR / "mkn421_fermi_wwz_significance.png", dpi=170)
    plt.close(fig)

    print("Wrote 5 figures to", OUT_DIR)


if __name__ == "__main__":
    main()
