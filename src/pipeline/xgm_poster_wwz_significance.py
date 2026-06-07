#!/usr/bin/env python3
"""Assess WWZ local significance for the xgm-poster reproduction windows."""

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
import numpy as np
import pandas as pd


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
DEFAULT_N_SURROGATES = 1000
DEFAULT_SEED = 6020061098
WWZ_LOCAL_WINDOW_FRACTION = 0.10
FIG_DPI = 180


@dataclass(frozen=True)
class TargetPeriod:
    label: str
    target_type: str
    period_days: float


@dataclass(frozen=True)
class PosterWindow:
    key: str
    title: str
    mjd_min: float
    mjd_max: float
    targets: tuple[TargetPeriod, ...]


WINDOWS = (
    PosterWindow(
        key="60200_60700",
        title="MJD 60200-60700",
        mjd_min=60200.0,
        mjd_max=60700.0,
        targets=(
            TargetPeriod("xgm ref 51.05 d", "xgm poster reference", 51.05),
            TargetPeriod("my peak 111.01 d", "my reproduction peak", 111.012232),
        ),
    ),
    PosterWindow(
        key="61020_61098",
        title="MJD 61020-61098",
        mjd_min=61020.0,
        mjd_max=61098.0,
        targets=(
            TargetPeriod("xgm ref 2.54 d", "xgm poster reference", 2.54),
            TargetPeriod("xgm ref 5.2 d", "xgm poster reference", 5.2),
            TargetPeriod("xgm ref 16.6 d", "xgm poster reference", 16.6),
            TargetPeriod("my boundary peak 50.00 d", "my reproduction boundary peak", 50.0),
        ),
    ),
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
    lc = _load_excess_counts(INPUT_CSV)
    rng = np.random.default_rng(args.seed)

    rows = []
    for window in WINDOWS:
        wwz = _load_npz_dict(OUTPUT_DIR / f"mkn421_daily_{window.key}_wwz.npz")
        sub = lc[(lc["mjd"] >= window.mjd_min) & (lc["mjd"] <= window.mjd_max)].copy()
        if len(sub) < 4:
            raise ValueError(f"{window.key} has fewer than four usable points.")

        window_rows, refs = assess_window(
            window,
            sub,
            wwz,
            n_surrogates=args.n_surrogates,
            rng=rng,
            workers=args.workers,
            parallel=args.wwz_parallel,
        )
        rows.extend(window_rows)
        out_refs = OUTPUT_DIR / f"mkn421_daily_{window.key}_wwz_significance_refs.npz"
        _save_significance_refs(out_refs, refs, n_surrogates=args.n_surrogates)
        print(f"[OK] wrote {out_refs.relative_to(PROJECT_ROOT)}")
        out_png = OUTPUT_DIR / f"mkn421_daily_{window.key}_wwz_local_significance.png"
        _plot_window_significance(out_png, window, wwz, window_rows, refs)
        print(f"[OK] wrote {out_png.relative_to(PROJECT_ROOT)}")

    out_csv = OUTPUT_DIR / "xgm_poster_wwz_local_significance.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"[OK] wrote {out_csv.relative_to(PROJECT_ROOT)}")


def assess_window(
    window: PosterWindow,
    lc: pd.DataFrame,
    wwz: dict,
    *,
    n_surrogates: int,
    rng: np.random.Generator,
    workers: int,
    parallel: bool,
) -> tuple[list[dict], dict]:
    period = np.asarray(wwz["period_axis"], dtype=float)
    global_wwz = np.asarray(wwz["global_wwz"], dtype=float)
    valid = (
        np.isfinite(period)
        & np.isfinite(global_wwz)
        & (period >= float(wwz["period_min"]))
        & (period <= float(wwz["period_max"]))
    )
    if not np.any(valid):
        raise ValueError(f"{window.key} has no valid WWZ period grid.")

    target_specs = []
    for target in window.targets:
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
    y = lc["excess_counts"].to_numpy(dtype=float)
    yerr = lc["excess_counts_err"].to_numpy(dtype=float)
    y_mean = float(np.nanmean(y))
    y_std = float(np.nanstd(y, ddof=1))
    alpha = _lag1_autocorr(standardize_flux(y))
    alpha = float(np.clip(alpha, -0.95, 0.95))

    seeds = rng.integers(0, np.iinfo(np.uint32).max, size=n_surrogates, dtype=np.uint32)
    tasks = [
        (
            int(seed),
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
        for seed in seeds
    ]
    if workers > 1 and n_surrogates > 1:
        with mp.Pool(processes=int(workers)) as pool:
            surrogate_global = np.vstack(pool.map(_run_wwz_surrogate_global, tasks))
    else:
        surrogate_global = np.vstack([_run_wwz_surrogate_global(task) for task in tasks])

    q95 = np.nanpercentile(surrogate_global, 95, axis=0)
    q99 = np.nanpercentile(surrogate_global, 99, axis=0)

    sorted_power = np.sort(global_wwz[valid])[::-1]
    t_span = float(np.nanmax(t) - np.nanmin(t))
    rows = []
    for target, window_min, window_max, mask, nearest_idx, local_max_idx in target_specs:
        surrogate_local_max = np.nanmax(surrogate_global[:, mask], axis=1)
        observed_local_max = float(global_wwz[local_max_idx])
        exceed_count = int(np.count_nonzero(surrogate_local_max >= observed_local_max))
        local_fap = (exceed_count + 1.0) / (n_surrogates + 1.0)
        nearest_power = float(global_wwz[nearest_idx])
        local_rank = int(np.count_nonzero(sorted_power > observed_local_max) + 1)
        nearest_rank = int(np.count_nonzero(sorted_power > nearest_power) + 1)
        rows.append(
            {
                "window": window.key,
                "window_label": window.title,
                "target_type": target.target_type,
                "target_label": target.label,
                "target_period_days": float(target.period_days),
                "nearest_grid_period_days": float(period[nearest_idx]),
                "nearest_grid_power": nearest_power,
                "nearest_grid_rank": nearest_rank,
                "local_window_min_days": float(window_min),
                "local_window_max_days": float(window_max),
                "local_window_peak_period_days": float(period[local_max_idx]),
                "local_window_peak_power": observed_local_max,
                "local_window_peak_rank": local_rank,
                "local_fap": float(local_fap),
                "local_confidence": float(1.0 - local_fap),
                "reference_95": float(q95[nearest_idx]),
                "reference_99": float(q99[nearest_idx]),
                "above_95": bool(observed_local_max >= q95[nearest_idx]),
                "above_99": bool(observed_local_max >= q99[nearest_idx]),
                "cycles": float(t_span / target.period_days),
                "n_points": int(len(lc)),
                "n_surrogates": int(n_surrogates),
                "exceed_count": exceed_count,
                "ar1_alpha": alpha,
                "null_model": "AR(1) Gaussian surrogate on same daily sampling",
                "series": "excess_counts_photon_count_flux_proxy",
                "note": _reading_note(window, target, local_fap),
            }
        )

    return rows, {"period": period, "q95": q95, "q99": q99, "alpha": alpha}


def _save_significance_refs(path: Path, refs: dict, *, n_surrogates: int) -> None:
    np.savez_compressed(
        path,
        period=np.asarray(refs["period"], dtype=float),
        q95=np.asarray(refs["q95"], dtype=float),
        q99=np.asarray(refs["q99"], dtype=float),
        alpha=float(refs["alpha"]),
        n_surrogates=int(n_surrogates),
        null_model="AR(1) Gaussian surrogate on same daily sampling",
    )


def _reading_note(window: PosterWindow, target: TargetPeriod, local_fap: float) -> str:
    if "boundary" in target.target_type:
        return "My reproduction peak is at the search boundary; do not treat as a robust QPO without a wider test."
    if target.target_type == "xgm poster reference":
        return "xgm poster reference period tested with my AR(1) surrogate local-window method."
    if local_fap < 0.05:
        return "My reproduction peak passes this local 95% surrogate check only; no trial correction."
    return "My reproduction peak tested with my AR(1) surrogate local-window method."


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
    return df.loc[mask, ["mjd", "tobs", "excess_counts", "excess_counts_err"]].sort_values("mjd").reset_index(drop=True)


def _load_npz_dict(path: Path) -> dict:
    with np.load(path) as data:
        return {key: data[key] for key in data.files}


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


def _plot_window_significance(path: Path, window: PosterWindow, wwz: dict, rows: list[dict], refs: dict) -> None:
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
    ax.plot(period_plot, wwz_plot, color="black", lw=1.5, label="My observed global WWZ")
    ax.plot(period_plot, q95, color="#255c99", lw=1.1, ls="-.", label="My AR(1) surrogate 95% reference")
    ax.plot(period_plot, q99, color="#7a3e9d", lw=1.1, ls=":", label="My AR(1) surrogate 99% reference")
    _draw_targets(ax, rows)
    ax.set_xscale("log")
    ax.set_xlim(float(wwz["period_min"]), float(wwz["period_max"]))
    ax.set_xlabel("Period (day)")
    ax.set_ylabel("Mean WWZ")
    ax.set_title(f"Mrk 421 daily {window.title}: WWZ local significance")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    ax.text(
        0.01,
        0.02,
        f"My AR(1) surrogate N = {int(rows[0]['n_surrogates'])}; alpha = {float(refs['alpha']):.3f}; local-window FAP only",
        transform=ax.transAxes,
        fontsize=8,
        color="#5f6c7b",
    )
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)


def _draw_targets(ax: plt.Axes, rows: list[dict]) -> None:
    y_min, y_max = ax.get_ylim()
    y_text = y_min + 0.90 * (y_max - y_min)
    for idx, row in enumerate(rows):
        is_xgm = row["target_type"] == "xgm poster reference"
        color = "red" if is_xgm else "#1261a6"
        ls = "--" if is_xgm else "-."
        period = float(row["target_period_days"])
        ax.axvline(period, color=color, ls=ls, lw=1.1, alpha=0.9)
        label_prefix = "xgm ref" if is_xgm else "my"
        ax.text(
            period,
            y_text,
            f"{label_prefix}\n{period:.2f} d\np={float(row['local_fap']):.3f}",
            color=color,
            fontsize=8,
            rotation=90,
            ha="right",
            va="top",
        )
        y_text = y_min + (0.90 - 0.13 * ((idx + 1) % 4)) * (y_max - y_min)


if __name__ == "__main__":
    main()
