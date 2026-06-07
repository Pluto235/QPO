#!/usr/bin/env python3
"""Build exploratory Mrk 421 optical/UV-LHAASO 2021-2026 synchronization plots."""

from __future__ import annotations

import argparse
import io
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from methods.periodicity import read_wcda_counts_csv, usable_light_curve  # noqa: E402
from utils.project_paths import MULTIWAVELENGTH_DIR, PROJECT_ROOT, WCDA_WEEK_DIR  # noqa: E402


OUTPUT_DIR = MULTIWAVELENGTH_DIR / "mkn421" / "optical_lhaaso_2021_2026"
REPORT_MD = PROJECT_ROOT / "reports" / "mkn421_optical_uv_lhaaso_2021_2026_sync.md"
DEFAULT_WCDA_WEEK = WCDA_WEEK_DIR / "LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv"

ATLAS_CSV = OUTPUT_DIR / "atlas_forced_photometry.csv"
ASASSN_CSV = OUTPUT_DIR / "asassn_skypatrol_mkn421.csv"
ZTF_CACHE = OUTPUT_DIR / "ztf_public_lc.csv"
AAVSO_CACHE = OUTPUT_DIR / "aavso_vsx_full_window.csv"
CDS_CACHE = OUTPUT_DIR / "cds_aa684_a127_fig1.csv"
UNIFIED_CSV = OUTPUT_DIR / "optical_uv_flux_points.csv"
QC_CSV = OUTPUT_DIR / "optical_uv_quality_summary.csv"
SYNC_PNG = OUTPUT_DIR / "mkn421_optical_uv_lhaaso_2021_2026_weekly.png"

DEFAULT_MJD_MIN = 59284.333
DEFAULT_MJD_MAX = 61125.167
JD_MINUS_MJD = 2400000.5

MRK421_RA_DEG = 166.11383
MRK421_DEC_DEG = 38.20883
ZTF_BASE_URL = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"
ZTF_BANDS = ("g", "r", "i")
AAVSO_URL = (
    "https://www.aavso.org/vsx/index.php?"
    "view=api.object&ident=000-BBR-960&data=100000&fromjd=2459284.833&tojd=2461125.667&csv"
)
CDS_FIG1_URL = "https://cdsarc.cds.unistra.fr/ftp/J/A+A/684/A127/fig1.dat"
CDS_README_URL = "https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/A+A/684/A127?format=html&tex=true"

OPTICAL_QUALITY_RULES = {
    "ATLAS": "uJy > 0, duJy > 0, and uJy/duJy >= 5",
    "ASAS-SN Sky Patrol": 'quality == "G" with finite g magnitude',
    "ZTF public": "IRSA query uses BAD_CATFLAGS_MASK=32768; finite mag/magerr retained",
    "AAVSO": "non-upper-limit points retained; Visual plotted with low alpha",
    "CDS/VizieR A&A 684 A127": "R-band and Swift-UVOT W1/M2/W2 mJy rows from fig1.dat",
}

ZERO_POINT_JY = {
    "B": 4063.0,
    "V": 3636.0,
    "R": 3064.0,
    "CR": 3064.0,
    "CV": 3636.0,
    "Vis.": 3636.0,
    "TG": 3631.0,
    "g": 3631.0,
    "r": 3631.0,
    "i": 3631.0,
    "zg": 3631.0,
    "zr": 3631.0,
    "zi": 3631.0,
}


