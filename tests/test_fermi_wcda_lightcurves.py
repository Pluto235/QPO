from __future__ import annotations

import numpy as np
import pytest

from pipeline.fermi_wcda_lightcurves import (
    CADENCE_BIN_COUNTS,
    MJD_START,
    build_time_edges,
    chunk_filename,
    failed_bin_frame,
    guarded_process_lc_bin,
    lightcurve_result_to_frame,
    load_cached_chunk,
    met_to_project_mjd,
    split_bin_indices,
    write_frame_csv,
)


def test_time_edges_match_official_wcda_grid() -> None:
    edges_2day = build_time_edges(2)
    edges_8day = build_time_edges(8)

    assert len(edges_2day) == CADENCE_BIN_COUNTS[2] + 1
    assert len(edges_8day) == CADENCE_BIN_COUNTS[8] + 1
    assert np.isclose(met_to_project_mjd(edges_2day[0]), MJD_START)
    assert np.isclose(met_to_project_mjd(edges_2day[-1]), 60886.66666667)
    assert np.isclose(met_to_project_mjd(edges_8day[-1]), 60880.66666667)

    centers_2day = met_to_project_mjd(0.5 * (edges_2day[:-1] + edges_2day[1:]))
    centers_8day = met_to_project_mjd(0.5 * (edges_8day[:-1] + edges_8day[1:]))
    assert np.isclose(centers_2day[0], 59281.66666667)
    assert np.isclose(centers_2day[-1], 60885.66666667)
    assert np.isclose(centers_8day[0], 59284.66666667)
    assert np.isclose(centers_8day[-1], 60876.66666667)


def test_low_ts_bins_are_retained_as_upper_limits() -> None:
    edges = build_time_edges(2)[:3]
    result = {
        "tmin": edges[:-1],
        "tmax": edges[1:],
        "flux": np.array([1.0e-7, 2.0e-8]),
        "flux_err": np.array([1.0e-8, 2.0e-8]),
        "flux_ul95": np.array([1.2e-7, 5.0e-8]),
        "ts": np.array([12.0, 2.0]),
        "npred": np.array([20.0, 3.0]),
        "fit_success": np.array([True, True]),
        "fit_status": np.array([0, 0]),
        "fit_quality": np.array([3, 3]),
    }

    frame = lightcurve_result_to_frame(result, "mkn421", 2)

    assert len(frame) == 2
    assert frame["is_detection"].tolist() == [True, False]
    assert frame["is_upper_limit"].tolist() == [False, True]
    assert np.allclose(frame["mjd"], [59281.66666667, 59283.66666667])


def test_chunks_preserve_global_bin_indices() -> None:
    chunks = split_bin_indices(np.arange(7, dtype=int), 3)

    assert [chunk.tolist() for chunk in chunks] == [[0, 1, 2], [3, 4, 5], [6]]
    assert [chunk_filename(chunk) for chunk in chunks] == [
        "chunk_0000_0002.csv",
        "chunk_0003_0005.csv",
        "chunk_0006_0006.csv",
    ]


def test_failed_bin_is_retained_and_cached(tmp_path) -> None:
    edges = build_time_edges(2)
    frame = failed_bin_frame("mkn421", 2, 95, edges, "RuntimeError: profile failed")
    chunk_path = tmp_path / "chunk_0095_0095.csv"
    write_frame_csv(frame, chunk_path)

    cached = load_cached_chunk(chunk_path, 2, np.array([95]), edges)

    assert cached is not None
    assert cached.loc[0, "bin_index"] == 95
    assert not cached.loc[0, "fit_success"]
    assert cached.loc[0, "failure_reason"] == "RuntimeError: profile failed"
    assert np.isclose(cached.loc[0, "mjd"], 59471.66666667)


def test_chunk_size_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        split_bin_indices(np.arange(3, dtype=int), 0)


def test_fermipy_bin_guard_isolates_worker_exception(tmp_path, monkeypatch) -> None:
    import pipeline.fermi_wcda_lightcurves as pipeline

    def fail_bin(*args, **kwargs):
        raise RuntimeError("profile failed")

    monkeypatch.setattr(pipeline, "_FERMIPY_PROCESS_LC_BIN", fail_bin)
    result = guarded_process_lc_bin(
        (0, (100.0, 200.0)),
        basedir="chunk/",
        workdir=str(tmp_path),
    )

    assert not result["fit_success"]
    assert result["failure_reason"] == "RuntimeError: profile failed"
    assert result["config"]["fileio"]["outdir"] == str(tmp_path / "chunk/lightcurve_100_200")
    assert (tmp_path / "chunk/lightcurve_100_200").is_dir()
