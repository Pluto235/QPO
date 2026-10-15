from __future__ import annotations

import csv
from pathlib import Path

import yaml

from pipeline.collect_official_qpo_spectral_fits import collect
from utils.project_paths import DATA_DIR


def test_collect_updates_only_validated_manifest_source(tmp_path: Path) -> None:
    registry = DATA_DIR / "config" / "official_qpo_source_models.yaml"
    registry_hash = __import__("hashlib").sha256(registry.read_bytes()).hexdigest()
    log = tmp_path / "fit.log"
    log.write_text("STATUS : OK\nTS = 12.0, BIC = 30.0, AIC = 22.0\n", encoding="utf-8")
    parres = tmp_path / "ParRes.yaml"
    parres.write_text("SRC:\n  Src0:\n    Epiv: 3\n    SEDModel:\n      type: PL\n      F0: [1.2, 0.0, 500.0, 0, 1e-12, 0.1]\n      alpha: [2.4, 1.0, 4.0, 0, 0.2]\n", encoding="utf-8")
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("source_id", "log", "parres", "registry_sha256", "data_config", "response_slot"))
        writer.writeheader()
        writer.writerow({"source_id": "mkn421", "log": log, "parres": parres, "registry_sha256": registry_hash, "data_config": "official.yaml", "response_slot": "Responsefile2"})

    result = collect(registry, [manifest], tmp_path / "collected.yaml")

    assert result["sources"] == ["mkn421"]
    data = yaml.safe_load((tmp_path / "collected.yaml").read_text(encoding="utf-8"))
    mkn421 = next(item for item in data["targets"] if item["source_id"] == "mkn421")
    assert mkn421["spectral_model"]["validation_status"] == "VERIFIED"
    assert mkn421["spectral_model"]["parameters"]["alpha"][0] == 2.4
    assert mkn421["spectral_model"]["dge_configuration"]["active"] is False


def test_collect_accepts_new_fit_log_manifest_field(tmp_path: Path) -> None:
    registry = DATA_DIR / "config" / "official_qpo_source_models.yaml"
    registry_hash = __import__("hashlib").sha256(registry.read_bytes()).hexdigest()
    log = tmp_path / "fit.log"
    log.write_text("STATUS : OK\nTS = 12.0, BIC = 30.0, AIC = 22.0\n", encoding="utf-8")
    parres = tmp_path / "ParRes.yaml"
    parres.write_text("SRC:\n  Src0:\n    Epiv: 3\n    SEDModel:\n      type: PL\n      F0: [1.2, 0.0, 500.0, 0, 1e-12, 0.1]\n      alpha: [2.4, 1.0, 4.0, 0, 0.2]\n", encoding="utf-8")
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("source_id", "fit_log", "parres", "registry_sha256", "data_config", "response_slot"))
        writer.writeheader()
        writer.writerow({"source_id": "mkn421", "fit_log": log, "parres": parres, "registry_sha256": registry_hash, "data_config": "official.yaml", "response_slot": "Responsefile2"})

    result = collect(registry, [manifest], tmp_path / "collected.yaml")

    assert result["sources"] == ["mkn421"]
