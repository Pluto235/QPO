#!/usr/bin/env python3
"""Assess targeted WWZ significance for the v2 xgm flux quick-look window."""

from __future__ import annotations

import argparse
import contextlib
import io
import multiprocessing as mp
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import run_wwz, standardize_flux  # noqa: E402
from utils.project_paths import ALIGNED_DIR, PERIODICITY_DIR, PROJECT_ROOT  # noqa: E402


ALIGNED_PATH = ALIGNED_DIR / "periodicity_v2" / "mkn421" / "wcda_daily_flux_aligned.csv"
OUTPUT_DIR = PERIODICITY_DIR / "periodicity_v2" / "xgm_poster_repro" / "mkn421"
WWZ_PATH = OUTPUT_DIR / "mkn421_daily_flux_60200_60700_wwz.npz"
SUMMARY_PATH = OUTPUT_DIR / "xgm_flux_quicklook_significance.csv"
REFS_PATH = OUTPUT_DIR / "mkn421_daily_flux_60200_60700_wwz_significance_refs.npz"
FIGURE_PATH = OUTPUT_DIR / "mkn421_daily_flux_60200_60700_wwz_significance.png"
DEFAULT_N_SURROGATES = 1000
DEFAULT_SEED = 6020060700
WWZ_LOCAL_WINDOW_FRACTION = 0.10
XGM_WINDOW = (60200.0, 60700.0)
XGM_REFERENCE_PERIOD_DAYS = 51.05
FIG_DPI = 180


@dataclass(frozen=True)
class TargetPeriod:
    label: str
    target_type: str
    period_days: float


