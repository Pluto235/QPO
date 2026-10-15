#!/usr/bin/env python3
"""Build matched LHAASO-WCDA/Fermi-LAT CWT and WWZ comparison maps."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
import numpy as np  # noqa: E402


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.project_paths import PERIODICITY_DIR, PROJECT_ROOT  # noqa: E402


SOURCE_LABELS = {"mkn421": "Mrk 421", "mkn501": "Mrk 501"}
CADENCES = ("2day", "8day")
CADENCE_LABELS = {"2day": "2-day", "8day": "8-day"}
WCDA_ROOT = PERIODICITY_DIR / "official_lc_20260817"
FERMI_ROOT = PERIODICITY_DIR / "fermi_wcda_20260818" / "all-successful"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "assets" / "fermi_wcda_qpo_20260825"
CWT_DISPLAY_CAPS = {("mkn421", "2day"): 20.0}
PEAK_MARKERS = {
    ("mkn501", "2day"): {
        "wcda_cwt": (157.25, 419.80),
        "wcda_wwz": (150.28, 436.66),
        "fermi_cwt": (249.62,),
        "fermi_wwz": (259.83,),
    },
    ("mkn501", "8day"): {
        "wcda_cwt": (157.25, 419.80),
        "wcda_wwz": (149.44, 435.77),
        "fermi_cwt": (264.46,),
        "fermi_wwz": (258.72,),
    },
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", nargs="+", choices=sorted(SOURCE_LABELS), default=sorted(SOURCE_LABELS))
    parser.add_argument("--cadences", nargs="+", choices=CADENCES, default=list(CADENCES))
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    output_dir = args.output_dir if args.output_dir.is_absolute() else PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    for source_id in args.sources:
        for cadence in args.cadences:
            output_stem = output_dir / f"{source_id}_{cadence}_wcda_fermi_cwt_wwz_comparison"
            build_comparison_figure(source_id, cadence, output_stem)
            print(f"[OK] {output_stem.relative_to(PROJECT_ROOT)}.png/.pdf")


def load_products(source_id: str, cadence: str) -> dict[str, dict[str, np.ndarray]]:
    products: dict[str, dict[str, np.ndarray]] = {}
    paths = {
        "wcda_cwt": WCDA_ROOT / cadence / source_id / f"wcda_official_{cadence}_cwt.npz",
        "wcda_wwz": WCDA_ROOT / cadence / source_id / f"wcda_official_{cadence}_wwz.npz",
        "fermi_cwt": FERMI_ROOT / cadence / source_id / f"fermi_wcda_{cadence}_cwt.npz",
        "fermi_wwz": FERMI_ROOT / cadence / source_id / f"fermi_wcda_{cadence}_wwz.npz",
    }
    for key, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Required comparison product is missing: {path}")
        with np.load(path) as archive:
            products[key] = {name: archive[name] for name in archive.files}
    return products


def shared_power_limit(arrays: list[np.ndarray], percentile: float = 99.5) -> float:
    finite = np.concatenate([np.asarray(array, dtype=float)[np.isfinite(array)] for array in arrays])
    if finite.size == 0:
        raise ValueError("Cannot derive a shared color scale from empty power maps.")
    upper = float(np.nanpercentile(finite, percentile))
    if not np.isfinite(upper) or upper <= 0:
        upper = float(np.nanmax(finite))
    if not np.isfinite(upper) or upper <= 0:
        raise ValueError("Power maps do not contain a positive finite color-scale maximum.")
    return upper


def build_comparison_figure(source_id: str, cadence: str, output_stem: Path) -> None:
    products = load_products(source_id, cadence)
    cwt_data_upper = shared_power_limit(
        [products["wcda_cwt"]["power"], products["fermi_cwt"]["power"]]
    )
    cwt_upper = CWT_DISPLAY_CAPS.get((source_id, cadence), cwt_data_upper)
    wwz_upper = shared_power_limit([products["wcda_wwz"]["wwz_mat"], products["fermi_wwz"]["wwz_mat"]])
    cwt_norm = Normalize(vmin=0.0, vmax=cwt_upper)
    wwz_norm = Normalize(vmin=0.0, vmax=wwz_upper)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10.5,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.linewidth": 0.8,
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(14.4, 7.2), sharex=True, sharey=True, constrained_layout=True)
    fig.set_constrained_layout_pads(w_pad=0.025, h_pad=0.025, wspace=0.035, hspace=0.045)
    x_limits = _shared_time_limits(products)
    period_min = float(products["wcda_cwt"]["period_min"])
    period_max = float(products["wcda_cwt"]["period_max"])

    cwt_images = []
    wwz_images = []
    for row, instrument in enumerate(("wcda", "fermi")):
        cwt = products[f"{instrument}_cwt"]
        wwz = products[f"{instrument}_wwz"]
        cwt_images.append(_plot_cwt_map(axes[row, 0], cwt, cwt_norm))
        wwz_images.append(_plot_wwz_map(axes[row, 1], wwz, wwz_norm))
        axes[row, 0].text(
            -0.13,
            0.5,
            "LHAASO-WCDA" if instrument == "wcda" else "Fermi-LAT",
            transform=axes[row, 0].transAxes,
            rotation=90,
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
            color="#24313a",
        )
        for column in range(2):
            axes[row, column].set_xlim(*x_limits)
            axes[row, column].set_ylim(period_min, period_max)
            axes[row, column].set_yscale("log")
            axes[row, column].grid(False)

    cwt_title = "CWT power - shared WCDA/Fermi scale"
    if cwt_upper < cwt_data_upper:
        cwt_title += f", display capped at {cwt_upper:g}"
    axes[0, 0].set_title(cwt_title, pad=8)
    axes[0, 1].set_title("WWZ power - shared WCDA/Fermi scale", pad=8)
    axes[0, 0].set_ylabel("Period (day)")
    axes[1, 0].set_ylabel("Period (day)")
    axes[1, 0].set_xlabel("MJD")
    axes[1, 1].set_xlabel("MJD")
    _draw_peak_markers(axes, source_id, cadence)

    cwt_colorbar = fig.colorbar(
        cwt_images[0],
        ax=axes[:, 0],
        pad=0.012,
        shrink=0.96,
        aspect=28,
        extend="max" if cwt_upper < cwt_data_upper else "neither",
    )
    cwt_colorbar.set_label("Standardized CWT power")
    wwz_colorbar = fig.colorbar(wwz_images[0], ax=axes[:, 1], pad=0.012, shrink=0.96, aspect=28)
    wwz_colorbar.set_label("WWZ statistic")
    fig.suptitle(
        f"{SOURCE_LABELS[source_id]} {CADENCE_LABELS[cadence]}: matched time-period comparison",
        fontsize=15,
        fontweight="bold",
    )
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_stem.with_suffix(".png"), dpi=240, facecolor="white")
    fig.savefig(output_stem.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)


def _shared_time_limits(products: dict[str, dict[str, np.ndarray]]) -> tuple[float, float]:
    arrays = [
        products["wcda_cwt"]["t_mjd"],
        products["fermi_cwt"]["t_mjd"],
        products["wcda_wwz"]["tau_mat"][:, 0],
        products["fermi_wwz"]["tau_mat"][:, 0],
    ]
    return min(float(np.nanmin(array)) for array in arrays), max(float(np.nanmax(array)) for array in arrays)


def _plot_cwt_map(axis: plt.Axes, result: dict[str, np.ndarray], norm: Normalize):
    period = np.asarray(result["period"], dtype=float)
    time = np.asarray(result["t_mjd"], dtype=float)
    power = np.asarray(result["power"], dtype=float)
    period_min = float(result["period_min"])
    period_max = float(result["period_max"])
    mask = np.isfinite(period) & (period >= period_min) & (period <= period_max)
    image = axis.pcolormesh(time, period[mask], power[mask], shading="auto", cmap="magma", norm=norm)
    coi = np.clip(np.asarray(result["coi"], dtype=float), period_min, period_max)
    axis.fill_between(
        time,
        period_max,
        coi,
        where=coi <= period_max,
        color="white",
        alpha=0.48,
        hatch="//",
        edgecolor="#d5d5d5",
        linewidth=0.0,
    )
    axis.plot(time, coi, color="white", lw=0.9, alpha=0.95)
    return image


def _plot_wwz_map(axis: plt.Axes, result: dict[str, np.ndarray], norm: Normalize):
    tau = np.asarray(result["tau_mat"], dtype=float)[:, 0]
    period = np.asarray(result["period_mat"], dtype=float)[0]
    power = np.asarray(result["wwz_mat"], dtype=float)
    order = np.argsort(period)
    image = axis.pcolormesh(tau, period[order], power[:, order].T, shading="auto", cmap="viridis", norm=norm)
    axis.plot(result["ridge_tau"], result["ridge_period"], color="white", lw=0.8, alpha=0.8)
    return image


def _draw_peak_markers(axes: np.ndarray, source_id: str, cadence: str) -> None:
    markers = PEAK_MARKERS.get((source_id, cadence))
    if markers is None:
        return
    for row, instrument in enumerate(("wcda", "fermi")):
        color = "#F0E442" if instrument == "wcda" else "#56B4E9"
        for column, method in enumerate(("cwt", "wwz")):
            for period in markers[f"{instrument}_{method}"]:
                axes[row, column].axhline(period, color=color, lw=1.2, ls="--", alpha=0.95)
                axes[row, column].text(
                    0.985,
                    period,
                    f" {period:.0f} d ",
                    transform=axes[row, column].get_yaxis_transform(),
                    ha="right",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                    color="#172126",
                    bbox={"facecolor": color, "edgecolor": "none", "alpha": 0.85, "pad": 1.2},
                )


if __name__ == "__main__":
    main()
