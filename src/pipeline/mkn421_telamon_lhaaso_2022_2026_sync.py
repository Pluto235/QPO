#!/usr/bin/env python3
"""Build exploratory Mrk 421 TELAMON-LHAASO 2022-2026 synchronization plots."""

from __future__ import annotations

import argparse
import ast
import os
import re
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
from utils.project_paths import MULTIWAVELENGTH_DIR, PROJECT_ROOT, WCDA_WEEK_DIR  # noqa: E402


TELAMON_SOURCE_URL = "https://telamon.astro.uni-wuerzburg.de/sources/1104-3812"
OUTPUT_DIR = MULTIWAVELENGTH_DIR / "mkn421" / "telamon_lhaaso_2022_2026"
REPORT_MD = PROJECT_ROOT / "reports" / "mkn421_telamon_lhaaso_2022_2026_sync.md"
DEFAULT_WCDA_WEEK = WCDA_WEEK_DIR / "LHAASO-WCDA_Mkn421_2021-03-08_2026-03-29_week.csv"
TELAMON_CACHE = OUTPUT_DIR / "telamon_averaged_bands.csv"
WEEKLY_PNG = OUTPUT_DIR / "mkn421_telamon_lhaaso_2022_2026_weekly.png"
DEFAULT_START_DATE = "2022-01-01"
DEFAULT_END_DATE = "2026-12-31"

TELAMON_SERIES = {
    "aver_lc14": {
        "band": "14mm",
        "label": "TELAMON Aver 14mm",
        "description": "TELAMON averaged 14 mm band",
        "color": "#2f7f6f",
    },
    "aver_lc7": {
        "band": "7mm",
        "label": "TELAMON Aver 7mm",
        "description": "TELAMON averaged 7 mm band",
        "color": "#9b2f3f",
    },
}


@dataclass(frozen=True)
class SyncCoverage:
    window: tuple[float, float]
    wcda_points: int
    telamon_points_by_band: dict[str, int]
    telamon_mjd_range: tuple[float, float]
    wcda_mjd_range: tuple[float, float]
    requested_dates: tuple[str, str]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--report-md", type=Path, default=REPORT_MD)
    parser.add_argument("--telamon-cache", type=Path, default=TELAMON_CACHE)
    parser.add_argument("--telamon-url", default=TELAMON_SOURCE_URL)
    parser.add_argument("--wcda-week", type=Path, default=DEFAULT_WCDA_WEEK)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Ignore the cached parsed TELAMON table and refetch the source page.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    output_dir = _project_path(args.output_dir)
    report_md = _project_path(args.report_md)
    telamon_cache = _project_path(args.telamon_cache)
    wcda_week_path = _project_path(args.wcda_week)
    weekly_png = output_dir / WEEKLY_PNG.name

    output_dir.mkdir(parents=True, exist_ok=True)
    report_md.parent.mkdir(parents=True, exist_ok=True)

    telamon = load_telamon_table(
        cache_path=telamon_cache,
        telamon_url=args.telamon_url,
        force_download=args.force_download,
    )
    validate_telamon_table(telamon)

    wcda = load_wcda_weekly(wcda_week_path)
    coverage = compute_sync_coverage(
        telamon=telamon,
        wcda=wcda,
        start_date=_parse_iso_date(args.start_date),
        end_date=_parse_iso_date(args.end_date),
    )
    telamon_window = _windowed(telamon, coverage.window)
    wcda_window = _windowed(wcda, coverage.window)

    plot_sync_figure(
        weekly_png,
        telamon=telamon_window,
        wcda=wcda_window,
        coverage=coverage,
    )
    report_md.write_text(
        build_report(
            telamon=telamon,
            coverage=coverage,
            telamon_cache=telamon_cache,
            wcda_week_path=wcda_week_path,
            weekly_png=weekly_png,
            report_md=report_md,
        ),
        encoding="utf-8",
    )

    print(f"[OK] TELAMON cache: {telamon_cache.relative_to(PROJECT_ROOT)}")
    print(f"[OK] weekly sync plot: {weekly_png.relative_to(PROJECT_ROOT)}")
    print(f"[OK] report: {report_md.relative_to(PROJECT_ROOT)}")
    print(
        "[OK] plot window: "
        f"MJD {coverage.window[0]:.3f}-{coverage.window[1]:.3f}; "
        f"WCDA weekly points={coverage.wcda_points}; "
        + ", ".join(f"{band}={count}" for band, count in coverage.telamon_points_by_band.items())
    )


