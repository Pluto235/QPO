#!/usr/bin/env python3
"""Reproduce the xgm poster WWZ quick-look panels for Mrk 421 daily WCDA data."""

from __future__ import annotations

import sys
import contextlib
import io
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import read_wcda_counts_csv, run_wwz, standardize_flux  # noqa: E402
from utils.project_paths import PROCESSED_DATA_DIR, PROJECT_ROOT  # noqa: E402


INPUT_CSV = (
    PROCESSED_DATA_DIR
    / "wcda_day"
    / "LHAASO-WCDA_Mkn421_2023-06-25_2026-03-29_day.csv"
)
OUTPUT_DIR = PROCESSED_DATA_DIR / "periodicity" / "xgm_poster_repro" / "mkn421"
VISUAL_REF_N_SURROGATES = 40
VISUAL_REF_SEED = 6020061098
VISUAL_REF_TIME_DIVISIONS = 24
VISUAL_REF_FREQ_STEP_FACTOR = 5.0


@dataclass(frozen=True)
class PosterWindow:
    key: str
    title: str
    mjd_min: float
    mjd_max: float
    period_min: float
    period_max: float
    flux_ylim: tuple[float, float]
    color_limits: tuple[float, float]
    fold_period: float | None = None
    candidate_periods: tuple[float, ...] = ()


