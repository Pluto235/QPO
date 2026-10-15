from __future__ import annotations

import numpy as np
import pytest

from pipeline.build_fermi_wcda_qpo_comparison_figures import (
    CWT_DISPLAY_CAPS,
    PEAK_MARKERS,
    shared_power_limit,
)


def test_shared_power_limit_uses_both_maps() -> None:
    first = np.arange(1.0, 101.0)
    second = np.arange(101.0, 201.0)

    result = shared_power_limit([first, second], percentile=100.0)

    assert result == pytest.approx(200.0)


def test_shared_power_limit_rejects_empty_maps() -> None:
    with pytest.raises(ValueError, match="empty power maps"):
        shared_power_limit([np.array([np.nan])])


def test_mkn421_2day_cwt_display_is_capped_at_20() -> None:
    assert CWT_DISPLAY_CAPS[("mkn421", "2day")] == pytest.approx(20.0)


def test_mkn501_wcda_markers_include_short_and_long_candidates() -> None:
    for cadence in ("2day", "8day"):
        markers = PEAK_MARKERS[("mkn501", cadence)]

        assert len(markers["wcda_cwt"]) == 2
        assert len(markers["wcda_wwz"]) == 2
        assert markers["wcda_cwt"][0] == pytest.approx(157.25)
        assert markers["wcda_wwz"][0] == pytest.approx(150.28 if cadence == "2day" else 149.44)