def load_telamon_table(*, cache_path: Path, telamon_url: str, force_download: bool) -> pd.DataFrame:
    if cache_path.exists() and not force_download:
        return pd.read_csv(cache_path)

    try:
        with urlopen(telamon_url, timeout=45) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (OSError, URLError) as exc:
        if cache_path.exists():
            print(f"[WARN] TELAMON fetch failed; using cached table: {exc}", file=sys.stderr)
            return pd.read_csv(cache_path)
        raise RuntimeError(f"Could not fetch TELAMON source page and no cache exists: {telamon_url}") from exc

    telamon = parse_telamon_averaged_bands(html, telamon_url=telamon_url)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    telamon.to_csv(cache_path, index=False)
    return telamon


def parse_telamon_averaged_bands(html: str, *, telamon_url: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for variable, meta in TELAMON_SERIES.items():
        body = _extract_js_object_body(html, variable)
        mjd = _extract_js_array(body, "x")
        flux = _extract_js_array(body, "y")
        flux_err = _extract_js_error_array(body)
        if not (len(mjd) == len(flux) == len(flux_err)):
            raise ValueError(
                f"TELAMON {variable} array length mismatch: "
                f"MJD={len(mjd)}, flux={len(flux)}, err={len(flux_err)}"
            )
        for mjd_value, flux_value, flux_err_value in zip(mjd, flux, flux_err, strict=True):
            rows.append(
                {
                    "mjd": float(mjd_value),
                    "flux_jy": float(flux_value),
                    "flux_err_jy": float(flux_err_value),
                    "band": meta["band"],
                    "series_label": meta["label"],
                    "description": meta["description"],
                    "source": "TELAMON",
                    "source_url": telamon_url,
                    "data_kind": "embedded Plotly averaged light curve",
                }
            )
    if not rows:
        raise ValueError("No TELAMON averaged 14mm/7mm rows were parsed.")
    return pd.DataFrame(rows).sort_values(["band", "mjd"]).reset_index(drop=True)


def validate_telamon_table(telamon: pd.DataFrame) -> None:
    required = {"mjd", "flux_jy", "flux_err_jy", "band", "series_label", "source_url"}
    missing = sorted(required - set(telamon.columns))
    if missing:
        raise ValueError(f"TELAMON table is missing required columns: {missing}")
    observed_bands = set(telamon["band"].dropna().astype(str))
    expected_bands = {meta["band"] for meta in TELAMON_SERIES.values()}
    if observed_bands != expected_bands:
        raise ValueError(f"Unexpected TELAMON bands: expected={expected_bands}, observed={observed_bands}")
    for band in sorted(expected_bands):
        sub = telamon.loc[telamon["band"] == band]
        if len(sub) < 10:
            raise ValueError(f"TELAMON {band} has too few points for a 2022-2026 sync plot: {len(sub)}")
    numeric = telamon[["mjd", "flux_jy", "flux_err_jy"]].apply(pd.to_numeric, errors="coerce")
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("TELAMON table contains non-finite numeric values.")
    if (numeric["flux_err_jy"] <= 0).any():
        raise ValueError("TELAMON table contains non-positive flux errors.")


def load_wcda_weekly(wcda_path: Path) -> pd.DataFrame:
    if not wcda_path.exists():
        raise FileNotFoundError(f"Missing WCDA weekly input: {wcda_path}")
    wcda = read_wcda_counts_csv(wcda_path)
    return usable_light_curve(wcda, "flux_excess", "flux_excess_err")


def compute_sync_coverage(
    *,
    telamon: pd.DataFrame,
    wcda: pd.DataFrame,
    start_date: date,
    end_date: date,
) -> SyncCoverage:
    requested_start = _date_to_mjd(start_date)
    requested_end = _date_to_mjd(end_date) + 1.0
    telamon_mjd_range = (float(telamon["mjd"].min()), float(telamon["mjd"].max()))
    wcda_mjd_range = (float(wcda["mjd"].min()), float(wcda["mjd"].max()))
    window = (
        max(requested_start, telamon_mjd_range[0], wcda_mjd_range[0]),
        min(requested_end, telamon_mjd_range[1], wcda_mjd_range[1]),
    )
    if window[1] <= window[0]:
        raise ValueError(f"No TELAMON/WCDA overlap in requested range: MJD {window[0]:.3f}-{window[1]:.3f}")

    telamon_window = _windowed(telamon, window)
    wcda_window = _windowed(wcda, window)
    if wcda_window.empty:
        raise ValueError(f"No finite WCDA weekly points in MJD {window[0]:.3f}-{window[1]:.3f}")
    if telamon_window.empty:
        raise ValueError(f"No TELAMON points in MJD {window[0]:.3f}-{window[1]:.3f}")

    counts = {
        band: int((telamon_window["band"] == band).sum())
        for band in [meta["band"] for meta in TELAMON_SERIES.values()]
    }
    return SyncCoverage(
        window=window,
        wcda_points=len(wcda_window),
        telamon_points_by_band=counts,
        telamon_mjd_range=telamon_mjd_range,
        wcda_mjd_range=wcda_mjd_range,
        requested_dates=(start_date.isoformat(), end_date.isoformat()),
    )


def plot_sync_figure(
    path: Path,
    *,
    telamon: pd.DataFrame,
    wcda: pd.DataFrame,
    coverage: SyncCoverage,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(
        3,
        1,
        figsize=(12.0, 7.8),
        sharex=True,
        constrained_layout=True,
    )
    fig.suptitle("Mrk 421 TELAMON-LHAASO weekly alignment (2022-2026)", fontsize=14)

    ax_wcda = axes[0]
    ax_wcda.errorbar(
        wcda["mjd"],
        wcda["flux_excess"],
        yerr=wcda["flux_excess_err"],
        fmt="o-",
        ms=3.3,
        lw=1.0,
        color="#245c9f",
        ecolor="#7da0c9",
        capsize=2,
        label=f"WCDA weekly ({coverage.wcda_points} points)",
    )
    ax_wcda.axhline(0.0, color="#7a7a7a", lw=0.8, alpha=0.6)
    ax_wcda.set_ylabel("WCDA excess-rate proxy\ncounts / s")
    ax_wcda.legend(loc="upper left", frameon=False)
    ax_wcda.grid(True, alpha=0.25)

    for ax, variable in zip(axes[1:], ("aver_lc14", "aver_lc7"), strict=True):
        meta = TELAMON_SERIES[variable]
        sub = telamon.loc[telamon["band"] == meta["band"]].sort_values("mjd")
        ax.errorbar(
            sub["mjd"],
            sub["flux_jy"],
            yerr=sub["flux_err_jy"],
            fmt="o-",
            ms=4.0,
            lw=1.0,
            color=meta["color"],
            ecolor=meta["color"],
            capsize=2,
            label=f"{meta['label']} ({len(sub)} points)",
        )
        ax.set_ylabel(f"{meta['band']} flux density\nJy")
        ax.legend(loc="upper left", frameon=False)
        ax.grid(True, alpha=0.25)

    axes[-1].set_xlabel("MJD")
    axes[-1].set_xlim(coverage.window)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def build_report(
    *,
    telamon: pd.DataFrame,
    coverage: SyncCoverage,
    telamon_cache: Path,
    wcda_week_path: Path,
    weekly_png: Path,
    report_md: Path,
) -> str:
    lines = [
        "# Mrk 421 TELAMON-LHAASO 2022-2026 Weekly Alignment",
        "",
        f"Generated on {date.today().isoformat()}.",
        "",
        "This quick-look aligns the TELAMON public Mrk 421 averaged 14 mm and 7 mm radio bands with the local LHAASO/WCDA weekly excess-rate proxy. It is exploratory only: no DCF, FAP, correlation coefficient, lag, or QPO significance is reported here.",
        "",
        "## Data Sources",
        "",
        f"- TELAMON source page: [{TELAMON_SOURCE_URL}]({TELAMON_SOURCE_URL}).",
        "- Radio extraction: embedded Plotly averaged light-curve arrays `aver_lc14` and `aver_lc7` from the source page.",
        f"- Parsed TELAMON cache: `{_rel(telamon_cache)}`.",
        f"- WCDA weekly input: `{_rel(wcda_week_path)}`.",
        "",
        "## Coverage",
        "",
        f"- Requested date range: {coverage.requested_dates[0]} to {coverage.requested_dates[1]}.",
        f"- Plotted overlap window: MJD {coverage.window[0]:.4f}-{coverage.window[1]:.4f}.",
        f"- Full TELAMON parsed range: MJD {coverage.telamon_mjd_range[0]:.4f}-{coverage.telamon_mjd_range[1]:.4f}; total parsed rows: {len(telamon)}.",
        f"- Full WCDA weekly finite range: MJD {coverage.wcda_mjd_range[0]:.4f}-{coverage.wcda_mjd_range[1]:.4f}.",
        f"- WCDA weekly points in plotted window: {coverage.wcda_points}.",
    ]
    for band, count in coverage.telamon_points_by_band.items():
        lines.append(f"- TELAMON {band} points in plotted window: {count}.")
    lines += [
        "",
        "## Figure",
        "",
        f"- Weekly TELAMON-LHAASO alignment: `{_report_rel(weekly_png, report_md.parent)}`.",
        f"![Mrk 421 TELAMON-LHAASO weekly alignment]({_report_rel(weekly_png, report_md.parent)})",
        "",
        "## Notes",
        "",
        "- TELAMON radio values are flux densities in Jy. The 14 mm and 7 mm products are averaged band light curves, not single-frequency points.",
        "- WCDA values use the project proxy `flux_excess = sum(n_on - n_bkg) / tobs` with propagated on/off errors. This is not calibrated physical flux.",
        "- This figure is intended for visual timing context only; the radio and gamma-ray panels are not normalized or cross-correlated.",
        "",
    ]
    return "\n".join(lines)


def _extract_js_object_body(html: str, variable: str) -> str:
    match = re.search(rf"var\s+{re.escape(variable)}\s*=\s*\{{(?P<body>.*?)\n\s*\}};", html, re.S)
    if not match:
        raise ValueError(f"Could not find TELAMON JavaScript object `{variable}`.")
    return match.group("body")


def _extract_js_array(body: str, key: str) -> list[float]:
    match = re.search(rf"\b{re.escape(key)}\s*:\s*\[(?P<values>[^\]]*)\]", body, re.S)
    if not match:
        raise ValueError(f"Could not find array `{key}` in TELAMON JavaScript object.")
    return _parse_number_array(match.group("values"))


def _extract_js_error_array(body: str) -> list[float]:
    match = re.search(r"error_y\s*:\s*\{.*?array\s*:\s*\[(?P<values>[^\]]*)\]", body, re.S)
    if not match:
        raise ValueError("Could not find TELAMON error_y array.")
    return _parse_number_array(match.group("values"))


def _parse_number_array(values: str) -> list[float]:
    parsed = ast.literal_eval("[" + values.strip() + "]")
    return [float(value) for value in parsed]


def _windowed(df: pd.DataFrame, window: tuple[float, float]) -> pd.DataFrame:
    return df.loc[(df["mjd"] >= window[0]) & (df["mjd"] <= window[1])].copy()


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Expected YYYY-MM-DD date, got {value!r}") from exc


def _date_to_mjd(value: date) -> float:
    return float((value - date(1858, 11, 17)).days)


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
