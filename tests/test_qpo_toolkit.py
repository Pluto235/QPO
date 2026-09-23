import json

import numpy as np
import pandas as pd
import pytest


def test_read_lightcurve_cleans_duplicates_and_reports_qc(tmp_path):
    from qpo.io import read_lightcurve

    path = tmp_path / "lc.csv"
    pd.DataFrame(
        {
            "time": [1.0, 2.0, 2.0, 3.0, np.nan],
            "flux": [1.0, 2.0, 4.0, 3.0, 9.0],
            "flux_err": [0.1, 0.2, 0.2, -1.0, 0.1],
        }
    ).to_csv(path, index=False)

    result = read_lightcurve(path)
    assert list(result.data.columns) == ["time", "flux", "flux_err"]
    assert len(result.data) == 2
    assert result.qc["input_rows"] == 5
    assert result.qc["duplicate_rows_merged"] == 1
    assert result.qc["invalid_rows_removed"] == 2


def test_prepare_cwt_grid_only_fills_short_gaps():
    from qpo.sampling import prepare_cwt_grid

    t = np.array([0.0, 1.0, 2.0, 6.0, 7.0])
    y = np.array([0.0, 1.0, 0.0, 1.0, 0.0])
    grid = prepare_cwt_grid(t, y, max_gap_cadences=2)
    assert np.allclose(grid.time, np.arange(8.0))
    assert np.isfinite(grid.flux[:3]).all()
    assert np.isnan(grid.flux[3:6]).all()
    assert grid.qc["median_cadence"] == 1.0


def test_period_grid_is_log_spaced_and_overridable():
    from qpo.sampling import make_period_grid

    periods = make_period_grid(10.0, 100.0, 5)
    assert len(periods) == 5
    assert np.allclose(np.diff(np.log(periods)), np.diff(np.log(periods))[0])
    assert periods[0] == 10.0 and periods[-1] == 100.0


def test_cli_pipeline_writes_contract_files(tmp_path):
    from qpo.pipeline import analyze_lightcurve

    path = tmp_path / "lc.csv"
    t = np.arange(0.0, 64.0, 1.0)
    y = np.sin(2 * np.pi * t / 16.0)
    pd.DataFrame({"time": t, "flux": y, "flux_err": np.full_like(t, 0.1)}).to_csv(path, index=False)
    out = tmp_path / "result"
    result = analyze_lightcurve(path, out, n_surrogates=4, n_periods=24, workers=1)
    for name in ("integrated.png", "candidates.csv", "significance.csv", "qc.json", "manifest.json", "cwt.npz", "wwz.npz"):
        assert (out / name).exists(), name
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["input_columns"] == ["time", "flux", "flux_err"]
    assert result.output_dir == out
