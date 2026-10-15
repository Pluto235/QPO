from __future__ import annotations
import numpy as np
import pycwt
from methods.periodicity import run_cwt, run_wwz

def run_cwt_analysis(time, flux, *, period_min, period_max):
    result = run_cwt(time, flux, period_min=period_min, period_max=period_max)
    mother = pycwt.Morlet(6)
    y = np.asarray(flux, float)
    alpha = float(np.corrcoef(y[:-1], y[1:])[0, 1]) if len(y) > 2 and np.std(y) else 0.0
    try:
        signif, _ = pycwt.significance(float(np.nanvar(y)), result["dt"], result["period"], 0, alpha, significance_level=0.95, wavelet=mother)
    except Exception:
        signif = np.full_like(result["period"], np.nan)
    result["ar1"] = alpha
    result["signif95"] = np.asarray(signif, dtype=float)
    return result

def run_wwz_analysis(time, flux, flux_err, *, period_min, period_max, time_divisions=80, freq_step_factor=0.5):
    return run_wwz(time, flux, flux_err, period_min=period_min, period_max=period_max, time_divisions=time_divisions, freq_step_factor=freq_step_factor)