WINDOWS = (
    PosterWindow(
        key="60200_60700",
        title="MJD 60200-60700",
        mjd_min=60200.0,
        mjd_max=60700.0,
        period_min=2.0,
        period_max=200.0,
        flux_ylim=(-100.0, 320.0),
        color_limits=(0.0, 10.0),
        fold_period=51.05,
    ),
    PosterWindow(
        key="61020_61098",
        title="MJD 61020-61098",
        mjd_min=61020.0,
        mjd_max=61098.0,
        period_min=2.0,
        period_max=50.0,
        flux_ylim=(-20.0, 320.0),
        color_limits=(0.0, 10.0),
        candidate_periods=(2.54, 5.2, 16.6),
    ),
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    lc = _load_excess_counts(INPUT_CSV)

    rows = []
    for window in WINDOWS:
        sub = lc[(lc["mjd"] >= window.mjd_min) & (lc["mjd"] <= window.mjd_max)].copy()
        if len(sub) < 4:
            raise ValueError(f"{window.key} has fewer than four usable points.")

        wwz = run_wwz(
            sub["mjd"].to_numpy(dtype=float),
            sub["excess_counts"].to_numpy(dtype=float),
            sub["excess_counts_err"].to_numpy(dtype=float),
            period_min=window.period_min,
            period_max=window.period_max,
            time_divisions=min(len(sub), 250),
            decay_constant=0.0125,
            freq_step_factor=0.5,
            parallel=False,
        )

        out_png = OUTPUT_DIR / f"mkn421_daily_{window.key}_wwz_poster_style.png"
        formal_refs_path = OUTPUT_DIR / f"mkn421_daily_{window.key}_wwz_significance_refs.npz"
        visual_refs_path = OUTPUT_DIR / f"mkn421_daily_{window.key}_wwz_visual_significance_refs.npz"
        refs = _load_significance_refs(formal_refs_path)
        if refs is None:
            refs = _load_significance_refs(visual_refs_path)
        if refs is None:
            refs = _build_visual_significance_refs(sub, wwz, window, visual_refs_path)
        _plot_window(out_png, sub, wwz, window, refs)

        out_npz = OUTPUT_DIR / f"mkn421_daily_{window.key}_wwz.npz"
        _save_wwz(out_npz, wwz)

        rows.append(_summary_row(window, sub, wwz, out_png, out_npz))

    summary = pd.DataFrame(rows)
    summary_path = OUTPUT_DIR / "xgm_poster_repro_summary.csv"
    summary.to_csv(summary_path, index=False)

    print(f"[OK] wrote xgm poster repro outputs -> {OUTPUT_DIR.relative_to(PROJECT_ROOT)}")
    print(summary.to_string(index=False))


def _load_excess_counts(path: Path) -> pd.DataFrame:
    df = read_wcda_counts_csv(path)
    df["excess_counts_err"] = df["flux_excess_err"] * df["tobs"]
    mask = (
        np.isfinite(df["mjd"])
        & np.isfinite(df["excess_counts"])
        & np.isfinite(df["excess_counts_err"])
        & (df["excess_counts_err"] > 0)
        & np.isfinite(df["tobs"])
        & (df["tobs"] > 0)
    )
    out = df.loc[mask, ["name", "mjd", "tobs", "excess_counts", "excess_counts_err"]].copy()
    return out.sort_values("mjd").reset_index(drop=True)


def _plot_window(path: Path, lc: pd.DataFrame, wwz: dict, window: PosterWindow, refs: dict | None) -> None:
    fig = plt.figure(figsize=(16, 9), constrained_layout=True)
    gs = fig.add_gridspec(
        2,
        5,
        width_ratios=[1.25, 1.25, 0.8, 0.12, 1.4],
        height_ratios=[0.72, 1.45],
    )
    ax_lc = fig.add_subplot(gs[0, 0:2])
    ax_map = fig.add_subplot(gs[1, 0:2])
    ax_global = fig.add_subplot(gs[1, 2], sharey=ax_map)
    ax_cbar = fig.add_subplot(gs[1, 3])
    ax_side = fig.add_subplot(gs[1, 4]) if window.fold_period else None

    t = lc["mjd"].to_numpy(dtype=float)
    y = lc["excess_counts"].to_numpy(dtype=float)
    yerr = lc["excess_counts_err"].to_numpy(dtype=float)

    ax_lc.errorbar(t, y, yerr=yerr, fmt="k.", ms=3.2, elinewidth=0.8, capsize=0)
    ax_lc.set_xlim(window.mjd_min, window.mjd_max)
    ax_lc.set_ylim(*window.flux_ylim)
    ax_lc.set_ylabel("Counts")
    ax_lc.set_title(window.title, loc="left", fontsize=28)

    tau = wwz["tau_mat"][:, 0]
    period_mat = wwz["period_mat"]
    sort_idx = np.argsort(period_mat[0, :])
    period_axis = period_mat[0, sort_idx]
    power = wwz["wwz_mat"][:, sort_idx]

    mesh = ax_map.pcolormesh(
        tau,
        period_axis,
        power.T,
        shading="auto",
        cmap="jet",
        norm=Normalize(vmin=window.color_limits[0], vmax=window.color_limits[1], clip=True),
    )
    ax_map.set_xlim(window.mjd_min, window.mjd_max)
    ax_map.set_yscale("log")
    ax_map.set_ylim(window.period_min, window.period_max)
    ax_map.set_xlabel("Time [MJD]")
    ax_map.set_ylabel("Period [days]")
    ax_map.minorticks_on()

    global_period = wwz["period_axis"]
    global_wwz = wwz["global_wwz"]
    global_sort = np.argsort(global_period)
    ax_global.plot(global_wwz[global_sort], global_period[global_sort], color="black", lw=1.7, label="Observed")
    if refs is not None:
        _plot_global_significance_refs(ax_global, refs)
    ax_global.set_yscale("log")
    ax_global.set_ylim(window.period_min, window.period_max)
    ax_global.set_xlabel("Mean WWZ")
    ax_global.grid(True, which="both", alpha=0.25)
    plt.setp(ax_global.get_yticklabels(), visible=False)

    peak_period = _peak_period(wwz)
    ax_global.axhline(peak_period, color="red", ls="--", lw=1.0, alpha=0.65)
    if window.fold_period:
        ax_map.axhline(window.fold_period, color="red", ls="--", lw=1.0, alpha=0.7)
        ax_global.axhline(window.fold_period, color="red", ls="--", lw=1.0, alpha=0.7)
        fig.text(0.70, 0.63, f"Period={window.fold_period:.2f} days", fontsize=20)
    if window.candidate_periods:
        label = ", ".join(f"{p:g}" for p in window.candidate_periods)
        fig.text(0.74, 0.61, f"Period={label} days", fontsize=18)
        for period in window.candidate_periods:
            ax_map.axhline(period, color="red", ls="--", lw=0.8, alpha=0.45)
            ax_global.axhline(period, color="red", ls="--", lw=0.8, alpha=0.45)
    if refs is not None:
        ax_global.legend(loc="lower right", fontsize=7, framealpha=0.82)
        ax_global.text(
            0.02,
            0.02,
            f"AR(1) N={int(refs['n_surrogates'])}\nalpha={float(refs['alpha']):.2f}",
            transform=ax_global.transAxes,
            fontsize=7,
            color="#334155",
            va="bottom",
            ha="left",
        )

    cbar = fig.colorbar(mesh, cax=ax_cbar)
    cbar.set_label("Wavelet Power")

    if ax_side is not None and window.fold_period is not None:
        _plot_folded(ax_side, t, y, window.fold_period, window.flux_ylim)
    elif ax_side is not None:
        ax_side.axis("off")

    fig.savefig(path, dpi=180)
    plt.close(fig)


def _load_significance_refs(path: Path) -> dict | None:
    if not path.exists():
        return None
    with np.load(path) as data:
        return {key: data[key].item() if data[key].ndim == 0 else data[key] for key in data.files}


def _build_visual_significance_refs(lc: pd.DataFrame, wwz: dict, window: PosterWindow, path: Path) -> dict:
    t = lc["mjd"].to_numpy(dtype=float)
    y = lc["excess_counts"].to_numpy(dtype=float)
    yerr = lc["excess_counts_err"].to_numpy(dtype=float)
    y_mean = float(np.nanmean(y))
    y_std = float(np.nanstd(y, ddof=1))
    alpha = float(np.clip(_lag1_autocorr(standardize_flux(y)), -0.95, 0.95))
    rng = np.random.default_rng(VISUAL_REF_SEED + sum(ord(ch) for ch in window.key))
    curves = []
    for _ in range(VISUAL_REF_N_SURROGATES):
        sim_y = _simulate_ar1(len(y), alpha, y_mean, y_std, rng)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            sim = run_wwz(
                t,
                sim_y,
                yerr,
                period_min=float(wwz["period_min"]),
                period_max=float(wwz["period_max"]),
                time_divisions=VISUAL_REF_TIME_DIVISIONS,
                decay_constant=float(wwz["decay_constant"]),
                freq_step_factor=VISUAL_REF_FREQ_STEP_FACTOR,
                parallel=False,
            )
        curves.append(np.asarray(sim["global_wwz"], dtype=float))

    surrogate_global = np.vstack(curves)
    refs = {
        "period": np.asarray(sim["period_axis"], dtype=float),
        "q95": np.nanpercentile(surrogate_global, 95, axis=0),
        "q99": np.nanpercentile(surrogate_global, 99, axis=0),
        "alpha": alpha,
        "n_surrogates": VISUAL_REF_N_SURROGATES,
        "time_divisions": VISUAL_REF_TIME_DIVISIONS,
        "freq_step_factor": VISUAL_REF_FREQ_STEP_FACTOR,
        "null_model": "AR(1) Gaussian surrogate visual reference on same daily sampling",
    }
    np.savez_compressed(path, **refs)
    print(f"[OK] wrote visual significance refs -> {path.relative_to(PROJECT_ROOT)}")
    return refs


def _plot_global_significance_refs(ax: plt.Axes, refs: dict) -> None:
    ref_period = np.asarray(refs["period"], dtype=float)
    q95 = np.asarray(refs["q95"], dtype=float)
    q99 = np.asarray(refs["q99"], dtype=float)
    if not np.array_equal(ref_period.shape, q95.shape) or not np.array_equal(ref_period.shape, q99.shape):
        return
    valid = np.isfinite(ref_period) & np.isfinite(q95) & np.isfinite(q99)
    if not np.any(valid):
        return
    valid_idx = np.flatnonzero(valid)
    order = valid_idx[np.argsort(ref_period[valid_idx])]
    ax.plot(q95[order], ref_period[order], color="#255c99", lw=1.0, ls="-.", label="AR(1) 95%")
    ax.plot(q99[order], ref_period[order], color="#7a3e9d", lw=1.0, ls=":", label="AR(1) 99%")


def _plot_folded(ax: plt.Axes, t: np.ndarray, y: np.ndarray, period: float, ylim: tuple[float, float]) -> None:
    phase = ((t - np.nanmin(t)) / period) % 1.0
    phase2 = np.concatenate([phase, phase + 1.0])
    y2 = np.concatenate([y, y])
    ax.scatter(phase2, y2, s=13, color="0.65", alpha=0.28, label="Original Data (Folded)")

    bins = np.linspace(0.0, 1.0, 11)
    centers = 0.5 * (bins[:-1] + bins[1:])
    means = np.full_like(centers, np.nan, dtype=float)
    errs = np.full_like(centers, np.nan, dtype=float)
    for i, (lo, hi) in enumerate(zip(bins[:-1], bins[1:])):
        in_bin = (phase >= lo) & (phase < hi if i < len(centers) - 1 else phase <= hi)
        values = y[in_bin]
        if values.size:
            means[i] = np.nanmean(values)
            errs[i] = np.nanstd(values) / np.sqrt(values.size) if values.size > 1 else 0.0

    centers2 = np.concatenate([centers, centers + 1.0])
    means2 = np.concatenate([means, means])
    errs2 = np.concatenate([errs, errs])
    finite = np.isfinite(means2)
    ax.errorbar(
        centers2[finite],
        means2[finite],
        yerr=errs2[finite],
        fmt="o-",
        color="red",
        ms=4,
        lw=1.2,
        capsize=2,
        label="Binned Mean",
    )
    ax.set_xlim(0.0, 2.0)
    ax.set_ylim(*ylim)
    ax.set_xlabel(f"Phase (P = {period:.2f} days)")
    ax.set_ylabel("Counts")
    ax.legend(fontsize=8, loc="upper right")


def _lag1_autocorr(y: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    y = y[np.isfinite(y)]
    if len(y) < 3:
        return 0.0
    y0 = y[:-1] - np.nanmean(y[:-1])
    y1 = y[1:] - np.nanmean(y[1:])
    denom = float(np.sqrt(np.sum(y0 * y0) * np.sum(y1 * y1)))
    if denom <= 0 or not np.isfinite(denom):
        return 0.0
    return float(np.clip(np.sum(y0 * y1) / denom, -0.95, 0.95))


def _simulate_ar1(n: int, alpha: float, mean: float, std: float, rng: np.random.Generator) -> np.ndarray:
    innovation_std = np.sqrt(max(1.0 - alpha**2, 1e-8))
    x = np.empty(n, dtype=float)
    x[0] = rng.normal()
    for idx in range(1, n):
        x[idx] = alpha * x[idx - 1] + innovation_std * rng.normal()
    x = (x - np.mean(x)) / np.std(x, ddof=1)
    return mean + std * x


def _peak_period(wwz: dict) -> float:
    period = wwz["period_axis"]
    power = wwz["global_wwz"]
    mask = (period >= wwz["period_min"]) & (period <= wwz["period_max"]) & np.isfinite(power)
    idx = np.nanargmax(np.where(mask, power, np.nan))
    return float(period[idx])


def _summary_row(window: PosterWindow, lc: pd.DataFrame, wwz: dict, png: Path, npz: Path) -> dict:
    t = lc["mjd"].to_numpy(dtype=float)
    gaps = np.diff(t)
    peak_period = _peak_period(wwz)
    peak_idx = int(np.nanargmin(np.abs(wwz["period_axis"] - peak_period)))
    return {
        "window": window.key,
        "mjd_min_requested": window.mjd_min,
        "mjd_max_requested": window.mjd_max,
        "n_points": int(len(lc)),
        "mjd_min_used": float(np.nanmin(t)),
        "mjd_max_used": float(np.nanmax(t)),
        "median_dt_days": float(np.nanmedian(gaps)) if len(gaps) else np.nan,
        "max_gap_days": float(np.nanmax(gaps)) if len(gaps) else np.nan,
        "period_min_days": window.period_min,
        "period_max_days": window.period_max,
        "wwz_peak_period_days": peak_period,
        "wwz_peak_power": float(wwz["global_wwz"][peak_idx]),
        "time_divisions": int(wwz["time_divisions"]),
        "decay_constant": float(wwz["decay_constant"]),
        "freq_step_factor": float(wwz["freq_step"] * wwz["t_span"]),
        "significance": "not_reproduced",
        "series": "excess_counts_photon_count_flux_proxy",
        "png": str(png.relative_to(PROJECT_ROOT)),
        "npz": str(npz.relative_to(PROJECT_ROOT)),
    }


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


if __name__ == "__main__":
    main()
