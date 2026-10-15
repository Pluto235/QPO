from __future__ import annotations
import json
import platform
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from .analysis import run_cwt_analysis, run_wwz_analysis
from .io import read_lightcurve
from .plotting import integrated_figure
from .sampling import make_period_grid, prepare_cwt_grid
from .significance import wwz_ar1_significance

@dataclass(frozen=True)
class AnalysisResult:
    output_dir: Path
    candidates: pd.DataFrame

def analyze_lightcurve(input_path, output_dir, config=None, *, label=None, period_min=None, period_max=None, n_periods=400, n_surrogates=1000, seed=20260922, workers=1, time_divisions=80, freq_step_factor=0.5, flux_unit=""):
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    lc = read_lightcurve(input_path); t = lc.data["time"].to_numpy(float); y = lc.data["flux"].to_numpy(float); e = lc.data["flux_err"].to_numpy(float)
    cadence = float(lc.qc["median_cadence"]); span = float(lc.qc["time_span"])
    pmin = float(period_min if period_min is not None else max(2 * cadence, span / 1000)); pmax = float(period_max if period_max is not None else span / 2)
    make_period_grid(pmin, pmax, n_periods)
    grid = prepare_cwt_grid(t, y); cwt_flux = grid.flux.copy()
    # ponytail: fill long gaps with the mean only for the CWT backend; the mask
    # remains in qc.json because the current PyCWT API requires finite input.
    cwt_flux[~np.isfinite(cwt_flux)] = float(np.nanmean(cwt_flux))
    cwt = run_cwt_analysis(grid.time, cwt_flux, period_min=pmin, period_max=pmax)
    wwz = run_wwz_analysis(t, y, e, period_min=pmin, period_max=pmax, time_divisions=time_divisions, freq_step_factor=freq_step_factor)
    sig = wwz_ar1_significance(t, y, e, wwz, n_surrogates=n_surrogates, seed=seed, workers=workers)
    cwt_rows = []
    cwt_period = np.asarray(cwt["period"], float)
    cwt_power = np.asarray(cwt["gws"], float)
    cwt_threshold = np.asarray(cwt["signif95"], float)
    for idx in find_peaks(np.nan_to_num(cwt_power, nan=-np.inf))[0]:
        if np.isfinite(cwt_threshold[idx]) and cwt_power[idx] >= cwt_threshold[idx]:
            cwt_rows.append({"method": "CWT", "period": float(cwt_period[idx]), "power": float(cwt_power[idx]), "local_fap": np.nan, "global_fap": np.nan, "n_surrogates": 0, "null_model": "PyCWT AR(1) theoretical reference"})
    candidates = pd.DataFrame(cwt_rows + sig["rows"])
    if candidates.empty: candidates = pd.DataFrame(columns=["method", "period", "power", "local_fap", "global_fap", "n_surrogates", "null_model"])
    candidates.to_csv(out / "candidates.csv", index=False); candidates.to_csv(out / "significance.csv", index=False)
    (out / "qc.json").write_text(json.dumps({**lc.qc, **grid.qc}, indent=2))
    np.savez_compressed(out / "cwt.npz", **{k: v for k, v in cwt.items() if isinstance(v, np.ndarray)}); np.savez_compressed(out / "wwz.npz", **{k: v for k, v in wwz.items() if isinstance(v, np.ndarray)})
    integrated_figure(out / "integrated.png", label or Path(input_path).stem, lc.data, cwt, wwz, sig, flux_unit=flux_unit)
    manifest = {"input_file": str(Path(input_path).resolve()), "input_columns": ["time", "flux", "flux_err"], "label": label or Path(input_path).stem, "time_unit": "MJD", "flux_unit": flux_unit, "period_min": pmin, "period_max": pmax, "n_periods": int(n_periods), "wwz_time_divisions": int(time_divisions), "wwz_freq_step_factor": float(freq_step_factor), "significance": "AR(1)+Monte Carlo", "n_surrogates": int(n_surrogates), "seed": int(seed), "python": platform.python_version(), "outputs": ["integrated.png", "candidates.csv", "significance.csv", "qc.json", "manifest.json", "cwt.npz", "wwz.npz"]}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return AnalysisResult(out, candidates)
