#!/usr/bin/env python3
"""Run the repository CWT/WWZ checks on the OQ 334 paper light curve.

The paper does not publish its daily table, so the bundled CSV is a provisional
digitization of Figure 1.  Pass a real Fermi-LAT table with columns
``mjd,flux,flux_err`` to replace it.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import run_cwt, run_wwz, usable_light_curve
from pipeline.periodicity_v1 import _plot_cwt, _plot_wwz
from utils.project_paths import PERIODICITY_DIR, PROJECT_ROOT

WINDOWS = {
    "full_61040_61280": (61040.0, 61280.0),
    "r1_61129_61165": (61129.0, 61165.0),
    "r2a_61167_61200": (61167.0, 61200.0),
    "r2b_61205_61257": (61205.0, 61257.0),
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, default=PERIODICITY_DIR / "oq334")
    p.add_argument("--wwz-time-divisions", type=int, default=80)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.input)
    required = {"mjd", "flux", "flux_err"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    df = usable_light_curve(df, "flux", "flux_err")
    args.output_dir = args.output_dir if args.output_dir.is_absolute() else PROJECT_ROOT / args.output_dir
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, (lo, hi) in WINDOWS.items():
        part = df[df.mjd.between(lo, hi)].copy()
        if len(part) < 8:
            raise ValueError(f"{name}: only {len(part)} usable points")
        t = part.mjd.to_numpy(float)
        y = part.flux.to_numpy(float)
        e = part.flux_err.to_numpy(float)
        cwt = run_cwt(t, y, period_min=5.0, period_max=30.0)
        wwz = run_wwz(
            t, y, e, period_min=5.0, period_max=30.0,
            time_divisions=args.wwz_time_divisions, freq_step_factor=0.1,
        )
        label = f"OQ 334 {name.replace('_', ' ')}"
        _plot_cwt(args.output_dir / f"{name}_cwt.png", label, t, y, e, cwt, xlim=(61040.0, 61280.0))
        _plot_wwz(
            args.output_dir / f"{name}_wwz.png",
            label,
            wwz,
            color_scale="linear",
            mark_global_peak=True,
            xlim=(61040.0, 61280.0),
        )
        cm = cwt["mask_period"]
        ci = np.nanargmax(np.where(cm, cwt["gws"], np.nan))
        wm = (wwz["period_axis"] >= 5.0) & (wwz["period_axis"] <= 30.0)
        wi = np.nanargmax(np.where(wm, wwz["global_wwz"], np.nan))
        np.savez_compressed(
            args.output_dir / f"{name}_cwt.npz", **{k: cwt[k] for k in ("t_mjd", "period", "power", "coi", "gws", "mask_period")}
        )
        np.savez_compressed(
            args.output_dir / f"{name}_wwz.npz", **{k: wwz[k] for k in ("t", "period_axis", "period_mat", "wwz_mat", "ridge_tau", "ridge_period", "ridge_power", "global_wwz")}
        )
        rows.append({
            "window": name, "n_points": len(part), "mjd_min": t.min(), "mjd_max": t.max(),
            "cwt_peak_period_days": cwt["period"][ci], "wwz_peak_period_days": wwz["period_axis"][wi],
            "wwz_peak_power": wwz["global_wwz"][wi],
        })
    out = pd.DataFrame(rows)
    out.to_csv(args.output_dir / "oq334_cwt_wwz_summary.csv", index=False)
    print(out.to_string(index=False))
    print(f"[OK] wrote {args.output_dir.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
