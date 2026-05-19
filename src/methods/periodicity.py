"""Light-curve preparation and CWT/WWZ helpers for QPO checks."""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pycwt as wavelet
from libwwz import wwt


WCDA_ARRAY_COLUMNS = ("n_on", "n_bkg", "n_off")


def parse_array_column(value) -> np.ndarray:
    """Parse WCDA list-valued CSV cells into float arrays."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.array([], dtype=float)
    if isinstance(value, np.ndarray):
        return value.astype(float)
    if isinstance(value, (list, tuple)):
        return np.asarray(value, dtype=float)
    text = str(value).strip()
    if text in {"", "None", "nan"}:
        return np.array([], dtype=float)
    return np.asarray(ast.literal_eval(text), dtype=float)


def read_wcda_counts_csv(path: Path) -> pd.DataFrame:
    """Read a WCDA counts CSV and add excess-rate products used downstream."""
    df = pd.read_csv(path, comment="#")
    df.columns = [str(c).strip() for c in df.columns]
    missing = {"mjd", "n_on", "n_bkg", "n_off", "tobs"} - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")

    for col in WCDA_ARRAY_COLUMNS:
        df[col] = df[col].apply(parse_array_column)

    products = df.apply(_compute_wcda_products, axis=1)
    df = df.join(products)
    df["mjd"] = pd.to_numeric(df["mjd"], errors="coerce")
    df["tobs"] = pd.to_numeric(df["tobs"], errors="coerce")
    df = df.sort_values("mjd").reset_index(drop=True)
    return df


def _compute_wcda_products(row: pd.Series) -> pd.Series:
    n_on = np.asarray(row["n_on"], dtype=float)
    n_bkg = np.asarray(row["n_bkg"], dtype=float)
    n_off = np.asarray(row["n_off"], dtype=float)
    tobs = float(row["tobs"]) if pd.notna(row["tobs"]) else np.nan

    if n_on.size == 0 or n_bkg.size == 0 or n_off.size == 0 or not np.isfinite(tobs) or tobs <= 0:
        return pd.Series(
            {
                "excess_counts": np.nan,
                "flux_excess": np.nan,
                "flux_excess_err": np.nan,
                "n_on_tot": np.nan,
                "n_bkg_tot": np.nan,
            }
        )

    excess = n_on - n_bkg
    excess_counts = float(np.sum(excess))
    flux_excess = excess_counts / tobs

    alpha = np.divide(n_bkg, n_off, out=np.zeros_like(n_bkg, dtype=float), where=n_off > 0)
    sigma_bin = np.sqrt(np.clip(n_on + np.square(alpha) * n_off, 0.0, None))
    flux_excess_err = float(np.sqrt(np.sum(np.square(sigma_bin))) / tobs)

    return pd.Series(
        {
            "excess_counts": excess_counts,
            "flux_excess": flux_excess,
            "flux_excess_err": flux_excess_err,
            "n_on_tot": float(np.sum(n_on)),
            "n_bkg_tot": float(np.sum(n_bkg)),
        }
    )


def usable_light_curve(df: pd.DataFrame, flux_col: str, err_col: str | None = None) -> pd.DataFrame:
    """Return sorted rows with finite time/flux and, when present, positive errors."""
    cols = ["mjd", flux_col]
    mask = np.isfinite(pd.to_numeric(df["mjd"], errors="coerce"))
    mask &= np.isfinite(pd.to_numeric(df[flux_col], errors="coerce"))
    if err_col is not None:
        cols.append(err_col)
        err = pd.to_numeric(df[err_col], errors="coerce")
        mask &= np.isfinite(err) & (err > 0)
    out = df.loc[mask, cols].copy()
    for col in cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.sort_values("mjd").reset_index(drop=True)


def align_to_reference_nearest(
    reference_mjd: np.ndarray,
    target: pd.DataFrame,
    *,
    tolerance_days: float,
    target_prefix: str,
) -> pd.DataFrame:
    """Align target rows to a reference MJD axis with nearest-neighbor matching."""
    ref = pd.DataFrame({"mjd": np.asarray(reference_mjd, dtype=float)})
    target = target.sort_values("mjd").reset_index(drop=True).copy()
    rename = {col: f"{target_prefix}_{col}" for col in target.columns if col != "mjd"}
    target = target.rename(columns=rename)
    aligned = pd.merge_asof(
        ref.sort_values("mjd"),
        target,
        on="mjd",
        direction="nearest",
        tolerance=float(tolerance_days),
    )
    return aligned


def standardize_flux(flux: np.ndarray) -> np.ndarray:
    flux = np.asarray(flux, dtype=float)
    flux = flux - np.nanmean(flux)
    std = np.nanstd(flux)
    if not np.isfinite(std) or std == 0:
        raise ValueError("Flux standard deviation is zero or non-finite.")
    return flux / std


def run_cwt(
    t_mjd: np.ndarray,
    flux: np.ndarray,
    *,
    dj: float = 1 / 12,
    period_min: float,
    period_max: float,
):
    """Run Morlet CWT and return arrays needed for plots and summaries."""
    t_mjd = np.asarray(t_mjd, dtype=float)
    flux = np.asarray(flux, dtype=float)
    mask = np.isfinite(t_mjd) & np.isfinite(flux)
    t_mjd, flux = t_mjd[mask], flux[mask]
    if len(t_mjd) < 4:
        raise ValueError("Need at least four finite points for CWT.")

    dt = float(np.median(np.diff(t_mjd)))
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("CWT requires a positive median cadence.")
    mother = wavelet.Morlet(6)
    s0 = 2.0 * dt
    j_count = int(np.log2(len(flux) * dt / s0) / dj)
    if j_count < 1:
        raise ValueError("CWT period grid is empty; check cadence and light-curve length.")

    y = standardize_flux(flux)
    wave, scales, freqs, coi, _fft, _fftfreqs = wavelet.cwt(y, dt, dj=dj, s0=s0, J=j_count, wavelet=mother)
    power = np.abs(wave) ** 2
    period = 1.0 / freqs
    gws = np.nanmean(power, axis=1)
    mask_period = (period >= period_min) & (period <= period_max)

    return {
        "t_mjd": t_mjd,
        "dt": dt,
        "dj": float(dj),
        "s0": s0,
        "J": int(j_count),
        "power": power,
        "period": period,
        "coi": np.asarray(coi, dtype=float),
        "gws": gws,
        "mask_period": mask_period,
        "period_min": float(period_min),
        "period_max": float(period_max),
    }


def clean_and_merge_weighted(t, y, yerr):
    """Clean, sort, and inverse-variance merge duplicate timestamps for WWZ."""
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)
    yerr = np.asarray(yerr, dtype=float)

    mask = np.isfinite(t) & np.isfinite(y) & np.isfinite(yerr) & (yerr > 0)
    t, y, yerr = t[mask], y[mask], yerr[mask]
    if len(t) < 4:
        raise ValueError("Need at least four finite points with positive errors for WWZ.")

    order = np.argsort(t)
    t, y, yerr = t[order], y[order], yerr[order]
    uniq_t, idx_start = np.unique(t, return_index=True)
    if len(uniq_t) == len(t):
        return t, y, yerr

    y_new = np.empty_like(uniq_t, dtype=float)
    e_new = np.empty_like(uniq_t, dtype=float)
    for k, _t0 in enumerate(uniq_t):
        i0 = idx_start[k]
        i1 = idx_start[k + 1] if (k + 1 < len(uniq_t)) else len(t)
        w = 1.0 / np.square(yerr[i0:i1])
        y_new[k] = np.sum(w * y[i0:i1]) / np.sum(w)
        e_new[k] = np.sqrt(1.0 / np.sum(w))
    return uniq_t, y_new, e_new


def run_wwz(
    t_mjd: np.ndarray,
    flux: np.ndarray,
    flux_err: np.ndarray,
    *,
    period_min: float,
    period_max: float,
    time_divisions: int = 250,
    decay_constant: float = 0.0125,
    freq_step_factor: float = 0.1,
    parallel: bool = False,
):
    """Run WWZ and return the time-period power map and ridge arrays."""
    t, y, yerr = clean_and_merge_weighted(t_mjd, flux, flux_err)
    t_span = float(t.max() - t.min())
    if not np.isfinite(t_span) or t_span <= 0:
        raise ValueError("WWZ requires a positive time span.")

    freq_low = 1.0 / float(period_max)
    freq_high = 1.0 / float(period_min)
    freq_step = float(freq_step_factor) / t_span

    tau_mat, freq_mat, wwz_mat, amp_mat, coef_mat, neff_mat = wwt(
        timestamps=t.astype(float),
        magnitudes=y.astype(float),
        time_divisions=int(time_divisions),
        freq_params=[freq_low, freq_high, freq_step, True],
        decay_constant=float(decay_constant),
        method="linear",
        parallel=parallel,
    )

    period_mat = 1.0 / freq_mat
    ridge_idx = np.argmax(wwz_mat, axis=1)
    ridge_tau = tau_mat[:, 0]
    ridge_period = period_mat[np.arange(len(ridge_idx)), ridge_idx]
    ridge_power = wwz_mat[np.arange(len(ridge_idx)), ridge_idx]
    global_wwz = np.nanmean(wwz_mat, axis=0)
    period_axis = 1.0 / freq_mat[0, :]

    return {
        "t": t,
        "y": y,
        "yerr": yerr,
        "t_span": t_span,
        "freq_low": freq_low,
        "freq_high": freq_high,
        "freq_step": freq_step,
        "time_divisions": int(time_divisions),
        "decay_constant": float(decay_constant),
        "tau_mat": tau_mat,
        "freq_mat": freq_mat,
        "period_mat": period_mat,
        "wwz_mat": wwz_mat,
        "amp_mat": amp_mat,
        "coef_mat": coef_mat,
        "neff_mat": neff_mat,
        "ridge_tau": ridge_tau,
        "ridge_period": ridge_period,
        "ridge_power": ridge_power,
        "global_wwz": global_wwz,
        "period_axis": period_axis,
        "period_min": float(period_min),
        "period_max": float(period_max),
    }
