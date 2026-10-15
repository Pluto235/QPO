#!/usr/bin/env python3
"""Build a lightweight provenance manifest from official WCDA LC DataConfigs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.official_lc import EXPECTED_BIN_COUNTS, read_all_official_lc_bins
from utils.project_paths import OFFICIAL_QPO_FIXTURE_DIR, OFFICIAL_QPO_MANIFEST_DIR, PROJECT_ROOT


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-root",
        type=Path,
        default=OFFICIAL_QPO_FIXTURE_DIR / "official_lc_configs",
        help="Directory containing 2Days/, 8Days/, and 32Days/ official DataConfigs.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=OFFICIAL_QPO_MANIFEST_DIR / "official_lc_config_manifest.csv",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=OFFICIAL_QPO_MANIFEST_DIR / "official_lc_config_manifest.json",
    )
    return parser.parse_args(argv)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _collection_sha256(config_root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(config_root.glob("*Days/Data_LC_*.yaml")):
        digest.update(path.relative_to(config_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config_root = args.config_root if args.config_root.is_absolute() else PROJECT_ROOT / args.config_root
    output_csv = args.output_csv if args.output_csv.is_absolute() else PROJECT_ROOT / args.output_csv
    output_json = args.output_json if args.output_json.is_absolute() else PROJECT_ROOT / args.output_json

    bins = read_all_official_lc_bins(config_root)
    rows = [item.as_manifest_row() for item in bins]
    frame = pd.DataFrame(rows).sort_values(["cadence_days", "lc_id"]).reset_index(drop=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_csv, index=False)

    summary = {
        "schema_version": "official_qpo_lc_config_manifest_v1",
        "config_root": str(config_root),
        "collection_sha256": _collection_sha256(config_root),
        "master_config_sha256": _file_sha256(config_root / "LCData_20210305_20250731.yaml"),
        "expected_counts": EXPECTED_BIN_COUNTS,
        "observed_counts": {
            str(cadence): int((frame["cadence_days"] == cadence).sum()) for cadence in EXPECTED_BIN_COUNTS
        },
        "total_bins": int(len(frame)),
        "csv": str(output_csv),
    }
    output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[OK] wrote {len(frame)} official config rows -> {output_csv.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