@dataclass(frozen=True)
class OpticalProducts:
    flux_points: pd.DataFrame
    quality_summary: pd.DataFrame
    wcda_points: int
    wcda_mjd_range: tuple[float, float]
    plot_window: tuple[float, float]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-md", type=Path, default=REPORT_MD)
    parser.add_argument("--wcda-week", type=Path, default=DEFAULT_WCDA_WEEK)
    parser.add_argument("--atlas-csv", type=Path, default=ATLAS_CSV)
    parser.add_argument("--asassn-csv", type=Path, default=ASASSN_CSV)
    parser.add_argument("--ztf-cache", type=Path, default=ZTF_CACHE)
    parser.add_argument("--aavso-cache", type=Path, default=AAVSO_CACHE)
    parser.add_argument("--cds-cache", type=Path, default=CDS_CACHE)
    parser.add_argument("--unified-csv", type=Path, default=UNIFIED_CSV)
    parser.add_argument("--qc-csv", type=Path, default=QC_CSV)
    parser.add_argument("--sync-png", type=Path, default=SYNC_PNG)
    parser.add_argument("--mjd-min", type=float, default=DEFAULT_MJD_MIN)
    parser.add_argument("--mjd-max", type=float, default=DEFAULT_MJD_MAX)
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Refresh public ZTF/AAVSO/CDS caches instead of reusing existing files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    output_dir = _project_path(args.output_dir)
    report_md = _project_path(args.report_md)
    wcda_week = _project_path(args.wcda_week)
    atlas_csv = _project_path(args.atlas_csv)
    asassn_csv = _project_path(args.asassn_csv)
    ztf_cache = _project_path(args.ztf_cache)
    aavso_cache = _project_path(args.aavso_cache)
    cds_cache = _project_path(args.cds_cache)
    unified_csv = _project_path(args.unified_csv)
    qc_csv = _project_path(args.qc_csv)
    sync_png = _project_path(args.sync_png)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_md.parent.mkdir(parents=True, exist_ok=True)

    atlas = _read_required_csv(atlas_csv, "ATLAS forced-photometry CSV")
    asassn = _read_required_csv(asassn_csv, "ASAS-SN Sky Patrol CSV")
    ztf = load_ztf_public(ztf_cache, force_download=args.force_download)
    aavso = load_aavso_vsx(aavso_cache, force_download=args.force_download)
    cds = load_cds_fig1(cds_cache, force_download=args.force_download)
    wcda = load_wcda_weekly(wcda_week)

    products = build_products(
        atlas=atlas,
        asassn=asassn,
        ztf=ztf,
        aavso=aavso,
        cds=cds,
        wcda=wcda,
        mjd_window=(args.mjd_min, args.mjd_max),
    )
    products.flux_points.to_csv(unified_csv, index=False)
    products.quality_summary.to_csv(qc_csv, index=False)
    plot_sync_figure(
        sync_png,
        flux_points=products.flux_points,
        wcda=wcda,
        plot_window=products.plot_window,
    )
    report_md.write_text(
        build_report(
            products=products,
            atlas_csv=atlas_csv,
            asassn_csv=asassn_csv,
            ztf_cache=ztf_cache,
            aavso_cache=aavso_cache,
            cds_cache=cds_cache,
            unified_csv=unified_csv,
            qc_csv=qc_csv,
            sync_png=sync_png,
            wcda_week=wcda_week,
            report_md=report_md,
        ),
        encoding="utf-8",
    )

    print(f"[OK] ZTF cache: {ztf_cache.relative_to(PROJECT_ROOT)} rows={len(ztf)}")
    print(f"[OK] AAVSO cache: {aavso_cache.relative_to(PROJECT_ROOT)} rows={len(aavso)}")
    print(f"[OK] CDS fig1 cache: {cds_cache.relative_to(PROJECT_ROOT)} rows={len(cds)}")
    print(f"[OK] unified optical/UV points: {unified_csv.relative_to(PROJECT_ROOT)} rows={len(products.flux_points)}")
    print(f"[OK] quality summary: {qc_csv.relative_to(PROJECT_ROOT)}")
    print(f"[OK] sync plot: {sync_png.relative_to(PROJECT_ROOT)}")
    print(f"[OK] report: {report_md.relative_to(PROJECT_ROOT)}")
    print(
        "[OK] plotted point counts: "
        + ", ".join(
            f"{row.survey} {row.band}={int(row.plotted_rows)}"
            for row in products.quality_summary.itertuples()
            if int(row.plotted_rows) > 0
        )
    )


def load_ztf_public(cache_path: Path, *, force_download: bool) -> pd.DataFrame:
    if cache_path.exists() and not force_download:
        return pd.read_csv(cache_path)

    rows: list[pd.DataFrame] = []
    for band in ZTF_BANDS:
        params = {
            "POS": f"CIRCLE {MRK421_RA_DEG:.4f} {MRK421_DEC_DEG:.4f} 0.0028",
            "BANDNAME": band,
            "NOBS_MIN": 3,
            "TIME": f"{DEFAULT_MJD_MIN:.3f} {DEFAULT_MJD_MAX:.3f}",
            "BAD_CATFLAGS_MASK": 32768,
            "FORMAT": "CSV",
        }
        url = f"{ZTF_BASE_URL}?{urlencode(params)}"
        try:
            with urlopen(url, timeout=90) as response:
                text = response.read().decode("utf-8", errors="replace")
        except (OSError, URLError) as exc:
            if cache_path.exists():
                print(f"[WARN] ZTF fetch failed for {band}; using cached table: {exc}", file=sys.stderr)
                return pd.read_csv(cache_path)
            raise RuntimeError(f"Could not fetch ZTF {band}-band light curve and no cache exists: {url}") from exc
        frame = pd.read_csv(io.StringIO(text))
        frame.insert(0, "query_band", band)
        frame.insert(1, "source_id", "mkn421")
        frame.insert(2, "survey", "ZTF public")
        frame.insert(3, "source_url", url)
        rows.append(frame)

    ztf = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    ztf.to_csv(cache_path, index=False)
    return ztf


