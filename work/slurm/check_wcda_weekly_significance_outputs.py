#!/usr/bin/env python3
"""Validate ETO WCDA weekly significance outputs."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PERIODICITY_DIR = ROOT / "data" / "processed" / "periodicity" / "agn_wcda_weekly_survey"
SOURCES = (
    "mkn421",
    "mkn501",
    "1es1959p650",
    "1es1727p502",
    "1es2344p514",
    "bllac",
    "ngc1275",
    "m87",
    "4c_p42d22",
    "ic310",
)
REQUIRED_COLUMNS = {
    "source_id",
    "method",
    "period_days",
    "cycles",
    "observed_statistic",
    "local_fap",
    "global_fap",
    "above_95",
    "above_99",
    "n_surrogates",
}


def main() -> int:
    summary_path = PERIODICITY_DIR / "agn_wcda_weekly_significance_summary.csv"
    if not summary_path.exists():
        print(f"[FAIL] missing {summary_path.relative_to(ROOT)}")
        return 1

    summary = pd.read_csv(summary_path)
    missing_cols = sorted(REQUIRED_COLUMNS - set(summary.columns))
    if missing_cols:
        print(f"[FAIL] missing summary columns: {missing_cols}")
        return 1

    observed_sources = set(summary["source_id"])
    expected_sources = set(SOURCES)
    if observed_sources != expected_sources:
        print(f"[FAIL] source coverage mismatch: missing={sorted(expected_sources - observed_sources)}, extra={sorted(observed_sources - expected_sources)}")
        return 1

    for source_id in SOURCES:
        source_dir = PERIODICITY_DIR / source_id
        for filename in (
            "wcda_weekly_local_significance.csv",
            "wcda_weekly_cwt_global_significance.png",
            "wcda_weekly_wwz_global_significance.png",
        ):
            path = source_dir / filename
            if not path.exists() or path.stat().st_size <= 0:
                print(f"[FAIL] missing or empty {path.relative_to(ROOT)}")
                return 1

    fap_cols = ["local_fap", "global_fap"]
    for col in fap_cols:
        values = pd.to_numeric(summary[col], errors="coerce")
        finite = values[np.isfinite(values)]
        if not ((finite >= 0).all() and (finite <= 1).all()):
            print(f"[FAIL] {col} contains values outside [0, 1]")
            return 1

    print(f"[OK] validated {summary_path.relative_to(ROOT)} with {len(summary)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
