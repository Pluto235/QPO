"""Build and validate frozen configuration records for the official QPO survey."""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, asin, cos, degrees, radians, sin
from pathlib import Path
from typing import Any, Iterable

import yaml


BLANK_VETO_RADIUS_DEG = 5.0
BLANK_RA_OFFSETS_DEG = (15, -15, 30, -30, 45, -45, 60, -60, 90, -90, 120, -120, 150, -150, 180)
PUBLIC_DGE_MAX_ABS_GALACTIC_LATITUDE_DEG = 15.0
_GALACTIC_NORTH_POLE_RA_DEG = 192.85948
_GALACTIC_NORTH_POLE_DEC_DEG = 27.12825


@dataclass(frozen=True, slots=True)
class SkyPosition:
    """A named equatorial sky position in degrees."""

    name: str
    ra_deg: float
    dec_deg: float


def angular_separation_deg(left: SkyPosition, right: SkyPosition) -> float:
    """Return the great-circle separation, with numerical clipping at the poles."""

    left_ra, left_dec = radians(left.ra_deg), radians(left.dec_deg)
    right_ra, right_dec = radians(right.ra_deg), radians(right.dec_deg)
    cosine = sin(left_dec) * sin(right_dec) + cos(left_dec) * cos(right_dec) * cos(left_ra - right_ra)
    return degrees(acos(max(-1.0, min(1.0, cosine))))


def galactic_latitude_deg(position: SkyPosition) -> float:
    """Return IAU Galactic latitude for an ICRS/J2000 position in degrees."""

    ra, dec = radians(position.ra_deg), radians(position.dec_deg)
    pole_ra, pole_dec = radians(_GALACTIC_NORTH_POLE_RA_DEG), radians(_GALACTIC_NORTH_POLE_DEC_DEG)
    sine_latitude = sin(dec) * sin(pole_dec) + cos(dec) * cos(pole_dec) * cos(ra - pole_ra)
    return degrees(asin(max(-1.0, min(1.0, sine_latitude))))


def public_dge_policy(position: SkyPosition) -> dict[str, Any]:
    """Encode the user-approved public-v1 DGE guard for one ROI center."""

    latitude = galactic_latitude_deg(position)
    active = abs(latitude) <= PUBLIC_DGE_MAX_ABS_GALACTIC_LATITUDE_DEG
    return {
        "galactic_latitude_deg": round(latitude, 6),
        "public_src_main_max_abs_galactic_latitude_deg": PUBLIC_DGE_MAX_ABS_GALACTIC_LATITUDE_DEG,
        "active": active,
        "decision": (
            "public_dge_active_within_supported_galactic_latitude"
            if active
            else "disabled_by_user_accepted_public_src_main_high_latitude_guard"
        ),
    }


def load_lhaaso_catalog_positions(path: Path) -> list[SkyPosition]:
    """Extract source coordinates from the public 1LHAASO WCDA YAML catalog."""

    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("source_dict"), dict):
        raise ValueError(f"{path} does not have the expected source_dict catalog schema")

    positions: list[SkyPosition] = []
    for name, item in data["source_dict"].items():
        if not isinstance(item, dict) or not isinstance(item.get("spatial_model"), dict):
            continue
        spatial = item["spatial_model"]
        try:
            positions.append(
                SkyPosition(
                    str(name),
                    float(spatial["ra"][0]),
                    float(spatial["dec"][0]),
                )
            )
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ValueError(f"Catalog source {name!r} lacks a parseable position") from exc
    if not positions:
        raise ValueError(f"No catalog coordinates parsed from {path}")
    return positions


