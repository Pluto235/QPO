from __future__ import annotations
import numpy as np
from scipy.signal import find_peaks
from concurrent.futures import ThreadPoolExecutor
from methods.periodicity import run_wwz

def _lag1(y):
    y = np.asarray(y, float); y = y - np.mean(y)
    return float(np.corrcoef(y[:-1], y[1:])[0, 1]) if len(y) > 2 and np.std(y) else 0.0

def _ar1(n, alpha, mean, std, rng):
    out = np.empty(n); out[0] = rng.normal(); noise = rng.normal(size=n)
    for i in range(1, n):
        out[i] = alpha * out[i - 1] + np.sqrt(max(1 - alpha * alpha, 1e-8)) * noise[i]
    return mean + std * (out - out.mean()) / max(out.std(), 1e-12)

def wwz_ar1_significance(t, y, yerr, wwz, *, n_surrogates=1000, seed=20260922, workers=1, local_fraction=0.10):
    t, y, yerr = np.asarray(t, float), np.asarray(y, float), np.asarray(yerr, float)
    period = np.asarray(wwz["period_axis"], float); observed = np.asarray(wwz["global_wwz"], float)
    alpha = _lag1(y)
    seeds = np.random.default_rng(seed).integers(0, np.iinfo(np.uint32).max, size=int(n_surrogates), dtype=np.uint32)
    def simulate(sim_seed):
        rng = np.random.default_rng(int(sim_seed))
        sim = _ar1(len(y), alpha, float(y.mean()), float(y.std()), rng)
        result = run_wwz(t, sim, yerr, period_min=float(period.min()), period_max=float(period.max()), time_divisions=int(wwz["time_divisions"]), freq_step_factor=float(wwz["freq_step"]) * (t.max() - t.min()))
        return result["global_wwz"]
    # ponytail: threads are enough for the current WWZ workload; process-level
    # isolation can be added if large surrogate runs become CPU-bound.
    if workers > 1 and n_surrogates > 1:
        with ThreadPoolExecutor(max_workers=int(workers)) as pool:
            sims = list(pool.map(simulate, seeds))
    else:
        sims = [simulate(i) for i in seeds]
    sims = np.asarray(sims)
    q95, q99 = np.nanpercentile(sims, [95, 99], axis=0)
    global_max = np.nanmax(sims, axis=1)
    rows = []
    for idx in find_peaks(np.nan_to_num(observed, nan=-np.inf))[0]:
        p = float(period[idx]); local = (period >= p * (1 - local_fraction)) & (period <= p * (1 + local_fraction)); local_obs = float(np.nanmax(observed[local]))
        local_fap = float((np.count_nonzero(np.nanmax(sims[:, local], axis=1) >= local_obs) + 1) / (len(sims) + 1))
        global_fap = float((np.count_nonzero(global_max >= local_obs) + 1) / (len(sims) + 1))
        rows.append({"method": "WWZ", "period": p, "power": local_obs, "local_fap": local_fap, "global_fap": global_fap, "n_surrogates": int(n_surrogates), "null_model": "AR(1) Gaussian surrogate"})
    return {"period": period, "observed": observed, "pointwise95": q95, "pointwise99": q99, "alpha": alpha, "rows": rows, "surrogate_global_max": global_max}
