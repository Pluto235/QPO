from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class CWTGrid:
    time: np.ndarray
    flux: np.ndarray
    mask_interpolated: np.ndarray
    qc: dict[str, object]

def make_period_grid(period_min: float, period_max: float, n_periods: int = 400) -> np.ndarray:
    if period_min <= 0 or period_max <= period_min or n_periods < 4:
        raise ValueError("Require 0 < period_min < period_max and n_periods >= 4.")
    return np.geomspace(float(period_min), float(period_max), int(n_periods))

def prepare_cwt_grid(time, flux, *, max_gap_cadences: float = 2.0) -> CWTGrid:
    time, flux = np.asarray(time, float), np.asarray(flux, float)
    order = np.argsort(time); time, flux = time[order], flux[order]
    diffs = np.diff(time); cadence = float(np.median(diffs[diffs > 0]))
    if not np.isfinite(cadence) or cadence <= 0:
        raise ValueError("Cannot infer a positive median cadence.")
    grid_time = np.arange(time[0], time[-1] + 0.5 * cadence, cadence)
    grid_flux = np.interp(grid_time, time, flux)
    mask_interp = np.zeros(len(grid_time), dtype=bool)
    short_limit = float(max_gap_cadences) * cadence
    for left, right in zip(time[:-1], time[1:]):
        mask = (grid_time > left) & (grid_time < right)
        if right - left <= short_limit + 1e-12:
            mask_interp[mask] = True
        else:
            grid_flux[mask] = np.nan
    return CWTGrid(grid_time, grid_flux, mask_interp, {"median_cadence": cadence, "max_gap_cadences": float(max_gap_cadences), "interpolated_bins": int(mask_interp.sum()), "masked_bins": int(np.isnan(grid_flux).sum())})