TARGETS = (
    TargetPeriod("v2 flux global peak", "v2 flux global peak", 111.012232),
    TargetPeriod("xgm poster reference 51.05 d", "xgm poster reference", XGM_REFERENCE_PERIOD_DAYS),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-surrogates", type=int, default=DEFAULT_N_SURROGATES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    parser.add_argument("--wwz-parallel", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.n_surrogates < 1:
        raise ValueError("--n-surrogates must be positive.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    lc = _load_v2_flux_window(ALIGNED_PATH, XGM_WINDOW)
    wwz = _load_npz_dict(WWZ_PATH)
    rows, refs = assess_targets(
        lc,
        wwz,
        targets=TARGETS,
        n_surrogates=args.n_surrogates,
        seed=args.seed,
        workers=args.workers,
        parallel=args.wwz_parallel,
    )
    pd.DataFrame(rows).to_csv(SUMMARY_PATH, index=False)
    _save_refs(REFS_PATH, refs, n_surrogates=args.n_surrogates)
    _plot_significance(FIGURE_PATH, wwz, rows, refs)
    print(f"[OK] wrote {SUMMARY_PATH.relative_to(PROJECT_ROOT)}")
    print(f"[OK] wrote {REFS_PATH.relative_to(PROJECT_ROOT)}")
    print(f"[OK] wrote {FIGURE_PATH.relative_to(PROJECT_ROOT)}")


def assess_targets(
    lc: pd.DataFrame,
    wwz: dict,
    *,
    targets: tuple[TargetPeriod, ...],
    n_surrogates: int,
    seed: int,
    workers: int,
    parallel: bool,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    period = np.asarray(wwz["period_axis"], dtype=float)
    global_wwz = np.asarray(wwz["global_wwz"], dtype=float)
    valid = (
        np.isfinite(period)
        & np.isfinite(global_wwz)
        & (period >= float(wwz["period_min"]))
        & (period <= float(wwz["period_max"]))
    )
    if not np.any(valid):
        raise ValueError("No finite WWZ period grid in requested range.")

    target_specs = []
    for target in targets:
        window_min = max(float(wwz["period_min"]), target.period_days * (1.0 - WWZ_LOCAL_WINDOW_FRACTION))
        window_max = min(float(wwz["period_max"]), target.period_days * (1.0 + WWZ_LOCAL_WINDOW_FRACTION))
        mask = valid & (period >= window_min) & (period <= window_max)
        if not np.any(mask):
            nearest = int(np.nanargmin(np.abs(period - target.period_days)))
            mask = np.zeros_like(period, dtype=bool)
            mask[nearest] = True
            window_min = window_max = float(period[nearest])
        nearest_idx = int(np.nanargmin(np.abs(period - target.period_days)))
        local_max_idx = int(np.nanargmax(np.where(mask, global_wwz, np.nan)))
        target_specs.append((target, window_min, window_max, mask, nearest_idx, local_max_idx))

    t = lc["mjd"].to_numpy(dtype=float)
    y = lc["flux"].to_numpy(dtype=float)
    yerr = lc["flux_err"].to_numpy(dtype=float)
    y_mean = float(np.nanmean(y))
    y_std = float(np.nanstd(y, ddof=1))
    alpha = float(np.clip(_lag1_autocorr(standardize_flux(y)), -0.95, 0.95))
    rng = np.random.default_rng(seed)
    seeds = rng.integers(0, np.iinfo(np.uint32).max, size=n_surrogates, dtype=np.uint32)
    tasks = [
        (
            int(sim_seed),
            t,
            yerr,
            len(y),
            alpha,
            y_mean,
            y_std,
            float(wwz["period_min"]),
            float(wwz["period_max"]),
            int(wwz["time_divisions"]),
            float(wwz["decay_constant"]),
            float(wwz["freq_step_factor"]),
            parallel,
        )
        for sim_seed in seeds
    ]
    if workers > 1 and n_surrogates > 1:
        with mp.Pool(processes=int(workers)) as pool:
            surrogate_global = np.vstack(pool.map(_run_wwz_surrogate_global, tasks))
    else:
        surrogate_global = np.vstack([_run_wwz_surrogate_global(task) for task in tasks])

    surrogate_global_max = np.nanmax(surrogate_global[:, valid], axis=1)
    q95 = np.nanpercentile(surrogate_global, 95, axis=0)
    q99 = np.nanpercentile(surrogate_global, 99, axis=0)
    sorted_power = np.sort(global_wwz[valid])[::-1]
    t_span = float(np.nanmax(t) - np.nanmin(t))
    rows: list[dict[str, object]] = []
    for target, window_min, window_max, mask, nearest_idx, local_max_idx in target_specs:
        surrogate_local_max = np.nanmax(surrogate_global[:, mask], axis=1)
        observed_local_max = float(global_wwz[local_max_idx])
        local_exceed_count = int(np.count_nonzero(surrogate_local_max >= observed_local_max))
        global_exceed_count = int(np.count_nonzero(surrogate_global_max >= observed_local_max))
        local_fap = (local_exceed_count + 1.0) / (n_surrogates + 1.0)
        global_fap = (global_exceed_count + 1.0) / (n_surrogates + 1.0)
        nearest_power = float(global_wwz[nearest_idx])
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
                "reference_95": float(q95[nearest_idx]),
                "reference_99": float(q99[nearest_idx]),
                "above_95": bool(observed_local_max >= q95[nearest_idx]),
                "above_99": bool(observed_local_max >= q99[nearest_idx]),
                "cycles": float(t_span / target.period_days),
                "n_points": int(len(lc)),
                "n_surrogates": int(n_surrogates),
                "local_exceed_count": local_exceed_count,
                "global_exceed_count": global_exceed_count,
                "ar1_alpha": alpha,
                "null_model": "AR(1) Gaussian surrogate on same v2 daily flux sampling",
                "note": "Targeted local-window WWZ check only; no source/method/window-search/post-trial correction.",
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


def _load_npz_dict(path: Path) -> dict[str, object]:
    with np.load(path) as data:
        return {key: data[key].item() if data[key].ndim == 0 else data[key] for key in data.files}


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


def _run_wwz_surrogate_global(task: tuple) -> np.ndarray:
    (
        seed,
        t,
        yerr,
        n,
        alpha,
        y_mean,
        y_std,
        period_min,
        period_max,
        time_divisions,
        decay_constant,
        freq_step_factor,
        parallel,
    ) = task
    rng = np.random.default_rng(seed)
    sim_y = _simulate_ar1(n, alpha, y_mean, y_std, rng)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        sim = run_wwz(
            t,
            sim_y,
            yerr,
            period_min=period_min,
            period_max=period_max,
            time_divisions=time_divisions,
            decay_constant=decay_constant,
            freq_step_factor=freq_step_factor,
            parallel=parallel,
        )
    return np.asarray(sim["global_wwz"], dtype=float)


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


def _plot_significance(path: Path, wwz: dict, rows: list[dict[str, object]], refs: dict[str, object]) -> None:
    period = np.asarray(wwz["period_axis"], dtype=float)
    global_wwz = np.asarray(wwz["global_wwz"], dtype=float)
    valid = (
        np.isfinite(period)
        & np.isfinite(global_wwz)
        & (period >= float(wwz["period_min"]))
        & (period <= float(wwz["period_max"]))
    )
    order = np.argsort(period[valid])
    period_plot = period[valid][order]
    wwz_plot = global_wwz[valid][order]
    q95 = np.asarray(refs["q95"], dtype=float)[valid][order]
    q99 = np.asarray(refs["q99"], dtype=float)[valid][order]

    fig, ax = plt.subplots(figsize=(8.8, 4.8), constrained_layout=True)
    ax.plot(period_plot, wwz_plot, color="black", lw=1.5, label="Observed global WWZ")
    ax.plot(period_plot, q95, color="#255c99", lw=1.1, ls="-.", label="AR(1) 95% pointwise")
    ax.plot(period_plot, q99, color="#7a3e9d", lw=1.1, ls=":", label="AR(1) 99% pointwise")
    _draw_targets(ax, rows)
    ax.set_xscale("log")
    ax.set_xlim(float(wwz["period_min"]), float(wwz["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Mean WWZ")
    ax.set_title("Mrk 421 v2 daily flux, MJD 60200-60700: WWZ significance")
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
        ax.text(
            period,
            y_text,
            label,
            color=color,
            fontsize=8,
            rotation=90,
            ha="right",
            va="top",
        )
        y_text = y_min + (0.88 - 0.13 * ((idx + 1) % 3)) * (y_max - y_min)


if __name__ == "__main__":
    main()
