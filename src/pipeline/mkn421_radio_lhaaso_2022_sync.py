#!/usr/bin/env python3
"""Build exploratory Mrk 421 2022 radio-LHAASO synchronization plots."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.error import URLError
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
from utils.project_paths import (  # noqa: E402
    MULTIWAVELENGTH_DIR,
    PROJECT_ROOT,
    WCDA_DAY_DIR,
    WCDA_WEEK_DIR,
)


CDS_FIG1_URL = "https://cdsarc.cds.unistra.fr/ftp/J/A+A/684/A127/fig1.dat"
CDS_README_URL = "https://cdsarc.cds.unistra.fr/ftp/J/A+A/684/A127/ReadMe"
OUTPUT_DIR = MULTIWAVELENGTH_DIR / "mkn421" / "radio_lhaaso_2022"
REPORT_MD = PROJECT_ROOT / "reports" / "mkn421_radio_lhaaso_2022_sync.md"
DEFAULT_WCDA_WEEK = WCDA_WEEK_DIR / "LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv"
DEFAULT_WCDA_DAY_2022 = WCDA_DAY_DIR / "LHAASO-WCDA_Mkn421_2022-04-15_2022-07-07_day.csv"
RADIO_CACHE = OUTPUT_DIR / "radio_2022_campaign.csv"
WEEKLY_PNG = OUTPUT_DIR / "mkn421_radio_lhaaso_2022_weekly.png"
DAILY_PNG = OUTPUT_DIR / "mkn421_radio_lhaaso_2022_daily.png"
WINDOW_PADDING_DAYS = 14.0
RADIO_BANDS = ("37GHz", "86GHz", "225GHz", "230GHz")
EXPECTED_BAND_COUNTS = {"37GHz": 6, "86GHz": 4, "225GHz": 3, "230GHz": 2}


@dataclass(frozen=True)
class WcdaPlotProduct:
    cadence: str
    path: Path
    png: Path
    status: str
    n_points_window: int = 0
    mjd_min: float | None = None
    mjd_max: float | None = None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-md", type=Path, default=REPORT_MD)
    parser.add_argument("--radio-cache", type=Path, default=RADIO_CACHE)
    parser.add_argument("--cds-fig1-url", default=CDS_FIG1_URL)
    parser.add_argument("--wcda-week", type=Path, default=DEFAULT_WCDA_WEEK)
    parser.add_argument("--wcda-day", type=Path, default=DEFAULT_WCDA_DAY_2022)
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Ignore any cached parsed radio table and refetch the CDS fig1.dat file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    output_dir = _project_path(args.output_dir)
    report_md = _project_path(args.report_md)
    radio_cache = _project_path(args.radio_cache)
    wcda_week_path = _project_path(args.wcda_week)
    wcda_day_path = _project_path(args.wcda_day)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_md.parent.mkdir(parents=True, exist_ok=True)

    radio = load_radio_table(
        cache_path=radio_cache,
        cds_url=args.cds_fig1_url,
        force_download=args.force_download,
    )
    validate_radio_table(radio)
    window = radio["mjd"].min() - WINDOW_PADDING_DAYS, radio["mjd"].max() + WINDOW_PADDING_DAYS

    weekly = build_wcda_product(
        cadence="weekly",
        wcda_path=wcda_week_path,
        png_path=output_dir / WEEKLY_PNG.name,
        radio=radio,
        window=window,
        required=True,
    )
    daily = build_wcda_product(
        cadence="daily",
        wcda_path=wcda_day_path,
        png_path=output_dir / DAILY_PNG.name,
        radio=radio,
        window=window,
        required=False,
    )

    report_md.write_text(build_report(radio, window, weekly, daily, radio_cache, report_md), encoding="utf-8")

    print(f"[OK] radio cache: {radio_cache.relative_to(PROJECT_ROOT)}")
    print(f"[OK] weekly plot: {weekly.png.relative_to(PROJECT_ROOT)}")
    if daily.status == "generated":
        print(f"[OK] daily plot: {daily.png.relative_to(PROJECT_ROOT)}")
    else:
        print(f"[INFO] daily plot skipped: {daily.status}")
    print(f"[OK] report: {report_md.relative_to(PROJECT_ROOT)}")


def load_radio_table(*, cache_path: Path, cds_url: str, force_download: bool) -> pd.DataFrame:
    if cache_path.exists() and not force_download:
        return pd.read_csv(cache_path)

    try:
        with urlopen(cds_url, timeout=30) as response:
            text = response.read().decode("utf-8")
    except (OSError, URLError) as exc:
        if cache_path.exists():
            print(f"[WARN] CDS fetch failed; using cached radio table: {exc}", file=sys.stderr)
            return pd.read_csv(cache_path)
        raise RuntimeError(f"Could not fetch CDS table and no cache exists: {cds_url}") from exc

    radio = parse_cds_fig1(text)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    radio.to_csv(cache_path, index=False)
    return radio


def parse_cds_fig1(text: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        mjd = _parse_float(line[0:10])
        value = _parse_float(line[16:24])
        error = _parse_float(line[32:40])
        energy = line[48:58].strip()
        instrument = line[64:74].strip()
        unit = line[80:102].strip()
        if mjd is None or value is None or error is None:
            continue
        if unit != "Jy" or energy not in RADIO_BANDS:
            continue
        rows.append(
            {
                "mjd": mjd,
                "flux_jy": value,
                "flux_err_jy": error,
                "band": energy,
                "frequency_ghz": float(energy.removesuffix("GHz")),
                "instrument": instrument,
                "unit": unit,
                "source_catalog": "CDS/VizieR J/A+A/684/A127 fig1.dat",
                "source_url": CDS_FIG1_URL,
            }
        )
    if not rows:
        raise ValueError("No radio flux-density rows found in CDS fig1.dat.")
    return pd.DataFrame(rows).sort_values(["frequency_ghz", "mjd"]).reset_index(drop=True)


def validate_radio_table(radio: pd.DataFrame) -> None:
    required = {"mjd", "flux_jy", "flux_err_jy", "band", "instrument", "unit"}
    missing = sorted(required - set(radio.columns))
    if missing:
        raise ValueError(f"Radio table is missing required columns: {missing}")
    if len(radio) != 15:
        raise ValueError(f"Expected 15 radio flux-density points, found {len(radio)}.")
    counts = radio["band"].value_counts().to_dict()
    if counts != EXPECTED_BAND_COUNTS:
        raise ValueError(f"Unexpected radio band counts: expected={EXPECTED_BAND_COUNTS}, observed={counts}")
    mjd_min = float(radio["mjd"].min())
    mjd_max = float(radio["mjd"].max())
    if not (59698.7 <= mjd_min <= 59698.8 and 59753.7 <= mjd_max <= 59753.8):
        raise ValueError(f"Unexpected radio MJD range: {mjd_min:.4f}-{mjd_max:.4f}")


def build_wcda_product(
    *,
    cadence: str,
    wcda_path: Path,
    png_path: Path,
    radio: pd.DataFrame,
    window: tuple[float, float],
    required: bool,
) -> WcdaPlotProduct:
    if not wcda_path.exists():
        if required:
            raise FileNotFoundError(f"Missing required WCDA {cadence} input: {wcda_path}")
        return WcdaPlotProduct(cadence=cadence, path=wcda_path, png=png_path, status="pending: input CSV missing")

    wcda = read_wcda_counts_csv(wcda_path)
    lc = usable_light_curve(wcda, "flux_excess", "flux_excess_err")
    in_window = _windowed(lc, window)
    if in_window.empty:
        message = f"no finite WCDA {cadence} points in MJD {window[0]:.3f}-{window[1]:.3f}"
        if required:
            raise ValueError(message)
        return WcdaPlotProduct(cadence=cadence, path=wcda_path, png=png_path, status=f"pending: {message}")

    plot_sync_figure(png_path, radio=radio, wcda=in_window, cadence=cadence, window=window)
    return WcdaPlotProduct(
        cadence=cadence,
        path=wcda_path,
        png=png_path,
        status="generated",
        n_points_window=len(in_window),
        mjd_min=float(in_window["mjd"].min()),
        mjd_max=float(in_window["mjd"].max()),
    )


def plot_sync_figure(
    path: Path,
    *,
    radio: pd.DataFrame,
    wcda: pd.DataFrame,
    cadence: str,
    window: tuple[float, float],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(
        1 + len(RADIO_BANDS),
        1,
        figsize=(11.5, 10.0),
        sharex=True,
        constrained_layout=True,
    )
    fig.suptitle(f"Mrk 421 2022 radio-LHAASO exploratory alignment ({cadence})", fontsize=14)

    ax_wcda = axes[0]
    ax_wcda.errorbar(
        wcda["mjd"],
        wcda["flux_excess"],
        yerr=wcda["flux_excess_err"],
        fmt="o-",
        ms=3.6,
        lw=1.1,
        color="#245c9f",
        ecolor="#7da0c9",
        capsize=2,
        label=f"WCDA {cadence}",
    )
    ax_wcda.axhline(0.0, color="#7a7a7a", lw=0.8, alpha=0.6)
    ax_wcda.set_ylabel("WCDA excess-rate proxy\ncounts / s")
    ax_wcda.legend(loc="upper left", frameon=False)
    ax_wcda.grid(True, alpha=0.25)

    colors = {
        "37GHz": "#8b4c9f",
        "86GHz": "#2f7f6f",
        "225GHz": "#c06f2b",
        "230GHz": "#9b2f3f",
    }
    for ax, band in zip(axes[1:], RADIO_BANDS, strict=True):
        sub = radio.loc[radio["band"] == band].sort_values("mjd")
        label = f"{band} {', '.join(sorted(sub['instrument'].unique()))}"
        ax.errorbar(
            sub["mjd"],
            sub["flux_jy"],
            yerr=sub["flux_err_jy"],
            fmt="o",
            ms=4.2,
            lw=1.0,
            color=colors[band],
            ecolor=colors[band],
            capsize=2,
            label=label,
        )
        ax.set_ylabel(f"{band}\nJy")
        ax.legend(loc="upper left", frameon=False)
        ax.grid(True, alpha=0.25)

    axes[-1].set_xlabel("MJD")
    axes[-1].set_xlim(window)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def build_report(
    radio: pd.DataFrame,
    window: tuple[float, float],
    weekly: WcdaPlotProduct,
    daily: WcdaPlotProduct,
    radio_cache: Path,
    report_md: Path,
) -> str:
    counts = radio["band"].value_counts().reindex(RADIO_BANDS).fillna(0).astype(int)
    lines = [
        "# Mrk 421 2022 Radio-LHAASO Exploratory Alignment",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "This quick-look aligns public 2022 radio flux-density points with the local LHAASO/WCDA Mrk 421 excess-rate proxy. It is an exploratory visualization only: no DCF, FAP, correlation coefficient, lag, or QPO significance is reported here.",
        "",
        "## Data Sources",
        "",
        f"- Radio: CDS/VizieR `J/A+A/684/A127`, table [`fig1.dat`]({CDS_FIG1_URL}); catalogue ReadMe: [{CDS_README_URL}]({CDS_README_URL}).",
        f"- Parsed radio cache: `{_rel(radio_cache)}`.",
        f"- WCDA weekly input: `{_rel(weekly.path)}`.",
        f"- WCDA daily input target: `{_rel(daily.path)}`.",
        "",
        "## Coverage",
        "",
        f"- Radio flux-density rows: {len(radio)}; MJD {radio['mjd'].min():.4f}-{radio['mjd'].max():.4f}.",
        f"- Plot window: MJD {window[0]:.4f}-{window[1]:.4f} (radio range padded by {WINDOW_PADDING_DAYS:.0f} days).",
    ]
    for band in RADIO_BANDS:
        lines.append(f"- {band}: {int(counts[band])} points.")
    lines += [
        f"- WCDA weekly status: {weekly.status}; points in window: {weekly.n_points_window}.",
        f"- WCDA daily status: {daily.status}; points in window: {daily.n_points_window}.",
        "",
        "## Figures",
        "",
        f"- Weekly alignment: `{_report_rel(weekly.png, report_md.parent)}`.",
    ]
    if weekly.status == "generated":
        lines.append(f"![Mrk 421 2022 radio-LHAASO weekly alignment]({_report_rel(weekly.png, report_md.parent)})")
    lines.append("")
    if daily.status == "generated":
        lines += [
            f"- Daily alignment: `{_report_rel(daily.png, report_md.parent)}`.",
            f"![Mrk 421 2022 radio-LHAASO daily alignment]({_report_rel(daily.png, report_md.parent)})",
            "",
        ]
    else:
        lines += [
            "- Daily alignment: pending. Generate the 2022 WCDA daily CSV on IHEP with the MakeLC workflow, then place it at the daily input target above and rerun this pipeline.",
            "",
        ]
    lines += [
        "## Notes",
        "",
        "- WCDA values use the existing project proxy `flux_excess = sum(n_on - n_bkg) / tobs` with propagated on/off errors. This is not calibrated physical flux.",
        "- Radio values are physical flux densities in Jy from the CDS table and are plotted in separate panels by frequency.",
        "- The figure is intentionally not a correlation or lag measurement because the radio sampling in this short campaign is sparse.",
        "",
    ]
    return "\n".join(lines)


def _parse_float(text: str) -> float | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def _windowed(df: pd.DataFrame, window: tuple[float, float]) -> pd.DataFrame:
    return df.loc[(df["mjd"] >= window[0]) & (df["mjd"] <= window[1])].copy()


def _project_path(path: Path) -> Path:
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
