from __future__ import annotations

import numpy as np

from pipeline.official_lc_xgm_window_qpo_analysis import parse_args
from pipeline.detector_controls_2day_qpo import parse_args as parse_control_args
from pipeline.periodicity_v1 import _global_peak_periods


def test_global_peak_periods_sorts_period_grid_and_returns_prominent_peaks() -> None:
    period = np.array([50.0, 10.0, 70.0, 30.0, 20.0, 60.0, 40.0])
    power = np.array([2.0, 0.0, 0.0, 0.0, 3.0, 0.0, 0.0])

    result = _global_peak_periods(period, power)

    np.testing.assert_allclose(result, [20.0, 50.0])


def test_window_map_peak_guides_are_opt_in() -> None:
    assert not parse_args([]).mark_global_peaks_on_maps
    assert parse_args(["--mark-global-peaks-on-maps"]).mark_global_peaks_on_maps


def test_control_map_peak_guides_are_opt_in() -> None:
    assert not parse_control_args([]).mark_global_peaks_on_maps
    assert parse_control_args(["--sources", "Crab", "--mark-global-peaks-on-maps"]).mark_global_peaks_on_maps
