#!/usr/bin/env python3
"""Build presentation-ready light-curve figures for the official WCDA QPO screen."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.project_paths import PROJECT_ROOT  # noqa: E402


RELEASE = "official_20260817"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "assets" / "official_qpo_20260817"
PRIMARY_SOURCES = {"Mkn421": "Mrk 421", "Mkn501": "Mrk 501"}
ALL_SOURCES = {
    "1ES1727p502": "1ES 1727+502",
    "1ES1959p650": "1ES 1959+650",
    "1ES2344p514": "1ES 2344+514",
    "4C_p42d22": "4C +42.22",
    "BLLacertae": "BL Lacertae",
    "Crab": "Crab",
    "IC310": "IC 310",
    "M87": "M 87",
    "Mkn421": "Mrk 421",
    "Mkn501": "Mrk 501",
    "NGC1275": "NGC 1275",
}
CADENCES = {"2day": ("2-day", 16), "8day": ("8-day", 4)}
COMPOSITE_TOP_FRACTION = 0.30


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    axis_limits = {source_token: eight_day_flux_limits(source_token) for source_token in ALL_SOURCES}
    for source_token, source_label in PRIMARY_SOURCES.items():
        for cadence, (cadence_label, rolling_bins) in CADENCES.items():
            input_path = light_curve_path(source_token, cadence)
            output_path = OUTPUT_DIR / f"{source_token.lower()}_{cadence}_lightcurve.png"
            plot_light_curve(
                input_path,
                output_path,
                source_label,
                cadence_label,
                rolling_bins,
                axis_limits[source_token],
            )
            print(f"[OK] {output_path.relative_to(PROJECT_ROOT)}")
    for source_token, source_label in ALL_SOURCES.items():
        for cadence, (cadence_label, _rolling_bins) in CADENCES.items():
            output_path = matched_periodicity_path(source_token, cadence)
            build_matched_axis_periodicity(
                light_curve_path(source_token, cadence),
                original_periodicity_path(source_token, cadence),
                output_path,
                source_label,
                cadence_label,
                axis_limits[source_token],
            )
            print(f"[OK] {output_path.relative_to(PROJECT_ROOT)}")


def light_curve_path(source_token: str, cadence: str) -> Path:
    input_dir = PROJECT_ROOT / "data" / "processed" / f"wcda_{cadence}" / RELEASE
    return next(input_dir.glob(f"LHAASO-WCDA_{source_token}_*_{cadence}_flux.csv"))


def source_id(source_token: str) -> str:
    return source_token.lower().replace("+", "p").replace("-", "m").replace(" ", "_")


def original_periodicity_path(source_token: str, cadence: str) -> Path:
    return (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "periodicity"
        / "official_lc_20260817"
        / cadence
        / source_id(source_token)
        / f"wcda_official_{cadence}_periodicity.png"
    )


def matched_periodicity_path(source_token: str, cadence: str) -> Path:
    return (
        OUTPUT_DIR
        / "periodicity"
        / cadence
        / source_id(source_token)
        / f"wcda_official_{cadence}_periodicity_matched_flux.png"
    )


def usable_light_curve(input_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(input_path)
    usable = raw.loc[raw["fit_status"].astype(str).str.strip().eq("OK")].copy()
    for column in ("mjd", "N0", "N0_err"):
        usable[column] = pd.to_numeric(usable[column], errors="coerce")
    usable = usable.loc[
        np.isfinite(usable["mjd"])
        & np.isfinite(usable["N0"])
        & np.isfinite(usable["N0_err"])
        & (usable["N0_err"] > 0)
    ].sort_values("mjd")
    return raw, usable


def eight_day_flux_limits(source_token: str) -> tuple[float, float]:
    _raw, usable = usable_light_curve(light_curve_path(source_token, "8day"))
    lower = float(np.nanmin(usable["N0"] - usable["N0_err"]))
    upper = float(np.nanmax(usable["N0"] + usable["N0_err"]))
    padding = max(0.06 * (upper - lower), np.finfo(float).eps)
    return lower - padding, upper + padding


def plot_light_curve(
    input_path: Path,
    output_path: Path,
    source_label: str,
    cadence_label: str,
    rolling_bins: int,
    y_limits: tuple[float, float],
) -> None:
    raw, usable = usable_light_curve(input_path)

    scale = 1e-12
    flux = usable["N0"].to_numpy(dtype=float) / scale
    error = usable["N0_err"].to_numpy(dtype=float) / scale
    rolling = pd.Series(flux).rolling(rolling_bins, center=True, min_periods=max(2, rolling_bins // 3)).median()

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titlesize": 17,
            "axes.labelsize": 12,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, axis = plt.subplots(figsize=(13.2, 5.1), constrained_layout=True)
    axis.errorbar(
        usable["mjd"],
        flux,
        yerr=error,
        fmt="o",
        ms=2.8 if cadence_label == "2-day" else 4.0,
        color="#2f6f8f",
        ecolor="#8fb5c8",
        elinewidth=0.55,
        capsize=0,
        alpha=0.82,
        label="Usable flux bins",
        zorder=2,
    )
    axis.plot(
        usable["mjd"],
        rolling,
        color="#b24c3f",
        lw=2.0,
        label=f"{rolling_bins * int(cadence_label.split('-')[0])}-day rolling median",
        zorder=3,
    )
    axis.axhline(0, color="#69717a", lw=0.8, alpha=0.65)
    axis.set_title(f"{source_label} · official WCDA {cadence_label} light curve", loc="left", pad=12)
    axis.set_xlabel("MJD")
    axis.set_ylabel(r"$N_0$ at 3 TeV ($10^{-12}$ TeV$^{-1}$ cm$^{-2}$ s$^{-1}$)")
    axis.grid(True, color="#d8d4ca", lw=0.7, alpha=0.65)
    axis.legend(loc="upper right", frameon=False, ncol=2)

    scaled_limits = y_limits[0] / scale, y_limits[1] / scale
    axis.set_ylim(*scaled_limits)
    clipped = count_clipped(usable, y_limits)
    axis.text(
        0.005,
        0.02,
        f"fit_status = OK: {len(usable)}/{len(raw)} bins · flux axis fixed to this source's 8-day range"
        + (f" · {clipped} point/error range(s) clipped" if clipped else ""),
        transform=axis.transAxes,
        color="#555b61",
        fontsize=9.5,
    )
    fig.savefig(output_path, dpi=180, facecolor="white")
    plt.close(fig)


def count_clipped(usable: pd.DataFrame, y_limits: tuple[float, float]) -> int:
    lower, upper = y_limits
    return int(
        np.count_nonzero(
            (usable["N0"].to_numpy(dtype=float) - usable["N0_err"].to_numpy(dtype=float) < lower)
            | (usable["N0"].to_numpy(dtype=float) + usable["N0_err"].to_numpy(dtype=float) > upper)
        )
    )


def build_matched_axis_periodicity(
    input_path: Path,
    original_path: Path,
    output_path: Path,
    source_label: str,
    cadence_label: str,
    y_limits: tuple[float, float],
) -> None:
    _raw, usable = usable_light_curve(input_path)
    with Image.open(original_path) as original_image:
        original = original_image.convert("RGB")
    top_height = int(round(original.height * COMPOSITE_TOP_FRACTION))
    top_panel = render_matched_top_panel(
        usable,
        source_label,
        cadence_label,
        y_limits,
        original.width,
        top_height,
    )
    composite = original.copy()
    composite.paste(top_panel, (0, 0))
    restore_periodicity_titles(composite, top_height)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    composite.save(output_path, dpi=(180, 180))


def restore_periodicity_titles(composite: Image.Image, top_height: int) -> None:
    draw = ImageDraw.Draw(composite)
    title_band_bottom = min(top_height + int(round(composite.height * 0.022)), composite.height)
    draw.rectangle((0, top_height - 2, composite.width, title_band_bottom), fill="white")
    font_size = max(18, int(round(composite.height * 0.017)))
    font = ImageFont.truetype(font_manager.findfont("DejaVu Sans"), font_size)
    title_y = top_height + 1
    draw.text((composite.width * 0.225, title_y), "CWT Power", fill="black", font=font, anchor="mt")
    draw.text((composite.width * 0.755, title_y), "WWZ Power", fill="black", font=font, anchor="mt")


def render_matched_top_panel(
    usable: pd.DataFrame,
    source_label: str,
    cadence_label: str,
    y_limits: tuple[float, float],
    width: int,
    height: int,
) -> Image.Image:
    dpi = 180
    fig = plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi, facecolor="white")
    axis = fig.add_axes([0.055, 0.19, 0.91, 0.67])
    axis.errorbar(
        usable["mjd"],
        usable["N0"],
        yerr=usable["N0_err"],
        fmt="o",
        ms=1.8 if cadence_label == "2-day" else 2.8,
        color="#2f6f8f",
        ecolor="#7faec4",
        elinewidth=0.5,
        capsize=0,
        alpha=0.86,
        clip_on=True,
    )
    lower, upper = y_limits
    span = upper - lower
    flux = usable["N0"].to_numpy(dtype=float)
    high = flux > upper
    low = flux < lower
    if np.any(high):
        axis.scatter(usable.loc[high, "mjd"], np.full(np.count_nonzero(high), upper - 0.025 * span), marker="^", s=12, color="#b24c3f", zorder=5)
    if np.any(low):
        axis.scatter(usable.loc[low, "mjd"], np.full(np.count_nonzero(low), lower + 0.025 * span), marker="v", s=12, color="#b24c3f", zorder=5)
    axis.set_ylim(lower, upper)
    axis.set_xlabel("MJD")
    axis.set_ylabel("Flux")
    axis.set_title(f"{source_label} official WCDA {cadence_label} flux · 8-day-matched y-axis", fontsize=13, pad=7)
    axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    axis.grid(True, color="#d8d4ca", lw=0.55, alpha=0.55)
    clipped = count_clipped(usable, y_limits)
    if clipped:
        axis.text(
            0.995,
            0.96,
            f"{clipped} point/error range(s) clipped by the 8-day display scale",
            transform=axis.transAxes,
            ha="right",
            va="top",
            fontsize=7.5,
            color="#8a3d35",
        )
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, facecolor="white")
    plt.close(fig)
    buffer.seek(0)
    with Image.open(buffer) as image:
        return image.convert("RGB")


if __name__ == "__main__":
    main()
