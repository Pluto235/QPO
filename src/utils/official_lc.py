"""Parse and validate official WCDA Cod light-curve DataConfigs.

This module handles only lightweight YAML configuration provenance. It does not
open ROOT files or evaluate a fit, so it is safe to run on ETO fixtures.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any

import yaml


OFFICIAL_LC_MJD0 = 59280.6666666667
SUPPORTED_CADENCES = (2, 8, 32)
EXPECTED_BIN_COUNTS = {2: 803, 8: 200, 32: 50}
EXPECTED_NHIT_EDGES = (30, 60, 100, 200, 300, 500, 800, 2000)
_CONFIG_NAME_RE = re.compile(r"Data_LC_(\d{4})\.yaml$")
_RESPONSE_PERIOD_RE = re.compile(r"/T(\d{3})/Response\.root$")


@dataclass(frozen=True, slots=True)
class OfficialLCBin:
    """One official cadence bin and its response provenance."""

    cadence_days: int
    lc_id: int
    mjd: float
    config_path: str
    mapfile: str
    response_period: str
    responsefile1: str
    responsefile2: str
    simufile1: str
    simufile2: str
    livetime_s: float
    nnhit: int
    nhit_edges: tuple[int, ...]

    def response_for_declination(self, declination_deg: float) -> tuple[str, str]:
        """Return the public response slot selected by the official convention."""

        if declination_deg < 28.0:
            return "Responsefile1", self.responsefile1
        return "Responsefile2", self.responsefile2

    def as_manifest_row(self) -> dict[str, object]:
        row = asdict(self)
        row["nhit_edges"] = ";".join(str(edge) for edge in self.nhit_edges)
        return row


def read_official_lc_bins(
    config_root: Path,
    cadence_days: int,
    *,
    require_expected_count: bool = True,
) -> list[OfficialLCBin]:
    """Read an official ``Data_LC_XXXX.yaml`` collection in stable ID order."""

    if cadence_days not in SUPPORTED_CADENCES:
        raise ValueError(f"Unsupported official cadence {cadence_days}; expected one of {SUPPORTED_CADENCES}.")

    config_dir = Path(config_root) / f"{cadence_days}Days"
    if not config_dir.is_dir():
        raise FileNotFoundError(f"Official LC config directory not found: {config_dir}")

    bins: list[OfficialLCBin] = []
    for path in sorted(config_dir.glob("Data_LC_*.yaml")):
        name_match = _CONFIG_NAME_RE.fullmatch(path.name)
        if name_match is None:
            continue
        data = _read_yaml_mapping(path)
        bins.append(_parse_config(path, cadence_days, int(name_match.group(1)), data))

    if not bins:
        raise ValueError(f"No official LC configs found in {config_dir}")
    _validate_collection(bins, cadence_days, require_expected_count=require_expected_count)
    return bins


def read_all_official_lc_bins(
    config_root: Path,
    *,
    require_expected_count: bool = True,
) -> list[OfficialLCBin]:
    """Read all frozen 2/8/32-day official config collections."""

    return [
        item
        for cadence_days in SUPPORTED_CADENCES
        for item in read_official_lc_bins(
            config_root,
            cadence_days,
            require_expected_count=require_expected_count,
        )
    ]


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def _parse_config(path: Path, cadence_days: int, lc_id: int, data: dict[str, Any]) -> OfficialLCBin:
    required = {
        "Nnhit",
        "Nhit",
        "Livetime",
        "Mapfile",
        "Responsefile1",
        "Responsefile2",
        "Simufile1",
        "Simufile2",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"{path} is missing required keys: {missing}")

    try:
        nnhit = int(data["Nnhit"])
        nhit_edges = tuple(int(value) for value in data["Nhit"])
        livetime_s = float(data["Livetime"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path} has invalid nhit or livetime metadata") from exc

    if nnhit != 7 or nhit_edges != EXPECTED_NHIT_EDGES:
        raise ValueError(
            f"{path} does not retain the frozen seven-nhit configuration: "
            f"Nnhit={nnhit}, Nhit={nhit_edges}"
        )
    if not livetime_s > 0:
        raise ValueError(f"{path} has non-positive Livetime={livetime_s}")

    responsefile1 = str(data["Responsefile1"])
    responsefile2 = str(data["Responsefile2"])
    response_period1 = _response_period(path, responsefile1)
    response_period2 = _response_period(path, responsefile2)
    if response_period1 != response_period2:
        raise ValueError(f"{path} has inconsistent response periods: {response_period1}, {response_period2}")

    return OfficialLCBin(
        cadence_days=cadence_days,
        lc_id=lc_id,
        mjd=OFFICIAL_LC_MJD0 + (lc_id - 0.5) * cadence_days,
        config_path=str(path),
        mapfile=str(data["Mapfile"]),
        response_period=f"T{response_period1}",
        responsefile1=responsefile1,
        responsefile2=responsefile2,
        simufile1=str(data["Simufile1"]),
        simufile2=str(data["Simufile2"]),
        livetime_s=livetime_s,
        nnhit=nnhit,
        nhit_edges=nhit_edges,
    )


def _response_period(config_path: Path, response_path: str) -> str:
    match = _RESPONSE_PERIOD_RE.search(response_path)
    if match is None:
        raise ValueError(f"{config_path} has an unparseable response path: {response_path}")
    return match.group(1)


def _validate_collection(
    bins: list[OfficialLCBin],
    cadence_days: int,
    *,
    require_expected_count: bool,
) -> None:
    ids = [item.lc_id for item in bins]
    if ids != list(range(1, len(bins) + 1)):
        raise ValueError(f"Official {cadence_days}-day LC IDs are not contiguous from 1: {ids[:3]} ... {ids[-3:]}")
    expected_count = EXPECTED_BIN_COUNTS[cadence_days]
    if require_expected_count and len(bins) != expected_count:
        raise ValueError(f"Official {cadence_days}-day config count is {len(bins)}, expected {expected_count}")
