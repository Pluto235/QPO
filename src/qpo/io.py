from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class LightCurve:
    data: pd.DataFrame
    qc: dict[str, object]

def read_lightcurve(path: str | Path) -> LightCurve:
    path = Path(path)
    df = pd.read_csv(path, comment="#")
    required = ["time", "flux", "flux_err"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")
    df = df[required].copy()
    n_input = len(df)
    for col in required:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    finite = np.isfinite(df[required]).all(axis=1)
    positive = df["flux_err"] > 0
    invalid_rows = int((~(finite & positive)).sum())
    df = df.loc[finite & positive].sort_values("time").reset_index(drop=True)
    duplicates = int(df["time"].duplicated(keep=False).sum() - df["time"].duplicated().sum())
    if duplicates:
        rows = []
        for time, group in df.groupby("time", sort=True):
            weights = 1.0 / np.square(group["flux_err"].to_numpy(float))
            rows.append({"time": time, "flux": float(np.sum(weights * group["flux"].to_numpy(float)) / np.sum(weights)), "flux_err": float(np.sqrt(1.0 / np.sum(weights)))})
        df = pd.DataFrame(rows)
    diffs = np.diff(df["time"].to_numpy(float))
    positive_diffs = diffs[diffs > 0]
    qc = {"input_rows": n_input, "valid_rows": int(len(df)), "invalid_rows_removed": invalid_rows, "duplicate_rows_merged": duplicates, "time_min": float(df["time"].min()), "time_max": float(df["time"].max()), "median_cadence": float(np.median(positive_diffs)) if len(positive_diffs) else None, "time_span": float(df["time"].max() - df["time"].min())}
    if len(df) < 2:
        raise ValueError("At least two valid light-curve rows are required.")
    return LightCurve(df.reset_index(drop=True), qc)
