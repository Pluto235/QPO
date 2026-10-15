#!/usr/bin/env python3
"""Validate and collect the official WCDA source-cadence QPO products."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipeline.official_lc_qpo_analysis import SIGNIFICANCE_COLUMNS  # noqa: E402
from utils.project_paths import PERIODICITY_DIR, PROJECT_ROOT  # noqa: E402


CADENCES = ("2day", "8day")
SOURCE_IDS = (
    "1es1727p502",
    "1es1959p650",
    "1es2344p514",
    "4c_p42d22",
    "bllacertae",
    "crab",
    "ic310",
    "m87",
    "mkn421",
    "mkn501",
    "ngc1275",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--periodicity-dir",
        type=Path,
        default=PERIODICITY_DIR / "official_lc_20260817",
    )
    parser.add_argument("--expected-time-divisions", type=int, default=80)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.periodicity_dir if args.periodicity_dir.is_absolute() else PROJECT_ROOT / args.periodicity_dir
    frames: list[pd.DataFrame] = []
    validations: list[dict[str, object]] = []

    for cadence in CADENCES:
        for source_id in SOURCE_IDS:
            source_dir = root / cadence / source_id
            stem = f"wcda_official_{cadence}"
            wwz_path = source_dir / f"{stem}_wwz.npz"
            significance_path = source_dir / f"{stem}_significance.csv"
            periodicity_path = source_dir / f"{stem}_periodicity.png"
            missing = [path for path in (wwz_path, significance_path, periodicity_path) if not path.is_file()]
            if missing:
                raise FileNotFoundError(f"Missing required products for {cadence}/{source_id}: {missing}")

            with np.load(wwz_path) as wwz:
                time_divisions = int(wwz["time_divisions"])
                frequency_bins = int(len(wwz["period_axis"]))
                wwz_shape = tuple(int(value) for value in wwz["wwz_mat"].shape)
                freq_step_factor = float(wwz["freq_step_factor"])
            if time_divisions != args.expected_time_divisions:
                raise ValueError(
                    f"{cadence}/{source_id} uses {time_divisions} WWZ time divisions; "
                    f"expected {args.expected_time_divisions}."
                )
            if wwz_shape != (time_divisions, frequency_bins):
                raise ValueError(f"Unexpected WWZ matrix shape for {cadence}/{source_id}: {wwz_shape}")

            frame = pd.read_csv(significance_path)
            missing_columns = sorted(set(SIGNIFICANCE_COLUMNS) - set(frame.columns))
            if missing_columns:
                raise ValueError(f"{significance_path} is missing columns: {missing_columns}")
            frames.append(frame.loc[:, SIGNIFICANCE_COLUMNS])
            validations.append(
                {
                    "cadence": cadence,
                    "source_id": source_id,
                    "time_divisions": time_divisions,
                    "frequency_bins": frequency_bins,
                    "wwz_rows": wwz_shape[0],
                    "wwz_columns": wwz_shape[1],
                    "freq_step_factor": freq_step_factor,
                    "candidate_rows": len(frame),
                }
            )

    summary_path = root / "official_lc_qpo_significance_summary.csv"
    validation_path = root / "official_lc_qpo_product_validation.csv"
    pd.concat(frames, ignore_index=True).to_csv(summary_path, index=False)
    pd.DataFrame(validations).to_csv(validation_path, index=False)
    print(f"[OK] validated {len(validations)}/22 source-cadence products")
    print(f"[OK] wrote {summary_path.relative_to(PROJECT_ROOT)}")
    print(f"[OK] wrote {validation_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
