#!/usr/bin/env python3
"""Collect validated full-interval IHEP spectral fits into a new registry copy."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import sys
from typing import Any

import yaml


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from utils.official_spectral import parse_validated_pl_spectrum, spectrum_registry_record
    from utils.project_paths import DATA_DIR, PROJECT_ROOT
except ModuleNotFoundError:
    from official_spectral import parse_validated_pl_spectrum, spectrum_registry_record  # type: ignore[no-redef]

    PROJECT_ROOT = Path.cwd()
    DATA_DIR = PROJECT_ROOT / "data"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DATA_DIR / "config" / "official_qpo_source_models.yaml")
    parser.add_argument("--manifest", type=Path, action="append", required=True, help="One or more spectral_fit_manifest.csv paths.")
    parser.add_argument("--output", type=Path, required=True, help="New registry path; existing files are never replaced.")
    return parser.parse_args(argv)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(registry_path: Path, manifests: list[Path], output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite collected registry: {output}")
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(registry, dict) or not isinstance(registry.get("targets"), list):
        raise ValueError("Registry has no target list")
    registry_hash = _sha256(registry_path)
    target_by_id = {item.get("source_id"): item for item in registry["targets"] if isinstance(item, dict)}
    rows: list[dict[str, str]] = []
    for manifest in manifests:
        with manifest.open(newline="", encoding="utf-8") as handle:
            manifest_rows = list(csv.DictReader(handle))
        if not manifest_rows:
            raise ValueError(f"Empty spectral manifest: {manifest}")
        if any(row.get("registry_sha256") != registry_hash for row in manifest_rows):
            raise RuntimeError(f"Registry hash mismatch in manifest: {manifest}")
        rows.extend(manifest_rows)
    source_ids = [row.get("source_id") for row in rows]
    if len(source_ids) != len(set(source_ids)) or any(source_id not in target_by_id for source_id in source_ids):
        raise ValueError("Spectral manifests contain duplicate or unknown source IDs")
    for row in rows:
        log_value = row.get("fit_log") or row.get("log")
        if not log_value:
            raise ValueError("Spectral manifest row lacks fit_log")
        log_path, parres_path = Path(log_value), Path(row["parres"])
        spectrum = parse_validated_pl_spectrum(log_path.read_text(encoding="utf-8"), parres_path.read_text(encoding="utf-8"))
        target = target_by_id[row["source_id"]]
        dge_policy = target.get("dge_policy")
        if not isinstance(dge_policy, dict) or not isinstance(dge_policy.get("active"), bool):
            raise ValueError(f"Target {row['source_id']} lacks an explicit DGE policy")
        if "dge_active" in row and row["dge_active"] != str(int(dge_policy["active"])):
            raise RuntimeError(f"DGE active-state mismatch in manifest for {row['source_id']}")
        if "dge_decision" in row and row["dge_decision"] != str(dge_policy.get("decision")):
            raise RuntimeError(f"DGE decision mismatch in manifest for {row['source_id']}")
        target["spectral_model"] = spectrum_registry_record(
            spectrum,
            provenance={
                "method": "full_interval_public_v1_src_main",
                "manifest": str(row.get("manifest", "")),
                "log": str(log_path), "log_sha256": _sha256(log_path),
                "parres": str(parres_path), "parres_sha256": _sha256(parres_path),
                "data_config": row["data_config"], "response_slot": row["response_slot"],
                "dge_policy": dge_policy,
            },
            dge_active=dge_policy["active"],
            dge_decision=str(dge_policy.get("decision", "")),
        )
    registry["survey_status"] = "CONFIGURATION_PENDING_DGE_PROFILE_SMOKE"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    return {"sources": sorted(source_ids), "output": str(output), "output_sha256": _sha256(output)}


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    registry = args.registry if args.registry.is_absolute() else PROJECT_ROOT / args.registry
    output = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
    result = collect(registry, args.manifest, output)
    print(f"[OK] collected {len(result['sources'])} validated spectra -> {result['output']}")


if __name__ == "__main__":
    main()
