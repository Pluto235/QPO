#!/usr/bin/env python3
"""Fetch Mrk 421 ASAS-SN Sky Patrol light curves for the LHAASO/WCDA window."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.project_paths import MULTIWAVELENGTH_DIR, PROJECT_ROOT  # noqa: E402


DEFAULT_RA_DEG = 166.11383
DEFAULT_DEC_DEG = 38.20883
DEFAULT_RADIUS_ARCSEC = 2.0
DEFAULT_ASASSN_ID = 128849645138
DEFAULT_MJD_MIN = 59281.0
DEFAULT_MJD_MAX = 61129.0
JD_MINUS_MJD = 2400000.5
OUTPUT_DIR = MULTIWAVELENGTH_DIR / "mkn421" / "optical_lhaaso_2021_2026"
OUTPUT_CSV = OUTPUT_DIR / "asassn_skypatrol_mkn421.csv"
INDEX_CSV = OUTPUT_DIR / "asassn_skypatrol_index.csv"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ra-deg", type=float, default=DEFAULT_RA_DEG)
    parser.add_argument("--dec-deg", type=float, default=DEFAULT_DEC_DEG)
    parser.add_argument("--radius-arcsec", type=float, default=DEFAULT_RADIUS_ARCSEC)
    parser.add_argument("--asas-sn-id", type=int, default=DEFAULT_ASASSN_ID)
    parser.add_argument("--mjd-min", type=float, default=DEFAULT_MJD_MIN)
    parser.add_argument("--mjd-max", type=float, default=DEFAULT_MJD_MAX)
    parser.add_argument("--output-csv", type=Path, default=OUTPUT_CSV)
    parser.add_argument("--index-csv", type=Path, default=INDEX_CSV)
    parser.add_argument(
        "--resolve-only",
        action="store_true",
        help="Only resolve the Sky Patrol ID near the supplied coordinates.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    output_csv = _project_path(args.output_csv)
    index_csv = _project_path(args.index_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    index_csv.parent.mkdir(parents=True, exist_ok=True)

    try:
        from pyasassn.client import SkyPatrolClient
    except ImportError as exc:
        raise SystemExit(
            "Missing ASAS-SN client. Install it with:\n"
            "/Users/luoji/miniconda3/envs/py310/bin/python -m pip install pyarrow==16.1.0 skypatrol==0.6.21"
        ) from exc

    client = SkyPatrolClient(verbose=False)
    index = client.cone_search(
        args.ra_deg,
        args.dec_deg,
        radius=args.radius_arcsec,
        units="arcsec",
        catalog="master_list",
    )
    index.to_csv(index_csv, index=False)
    print(f"[OK] ASAS-SN index: {index_csv.relative_to(PROJECT_ROOT)}")
    print(index.to_string(index=False))

    if args.resolve_only:
        return

    if args.asas_sn_id not in set(index["asas_sn_id"].astype(int)):
        print(
            f"[WARN] requested ASAS-SN id {args.asas_sn_id} is not in the "
            f"{args.radius_arcsec:g} arcsec cone-search result.",
            file=sys.stderr,
        )

    collection = client.query_list(
        [args.asas_sn_id],
        catalog="master_list",
        id_col="asas_sn_id",
        download=True,
        threads=1,
    )
    light_curve = collection[args.asas_sn_id].data.copy()
    light_curve.insert(0, "source_id", "mkn421")
    light_curve.insert(1, "survey", "ASAS-SN Sky Patrol")
    light_curve["mjd"] = light_curve["jd"].astype(float) - JD_MINUS_MJD
    light_curve = light_curve[(light_curve["mjd"] >= args.mjd_min) & (light_curve["mjd"] <= args.mjd_max)]
    light_curve = normalize_column_order(light_curve)
    light_curve.to_csv(output_csv, index=False)

    print(f"[OK] ASAS-SN light curve: {output_csv.relative_to(PROJECT_ROOT)}")
    print(f"[OK] rows={len(light_curve)}")
    if not light_curve.empty:
        print(f"[OK] MJD range={light_curve['mjd'].min():.4f}--{light_curve['mjd'].max():.4f}")
        print(f"[OK] filters={light_curve['phot_filter'].value_counts(dropna=False).to_dict()}")
        print(f"[OK] quality={light_curve['quality'].value_counts(dropna=False).to_dict()}")


def normalize_column_order(frame: pd.DataFrame) -> pd.DataFrame:
    preferred = [
        "source_id",
        "survey",
        "asas_sn_id",
        "mjd",
        "jd",
        "phot_filter",
        "mag",
        "mag_err",
        "flux",
        "flux_err",
        "limit",
        "fwhm",
        "image_id",
        "camera",
        "quality",
    ]
    cols = [col for col in preferred if col in frame.columns]
    cols.extend(col for col in frame.columns if col not in cols)
    return frame[cols].sort_values("mjd").reset_index(drop=True)


def _project_path(path: Path) -> Path:
    path = path.expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


if __name__ == "__main__":
    main()