def load_aavso_vsx(cache_path: Path, *, force_download: bool) -> pd.DataFrame:
    if cache_path.exists() and not force_download:
        return pd.read_csv(cache_path)

    try:
        with urlopen(AAVSO_URL, timeout=120) as response:
            text = response.read().decode("utf-8", errors="replace")
    except (OSError, URLError) as exc:
        if cache_path.exists():
            print(f"[WARN] AAVSO fetch failed; using cached table: {exc}", file=sys.stderr)
            return pd.read_csv(cache_path)
        raise RuntimeError(f"Could not fetch AAVSO VSX data and no cache exists: {AAVSO_URL}") from exc

    root = ET.fromstring(text)
    csv_text = root.findtext("Data")
    if not csv_text:
        raise RuntimeError("AAVSO VSX response did not contain a Data CSV payload.")
    aavso = pd.read_csv(io.StringIO(csv_text))
    aavso.insert(0, "source_id", "mkn421")
    aavso.insert(1, "survey", "AAVSO")
    aavso.insert(2, "source_url", AAVSO_URL)
    aavso["mjd"] = pd.to_numeric(aavso["JD"], errors="coerce") - JD_MINUS_MJD
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    aavso.to_csv(cache_path, index=False)
    return aavso


def load_cds_fig1(cache_path: Path, *, force_download: bool) -> pd.DataFrame:
    if cache_path.exists() and not force_download:
        return pd.read_csv(cache_path)

    try:
        with urlopen(CDS_FIG1_URL, timeout=90) as response:
            text = response.read().decode("utf-8", errors="replace")
    except (OSError, URLError) as exc:
        if cache_path.exists():
            print(f"[WARN] CDS fetch failed; using cached table: {exc}", file=sys.stderr)
            return pd.read_csv(cache_path)
        raise RuntimeError(f"Could not fetch CDS fig1.dat and no cache exists: {CDS_FIG1_URL}") from exc

    cds = parse_cds_fig1(text)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cds.to_csv(cache_path, index=False)
    return cds


