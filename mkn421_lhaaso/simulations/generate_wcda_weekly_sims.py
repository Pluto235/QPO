#!/usr/bin/env python3
"""Generate Emmanoulopoulos simulations for the WCDA weekly light curve.

Example:
    python mkn421_lhaaso/simulations/generate_wcda_weekly_sims.py         --output mkn421_lhaaso/simulations/wcda_weekly_sims_full.h5         --nsim 10000         --ncores 48         --chunk 256         --overwrite

Example Slurm command:
    srun python mkn421_lhaaso/simulations/generate_wcda_weekly_sims.py         --output /path/to/wcda_weekly_sims_full.h5         --nsim 10000         --ncores ${SLURM_CPUS_PER_TASK:-8}         --chunk 256         --overwrite
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import time
from pathlib import Path

import h5py
import joblib
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tqdm import tqdm


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
DEFAULT_CSV = BASE_DIR.parent / "LHAASO-WCDA_Mrk421_2021-03-08_2025-11-06_week(1).csv"
DEFAULT_OUTPUT = BASE_DIR / "wcda_weekly_sims_full.h5"
EMMA_PATH = PROJECT_ROOT / "mkn421" / "emmanoulopoulos"


def import_emmanoulopoulos():
    if str(EMMA_PATH) not in sys.path:
        sys.path.insert(0, str(EMMA_PATH))
    import astropy.units as u
    from emmanoulopoulos.emmanoulopoulos_lc_simulation import Emmanoulopoulos_Sampler
    from emmanoulopoulos.lightcurve import LC
    return u, LC, Emmanoulopoulos_Sampler


class _TqdmBatchCompletionCallback(joblib.parallel.BatchCompletionCallBack):
    def __init__(self, *args, **kwargs):
        self._tqdm = kwargs.pop("tqdm_instance")
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        self._tqdm.update(n=self.batch_size)
        return super().__call__(*args, **kwargs)


class tqdm_joblib:
    def __init__(self, tqdm_object):
        self.tqdm_object = tqdm_object
        self._old_callback = None

    def __enter__(self):
        self._old_callback = joblib.parallel.BatchCompletionCallBack

        def _new_callback(*args, **kwargs):
            return _TqdmBatchCompletionCallback(*args, tqdm_instance=self.tqdm_object, **kwargs)

        joblib.parallel.BatchCompletionCallBack = _new_callback
        return self.tqdm_object

    def __exit__(self, exc_type, exc_val, exc_tb):
        joblib.parallel.BatchCompletionCallBack = self._old_callback
        self.tqdm_object.close()


def load_wcda_excess_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, comment="#")
    df.columns = [c.strip() for c in df.columns]

    for col in ["n_on", "n_bkg"]:
        df[col] = df[col].apply(ast.literal_eval)

    def excess_rate(row):
        return sum(on - bkg for on, bkg in zip(row["n_on"], row["n_bkg"])) / row["tobs"]

    df["flux_excess"] = df.apply(excess_rate, axis=1)
    return df.sort_values("mjd").reset_index(drop=True)


def clean_obs(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    t_mjd = np.asarray(df["mjd"], dtype=float)
    flux = np.asarray(df["flux_excess"], dtype=float)

    mask = np.isfinite(t_mjd) & np.isfinite(flux)
    t_mjd = t_mjd[mask]
    flux = flux[mask]

    if len(t_mjd) < 10:
        raise RuntimeError("Too few valid points after cleaning. Check flux_excess/CSV.")
    return t_mjd, flux


def build_lc_obs(t_mjd: np.ndarray, flux: np.ndarray):
    u, LC, _ = import_emmanoulopoulos()

    if len(t_mjd) >= 2:
        dt_days = float(np.median(np.diff(t_mjd)))
        if (not np.isfinite(dt_days)) or (dt_days <= 0):
            dt_days = 7.0
    else:
        dt_days = 7.0

    original_time = np.asarray(t_mjd, dtype=float) * u.day
    tbin = dt_days * u.day
    lc_obs = LC(original_time, np.asarray(flux, dtype=float), errors=None, tbin=tbin)
    return lc_obs, dt_days


def one_sim(i: int, lc_obs, nt: int, base_seed: int):
    _, _, Emmanoulopoulos_Sampler = import_emmanoulopoulos()

    seed = (int(base_seed) + 1000003 * int(i) + (os.getpid() % 100000)) % (2**32 - 1)
    np.random.seed(seed)

    sampler = Emmanoulopoulos_Sampler()
    lc_sim = sampler.sample_from_lc(lc_obs)

    if hasattr(lc_sim, "original_flux"):
        flux_sim = np.asarray(lc_sim.original_flux, dtype=np.float32)
    else:
        flux_sim = np.asarray(lc_sim.flux, dtype=np.float32)

    if flux_sim.shape[0] != nt:
        raise RuntimeError(f"Nt mismatch in sim {i}: got {flux_sim.shape[0]} expected {nt}")

    return i, np.uint32(seed), flux_sim


def init_h5(out_path: Path, nsim: int, t_mjd: np.ndarray, flux_obs: np.ndarray, meta: dict, chunk_rows: int = 256):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    nt = len(t_mjd)

    with h5py.File(out_path, "w") as f:
        f.attrs["meta_json"] = json.dumps(meta, ensure_ascii=False)
        f.create_dataset("t_mjd_clean", data=np.asarray(t_mjd, dtype=np.float64))
        f.create_dataset("flux_obs_clean", data=np.asarray(flux_obs, dtype=np.float64))
        f.create_dataset(
            "flux_sims",
            shape=(nsim, nt),
            dtype="f4",
            chunks=(min(chunk_rows, nsim), nt),
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )
        f.create_dataset(
            "seed_sims",
            shape=(nsim,),
            dtype="u4",
            chunks=(min(chunk_rows, nsim),),
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )
        done = f.create_dataset(
            "done_mask",
            shape=(nsim,),
            dtype="u1",
            chunks=(min(chunk_rows, nsim),),
            compression="gzip",
            compression_opts=1,
            shuffle=True,
        )
        done[...] = 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Input WCDA CSV file.")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output HDF5 file.")
    ap.add_argument("--nsim", type=int, default=10000, help="Number of light curves to simulate.")
    ap.add_argument("--ncores", type=int, default=48, help="Number of parallel workers.")
    ap.add_argument("--chunk", type=int, default=256, help="Number of simulations per write batch.")
    ap.add_argument("--base-seed", type=int, default=123456, help="Base random seed.")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite the output HDF5 if it already exists.")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    csv_path = args.csv.resolve()
    out_path = args.output.resolve()

    if out_path.exists() and not args.overwrite:
        raise FileExistsError(f"{out_path} already exists. Use --overwrite to replace it.")

    df = load_wcda_excess_csv(csv_path)
    t_mjd, flux = clean_obs(df)
    lc_obs, dt_days = build_lc_obs(t_mjd, flux)

    if hasattr(lc_obs, "fit_PSD"):
        lc_obs.fit_PSD()
    if hasattr(lc_obs, "fit_PDF"):
        lc_obs.fit_PDF()

    nt = len(t_mjd)
    meta = dict(
        created=time.strftime("%Y-%m-%d %H:%M:%S"),
        obs_csv=str(csv_path),
        Nsim=int(args.nsim),
        Nt=int(nt),
        base_seed=int(args.base_seed),
        dt_days=float(dt_days),
        emma_path=str(EMMA_PATH),
        lc_signature="LC(original_time, original_flux, errors=None, tbin=None)",
        note="Full simulated light curves saved. Designed for notebook reuse and Slurm submission.",
    )

    init_h5(out_path, args.nsim, t_mjd, flux, meta, chunk_rows=args.chunk)
    print(f"[OK] Initialized: {out_path}")
    print(f"[INFO] Nt={nt}, Nsim={args.nsim}, ncores={args.ncores}, chunk={args.chunk}, dt~{dt_days:.3f} d")

    for start in range(0, args.nsim, args.chunk):
        end = min(args.nsim, start + args.chunk)
        idxs = list(range(start, end))
        tasks = (delayed(one_sim)(i, lc_obs, nt, args.base_seed) for i in idxs)

        with tqdm_joblib(tqdm(total=(end - start), desc=f"Sim {start}-{end-1}", dynamic_ncols=True)):
            results = Parallel(
                n_jobs=args.ncores,
                backend="loky",
                batch_size="auto",
                verbose=0,
            )(tasks)

        with h5py.File(out_path, "a") as f:
            d_flux = f["flux_sims"]
            d_seed = f["seed_sims"]
            d_done = f["done_mask"]
            for i, seed, flux_sim in results:
                d_flux[i, :] = flux_sim
                d_seed[i] = seed
                d_done[i] = 1

    print(f"[DONE] Saved {args.nsim} sims -> {out_path}")


if __name__ == "__main__":
    main()
