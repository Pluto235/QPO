#!/usr/bin/env python3
"""Build Mrk 421 and Mrk 501 Fermi-LAT light curves on the WCDA bins."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from astropy.io import fits
from astropy.table import Table


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.project_paths import (
    FERMI_MKN501_RAW_DIR,
    FERMI_WCDA_PROCESSED_DIR,
    FERMI_WCDA_RAW_DIR,
    PROJECT_ROOT,
)


MJD_START = 59280.66666667
MET_START = 636825605.0
SECONDS_PER_DAY = 86400.0
CADENCE_BIN_COUNTS = {2: 803, 8: 200}
TS_DETECTION_THRESHOLD = 9.0
MKN421_QUERY_ID = "L260818011233F357373F66"
SPACECRAFT_QUERY_ID = "L260818011232F357373F77"
_FERMIPY_PROCESS_LC_BIN = None


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    label: str
    catalog_name: str
    ra: float
    dec: float
    event_dir: Path
    event_pattern: str


SOURCE_SPECS = {
    "mkn421": SourceSpec(
        source_id="mkn421",
        label="Mrk 421",
        catalog_name="4FGL J1104.4+3812",
        ra=166.1138,
        dec=38.2088,
        event_dir=FERMI_WCDA_RAW_DIR / "mkn421",
        event_pattern="L260818011233F357373F66_PH*.fits",
    ),
    "mkn501": SourceSpec(
        source_id="mkn501",
        label="Mrk 501",
        catalog_name="4FGL J1653.8+3945",
        ra=253.4738,
        dec=39.7595,
        event_dir=FERMI_MKN501_RAW_DIR,
        event_pattern="L260703025740F357373F96_PH*.fits",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(SOURCE_SPECS), required=True)
    parser.add_argument("--cadences", nargs="+", type=int, choices=sorted(CADENCE_BIN_COUNTS), default=[2, 8])
    parser.add_argument("--workers", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", "8")))
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=0,
        help="Bins persisted per chunk; defaults to the worker count.",
    )
    parser.add_argument("--smoke", action="store_true", help="Fit one bin per requested cadence.")
    parser.add_argument("--smoke-bin-index", type=int, default=0)
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Recompute cached chunks that contain unsuccessful bins.",
    )
    parser.add_argument("--force-setup", action="store_true", help="Rebuild the full-baseline ROI fit.")
    return parser.parse_args()


def build_time_edges(cadence_days: int) -> np.ndarray:
    """Return the exact official-WCDA bin edges in Fermi MET seconds."""

    if cadence_days not in CADENCE_BIN_COUNTS:
        raise ValueError(f"Unsupported cadence: {cadence_days}")
    count = CADENCE_BIN_COUNTS[cadence_days]
    return MET_START + np.arange(count + 1, dtype=float) * cadence_days * SECONDS_PER_DAY


def met_to_project_mjd(values: np.ndarray | float) -> np.ndarray:
    """Convert MET to the MJD convention used by the frozen WCDA grid."""

    return MJD_START + (np.asarray(values, dtype=float) - MET_START) / SECONDS_PER_DAY


def discover_inputs(spec: SourceSpec) -> tuple[list[Path], Path]:
    events = sorted(spec.event_dir.glob(spec.event_pattern))
    spacecraft = sorted((FERMI_WCDA_RAW_DIR / "shared").glob("L260818011232F357373F77_SC00.fits"))
    if not events:
        raise FileNotFoundError(f"No event files found: {spec.event_dir / spec.event_pattern}")
    if len(spacecraft) != 1:
        raise FileNotFoundError(f"Expected one exact-range spacecraft file, found {len(spacecraft)}")
    return events, spacecraft[0]


def validate_inputs(events: list[Path], spacecraft: Path) -> dict[str, float | int]:
    event_ranges = [_fits_time_range(path) for path in events]
    sc_start, sc_stop, sc_rows = _fits_time_range(spacecraft)
    required_stop = float(build_time_edges(2)[-1])

    event_start = min(item[0] for item in event_ranges)
    event_stop = max(item[1] for item in event_ranges)
    if event_start > MET_START or event_stop < required_stop:
        raise ValueError(
            f"Event coverage {event_start:.0f}-{event_stop:.0f} does not cover "
            f"{MET_START:.0f}-{required_stop:.0f}."
        )
    if sc_start > MET_START or sc_stop < required_stop:
        raise ValueError(
            f"Spacecraft coverage {sc_start:.0f}-{sc_stop:.0f} does not cover "
            f"{MET_START:.0f}-{required_stop:.0f}."
        )
    return {
        "event_files": len(events),
        "event_tstart": event_start,
        "event_tstop": event_stop,
        "spacecraft_rows": sc_rows,
        "spacecraft_tstart": sc_start,
        "spacecraft_tstop": sc_stop,
    }


def _fits_time_range(path: Path) -> tuple[float, float, int]:
    with fits.open(path, memmap=True) as hdul:
        table = hdul[1]
        return float(table.header["TSTART"]), float(table.header["TSTOP"]), len(table.data)


def build_config(spec: SourceSpec, events: list[Path], spacecraft: Path, output_root: Path) -> dict[str, Any]:
    event_list = output_root / "event_files.txt"
    event_list.parent.mkdir(parents=True, exist_ok=True)
    event_list.write_text("".join(f"{path.resolve()}\n" for path in events), encoding="utf-8")

    roi_work = output_root / "roi" / "work"
    roi_work.mkdir(parents=True, exist_ok=True)
    return {
        "data": {"evfile": str(event_list.resolve()), "scfile": str(spacecraft.resolve())},
        "binning": {"roiwidth": 16.9, "binsz": 0.1, "enumbins": 37},
        "selection": {
            "ra": spec.ra,
            "dec": spec.dec,
            "radius": 12.0,
            "emin": 100,
            "emax": 300000,
            "zmax": 90,
            "evclass": 128,
            "evtype": 3,
            "filter": "(DATA_QUAL>0)&&(LAT_CONFIG==1)",
            "tmin": MET_START,
            "tmax": float(build_time_edges(2)[-1]),
            "target": spec.catalog_name,
        },
        "gtlike": {
            "edisp": True,
            "irfs": "P8R3_SOURCE_V3",
            "edisp_disable": ["isodiff", "galdiff"],
        },
        "model": {
            "src_roiwidth": 17.0,
            "galdiff": ["$FERMI_DIFFUSE_DIR/gll_iem_v07.fits"],
            "isodiff": ["$FERMI_DIFFUSE_DIR/iso_P8R3_SOURCE_V3_v1.txt"],
            "catalogs": ["4FGL"],
        },
        "fileio": {"outdir": str(roi_work.resolve()), "logfile": str((roi_work / "fermipy.log").resolve())},
    }


def prepare_roi(config_path: Path, spec: SourceSpec, output_root: Path, force: bool):
    from fermipy.gtanalysis import GTAnalysis

    roi_fits = output_root / "roi" / "full_baseline.fits"
    gta = GTAnalysis(str(config_path), logging={"verbosity": 3})
    if roi_fits.exists() and not force:
        print(f"[INFO] Loading existing ROI: {roi_fits}", flush=True)
        gta.load_roi(str(roi_fits))
        return gta

    print(f"[INFO] Setting up full-baseline ROI for {spec.label}", flush=True)
    gta.setup()
    gta.optimize()
    gta.free_sources(free=False)
    gta.free_sources(distance=3.0, pars="norm")
    gta.free_source(spec.catalog_name)
    diffuse_names = [source.name for source in gta.roi.sources if source.diffuse]
    gta.free_sources_by_name(diffuse_names, pars="norm")
    fit = gta.fit()
    if not fit["fit_success"]:
        raise RuntimeError(f"Full-baseline ROI fit failed for {spec.label}: {fit}")
    gta.write_roi(str(roi_fits))
    print(f"[INFO] Saved ROI: {roi_fits}", flush=True)
    return gta


def install_fermipy_lightcurve_failure_guard() -> None:
    """Keep one pathological time bin from aborting a complete Fermipy chunk."""

    from fermipy import lightcurve

    global _FERMIPY_PROCESS_LC_BIN
    if lightcurve._process_lc_bin is guarded_process_lc_bin:
        return
    _FERMIPY_PROCESS_LC_BIN = lightcurve._process_lc_bin
    lightcurve._process_lc_bin = guarded_process_lc_bin


def guarded_process_lc_bin(itime, *args, **kwargs):
    if _FERMIPY_PROCESS_LC_BIN is None:
        raise RuntimeError("Fermipy light-curve failure guard is not installed.")

    _, time_range = itime
    basedir = kwargs.get("basedir", "")
    workdir = kwargs.get("workdir", "")
    relative_outdir = basedir + "lightcurve_%.0f_%.0f" % time_range
    output_dir = Path(workdir) / relative_outdir
    try:
        result = _FERMIPY_PROCESS_LC_BIN(itime, *args, **kwargs)
    except Exception as exc:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(
            f"[WARN] Isolated failed Fermipy bin {time_range[0]:.0f}-{time_range[1]:.0f}: "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )
        result = {"fit_success": False, "failure_reason": f"{type(exc).__name__}: {exc}"}

    if "config" not in result:
        output_dir.mkdir(parents=True, exist_ok=True)
        result["config"] = {"fileio": {"outdir": str(output_dir)}}
    return result


def run_lightcurve(
    gta,
    spec: SourceSpec,
    cadence_days: int,
    output_root: Path,
    workers: int,
    chunk_size: int,
    smoke: bool,
    smoke_bin_index: int,
    retry_failed: bool,
) -> Path:
    all_edges = build_time_edges(cadence_days)
    if smoke:
        if smoke_bin_index < 0 or smoke_bin_index >= len(all_edges) - 1:
            raise ValueError(f"Smoke bin index {smoke_bin_index} is outside cadence {cadence_days}.")
        bin_indices = np.array([smoke_bin_index], dtype=int)
    else:
        bin_indices = np.arange(CADENCE_BIN_COUNTS[cadence_days], dtype=int)

    cadence_tag = f"{cadence_days}day"
    mode_tag = "smoke" if smoke else "full"
    output_dir = output_root / cadence_tag / mode_tag
    output_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir = output_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    chunk_work_root = output_dir / "chunk_work"
    chunk_work_root.mkdir(parents=True, exist_ok=True)

    # Preserve the full-baseline spectral fit but only allow normalizations to move in each time bin.
    gta.free_sources(free=False)
    diffuse_names = [source.name for source in gta.roi.sources if source.diffuse]
    gta.free_sources_by_name(diffuse_names, pars="norm")

    print(
        f"[INFO] Running {spec.label} {cadence_tag} {mode_tag}: "
        f"{len(bin_indices)} bins, workers={workers}, chunk_size={chunk_size}",
        flush=True,
    )
    frames = []
    for chunk_indices in split_bin_indices(bin_indices, chunk_size):
        chunk_path = chunks_dir / chunk_filename(chunk_indices)
        cached = load_cached_chunk(chunk_path, cadence_days, chunk_indices, all_edges)
        if cached is not None and not (retry_failed and not cached["fit_success"].all()):
            print(f"[INFO] Reusing chunk {chunk_path.name}", flush=True)
            frames.append(cached)
            continue

        frame = run_chunk_with_fallback(
            gta,
            spec,
            cadence_days,
            chunk_indices,
            all_edges,
            workers,
            chunk_work_root,
        )
        write_frame_csv(frame, chunk_path)
        frames.append(frame)
        print(
            f"[OK] Persisted {chunk_path.name}: "
            f"{int(frame['fit_success'].sum())}/{len(frame)} successful bins",
            flush=True,
        )

    frame = pd.concat(frames, ignore_index=True).sort_values("bin_index").reset_index(drop=True)
    expected_rows = 1 if smoke else CADENCE_BIN_COUNTS[cadence_days]
    if len(frame) != expected_rows:
        raise RuntimeError(f"Expected {expected_rows} bins, received {len(frame)}.")
    _validate_output_grid(frame, cadence_days, bin_indices)

    csv_path = output_dir / f"{spec.source_id}_fermi_{cadence_tag}_{mode_tag}.csv"
    write_frame_csv(frame, csv_path)
    fits_path = output_dir / f"{spec.source_id}_fermi_{cadence_tag}_{mode_tag}.fits"
    write_frame_fits(frame, fits_path)
    plot_path = output_dir / f"{spec.source_id}_fermi_{cadence_tag}_{mode_tag}.png"
    plot_lightcurve(frame, spec, cadence_days, plot_path)
    failures_path = output_dir / f"{spec.source_id}_fermi_{cadence_tag}_{mode_tag}_failures.csv"
    write_frame_csv(frame.loc[~frame["fit_success"]], failures_path)
    shutil.rmtree(chunk_work_root, ignore_errors=True)

    summary = {
        "source_id": spec.source_id,
        "cadence_days": cadence_days,
        "mode": mode_tag,
        "bins": len(frame),
        "fit_success": int(frame["fit_success"].sum()),
        "fit_failed": int((~frame["fit_success"]).sum()),
        "ts_ge_9": int(frame["is_detection"].sum()),
        "mjd_min": float(frame["mjd"].min()),
        "mjd_max": float(frame["mjd"].max()),
        "csv": str(csv_path),
        "fits": str(fits_path),
        "plot": str(plot_path),
        "failures": str(failures_path),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] Saved {csv_path}, {fits_path}, and {plot_path}", flush=True)
    return csv_path


def split_bin_indices(bin_indices: np.ndarray, chunk_size: int) -> list[np.ndarray]:
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive.")
    return [bin_indices[start : start + chunk_size] for start in range(0, len(bin_indices), chunk_size)]


def chunk_filename(bin_indices: np.ndarray) -> str:
    return f"chunk_{int(bin_indices[0]):04d}_{int(bin_indices[-1]):04d}.csv"


def run_chunk_with_fallback(
    gta,
    spec: SourceSpec,
    cadence_days: int,
    bin_indices: np.ndarray,
    all_edges: np.ndarray,
    workers: int,
    chunk_work_root: Path,
) -> pd.DataFrame:
    try:
        return run_fermipy_bins(
            gta,
            spec,
            cadence_days,
            bin_indices,
            all_edges,
            workers,
            chunk_work_root / chunk_filename(bin_indices).removesuffix(".csv"),
        )
    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
        print(
            f"[WARN] Chunk {chunk_filename(bin_indices)} failed with "
            f"{reason}.",
            flush=True,
        )
        print(traceback.format_exc(), flush=True)
        if len(bin_indices) == 1:
            return failed_bin_frame(
                spec.source_id,
                cadence_days,
                int(bin_indices[0]),
                all_edges,
                reason,
            )
        print("[INFO] Retrying the failed chunk one bin at a time.", flush=True)

    frames = []
    for bin_index in bin_indices:
        single_index = np.array([bin_index], dtype=int)
        work_dir = chunk_work_root / f"bin_{int(bin_index):04d}"
        try:
            frame = run_fermipy_bins(
                gta,
                spec,
                cadence_days,
                single_index,
                all_edges,
                1,
                work_dir,
            )
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"
            print(f"[WARN] Bin {int(bin_index)} failed: {reason}", flush=True)
            frame = failed_bin_frame(spec.source_id, cadence_days, int(bin_index), all_edges, reason)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def run_fermipy_bins(
    gta,
    spec: SourceSpec,
    cadence_days: int,
    bin_indices: np.ndarray,
    all_edges: np.ndarray,
    workers: int,
    work_dir: Path,
) -> pd.DataFrame:
    first = int(bin_indices[0])
    last = int(bin_indices[-1])
    if not np.array_equal(bin_indices, np.arange(first, last + 1)):
        raise ValueError("Fermipy chunks must contain contiguous bin indices.")
    edges = all_edges[first : last + 2]
    try:
        result = gta.lightcurve(
            spec.catalog_name,
            time_bins=edges.tolist(),
            free_background=True,
            free_radius=3.0,
            free_sources=[],
            free_params=["norm"],
            max_free_sources=5,
            shape_ts_threshold=1.0e9,
            use_local_ltcube=False,
            use_scaled_srcmap=False,
            save_bin_data=False,
            make_plots=False,
            write_fits=False,
            write_npy=False,
            multithread=workers > 1 and len(bin_indices) > 1,
            nthread=max(1, min(workers, len(bin_indices))),
            prefix=f"{spec.source_id}_{cadence_days}day_{first:04d}_{last:04d}",
            outdir=str(work_dir.resolve()),
        )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
    return lightcurve_result_to_frame(result, spec.source_id, cadence_days, bin_indices)


def failed_bin_frame(
    source_id: str,
    cadence_days: int,
    bin_index: int,
    all_edges: np.ndarray,
    reason: str,
) -> pd.DataFrame:
    result = {
        "tmin": np.array([all_edges[bin_index]]),
        "tmax": np.array([all_edges[bin_index + 1]]),
        "fit_success": np.array([False]),
    }
    frame = lightcurve_result_to_frame(result, source_id, cadence_days, np.array([bin_index]))
    frame.loc[0, "failure_reason"] = reason[:1000]
    return frame


def load_cached_chunk(
    path: Path,
    cadence_days: int,
    bin_indices: np.ndarray,
    all_edges: np.ndarray,
) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        frame = pd.read_csv(path)
        frame["failure_reason"] = frame["failure_reason"].fillna("")
        _validate_output_grid(frame, cadence_days, bin_indices)
        expected_tmin = all_edges[bin_indices]
        expected_tmax = all_edges[bin_indices + 1]
        if not np.allclose(frame["tmin_met"], expected_tmin, atol=1.0e-6):
            raise ValueError("Cached tmin values do not match the requested chunk.")
        if not np.allclose(frame["tmax_met"], expected_tmax, atol=1.0e-6):
            raise ValueError("Cached tmax values do not match the requested chunk.")
    except Exception as exc:
        print(f"[WARN] Ignoring invalid cached chunk {path}: {exc}", flush=True)
        return None
    return frame


def write_frame_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    temporary.replace(path)


def write_frame_fits(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output = frame.copy()
    output["failure_reason"] = output["failure_reason"].fillna("").astype(str)
    Table.from_pandas(output).write(path, overwrite=True)


def lightcurve_result_to_frame(
    result: dict[str, Any],
    source_id: str,
    cadence_days: int,
    bin_indices: np.ndarray | None = None,
) -> pd.DataFrame:
    tmin = np.asarray(result["tmin"], dtype=float)
    tmax = np.asarray(result["tmax"], dtype=float)
    size = len(tmin)

    def column(name: str, dtype=float, default=np.nan) -> np.ndarray:
        if name not in result:
            return np.full(size, default, dtype=dtype)
        values = np.asarray(result[name])
        if values.ndim != 1 or len(values) != size:
            return np.full(size, default, dtype=dtype)
        return values.astype(dtype, copy=False)

    if bin_indices is None:
        bin_indices = np.arange(size, dtype=int)
    if len(bin_indices) != size:
        raise ValueError("bin_indices length does not match the light-curve result.")

    frame = pd.DataFrame(
        {
            "source_id": source_id,
            "cadence_days": cadence_days,
            "bin_index": bin_indices,
            "tmin_met": tmin,
            "tmax_met": tmax,
            "tmin_mjd": met_to_project_mjd(tmin),
            "tmax_mjd": met_to_project_mjd(tmax),
            "mjd": met_to_project_mjd(0.5 * (tmin + tmax)),
            "flux": column("flux"),
            "flux_err": column("flux_err"),
            "flux_ul95": column("flux_ul95"),
            "ts": column("ts"),
            "npred": column("npred"),
            "fit_success": column("fit_success", dtype=bool, default=False),
            "fit_status": column("fit_status", dtype=int, default=-1),
            "fit_quality": column("fit_quality", dtype=int, default=-1),
            "failure_reason": np.full(size, "", dtype=object),
        }
    )
    frame["is_detection"] = frame["fit_success"] & (frame["ts"] >= TS_DETECTION_THRESHOLD)
    frame["is_upper_limit"] = frame["fit_success"] & ~frame["is_detection"]
    frame.loc[~frame["fit_success"], "failure_reason"] = "Fermipy fit unsuccessful"
    return frame


def _validate_output_grid(frame: pd.DataFrame, cadence_days: int, expected_indices: np.ndarray) -> None:
    actual_indices = frame["bin_index"].to_numpy(dtype=int)
    if not np.array_equal(actual_indices, expected_indices):
        raise ValueError(f"Unexpected bin indices: {actual_indices}")
    widths = frame["tmax_mjd"].to_numpy() - frame["tmin_mjd"].to_numpy()
    if not np.allclose(widths, cadence_days, atol=1.0e-8):
        raise ValueError(f"Output contains non-{cadence_days}-day bins: {widths}")
    edges = build_time_edges(cadence_days)
    expected_centers = met_to_project_mjd(0.5 * (edges[expected_indices] + edges[expected_indices + 1]))
    if not np.allclose(frame["mjd"].to_numpy(), expected_centers, atol=1.0e-8):
        raise ValueError("Fermi light-curve centers do not match the official WCDA grid.")


def plot_lightcurve(frame: pd.DataFrame, spec: SourceSpec, cadence_days: int, output_path: Path) -> None:
    fig, axis = plt.subplots(figsize=(13.5, 4.6), constrained_layout=True)
    good = frame["fit_success"] & np.isfinite(frame["mjd"])
    detected = good & frame["is_detection"] & np.isfinite(frame["flux"]) & np.isfinite(frame["flux_err"])
    upper = good & frame["is_upper_limit"] & np.isfinite(frame["flux_ul95"])

    axis.errorbar(
        frame.loc[detected, "mjd"],
        frame.loc[detected, "flux"],
        yerr=frame.loc[detected, "flux_err"],
        fmt="o",
        ms=2.8,
        elinewidth=0.65,
        capsize=0,
        color="#1f5a7a",
        alpha=0.9,
        label=f"TS >= {TS_DETECTION_THRESHOLD:g}",
    )
    axis.scatter(
        frame.loc[upper, "mjd"],
        frame.loc[upper, "flux_ul95"],
        marker="v",
        s=12,
        color="#a64b2a",
        alpha=0.55,
        label="95% upper limit (TS < 9)",
    )
    axis.set_title(f"{spec.label} Fermi-LAT {cadence_days}-day light curve")
    axis.set_xlabel("MJD")
    axis.set_ylabel(r"Photon flux (0.1-300 GeV) [ph cm$^{-2}$ s$^{-1}$]")
    axis.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    axis.grid(alpha=0.2, linewidth=0.6)
    axis.legend(loc="upper right", frameon=False, ncol=2)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    if args.workers < 1:
        raise ValueError("--workers must be positive.")
    chunk_size = args.chunk_size or args.workers
    if chunk_size < 1:
        raise ValueError("--chunk-size must be positive when provided.")
    spec = SOURCE_SPECS[args.source]
    output_root = FERMI_WCDA_PROCESSED_DIR / spec.source_id
    output_root.mkdir(parents=True, exist_ok=True)

    events, spacecraft = discover_inputs(spec)
    input_summary = validate_inputs(events, spacecraft)
    print(f"[INFO] Input validation: {input_summary}", flush=True)

    config = build_config(spec, events, spacecraft, output_root)
    config_path = output_root / "fermipy_config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    provenance = {
        "source": spec.source_id,
        "events": [str(path.relative_to(PROJECT_ROOT)) for path in events],
        "spacecraft": str(spacecraft.relative_to(PROJECT_ROOT)),
        "input_summary": input_summary,
        "fermi_query_ids": {
            "mkn421_photon_and_spacecraft": MKN421_QUERY_ID,
            "shared_spacecraft": SPACECRAFT_QUERY_ID,
            "mkn501_photon": "L260703025740F357373F96",
        },
        "energy_mev": [100, 300000],
        "event_class": 128,
        "event_type": 3,
        "irfs": "P8R3_SOURCE_V3",
        "selection_radius_deg": 12.0,
        "model_catalog": "4FGL",
        "mjd_start_edge": MJD_START,
        "mjd_stop_edge_2day": float(met_to_project_mjd(build_time_edges(2)[-1])),
        "mjd_stop_edge_8day": float(met_to_project_mjd(build_time_edges(8)[-1])),
    }
    (output_root / "input_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")

    os.chdir(PROJECT_ROOT)
    gta = prepare_roi(config_path, spec, output_root, args.force_setup)
    install_fermipy_lightcurve_failure_guard()
    for cadence_days in args.cadences:
        run_lightcurve(
            gta,
            spec,
            cadence_days,
            output_root,
            args.workers,
            chunk_size,
            args.smoke,
            args.smoke_bin_index,
            args.retry_failed,
        )


if __name__ == "__main__":
    main()
