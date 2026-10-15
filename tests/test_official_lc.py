from __future__ import annotations

from pathlib import Path

import pytest

from utils.official_lc import EXPECTED_BIN_COUNTS, read_all_official_lc_bins, read_official_lc_bins
from utils.project_paths import OFFICIAL_QPO_FIXTURE_DIR


CONFIG_ROOT = OFFICIAL_QPO_FIXTURE_DIR / "official_lc_configs"


def test_all_frozen_official_collections_parse() -> None:
    bins = read_all_official_lc_bins(CONFIG_ROOT)

    assert len(bins) == sum(EXPECTED_BIN_COUNTS.values())
    assert {item.cadence_days for item in bins} == {2, 8, 32}
    assert {item.response_period for item in bins} == {f"T{index:03d}" for index in range(1, 84)}
    assert all(item.nnhit == 7 for item in bins)


def test_declination_selects_the_recorded_public_response_slot() -> None:
    first = read_official_lc_bins(CONFIG_ROOT, 2)[0]

    assert first.response_for_declination(38.209) == ("Responsefile2", first.responsefile2)
    assert "/Group1/T001/Response.root" in first.responsefile2
    assert first.response_for_declination(12.45) == ("Responsefile1", first.responsefile1)
    assert "/Group2/T001/Response.root" in first.responsefile1


def test_invalid_config_missing_frozen_nhit_metadata_is_rejected(tmp_path: Path) -> None:
    config_dir = tmp_path / "2Days"
    config_dir.mkdir()
    (config_dir / "Data_LC_0001.yaml").write_text(
        "Mapfile: root://example/map.root\n"
        "Responsefile1: root://example/Group2/T001/Response.root\n"
        "Responsefile2: root://example/Group1/T001/Response.root\n"
        "Simufile1: root://example/simu1.root\n"
        "Simufile2: root://example/simu2.root\n"
        "Livetime: 1\n"
        "Nnhit: 7\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Nhit"):
        read_official_lc_bins(tmp_path, 2, require_expected_count=False)
