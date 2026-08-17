#!/usr/bin/env python3
"""Run the Fermi-LAT weekly Mrk 501 light curve pipeline (analogous to fermi_month.py
but weekly-binned, full mission baseline, for source_id mkn501 / 4FGL J1653.8+3945)."""

import os
import sys
from pathlib import Path

from fermipy.gtanalysis import GTAnalysis
from astropy.io import fits
import numpy as np
import pandas as pd
from astropy.time import Time, TimeDelta

RUN_DIR = Path("/mnt/mydisk/server/projects/QPO/src/pipeline/fermi_mkn501_run")
CONFIG_PATH = RUN_DIR / "fermi_mkn501_week_config.yaml"
OUTDIR = Path("/mnt/mydisk/server/projects/QPO/data/processed/fermi_month/mkn501")
LC_OUTDIR = Path("/mnt/mydisk/server/projects/QPO/data/processed/fermi_week/mkn501_lc_weekly")
ROI_PATH = OUTDIR / "mkn501_fulltime.fits"
SRC_NAME = "4FGL J1653.8+3945"
FINAL_CSV = Path(
    "/mnt/mydisk/server/projects/QPO/data/processed/fermi_week/Mrk501_Fermi_weekly_TSge9_MJD.csv"
)

WEEK_SECONDS = 7 * 86400


def convert_lightcurve_to_csv(lc_fits_path: Path) -> None:
    """Match the exact convention used for Mrk421_Fermi_weekly_TSge9_MJD.csv:
    0.1-300 GeV flux (analysis-range 'flux' column), TS>=9 filter, sorted, mjd/flux/flux_err columns.
    fermipy's own lightcurve FITS output already carries tmin_mjd/tmax_mjd (astropy Time-derived),
    so we use those directly rather than re-deriving MET->MJD ourselves."""
    with fits.open(lc_fits_path) as hdul:
        ext = "LIGHTCURVE" if "LIGHTCURVE" in [h.name for h in hdul] else 1
        data = hdul[ext].data
        df = pd.DataFrame(np.array(data).byteswap().newbyteorder())

    if "tmin_mjd" in df.columns and "tmax_mjd" in df.columns:
        t_mjd = 0.5 * (df["tmin_mjd"].values + df["tmax_mjd"].values)
    else:
        t_mid_met = 0.5 * (df["tmin"].values + df["tmax"].values)
        t0 = Time("2001-01-01T00:00:00", scale="utc")
        t_mjd = (t0 + TimeDelta(t_mid_met, format="sec")).mjd

    flux_col = None
    err_col = None
    ts_col = None
    for c in df.columns:
        if c.lower() == "flux":
            flux_col = c
        if c.lower() == "flux_err":
            err_col = c
        if c.lower() == "ts":
            ts_col = c
    if flux_col is None or err_col is None or ts_col is None:
        raise RuntimeError(f"Could not find flux/flux_err/ts columns in {list(df.columns)}")

    flux = df[flux_col].values
    flux_err = df[err_col].values
    ts = df[ts_col].values

    mask = (
        (ts >= 9)
        & np.isfinite(t_mjd)
        & np.isfinite(flux)
        & np.isfinite(flux_err)
        & (flux_err > 0)
    )

    t_sel = t_mjd[mask]
    f_sel = flux[mask]
    e_sel = flux_err[mask]

    idx = np.argsort(t_sel)
    t_sel, f_sel, e_sel = t_sel[idx], f_sel[idx], e_sel[idx]

    out = pd.DataFrame({"mjd": t_sel, "flux": f_sel, "flux_err": e_sel})
    FINAL_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(FINAL_CSV, index=False)
    print(f"Total bins: {len(df)}, TS>=9 bins used: {len(t_sel)}")
    print(f"Saved: {FINAL_CSV}")


def main():
    os.chdir(RUN_DIR)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    LC_OUTDIR.mkdir(parents=True, exist_ok=True)

    print("=== Setting up ROI ===", flush=True)
    gta = GTAnalysis(str(CONFIG_PATH), logging={"verbosity": 3})
    gta.setup()
    print("=== ROI setup complete, optimizing ===", flush=True)
    gta.optimize()
    print("=== Optimize complete, freeing sources within 3 deg ===", flush=True)
    gta.free_sources(distance=3.0)
    print("=== Running full-time fit ===", flush=True)
    gta.fit()
    gta.write_roi(str(ROI_PATH))
    print(f"=== Full-time ROI fit written to {ROI_PATH} ===", flush=True)

    print("=== Reloading ROI for lightcurve stage ===", flush=True)
    gta = GTAnalysis(str(CONFIG_PATH), logging={"verbosity": 3})
    gta.load_roi(str(ROI_PATH))

    print(f"=== Starting weekly lightcurve computation for {SRC_NAME} (binsz={WEEK_SECONDS}s) ===", flush=True)
    lc = gta.lightcurve(
        SRC_NAME,
        binsz=WEEK_SECONDS,
        free_background=True,
        use_local_ltcube=False,
        outdir=str(LC_OUTDIR),
        multithread=True,
        nthread=int(os.environ.get("SLURM_CPUS_PER_TASK", "8")),
    )
    print("=== Lightcurve computation complete ===", flush=True)

    # fermipy writes a FITS light curve table under LC_OUTDIR; locate it.
    # Expected filename is 'lightcurve.fits' (no prefix configured), but search broadly to be safe.
    if lc.get("file"):
        candidate = LC_OUTDIR / lc["file"]
        lc_fits_candidates = [candidate] if candidate.exists() else []
    else:
        lc_fits_candidates = []
    if not lc_fits_candidates:
        lc_fits_candidates = sorted(LC_OUTDIR.glob("*lightcurve*.fits"))
    if not lc_fits_candidates:
        raise RuntimeError(f"No lightcurve FITS output found under {LC_OUTDIR}")
    lc_fits_path = lc_fits_candidates[0]
    print(f"=== Converting {lc_fits_path} to final CSV ===", flush=True)
    convert_lightcurve_to_csv(lc_fits_path)
    print("=== DONE ===", flush=True)


if __name__ == "__main__":
    main()