def parse_cds_fig1(text: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        mjd = _parse_float(line[0:10])
        value = _parse_float(line[16:24])
        error = _parse_float(line[32:40])
        band = line[48:58].strip()
        instrument = line[64:74].strip()
        unit = line[80:110].strip()
        if mjd is None or value is None or error is None:
            continue
        rows.append(
            {
                "source_id": "mkn421",
                "survey": "CDS/VizieR A&A 684 A127",
                "mjd": mjd,
                "value": value,
                "value_err": error,
                "band": band,
                "instrument": instrument,
                "unit": unit,
                "source_catalog": "CDS/VizieR J/A+A/684/A127 fig1.dat",
                "source_url": CDS_FIG1_URL,
            }
        )
    if not rows:
        raise ValueError("No numeric rows found in CDS fig1.dat.")
    return pd.DataFrame(rows).sort_values(["mjd", "band", "instrument"]).reset_index(drop=True)


def load_wcda_weekly(wcda_path: Path) -> pd.DataFrame:
    if not wcda_path.exists():
        raise FileNotFoundError(f"Missing WCDA weekly input: {wcda_path}")
    wcda = read_wcda_counts_csv(wcda_path)
    return usable_light_curve(wcda, "flux_excess", "flux_excess_err")


def build_products(
    *,
    atlas: pd.DataFrame,
    asassn: pd.DataFrame,
    ztf: pd.DataFrame,
    aavso: pd.DataFrame,
    cds: pd.DataFrame,
    wcda: pd.DataFrame,
    mjd_window: tuple[float, float],
) -> OpticalProducts:
    normalized_frames: list[pd.DataFrame] = []
    raw_counts: dict[tuple[str, str, str], int] = {}

    atlas_points = normalize_atlas(atlas, mjd_window=mjd_window)
    normalized_frames.append(atlas_points)
    raw_counts.update(_raw_counts(atlas, "ATLAS", "optical", "F", mjd_window=mjd_window))

    asassn_points = normalize_asassn(asassn, mjd_window=mjd_window)
    normalized_frames.append(asassn_points)
    raw_counts.update(_raw_counts(asassn, "ASAS-SN Sky Patrol", "optical", "phot_filter", mjd_window=mjd_window))

    ztf_points = normalize_ztf(ztf, mjd_window=mjd_window)
    normalized_frames.append(ztf_points)
    raw_counts.update(_raw_counts(ztf, "ZTF public", "optical", "filtercode", mjd_window=mjd_window))

    aavso_points = normalize_aavso(aavso, mjd_window=mjd_window)
    normalized_frames.append(aavso_points)
    raw_counts.update(_raw_counts(aavso, "AAVSO", "optical", "band", mjd_window=mjd_window))

    cds_points = normalize_cds(cds, mjd_window=mjd_window)
    normalized_frames.append(cds_points)
    raw_counts.update(_raw_counts(cds.loc[cds["band"].isin(["R-band"])], "CDS/VizieR A&A 684 A127", "optical", "band", mjd_window=mjd_window))
    raw_counts.update(_raw_counts(cds.loc[cds["band"].isin(["W1", "M2", "W2"])], "CDS/VizieR A&A 684 A127", "near-UV", "band", mjd_window=mjd_window))

    flux_points = (
        pd.concat([frame for frame in normalized_frames if not frame.empty], ignore_index=True)
        if any(not frame.empty for frame in normalized_frames)
        else pd.DataFrame(columns=_flux_columns())
    )
    flux_points = flux_points[_flux_columns()].sort_values(["panel", "survey", "band", "mjd"]).reset_index(drop=True)
    quality_summary = build_quality_summary(flux_points, raw_counts)

    wcda_window = _windowed(wcda, mjd_window)
    if wcda_window.empty:
        raise ValueError(f"No finite WCDA weekly points in MJD {mjd_window[0]:.3f}-{mjd_window[1]:.3f}")

    return OpticalProducts(
        flux_points=flux_points,
        quality_summary=quality_summary,
        wcda_points=len(wcda_window),
        wcda_mjd_range=(float(wcda_window["mjd"].min()), float(wcda_window["mjd"].max())),
        plot_window=mjd_window,
    )


def normalize_atlas(atlas: pd.DataFrame, *, mjd_window: tuple[float, float]) -> pd.DataFrame:
    frame = atlas.copy()
    frame["mjd"] = pd.to_numeric(frame["mjd"], errors="coerce")
    frame["uJy"] = pd.to_numeric(frame["uJy"], errors="coerce")
    frame["duJy"] = pd.to_numeric(frame["duJy"], errors="coerce")
    frame["m"] = pd.to_numeric(frame.get("m"), errors="coerce")
    frame["dm"] = pd.to_numeric(frame.get("dm"), errors="coerce")
    frame["snr"] = frame["uJy"] / frame["duJy"]
    mask = (
        frame["mjd"].between(*mjd_window)
        & frame["F"].isin(["c", "o"])
        & np.isfinite(frame["uJy"])
        & np.isfinite(frame["duJy"])
        & (frame["uJy"] > 0)
        & (frame["duJy"] > 0)
        & (frame["snr"] >= 5.0)
    )
    sub = frame.loc[mask].copy()
    return _make_flux_frame(
        source="ATLAS",
        instrument="ATLAS forced photometry",
        panel="optical",
        band=sub["F"].astype(str),
        mjd=sub["mjd"],
        flux_mjy=sub["uJy"] / 1000.0,
        flux_err_mjy=sub["duJy"] / 1000.0,
        mag=sub["m"],
        mag_err=sub["dm"],
        quality_rule=OPTICAL_QUALITY_RULES["ATLAS"],
        source_url="https://fallingstar-data.com/forcedphot/apiguide/",
        note="ATLAS forced-flux points; negative forced fluxes excluded from the main plot.",
    )


def normalize_asassn(asassn: pd.DataFrame, *, mjd_window: tuple[float, float]) -> pd.DataFrame:
    frame = asassn.copy()
    frame["mjd"] = pd.to_numeric(frame["mjd"], errors="coerce")
    frame["mag"] = pd.to_numeric(frame["mag"], errors="coerce")
    frame["mag_err"] = pd.to_numeric(frame["mag_err"], errors="coerce")
    mask = (
        frame["mjd"].between(*mjd_window)
        & frame["quality"].eq("G")
        & frame["phot_filter"].eq("g")
        & np.isfinite(frame["mag"])
    )
    sub = frame.loc[mask].copy()
    flux = mag_to_mjy(sub["mag"], "g")
    return _make_flux_frame(
        source="ASAS-SN Sky Patrol",
        instrument="ASAS-SN Sky Patrol",
        panel="optical",
        band=sub["phot_filter"].astype(str),
        mjd=sub["mjd"],
        flux_mjy=flux,
        flux_err_mjy=mag_err_to_flux_err_mjy(flux, sub["mag_err"]),
        mag=sub["mag"],
        mag_err=sub["mag_err"],
        quality_rule=OPTICAL_QUALITY_RULES["ASAS-SN Sky Patrol"],
        source_url="https://asas-sn.github.io/skypatrol/lightcurves.html",
        note="ASAS-SN g magnitudes converted to approximate mJy for quick-look plotting.",
    )


def normalize_ztf(ztf: pd.DataFrame, *, mjd_window: tuple[float, float]) -> pd.DataFrame:
    frame = ztf.copy()
    frame["mjd"] = pd.to_numeric(frame["mjd"], errors="coerce")
    frame["mag"] = pd.to_numeric(frame["mag"], errors="coerce")
    frame["magerr"] = pd.to_numeric(frame["magerr"], errors="coerce")
    mask = (
        frame["mjd"].between(*mjd_window)
        & frame["filtercode"].isin(["zg", "zr", "zi"])
        & np.isfinite(frame["mag"])
        & np.isfinite(frame["magerr"])
    )
    sub = frame.loc[mask].copy()
    flux = mag_to_mjy(sub["mag"], sub["filtercode"])
    return _make_flux_frame(
        source="ZTF public",
        instrument="ZTF public light-curve API",
        panel="optical",
        band=sub["filtercode"].astype(str),
        mjd=sub["mjd"],
        flux_mjy=flux,
        flux_err_mjy=mag_err_to_flux_err_mjy(flux, sub["magerr"]),
        mag=sub["mag"],
        mag_err=sub["magerr"],
        quality_rule=OPTICAL_QUALITY_RULES["ZTF public"],
        source_url="https://irsa.ipac.caltech.edu/docs/program_interface/ztf_lightcurve_api.html",
        note="ZTF public PSF magnitudes converted to approximate mJy.",
    )


def normalize_aavso(aavso: pd.DataFrame, *, mjd_window: tuple[float, float]) -> pd.DataFrame:
    frame = aavso.copy()
    frame["mjd"] = pd.to_numeric(frame["mjd"], errors="coerce")
    frame["mag"] = pd.to_numeric(frame["mag"], errors="coerce")
    frame["uncert"] = pd.to_numeric(frame["uncert"], errors="coerce")
    frame["fainterThan"] = pd.to_numeric(frame["fainterThan"], errors="coerce").fillna(0)
    mask = (
        frame["mjd"].between(*mjd_window)
        & np.isfinite(frame["mag"])
        & (frame["fainterThan"] == 0)
        & frame["band"].notna()
    )
    sub = frame.loc[mask].copy()
    flux = mag_to_mjy(sub["mag"], sub["band"])
    note = np.where(
        sub["band"].eq("Vis."),
        "AAVSO Visual points are approximate and plotted with low alpha.",
        "AAVSO CCD/DSLR points converted to approximate mJy by reported band.",
    )
    return _make_flux_frame(
        source="AAVSO",
        instrument=sub["obsType"].fillna("AAVSO").astype(str),
        panel="optical",
        band=sub["band"].astype(str),
        mjd=sub["mjd"],
        flux_mjy=flux,
        flux_err_mjy=mag_err_to_flux_err_mjy(flux, sub["uncert"]),
        mag=sub["mag"],
        mag_err=sub["uncert"],
        quality_rule=OPTICAL_QUALITY_RULES["AAVSO"],
        source_url="https://www.aavso.org/vsx/index.php?view=api.object&ident=MRK%20421&format=json",
        note=note,
    )


def normalize_cds(cds: pd.DataFrame, *, mjd_window: tuple[float, float]) -> pd.DataFrame:
    frame = cds.copy()
    frame["mjd"] = pd.to_numeric(frame["mjd"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame["value_err"] = pd.to_numeric(frame["value_err"], errors="coerce")
    mask = (
        frame["mjd"].between(*mjd_window)
        & frame["band"].isin(["R-band", "W1", "M2", "W2"])
        & frame["unit"].eq("mJy")
        & np.isfinite(frame["value"])
        & np.isfinite(frame["value_err"])
    )
    sub = frame.loc[mask].copy()
    panel = np.where(sub["band"].eq("R-band"), "optical", "near-UV")
    return _make_flux_frame(
        source="CDS/VizieR A&A 684 A127",
        instrument=sub["instrument"].astype(str),
        panel=panel,
        band=sub["band"].astype(str),
        mjd=sub["mjd"],
        flux_mjy=sub["value"],
        flux_err_mjy=sub["value_err"],
        mag=np.nan,
        mag_err=np.nan,
        quality_rule=OPTICAL_QUALITY_RULES["CDS/VizieR A&A 684 A127"],
        source_url=CDS_FIG1_URL,
        note="CDS fig1.dat values are already provided in mJy.",
    )


def build_quality_summary(
    flux_points: pd.DataFrame,
    raw_counts: dict[tuple[str, str, str], int],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for survey, panel, band in sorted(raw_counts):
        sub = flux_points.loc[
            (flux_points["survey"] == survey)
            & (flux_points["panel"] == panel)
            & (flux_points["band"] == band)
        ]
        rows.append(
            {
                "survey": survey,
                "panel": panel,
                "band": band,
                "input_rows": int(raw_counts[(survey, panel, band)]),
                "plotted_rows": int(len(sub)),
                "mjd_min": _finite_min(sub["mjd"]) if not sub.empty else np.nan,
                "mjd_max": _finite_max(sub["mjd"]) if not sub.empty else np.nan,
                "flux_min_mjy": _finite_min(sub["flux_mjy"]) if not sub.empty else np.nan,
                "flux_max_mjy": _finite_max(sub["flux_mjy"]) if not sub.empty else np.nan,
                "quality_rule": OPTICAL_QUALITY_RULES.get(survey, ""),
            }
        )
    return pd.DataFrame(rows)


def plot_sync_figure(
    path: Path,
    *,
    flux_points: pd.DataFrame,
    wcda: pd.DataFrame,
    plot_window: tuple[float, float],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    wcda_window = _windowed(wcda, plot_window)
    optical = flux_points.loc[flux_points["panel"] == "optical"]
    uv = flux_points.loc[flux_points["panel"] == "near-UV"]

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(13.5, 9.2),
        sharex=True,
        constrained_layout=True,
        gridspec_kw={"height_ratios": [2.3, 1.35, 1.45]},
    )
    fig.suptitle("Mrk 421 optical/near-UV and LHAASO/WCDA weekly alignment (2021-2026)", fontsize=14)

    _plot_flux_panel(
        axes[0],
        optical,
        panel="optical",
        ylabel="Optical F_nu\nmJy (approx.)",
        max_errorbar_points=320,
    )
    axes[0].text(
        0.01,
        0.03,
        "Quick-look mJy: no host-galaxy subtraction, color correction, or cross-filter normalization.",
        transform=axes[0].transAxes,
        fontsize=8.5,
        color="#5a6876",
        va="bottom",
    )

    _plot_flux_panel(
        axes[1],
        uv,
        panel="near-UV",
        ylabel="Swift-UVOT F_nu\nmJy",
        max_errorbar_points=500,
    )

    ax_wcda = axes[2]
    ax_wcda.errorbar(
        wcda_window["mjd"],
        wcda_window["flux_excess"],
        yerr=wcda_window["flux_excess_err"],
        fmt="o-",
        ms=3.0,
        lw=1.0,
        color="#245c9f",
        ecolor="#7da0c9",
        capsize=2,
        label=f"WCDA weekly ({len(wcda_window)} points)",
    )
    ax_wcda.axhline(0.0, color="#7a7a7a", lw=0.8, alpha=0.6)
    ax_wcda.set_ylabel("WCDA excess-rate proxy\ncounts / s")
    ax_wcda.legend(loc="upper left", frameon=False, fontsize=8.5)
    ax_wcda.grid(True, alpha=0.25)

    axes[-1].set_xlabel("MJD")
    axes[-1].set_xlim(plot_window)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def _plot_flux_panel(
    ax: plt.Axes,
    frame: pd.DataFrame,
    *,
    panel: str,
    ylabel: str,
    max_errorbar_points: int,
) -> None:
    if frame.empty:
        ax.text(0.5, 0.5, f"No {panel} points", transform=ax.transAxes, ha="center", va="center")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.25)
        return

    for (survey, band), sub in frame.groupby(["survey", "band"], sort=True):
        sub = sub.sort_values("mjd")
        style = _plot_style(survey, band)
        label = f"{survey_short_label(survey)} {band} ({len(sub)})"
        yerr = sub["flux_err_mjy"] if len(sub) <= max_errorbar_points and sub["flux_err_mjy"].notna().any() else None
        if yerr is not None:
            ax.errorbar(
                sub["mjd"],
                sub["flux_mjy"],
                yerr=yerr,
                fmt=style["marker"],
                ms=style["ms"],
                lw=0.0,
                elinewidth=0.6,
                color=style["color"],
                ecolor=style["color"],
                alpha=style["alpha"],
                capsize=1.5,
                label=label,
                zorder=style["zorder"],
            )
        else:
            ax.scatter(
                sub["mjd"],
                sub["flux_mjy"],
                s=style["size"],
                marker=style["marker"],
                color=style["color"],
                alpha=style["alpha"],
                label=label,
                zorder=style["zorder"],
                linewidths=0.0,
            )

    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left", bbox_to_anchor=(1.005, 1.0), frameon=False, fontsize=7.5)


def build_report(
    *,
    products: OpticalProducts,
    atlas_csv: Path,
    asassn_csv: Path,
    ztf_cache: Path,
    aavso_cache: Path,
    cds_cache: Path,
    unified_csv: Path,
    qc_csv: Path,
    sync_png: Path,
    wcda_week: Path,
    report_md: Path,
) -> str:
    optical_points = int((products.flux_points["panel"] == "optical").sum())
    uv_points = int((products.flux_points["panel"] == "near-UV").sum())
    lines = [
        "# Mrk 421 Optical/UV-LHAASO 2021-2026 Alignment",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "This quick-look aligns public optical and near-UV monitoring points with the local LHAASO/WCDA weekly excess-rate proxy. It is exploratory only and reports no DCF, FAP, correlation coefficient, lag, or optical QPO significance.",
        "",
        "## Data Sources",
        "",
        f"- ATLAS forced photometry cache: `{_rel(atlas_csv)}`.",
        f"- ASAS-SN Sky Patrol cache: `{_rel(asassn_csv)}`.",
        f"- ZTF public light-curve cache: `{_rel(ztf_cache)}`.",
        f"- AAVSO VSX export cache: `{_rel(aavso_cache)}`.",
        f"- CDS/VizieR A&A 684 A127 fig1 cache: `{_rel(cds_cache)}`; ReadMe: [{CDS_README_URL}]({CDS_README_URL}).",
        f"- WCDA weekly input: `{_rel(wcda_week)}`.",
        "",
        "## Coverage",
        "",
        f"- Plotted MJD window: {products.plot_window[0]:.3f}-{products.plot_window[1]:.3f}.",
        f"- Finite WCDA weekly points in plotted window: {products.wcda_points} (MJD {products.wcda_mjd_range[0]:.3f}-{products.wcda_mjd_range[1]:.3f}).",
        f"- Plotted optical points: {optical_points}.",
        f"- Plotted near-UV points: {uv_points}.",
        f"- Unified quick-look flux table: `{_rel(unified_csv)}`.",
        f"- Quality and coverage summary: `{_rel(qc_csv)}`.",
        "",
        "## Quality Summary",
        "",
        _markdown_table(products.quality_summary),
        "",
        "## Figure",
        "",
        f"![Mrk 421 optical/UV-LHAASO alignment]({_report_rel(sync_png, report_md.parent)})",
        "",
        "## Notes",
        "",
        "- Optical magnitudes are converted to approximate flux density in mJy for quick-look plotting. The plot does not apply host-galaxy subtraction, color correction, cross-filter normalization, or SED modeling.",
        "- AAVSO Visual points are retained with low alpha to preserve cadence context without giving them the same visual weight as CCD/DSLR/filter photometry.",
        "- CDS R-band is plotted with the optical points; Swift-UVOT W1/M2/W2 are plotted in a separate near-UV panel.",
        "- WCDA values use the project proxy `flux_excess = sum(n_on - n_bkg) / tobs`; they are not calibrated physical gamma-ray fluxes and are not plotted on the optical mJy axis.",
        "",
    ]
    return "\n".join(lines)


def mag_to_mjy(mag: pd.Series, band: str | pd.Series) -> pd.Series:
    mag = pd.to_numeric(mag, errors="coerce")
    if isinstance(band, pd.Series):
        zero_jy = band.astype(str).map(lambda value: ZERO_POINT_JY.get(value, 3631.0))
    else:
        zero_jy = ZERO_POINT_JY.get(str(band), 3631.0)
    return zero_jy * 1000.0 * np.power(10.0, -0.4 * mag)


def mag_err_to_flux_err_mjy(flux_mjy: pd.Series, mag_err: pd.Series | float) -> pd.Series:
    err = pd.to_numeric(mag_err, errors="coerce")
    return pd.to_numeric(flux_mjy, errors="coerce") * np.log(10.0) * 0.4 * err


def _make_flux_frame(
    *,
    source: str,
    instrument: str | pd.Series | np.ndarray,
    panel: str | pd.Series | np.ndarray,
    band: pd.Series,
    mjd: pd.Series,
    flux_mjy: pd.Series,
    flux_err_mjy: pd.Series | float,
    mag: pd.Series | float,
    mag_err: pd.Series | float,
    quality_rule: str,
    source_url: str,
    note: str | pd.Series | np.ndarray,
) -> pd.DataFrame:
    n = len(mjd)
    return pd.DataFrame(
        {
            "source_id": ["mkn421"] * n,
            "survey": [source] * n,
            "instrument": _as_len(instrument, n),
            "panel": _as_len(panel, n),
            "band": band.to_numpy() if isinstance(band, pd.Series) else band,
            "mjd": pd.to_numeric(mjd, errors="coerce").to_numpy(),
            "flux_mjy": pd.to_numeric(flux_mjy, errors="coerce").to_numpy(),
            "flux_err_mjy": _numeric_as_len(flux_err_mjy, n),
            "mag": _numeric_as_len(mag, n),
            "mag_err": _numeric_as_len(mag_err, n),
            "quality_rule": [quality_rule] * n,
            "source_url": [source_url] * n,
            "note": _as_len(note, n),
        }
    )


def _flux_columns() -> list[str]:
    return [
        "source_id",
        "survey",
        "instrument",
        "panel",
        "band",
        "mjd",
        "flux_mjy",
        "flux_err_mjy",
        "mag",
        "mag_err",
        "quality_rule",
        "source_url",
        "note",
    ]


def _raw_counts(
    frame: pd.DataFrame,
    survey: str,
    panel: str,
    band_column: str,
    *,
    mjd_window: tuple[float, float],
) -> dict[tuple[str, str, str], int]:
    if frame.empty or band_column not in frame.columns:
        return {}
    local = frame.copy()
    if "mjd" in local.columns:
        local["mjd"] = pd.to_numeric(local["mjd"], errors="coerce")
        local = local.loc[local["mjd"].between(*mjd_window)]
    counts: dict[tuple[str, str, str], int] = {}
    for band, count in local[band_column].astype(str).value_counts(dropna=False).items():
        if band and band != "nan":
            counts[(survey, panel, band)] = int(count)
    return counts


def _plot_style(survey: str, band: str) -> dict[str, object]:
    styles = {
        ("ATLAS", "c"): {"color": "#159a9c", "marker": "o", "size": 10, "ms": 3.0, "alpha": 0.38, "zorder": 3},
        ("ATLAS", "o"): {"color": "#d58a00", "marker": "o", "size": 10, "ms": 3.0, "alpha": 0.34, "zorder": 3},
        ("ASAS-SN Sky Patrol", "g"): {"color": "#2b6cb0", "marker": "D", "size": 18, "ms": 3.3, "alpha": 0.62, "zorder": 5},
        ("ZTF public", "zg"): {"color": "#2f855a", "marker": "^", "size": 18, "ms": 3.3, "alpha": 0.62, "zorder": 5},
        ("ZTF public", "zr"): {"color": "#c53030", "marker": "v", "size": 18, "ms": 3.3, "alpha": 0.62, "zorder": 5},
        ("ZTF public", "zi"): {"color": "#975a16", "marker": "s", "size": 22, "ms": 3.5, "alpha": 0.68, "zorder": 5},
        ("AAVSO", "Vis."): {"color": "#606f7b", "marker": ".", "size": 8, "ms": 2.0, "alpha": 0.20, "zorder": 1},
        ("CDS/VizieR A&A 684 A127", "R-band"): {"color": "#111827", "marker": "*", "size": 42, "ms": 5.5, "alpha": 0.86, "zorder": 7},
        ("CDS/VizieR A&A 684 A127", "W1"): {"color": "#6b46c1", "marker": "o", "size": 20, "ms": 3.5, "alpha": 0.76, "zorder": 5},
        ("CDS/VizieR A&A 684 A127", "M2"): {"color": "#805ad5", "marker": "s", "size": 20, "ms": 3.5, "alpha": 0.76, "zorder": 5},
        ("CDS/VizieR A&A 684 A127", "W2"): {"color": "#9f7aea", "marker": "^", "size": 20, "ms": 3.5, "alpha": 0.76, "zorder": 5},
    }
    if survey == "AAVSO":
        fallback = {
            "B": "#3182ce",
            "V": "#38a169",
            "R": "#e53e3e",
            "CV": "#68d391",
            "CR": "#fc8181",
            "TG": "#2f855a",
        }
        return {
            "color": fallback.get(band, "#4a5568"),
            "marker": "x",
            "size": 18,
            "ms": 3.4,
            "alpha": 0.62,
            "zorder": 4,
        }
    return styles.get(
        (survey, band),
        {"color": "#4a5568", "marker": "o", "size": 16, "ms": 3.0, "alpha": 0.58, "zorder": 3},
    )


def survey_short_label(survey: str) -> str:
    labels = {
        "ASAS-SN Sky Patrol": "ASAS-SN",
        "CDS/VizieR A&A 684 A127": "CDS",
        "ZTF public": "ZTF",
    }
    return labels.get(survey, survey)


def _markdown_table(frame: pd.DataFrame) -> str:
    display = frame.copy()
    for col in ["mjd_min", "mjd_max"]:
        display[col] = display[col].map(lambda value: "" if pd.isna(value) else f"{float(value):.4f}")
    for col in ["flux_min_mjy", "flux_max_mjy"]:
        display[col] = display[col].map(lambda value: "" if pd.isna(value) else f"{float(value):.3f}")
    cols = [
        "survey",
        "panel",
        "band",
        "input_rows",
        "plotted_rows",
        "mjd_min",
        "mjd_max",
        "flux_min_mjy",
        "flux_max_mjy",
    ]
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = [
        "| " + " | ".join(str(row[col]) for col in cols) + " |"
        for _, row in display[cols].iterrows()
    ]
    return "\n".join([header, sep, *rows])


def _read_required_csv(path: Path, description: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {description}: {path}")
    return pd.read_csv(path)


def _as_len(value: str | pd.Series | np.ndarray, n: int) -> list[object] | np.ndarray:
    if isinstance(value, pd.Series):
        return value.to_numpy()
    if isinstance(value, np.ndarray):
        return value
    return [value] * n


def _numeric_as_len(value: pd.Series | float, n: int) -> np.ndarray:
    if isinstance(value, pd.Series):
        return pd.to_numeric(value, errors="coerce").to_numpy()
    return np.repeat(value, n).astype(float)


def _windowed(df: pd.DataFrame, window: tuple[float, float]) -> pd.DataFrame:
    return df.loc[(df["mjd"] >= window[0]) & (df["mjd"] <= window[1])].copy()


def _parse_float(value: str) -> float | None:
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _finite_min(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    return float(numeric.min())


def _finite_max(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    return float(numeric.max())


def _project_path(path: Path) -> Path:
    path = path.expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _report_rel(path: Path, report_dir: Path) -> str:
    return os.path.relpath(path, report_dir)


if __name__ == "__main__":
    main()
