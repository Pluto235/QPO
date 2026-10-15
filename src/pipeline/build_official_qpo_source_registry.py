#!/usr/bin/env python3
"""Create the auditable frozen target/control registry for the official QPO survey."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import yaml


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.official_qpo_registry import (
    BLANK_RA_OFFSETS_DEG,
    BLANK_VETO_RADIUS_DEG,
    SkyPosition,
    load_lhaaso_catalog_positions,
    public_dge_policy,
    select_same_declination_blanks,
    validate_registry,
)
from utils.project_paths import DATA_DIR, OFFICIAL_QPO_FIXTURE_DIR, PROJECT_ROOT


TARGETS = (
    ("mkn421", "Mkn421", "Mrk 421", 166.114, 38.209),
    ("mkn501", "Mkn501", "Mrk 501", 253.468, 39.760),
    ("1es1959p650", "1ES1959p650", "1ES 1959+650", 299.950, 65.150),
    ("1es1727p502", "1ES1727p502", "1ES 1727+502", 262.050, 50.150),
    ("1es2344p514", "1ES2344p514", "1ES 2344+514", 356.750, 51.750),
    ("bllac", "BLLacertae", "BL Lacertae", 330.750, 42.150),
    ("ngc1275", "NGC1275", "NGC 1275", 49.950, 41.450),
    ("m87", "M87", "M 87", 187.750, 12.450),
    ("4c_p42d22", "4C_p42d22", "4C +42.22", 104.060, 42.600),
    ("ic310", "IC310", "IC 310", 49.050, 41.250),
)

COORDINATE_PROVENANCE = "docs/ihep-wcda-pull-tasklist.md, section 8 (frozen handoff coordinates)"
PUBLIC_DGE_PATH = "/home/lhaaso/hushicong/public/DGE_Template/gll_dust_process_Eqm.root"
PUBLISHED_ASSOCIATION_MAX_SEPARATION_DEG = 0.2
SRC_MAIN_SED_TYPES = {"PL", "LP", "PEC", "PSEC", "BPL", "SBPL", "SBPL2"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=OFFICIAL_QPO_FIXTURE_DIR / "catalog" / "2LHAASO.yaml",
    )
    parser.add_argument(
        "--blank-veto-catalog",
        type=Path,
        default=OFFICIAL_QPO_FIXTURE_DIR / "catalog" / "1LHAASO_wcda_all_info.yaml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DATA_DIR / "config" / "official_qpo_source_models.yaml",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args(argv)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _catalog_spectral_associations(catalog_path: Path) -> dict[str, dict[str, object]]:
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    source_dict = catalog.get("source_dict") if isinstance(catalog, dict) else None
    if not isinstance(source_dict, dict):
        raise ValueError(f"{catalog_path} does not have the expected source_dict catalog schema")

    catalog_rows = []
    for name, item in source_dict.items():
        spatial = item.get("spatial_model", {}) if isinstance(item, dict) else {}
        try:
            catalog_rows.append(
                (
                    str(name),
                    SkyPosition(str(name), float(spatial["ra"][0]), float(spatial["dec"][0])),
                    item["sed_model"],
                )
            )
        except (KeyError, IndexError, TypeError, ValueError):
            continue

    associations: dict[str, dict[str, object]] = {}
    for source_id, _, _, ra_deg, dec_deg in TARGETS:
        target = SkyPosition(source_id, ra_deg, dec_deg)
        name, position, sed_model = min(catalog_rows, key=lambda row: _angular_separation(target, row[1]))
        separation_deg = _angular_separation(target, position)
        if separation_deg <= PUBLISHED_ASSOCIATION_MAX_SEPARATION_DEG:
            associations[source_id] = {
                "catalog_source_id": name,
                "separation_deg": round(separation_deg, 6),
                "sed_model": sed_model,
            }
    return associations


def _angular_separation(left: SkyPosition, right: SkyPosition) -> float:
    from utils.official_qpo_registry import angular_separation_deg

    return angular_separation_deg(left, right)


def _target_record(
    source_id: str,
    token: str,
    label: str,
    ra_deg: float,
    dec_deg: float,
    association: dict[str, object] | None,
    catalog_path: Path,
) -> dict[str, object]:
    response_slot = "Responsefile1" if dec_deg < 28.0 else "Responsefile2"
    return {
        "source_id": source_id,
        "token": token,
        "label": label,
        "ra_deg": ra_deg,
        "dec_deg": dec_deg,
        "dge_policy": public_dge_policy(SkyPosition(source_id, ra_deg, dec_deg)),
        "response_slot_rule": {"threshold_deg": 28.0, "selected_slot": response_slot},
        "spectral_model": _spectral_record(association, catalog_path),
        "coordinate_provenance": COORDINATE_PROVENANCE,
        "roi_note": "single-target ROI",
        "source_confusion_note": (
            "Report as ROI variability; no multi-source ROI expansion."
            if source_id in {"ngc1275", "ic310"}
            else None
        ),
    }


def _spectral_record(association: dict[str, object] | None, catalog_path: Path) -> dict[str, object]:
    selection_rule = "published LHAASO spectrum, otherwise full-interval fit, otherwise Gamma=2.6 only if index is unconstrained"
    if association is None:
        return {
            "validation_status": "UNVERIFIED",
            "selection_rule": selection_rule,
            "current_action": "full_interval_fit_required",
            "model_type": None,
            "parameters": None,
            "provenance": None,
        }
    parameters = association["sed_model"]
    provenance = {
        "catalog": "public v1.0 2LHAASO catalog",
        "path": str(catalog_path),
        "catalog_source_id": association["catalog_source_id"],
        "position_association_max_separation_deg": PUBLISHED_ASSOCIATION_MAX_SEPARATION_DEG,
        "position_separation_deg": association["separation_deg"],
    }
    if parameters["sed_type"] not in SRC_MAIN_SED_TYPES:
        return {
            "validation_status": "UNVERIFIED",
            "selection_rule": selection_rule,
            "current_action": "full_interval_fit_required",
            "model_type": None,
            "parameters": None,
            "published_catalog_model_reference": {"model_type": parameters["sed_type"], "parameters": parameters, "provenance": provenance},
            "provenance": None,
            "compatibility_note": (
                f"Catalog {parameters['sed_type']} is not among public v1.0 Src_Main model tags; "
                "no authoritative conversion was found."
            ),
        }
    return {
        "validation_status": "VERIFIED",
        "selection_rule": selection_rule,
        "current_action": "translate the public catalog model to Src_Main syntax and verify in the profile smoke",
        "model_type": parameters["sed_type"],
        "parameters": parameters,
        "provenance": provenance,
    }


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    catalog_path = args.catalog if args.catalog.is_absolute() else PROJECT_ROOT / args.catalog
    blank_veto_catalog_path = (
        args.blank_veto_catalog if args.blank_veto_catalog.is_absolute() else PROJECT_ROOT / args.blank_veto_catalog
    )
    output = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
    if output.exists() and not args.overwrite:
        raise FileExistsError(f"Refusing to overwrite frozen registry without --overwrite: {output}")

    target_positions = [SkyPosition(source_id, ra, dec) for source_id, _, _, ra, dec in TARGETS]
    associations = _catalog_spectral_associations(catalog_path)
    blank_catalog_positions = load_lhaaso_catalog_positions(blank_veto_catalog_path)
    blank_positions = select_same_declination_blanks(target_positions, blank_catalog_positions)
    registry = {
        "schema_version": "official_qpo_source_registry_v2_public_dge_guard",
        "survey_status": "CONFIGURATION_PENDING_SOURCE_SPECTRA_AND_DGE_PROFILE_SMOKE",
        "frozen_protocol": "docs/official_daily_qpo_execution_plan.md",
        "targets": [
            _target_record(*target, associations.get(target[0]), catalog_path)
            for target in TARGETS
        ],
        "crab_control": {
            "source_id": "crab",
            "label": "Crab Nebula",
            "ra_deg": 83.6331,
            "dec_deg": 22.0145,
            "dge_policy": public_dge_policy(SkyPosition("crab", 83.6331, 22.0145)),
            "spectral_model": {
                "validation_status": "UNVERIFIED",
                "current_action": "confirm public-v1.0 tutorial model before production",
                "provenance": "/home/lhaaso/hushicong/public/v1.0/config/Tutorial/Example1_Crab/ParInit.yaml",
            },
        },
        "blank_selection": {
            "catalog_path": str(blank_veto_catalog_path),
            "catalog_sha256": _sha256(blank_veto_catalog_path),
            "catalog_name": "public v1.0 1LHAASO WCDA catalog",
            "veto_radius_deg": BLANK_VETO_RADIUS_DEG,
            "ra_offset_order_deg": list(BLANK_RA_OFFSETS_DEG),
            "selection_timing": "before target/control periodograms",
        },
        "blank_controls": [
            {
                "source_id": f"blank_{source_id}",
                "matched_target_id": source_id,
                "label": f"Catalog-vetoed blank for {label}",
                "ra_deg": blank_positions[source_id].ra_deg,
                "dec_deg": blank_positions[source_id].dec_deg,
                "dge_policy": public_dge_policy(blank_positions[source_id]),
                "spectrum_rule": "use the matched target fixed spectrum after that spectrum is validated",
            }
            for source_id, _, label, _, _ in TARGETS
        ],
        "dge": {
            "validation_status": "UNVERIFIED",
            "active": True,
            "convo_psf": True,
            "template_path": PUBLIC_DGE_PATH,
            "template_hist": "hTemp_ana",
            "interface_provenance": "/home/lhaaso/hushicong/public/v1.0/config/Tutorial/Example3_withDGE/ParInit.yaml",
            "public_tutorial_model": {
                "type": "PL",
                "F0": [7.64289, 0.0, 228.09, 0, "1.e-11"],
                "alpha": [2.60069, 1.0, 4.0, 0],
                "Epiv_TeV": 3,
            },
            "current_action": "validate the DGE parameterization in the three profile smoke bins",
            "high_latitude_policy": "User accepted 2026-08-05: set DGE.Active=0 where public Src_Main rejects |b| > 15 degrees; retain the public template for supported ROIs.",
        },
    }
    validate_registry(registry, require_production_ready=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    print(f"[OK] wrote frozen pending-validation registry -> {output.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
