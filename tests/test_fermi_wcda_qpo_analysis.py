from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pipeline import fermi_wcda_qpo_analysis as analysis


def _frame(source_id: str = "mkn421", cadence: str = "8day") -> pd.DataFrame:
    cadence_days = analysis.CADENCES[cadence]
    count = analysis.EXPECTED_BIN_COUNTS[cadence]
    index = np.arange(count)
    return pd.DataFrame(
        {
            "source_id": source_id,
            "cadence_days": cadence_days,
            "bin_index": index,
            "mjd": analysis.MJD_START + (index + 0.5) * cadence_days,
            "flux": np.linspace(1.0, 2.0, count),
            "flux_err": np.full(count, 0.1),
            "flux_ul95": np.linspace(1.2, 2.2, count),
            "ts": np.full(count, 12.0),
            "fit_success": np.ones(count, dtype=bool),
            "is_detection": np.ones(count, dtype=bool),
            "is_upper_limit": np.zeros(count, dtype=bool),
        }
    )


def test_prepare_light_curve_preserves_full_grid_and_failed_gap(tmp_path: Path) -> None:
    frame = _frame()
    frame.loc[5, ["flux", "flux_err", "flux_ul95"]] = np.nan
    frame.loc[5, "fit_success"] = False
    path = tmp_path / "lc.csv"
    frame.to_csv(path, index=False)

    grid, selected = analysis.prepare_light_curve(path, "mkn421", "8day", "all-successful")

    assert len(grid) == 200
    assert len(selected) == 199
    assert not bool(grid.loc[5, "is_usable_for_periodicity"])
    assert np.isnan(grid.loc[5, "flux"])


def test_detection_policy_excludes_low_ts_without_replacing_upper_limit(tmp_path: Path) -> None:
    frame = _frame(source_id="mkn501")
    frame.loc[3, "ts"] = 4.0
    frame.loc[3, "is_detection"] = False
    frame.loc[3, "is_upper_limit"] = True
    path = tmp_path / "lc.csv"
    frame.to_csv(path, index=False)

    grid, selected = analysis.prepare_light_curve(path, "mkn501", "8day", "detections-only")

    assert len(grid) == 200
    assert len(selected) == 199
    assert 3 not in set(selected["bin_index"])
    assert grid.loc[3, "flux_ul95"] == pytest.approx(frame.loc[3, "flux_ul95"])


def test_prepare_light_curve_rejects_shifted_mjd_grid(tmp_path: Path) -> None:
    frame = _frame()
    frame.loc[10, "mjd"] += 0.25
    path = tmp_path / "lc.csv"
    frame.to_csv(path, index=False)

    with pytest.raises(ValueError, match="frozen WCDA grid"):
        analysis.prepare_light_curve(path, "mkn421", "8day", "all-successful")


def test_finalize_rows_adds_four_curve_bonferroni_value() -> None:
    row = {column: np.nan for column in analysis.SIGNIFICANCE_COLUMNS}
    row.update({"global_fap": 0.02, "note": "Response-period systematics are not modeled."})

    result = analysis.finalize_rows([row], "2day", "all-successful")[0]

    assert result["series"] == "fermi_wcda_2day"
    assert result["bonferroni_4curve_global_fap"] == pytest.approx(0.08)
    assert not result["passes_4curve_global_0p05"]


def test_fermi_display_range_uses_detections_not_extreme_upper_limits() -> None:
    frame = _frame()
    frame.loc[:, "flux"] = 2.0
    frame.loc[:, "flux_err"] = 0.2
    frame.loc[0, ["ts", "is_detection", "is_upper_limit", "flux_ul95"]] = [4.0, False, True, 100.0]
    detections = frame["ts"] >= 9.0

    lower, upper = analysis.fermi_light_curve_display_ylim(frame, detections)

    assert lower == pytest.approx(-0.121)
    assert upper == pytest.approx(2.42)
