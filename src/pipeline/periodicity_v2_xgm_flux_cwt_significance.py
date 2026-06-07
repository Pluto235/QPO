#!/usr/bin/env python3
"""Assess targeted CWT significance for the v2 xgm flux quick-look window."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import run_cwt, standardize_flux  # noqa: E402
from utils.project_paths import ALIGNED_DIR, PERIODICITY_DIR, PROJECT_ROOT  # noqa: E402


ALIGNED_PATH = ALIGNED_DIR / "periodicity_v2" / "mkn421" / "wcda_daily_flux_aligned.csv"
OUTPUT_DIR = PERIODICITY_DIR / "periodicity_v2" / "xgm_poster_repro" / "mkn421"
CWT_PATH = OUTPUT_DIR / "mkn421_daily_flux_60200_60700_cwt.npz"
QUICKLOOK_SUMMARY_PATH = OUTPUT_DIR / "xgm_flux_cwt_quicklook_summary.csv"
QUICKLOOK_FIGURE_PATH = OUTPUT_DIR / "mkn421_daily_flux_60200_60700_cwt_quicklook.png"
SUMMARY_PATH = OUTPUT_DIR / "xgm_flux_cwt_significance.csv"
REFS_PATH = OUTPUT_DIR / "mkn421_daily_flux_60200_60700_cwt_significance_refs.npz"
FIGURE_PATH = OUTPUT_DIR / "mkn421_daily_flux_60200_60700_cwt_significance.png"
DEFAULT_N_SURROGATES = 1000
DEFAULT_SEED = 6020060701
CWT_LOCAL_WINDOW_FRACTION = 0.10
XGM_WINDOW = (60200.0, 60700.0)
XGM_REFERENCE_PERIOD_DAYS = 51.05
FIG_DPI = 180


@dataclass(frozen=True)
class TargetPeriod:
    label: str
    target_type: str
    period_days: float


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-surrogates", type=int, default=DEFAULT_N_SURROGATES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.n_surrogates < 1:
        raise ValueError("--n-surrogates must be positive.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    lc = _load_v2_flux_window(ALIGNED_PATH, XGM_WINDOW)
    cwt = run_cwt(
        lc["mjd"].to_numpy(dtype=float),
        lc["flux"].to_numpy(dtype=float),
        period_min=2.0,
        period_max=200.0,
    )
    _save_cwt(CWT_PATH, cwt)
    quicklook = build_quicklook_summary(lc, cwt)
    quicklook.to_csv(QUICKLOOK_SUMMARY_PATH, index=False)
    _plot_cwt_quicklook(QUICKLOOK_FIGURE_PATH, lc, cwt, quicklook)

    global_peak_period = float(quicklook.loc[quicklook["target"].eq("v2 flux CWT global peak"), "period_days"].iloc[0])
    targets = (
        TargetPeriod("v2 flux CWT global peak", "v2 flux CWT global peak", global_peak_period),
        TargetPeriod("xgm poster reference 51.05 d", "xgm poster reference", XGM_REFERENCE_PERIOD_DAYS),
    )
    rows, refs = assess_targets(
        lc,
        cwt,
        targets=targets,
        n_surrogates=args.n_surrogates,
        seed=args.seed,
    )
    pd.DataFrame(rows).to_csv(SUMMARY_PATH, index=False)
    _save_refs(REFS_PATH, refs, n_surrogates=args.n_surrogates)
    _plot_significance(FIGURE_PATH, cwt, rows, refs)
    print(f"[OK] wrote {QUICKLOOK_SUMMARY_PATH.relative_to(PROJECT_ROOT)}")
    print(f"[OK] wrote {QUICKLOOK_FIGURE_PATH.relative_to(PROJECT_ROOT)}")
    print(f"[OK] wrote {SUMMARY_PATH.relative_to(PROJECT_ROOT)}")
    print(f"[OK] wrote {REFS_PATH.relative_to(PROJECT_ROOT)}")
    print(f"[OK] wrote {FIGURE_PATH.relative_to(PROJECT_ROOT)}")


def build_quicklook_summary(lc: pd.DataFrame, cwt: dict) -> pd.DataFrame:
    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    valid = _valid_period_mask(cwt)
    peak_idx = int(np.nanargmax(np.where(valid, gws, np.nan)))
    nearest_idx = int(np.nanargmin(np.abs(period - XGM_REFERENCE_PERIOD_DAYS)))
    t_span = float(lc["mjd"].max() - lc["mjd"].min())
    return pd.DataFrame(
        [
            {
                "window": "60200-60700",
                "target": "v2 flux CWT global peak",
                "period_days": float(period[peak_idx]),
                "cwt_power": float(gws[peak_idx]),
                "cycles": t_span / float(period[peak_idx]),
                "significance": "pending",
            },
            {
                "window": "60200-60700",
                "target": "xgm poster reference 51.05 d nearest grid",
                "period_days": float(period[nearest_idx]),
                "cwt_power": float(gws[nearest_idx]),
                "cycles": t_span / float(period[nearest_idx]),
                "significance": "pending",
            },
        ]
    )


def assess_targets(
    lc: pd.DataFrame,
    cwt: dict,
    *,
    targets: tuple[TargetPeriod, ...],
    n_surrogates: int,
    seed: int,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    valid = _valid_period_mask(cwt)
    if not np.any(valid):
        raise ValueError("No finite CWT period grid in requested range.")

    target_specs = []
    for target in targets:
        window_min = max(float(cwt["period_min"]), target.period_days * (1.0 - CWT_LOCAL_WINDOW_FRACTION))
        window_max = min(float(cwt["period_max"]), target.period_days * (1.0 + CWT_LOCAL_WINDOW_FRACTION))
        mask = valid & (period >= window_min) & (period <= window_max)
        if not np.any(mask):
            nearest = int(np.nanargmin(np.abs(period - target.period_days)))
            mask = np.zeros_like(period, dtype=bool)
            mask[nearest] = True
            window_min = window_max = float(period[nearest])
        nearest_idx = int(np.nanargmin(np.abs(period - target.period_days)))
        local_max_idx = int(np.nanargmax(np.where(mask, gws, np.nan)))
        target_specs.append((target, window_min, window_max, mask, nearest_idx, local_max_idx))

    t = lc["mjd"].to_numpy(dtype=float)
    y = lc["flux"].to_numpy(dtype=float)
    y_mean = float(np.nanmean(y))
    y_std = float(np.nanstd(y, ddof=1))
    alpha = float(np.clip(_lag1_autocorr(standardize_flux(y)), -0.95, 0.95))
    rng = np.random.default_rng(seed)

    surrogate_gws = np.empty((n_surrogates, len(period)), dtype=float)
    for idx in range(n_surrogates):
        sim_y = _simulate_ar1(len(y), alpha, y_mean, y_std, rng)
        sim = run_cwt(t, sim_y, period_min=float(cwt["period_min"]), period_max=float(cwt["period_max"]))
        surrogate_gws[idx] = np.asarray(sim["gws"], dtype=float)

    surrogate_global_max = np.nanmax(surrogate_gws[:, valid], axis=1)
    q95 = np.nanpercentile(surrogate_gws, 95, axis=0)
    q99 = np.nanpercentile(surrogate_gws, 99, axis=0)
    sorted_power = np.sort(gws[valid])[::-1]
    t_span = float(np.nanmax(t) - np.nanmin(t))
    rows: list[dict[str, object]] = []
    for target, window_min, window_max, mask, nearest_idx, local_max_idx in target_specs:
        surrogate_local_max = np.nanmax(surrogate_gws[:, mask], axis=1)
        observed_local_max = float(gws[local_max_idx])
        local_exceed_count = int(np.count_nonzero(surrogate_local_max >= observed_local_max))
        global_exceed_count = int(np.count_nonzero(surrogate_global_max >= observed_local_max))
        local_fap = (local_exceed_count + 1.0) / (n_surrogates + 1.0)
        global_fap = (global_exceed_count + 1.0) / (n_surrogates + 1.0)
        nearest_power = float(gws[nearest_idx])
        rows.append(
            {
                "source": "Mrk 421",
                "series": "wcda_daily_flux_v2",
                "window": "60200-60700",
                "target": target.label,
                "target_type": target.target_type,
                "target_period_days": float(target.period_days),
                "nearest_grid_period_days": float(period[nearest_idx]),
                "nearest_grid_power": nearest_power,
                "nearest_grid_rank": int(np.count_nonzero(sorted_power > nearest_power) + 1),
                "local_window_min_days": float(window_min),
                "local_window_max_days": float(window_max),
                "local_window_peak_period_days": float(period[local_max_idx]),
                "local_window_peak_power": observed_local_max,
                "local_window_peak_rank": int(np.count_nonzero(sorted_power > observed_local_max) + 1),
                "local_fap": float(local_fap),
                "global_fap": float(global_fap),
                "local_confidence": float(1.0 - local_fap),
                "global_confidence": float(1.0 - global_fap),
                "reference_95": float(q95[local_max_idx]),
                "reference_99": float(q99[local_max_idx]),
                "above_95": bool(observed_local_max >= q95[local_max_idx]),
                "above_99": bool(observed_local_max >= q99[local_max_idx]),
                "cycles": float(t_span / target.period_days),
                "n_points": int(len(lc)),
                "n_surrogates": int(n_surrogates),
                "local_exceed_count": local_exceed_count,
                "global_exceed_count": global_exceed_count,
                "ar1_alpha": alpha,
                "null_model": "AR(1) Gaussian surrogate on same v2 daily flux sampling",
                "note": "Targeted local-window CWT global-spectrum check only; no source/method/window-search/post-trial correction.",
            }
        )
    refs = {"period": period, "q95": q95, "q99": q99, "alpha": alpha, "surrogate_global_max": surrogate_global_max}
    return rows, refs


def _load_v2_flux_window(path: Path, window: tuple[float, float]) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"mjd", "wcda_n0", "wcda_n0_err"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    out = df.rename(columns={"wcda_n0": "flux", "wcda_n0_err": "flux_err"}).copy()
    for col in ("mjd", "flux", "flux_err"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    mask = (
        np.isfinite(out["mjd"])
        & np.isfinite(out["flux"])
        & np.isfinite(out["flux_err"])
        & (out["flux_err"] > 0)
        & (out["mjd"] >= float(window[0]))
        & (out["mjd"] <= float(window[1]))
    )
    out = out.loc[mask, ["mjd", "flux", "flux_err"]].sort_values("mjd").reset_index(drop=True)
    if len(out) < 4:
        raise ValueError("MJD 60200-60700 has fewer than four usable v2 flux points.")
    return out


def _valid_period_mask(cwt: dict) -> np.ndarray:
    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    return (
        np.isfinite(period)
        & np.isfinite(gws)
        & (period >= float(cwt["period_min"]))
        & (period <= float(cwt["period_max"]))
    )


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


def _save_refs(path: Path, refs: dict[str, object], *, n_surrogates: int) -> None:
    np.savez_compressed(
        path,
        period=np.asarray(refs["period"], dtype=float),
        q95=np.asarray(refs["q95"], dtype=float),
        q99=np.asarray(refs["q99"], dtype=float),
        alpha=float(refs["alpha"]),
        surrogate_global_max=np.asarray(refs["surrogate_global_max"], dtype=float),
        n_surrogates=int(n_surrogates),
        null_model="AR(1) Gaussian surrogate on same v2 daily flux sampling",
    )


def _plot_cwt_quicklook(path: Path, lc: pd.DataFrame, cwt: dict, summary: pd.DataFrame) -> None:
    t = lc["mjd"].to_numpy(dtype=float)
    y = lc["flux"].to_numpy(dtype=float)
    yerr = lc["flux_err"].to_numpy(dtype=float)
    period = np.asarray(cwt["period"], dtype=float)
    mask = np.asarray(cwt["mask_period"], dtype=bool)
    fig = plt.figure(figsize=(15, 4.8), constrained_layout=True)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 2.2, 1.0])
    ax_lc = fig.add_subplot(gs[0, 0])
    ax_map = fig.add_subplot(gs[0, 1])
    ax_global = fig.add_subplot(gs[0, 2])

    ax_lc.errorbar(t, y, yerr=yerr, fmt="o", ms=3.0, capsize=2, elinewidth=0.8)
    ax_lc.set_title("Mrk 421 WCDA daily N0, MJD 60200-60700")
    ax_lc.set_xlabel("MJD")
    ax_lc.set_ylabel("N0 [cm^-2 s^-1 TeV^-1]")
    ax_lc.grid(True, alpha=0.25)

    t_grid, p_grid = np.meshgrid(t, period)
    mesh = ax_map.contourf(
        t_grid[mask, :],
        p_grid[mask, :],
        np.asarray(cwt["power"])[mask, :],
        levels=50,
        cmap="magma",
        extend="both",
    )
    coi_clip = np.clip(cwt["coi"], cwt["period_min"], cwt["period_max"])
    ax_map.fill_between(t, cwt["period_max"], coi_clip, color="white", alpha=0.45, hatch="/", edgecolor="0.7", linewidth=0.0)
    ax_map.plot(t, coi_clip, color="white", lw=1.0)
    ax_map.axhline(XGM_REFERENCE_PERIOD_DAYS, color="red", ls="--", lw=1.0, alpha=0.8)
    ax_map.set_yscale("log")
    ax_map.set_ylim(float(cwt["period_min"]), float(cwt["period_max"]))
    ax_map.set_title("CWT Power")
    ax_map.set_xlabel("MJD")
    ax_map.set_ylabel("Period (day)")
    ax_map.grid(True, alpha=0.25)
    fig.colorbar(mesh, ax=ax_map, pad=0.02, label="Power")

    valid = _valid_period_mask(cwt)
    order = np.argsort(period[valid])
    period_plot = period[valid][order]
    gws_plot = np.asarray(cwt["gws"], dtype=float)[valid][order]
    ax_global.plot(gws_plot, period_plot, color="black", lw=1.4)
    for row in summary.itertuples(index=False):
        color = "red" if "reference" in row.target else "#1261a6"
        ax_global.axhline(row.period_days, color=color, ls="--", lw=1.0, alpha=0.8)
    ax_global.set_yscale("log")
    ax_global.set_ylim(float(cwt["period_min"]), float(cwt["period_max"]))
    ax_global.set_title("Global CWT")
    ax_global.set_xlabel("GWS")
    ax_global.grid(True, which="both", alpha=0.25)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def _plot_significance(path: Path, cwt: dict, rows: list[dict[str, object]], refs: dict[str, object]) -> None:
    period = np.asarray(cwt["period"], dtype=float)
    gws = np.asarray(cwt["gws"], dtype=float)
    valid = _valid_period_mask(cwt)
    order = np.argsort(period[valid])
    period_plot = period[valid][order]
    gws_plot = gws[valid][order]
    q95 = np.asarray(refs["q95"], dtype=float)[valid][order]
    q99 = np.asarray(refs["q99"], dtype=float)[valid][order]

    fig, ax = plt.subplots(figsize=(8.8, 4.8), constrained_layout=True)
    ax.plot(period_plot, gws_plot, color="black", lw=1.5, label="Observed global CWT")
    ax.plot(period_plot, q95, color="#255c99", lw=1.1, ls="-.", label="AR(1) 95% pointwise")
    ax.plot(period_plot, q99, color="#7a3e9d", lw=1.1, ls=":", label="AR(1) 99% pointwise")
    _draw_targets(ax, rows)
    ax.set_xscale("log")
    ax.set_xlim(float(cwt["period_min"]), float(cwt["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Global wavelet spectrum")
    ax.set_title("Mrk 421 v2 daily flux, MJD 60200-60700: CWT significance")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    ax.text(
        0.01,
        0.02,
        f"AR(1) surrogate N={int(rows[0]['n_surrogates'])}; alpha={float(refs['alpha']):.3f}; no trial correction",
        transform=ax.transAxes,
        fontsize=8,
        color="#5f6c7b",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def _draw_targets(ax: plt.Axes, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    y_min, y_max = ax.get_ylim()
    y_text = y_min + 0.88 * (y_max - y_min)
    for idx, row in enumerate(rows):
        is_xgm = row["target_type"] == "xgm poster reference"
        color = "red" if is_xgm else "#1261a6"
        ls = "--" if is_xgm else "-."
        period = float(row["target_period_days"])
        ax.axvline(period, color=color, ls=ls, lw=1.1, alpha=0.9)
        label = f"{period:.1f} d\npl={float(row['local_fap']):.3f}\npg={float(row['global_fap']):.3f}"
        ax.text(period, y_text, label, color=color, fontsize=8, rotation=90, ha="right", va="top")
        y_text = y_min + (0.88 - 0.13 * ((idx + 1) % 3)) * (y_max - y_min)


if __name__ == "__main__":
    main()
