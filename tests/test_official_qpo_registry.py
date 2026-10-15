from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from utils.official_qpo_registry import (
    BLANK_VETO_RADIUS_DEG,
    SkyPosition,
    angular_separation_deg,
    galactic_latitude_deg,
    load_lhaaso_catalog_positions,
    public_dge_policy,
    select_same_declination_blanks,
    validate_registry,
)
from utils.project_paths import DATA_DIR, OFFICIAL_QPO_FIXTURE_DIR


CATALOG_PATH = OFFICIAL_QPO_FIXTURE_DIR / "catalog" / "1LHAASO_wcda_all_info.yaml"
REGISTRY_PATH = DATA_DIR / "config" / "official_qpo_source_models.yaml"


def test_blank_selector_is_deterministic_and_catalog_vetoed() -> None:
    targets = [SkyPosition("first", 100.0, 42.0), SkyPosition("second", 200.0, 12.0)]
    catalog = [SkyPosition("catalog", 115.0, 42.0)]

    selected = select_same_declination_blanks(targets, catalog)

    assert selected["first"].ra_deg == 85.0
    assert selected["first"].dec_deg == 42.0
    for blank in selected.values():
        assert all(angular_separation_deg(blank, item) > BLANK_VETO_RADIUS_DEG for item in catalog + targets)


def test_public_dge_policy_matches_the_documented_galactic_latitude_guard() -> None:
    supported = SkyPosition("crab", 83.6331, 22.0145)
    rejected = SkyPosition("mkn421", 166.114, 38.209)

    assert abs(galactic_latitude_deg(supported)) < 15.0
    assert abs(galactic_latitude_deg(rejected)) > 15.0
    assert public_dge_policy(supported)["active"] is True
    assert public_dge_policy(rejected)["active"] is False


def test_frozen_registry_has_all_targets_and_vetoed_blanks() -> None:
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    catalog = load_lhaaso_catalog_positions(CATALOG_PATH)

    validate_registry(registry, require_production_ready=False)
    assert len(registry["targets"]) == 10
    assert len(registry["blank_controls"]) == 10
    for record in registry["targets"] + registry["blank_controls"] + [registry["crab_control"]]:
        assert isinstance(record["dge_policy"]["active"], bool)
    for blank in registry["blank_controls"]:
        position = SkyPosition(blank["source_id"], blank["ra_deg"], blank["dec_deg"])
        assert all(angular_separation_deg(position, item) > BLANK_VETO_RADIUS_DEG for item in catalog)


def test_pending_registry_cannot_be_used_for_production() -> None:
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))

    with pytest.raises(ValueError, match="not production-verified"):
        validate_registry(registry, require_production_ready=True)


def test_registry_uses_only_predeclared_close_2lhaaso_spectral_associations() -> None:
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    verified = [target for target in registry["targets"] if target["spectral_model"]["validation_status"] == "VERIFIED"]
    pending = [target for target in registry["targets"] if target["spectral_model"]["validation_status"] == "UNVERIFIED"]

    assert {target["source_id"] for target in verified} == {"1es2344p514"}
    assert {target["source_id"] for target in pending} == {
        "mkn421",
        "mkn501",
        "1es1959p650",
        "1es1727p502",
        "bllac",
        "ngc1275",
        "m87",
        "4c_p42d22",
        "ic310",
    }
    assert all(
        target["spectral_model"]["provenance"]["position_separation_deg"] <= 0.2 for target in verified
    )