def select_same_declination_blanks(
    targets: Iterable[SkyPosition],
    veto_catalog: Iterable[SkyPosition],
    *,
    veto_radius_deg: float = BLANK_VETO_RADIUS_DEG,
    offsets_deg: Iterable[int] = BLANK_RA_OFFSETS_DEG,
) -> dict[str, SkyPosition]:
    """Choose one predeclared catalog-vetoed same-declination blank per target.

    Candidate positions are assessed in the given RA-offset order before any
    periodogram is available. Every selected blank must clear the public catalog,
    every target, and every previously selected blank by ``veto_radius_deg``.
    """

    fixed_targets = list(targets)
    protected = list(veto_catalog) + fixed_targets
    selected: dict[str, SkyPosition] = {}
    for target in fixed_targets:
        for offset in offsets_deg:
            candidate = SkyPosition(
                name=f"blank_{target.name}",
                ra_deg=(target.ra_deg + offset) % 360.0,
                dec_deg=target.dec_deg,
            )
            if all(angular_separation_deg(candidate, other) > veto_radius_deg for other in protected):
                selected[target.name] = candidate
                protected.append(candidate)
                break
        else:
            raise ValueError(f"No catalog-vetoed blank found for {target.name}")
    return selected


def validate_registry(registry: dict[str, Any], *, require_production_ready: bool) -> None:
    """Validate frozen scope and block production while required evidence is absent."""

    targets = registry.get("targets")
    blanks = registry.get("blank_controls")
    if not isinstance(targets, list) or len(targets) != 10:
        raise ValueError("Registry must contain exactly 10 frozen target records")
    if not isinstance(blanks, list) or len(blanks) != 10:
        raise ValueError("Registry must contain exactly 10 frozen blank controls")

    target_ids = {item.get("source_id") for item in targets if isinstance(item, dict)}
    if len(target_ids) != 10 or None in target_ids:
        raise ValueError("Target source IDs must be present and unique")
    for target in targets:
        _validate_position(target, "target")
        _validate_dge_policy(target, "target")
        spectrum = target.get("spectral_model")
        if not isinstance(spectrum, dict):
            raise ValueError(f"Target {target.get('source_id')} has no spectral_model record")
        if require_production_ready and spectrum.get("validation_status") != "VERIFIED":
            raise ValueError(f"Target {target.get('source_id')} spectrum is not production-verified")
    for blank in blanks:
        _validate_position(blank, "blank control")
        _validate_dge_policy(blank, "blank control")
        if blank.get("matched_target_id") not in target_ids:
            raise ValueError(f"Blank {blank.get('source_id')} is not linked to a frozen target")
    dge = registry.get("dge")
    if not isinstance(dge, dict) or not dge.get("template_path"):
        raise ValueError("Registry must record the public DGE template path")
    if require_production_ready and dge.get("validation_status") != "VERIFIED":
        raise ValueError("DGE configuration is not production-verified")
    crab = registry.get("crab_control")
    if not isinstance(crab, dict):
        raise ValueError("Registry must contain the Crab control")
    _validate_position(crab, "Crab control")
    _validate_dge_policy(crab, "Crab control")


def _validate_position(record: dict[str, Any], kind: str) -> None:
    try:
        ra = float(record["ra_deg"])
        dec = float(record["dec_deg"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{kind} has no valid coordinates") from exc
    if not 0.0 <= ra < 360.0 or not -90.0 <= dec <= 90.0:
        raise ValueError(f"{kind} coordinates are out of range: ra={ra}, dec={dec}")


def _validate_dge_policy(record: dict[str, Any], kind: str) -> None:
    policy = record.get("dge_policy")
    if not isinstance(policy, dict) or not isinstance(policy.get("active"), bool):
        raise ValueError(f"{kind} lacks an explicit public-DGE policy")
    try:
        latitude = float(policy["galactic_latitude_deg"])
        threshold = float(policy["public_src_main_max_abs_galactic_latitude_deg"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{kind} has an invalid public-DGE policy") from exc
    if threshold != PUBLIC_DGE_MAX_ABS_GALACTIC_LATITUDE_DEG:
        raise ValueError(f"{kind} has an unexpected public-DGE latitude threshold")
    if policy["active"] != (abs(latitude) <= threshold):
        raise ValueError(f"{kind} public-DGE state disagrees with its Galactic latitude")
