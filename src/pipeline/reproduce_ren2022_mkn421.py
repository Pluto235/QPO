#!/usr/bin/env python3
"""Reproduce Ren et al. (2022)'s Fermi-LAT CWT + Emmanoulopoulos-MC QPO search for
Mrk 421, using the project's existing weekly Fermi-LAT TS>=9 flux light curve
(data/processed/fermi_week/Mrk421_Fermi_weekly_TSge9_MJD.csv) sliced to their
published baseline (2008-08 to 2021-04).

Method matches the project's own literature summary of Ren+22: Morlet CWT global
wavelet spectrum (GWS), significance from Emmanoulopoulos Monte Carlo simulations
(vendored under src/methods/emmanoulopoulos/) rather than an AR(1) surrogate model.
Reuses src/methods/periodicity.run_cwt (the canonical CWT helper already used by
the AGN survey pipeline) rather than duplicating it.

Run: ~/miniconda3/envs/py310/bin/python src/pipeline/reproduce_ren2022_mkn421.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
EMMA_PATH = SRC_ROOT / "methods" / "emmanoulopoulos"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from methods.periodicity import run_cwt  # noqa: E402  (canonical CWT helper)

FERMI_CSV = PROJECT_ROOT / "data" / "processed" / "fermi_week" / "Mrk421_Fermi_weekly_TSge9_MJD.csv"
OUT_DIR = PROJECT_ROOT / "data" / "processed" / "periodicity" / "ren2022_repro" / "mkn421"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Ren et al. (2022) baseline, as recorded in any-reports/qpo-fermi-lat-detections.md
REN_START_MJD = 54679.0  # 2008-08-01
REN_END_MJD = 59334.0    # 2021-04-30

PERIOD_MIN, PERIOD_MAX = 50.0, 600.0
TARGET_PERIOD = 300.0  # Ren+22 Mrk 421 candidate, 7-day bins: 300 +/- 65 d
N_SIMS = 300
N_JOBS = 8


def import_emmanoulopoulos():
    if str(EMMA_PATH) not in sys.path:
        sys.path.insert(0, str(EMMA_PATH))
    import astropy.units as u
    from emmanoulopoulos.emmanoulopoulos_lc_simulation import Emmanoulopoulos_Sampler
    from emmanoulopoulos.lightcurve import LC
    return u, LC, Emmanoulopoulos_Sampler


def top_period_candidates(period, spectrum, topk=5):
    from scipy.signal import find_peaks

    period = np.asarray(period, dtype=float)
    spectrum = np.asarray(spectrum, dtype=float)
    mask = np.isfinite(period) & np.isfinite(spectrum)
    period, spectrum = period[mask], spectrum[mask]
    peaks, _ = find_peaks(spectrum)
    if len(peaks) == 0:
        peaks = np.argsort(spectrum)[-min(topk, len(spectrum)):]
    order = peaks[np.argsort(spectrum[peaks])[::-1][:topk]]
    return pd.DataFrame({"period_day": period[order], "power": spectrum[order]}).sort_values(
        "power", ascending=False
    ).reset_index(drop=True)


def gws_at_period(period_axis, gws, target_period):
    order = np.argsort(period_axis)
    return float(np.interp(target_period, period_axis[order], gws[order]))


def _one_sim(i, t_mjd, base_seed):
    """Run in a worker process: build a fresh LC/sampler (astropy Quantity /
    fitted PSD-PDF objects are not reliably picklable across processes), draw
    one Emmanoulopoulos realization, and CWT it."""
    u, LC, Emmanoulopoulos_Sampler = import_emmanoulopoulos()
    df = pd.read_csv(FERMI_CSV).sort_values("mjd").reset_index(drop=True)
    mask = (df["mjd"] >= REN_START_MJD) & (df["mjd"] <= REN_END_MJD)
    flux = df.loc[mask].reset_index(drop=True)["flux"].to_numpy(dtype=float)
    dt_days = float(np.median(np.diff(t_mjd)))
    lc_obs = LC(t_mjd * u.day, flux, errors=None, tbin=dt_days * u.day)
    if hasattr(lc_obs, "fit_PSD"):
        lc_obs.fit_PSD()
    if hasattr(lc_obs, "fit_PDF"):
        lc_obs.fit_PDF()

    seed = (int(base_seed) + 1000003 * int(i)) % (2**32 - 1)
    np.random.seed(seed)
    sampler = Emmanoulopoulos_Sampler()
    try:
        lc_sim = sampler.sample_from_lc(lc_obs)
        flux_sim = np.asarray(getattr(lc_sim, "original_flux", getattr(lc_sim, "flux", None)), dtype=float)
        if flux_sim.shape[0] != len(t_mjd):
            raise RuntimeError(f"Nt mismatch: got {flux_sim.shape[0]} expected {len(t_mjd)}")
        sim = run_cwt(t_mjd, flux_sim, period_min=PERIOD_MIN, period_max=PERIOD_MAX)
        gws_target = gws_at_period(sim["period"], sim["gws"], TARGET_PERIOD)
        gws_global_max = float(np.nanmax(sim["gws"][sim["mask_period"]]))
        return gws_target, gws_global_max
    except Exception:
        return np.nan, np.nan


def main():
    df = pd.read_csv(FERMI_CSV).sort_values("mjd").reset_index(drop=True)
    mask = (df["mjd"] >= REN_START_MJD) & (df["mjd"] <= REN_END_MJD)
    df_win = df.loc[mask].reset_index(drop=True)
    t_mjd = df_win["mjd"].to_numpy(dtype=float)
    flux = df_win["flux"].to_numpy(dtype=float)
    n = len(t_mjd)
    print(f"Ren+22-window slice: N={n}, MJD {t_mjd.min():.1f}-{t_mjd.max():.1f} "
          f"({(t_mjd.max() - t_mjd.min()) / 365.25:.1f} yr)")

    obs = run_cwt(t_mjd, flux, period_min=PERIOD_MIN, period_max=PERIOD_MAX)
    period, gws, mask_p = obs["period"], obs["gws"], obs["mask_period"]
    candidates = top_period_candidates(period[mask_p], gws[mask_p], topk=5)
    print("Top observed CWT candidates (period_day, power):")
    print(candidates.to_string(index=False))

    obs_gws_at_target = gws_at_period(period, gws, TARGET_PERIOD)
    print(f"Observed GWS at {TARGET_PERIOD:.0f} d = {obs_gws_at_target:.4f}")

    print(f"Running {N_SIMS} Emmanoulopoulos MC sims across {N_JOBS} workers ...")
    t0 = time.time()
    results = Parallel(n_jobs=N_JOBS, backend="loky")(
        delayed(_one_sim)(i, t_mjd, base_seed=20260703) for i in range(N_SIMS)
    )
    print(f"MC sims done in {time.time() - t0:.1f} s")

    sim_gws_at_target = np.array([r[0] for r in results], dtype=float)
    sim_gws_global_max = np.array([r[1] for r in results], dtype=float)
    ok = np.isfinite(sim_gws_at_target)
    n_ok = int(ok.sum())
    local_fap = float(np.mean(sim_gws_at_target[ok] >= obs_gws_at_target))
    global_fap = float(np.mean(sim_gws_global_max[ok] >= obs_gws_at_target))

    result = {
        "source": "Mrk 421",
        "window": "Ren+22 baseline (2008-08 to 2021-04)",
        "n_points": n,
        "mjd_min": float(t_mjd.min()),
        "mjd_max": float(t_mjd.max()),
        "target_period_days": TARGET_PERIOD,
        "observed_gws_at_target": obs_gws_at_target,
        "n_sims_requested": N_SIMS,
        "n_sims_ok": n_ok,
        "n_sims_failed": N_SIMS - n_ok,
        "local_fap_at_300d": local_fap,
        "global_fap_at_300d": global_fap,
        "top_observed_candidates": candidates.to_dict(orient="records"),
        "ren2022_claim": "300 +/- 65 d (7-day bins, >5 sigma, 3 cycles)",
    }
    print(json.dumps(result, indent=2))

    (OUT_DIR / "ren2022_repro_summary.json").write_text(json.dumps(result, indent=2))
    np.savez(
        OUT_DIR / "ren2022_repro_cwt.npz",
        t_mjd=t_mjd, flux=flux, period=period, gws=gws, mask_period=mask_p,
        sim_gws_at_target=sim_gws_at_target, sim_gws_global_max=sim_gws_global_max,
    )

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(17, 4.8), gridspec_kw={"width_ratios": [1.4, 1.0, 1.2]},
                              constrained_layout=True)
    ax_lc, ax_gws, ax_mc = axes

    ax_lc.plot(t_mjd, flux, "o-", ms=3, lw=0.8, color="#1c1f24")
    ax_lc.set_xlabel("MJD")
    ax_lc.set_ylabel("Fermi-LAT photon flux (0.1-300 GeV)")
    ax_lc.set_title(f"Mrk 421 Fermi weekly, Ren+22 window (N={n})")

    ax_gws.plot(gws[mask_p], period[mask_p], color="black", lw=1.6, label="Observed GWS")
    ax_gws.axhline(TARGET_PERIOD, color="#a6362c", ls="--", lw=1, label=f"Ren+22 {TARGET_PERIOD:.0f} d")
    ax_gws.set_xscale("log")
    ax_gws.set_yscale("log")
    ax_gws.set_ylim(PERIOD_MIN, PERIOD_MAX)
    ax_gws.set_xlabel("Global Wavelet Power")
    ax_gws.set_ylabel("Period (day)")
    ax_gws.set_title("Observed CWT global wavelet spectrum")
    ax_gws.legend(fontsize=8)

    finite_sim = sim_gws_at_target[np.isfinite(sim_gws_at_target)]
    ax_mc.hist(finite_sim, bins=40, color="#8a95a5", alpha=0.85, label=f"{n_ok} Emmanoulopoulos MC sims")
    ax_mc.axvline(obs_gws_at_target, color="#a6362c", lw=2, label="Observed")
    ax_mc.set_xlabel(f"GWS at {TARGET_PERIOD:.0f} d")
    ax_mc.set_ylabel("Count")
    ax_mc.set_title(f"Local FAP={local_fap:.3f}, Global FAP={global_fap:.3f}")
    ax_mc.legend(fontsize=8)

    fig.savefig(OUT_DIR / "ren2022_repro_mkn421.png", dpi=140)
    print(f"Wrote figure to {OUT_DIR / 'ren2022_repro_mkn421.png'}")


if __name__ == "__main__":
    main()
