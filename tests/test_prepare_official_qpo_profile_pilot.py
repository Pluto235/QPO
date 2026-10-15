from __future__ import annotations

import csv
from pathlib import Path

import yaml

from pipeline.prepare_official_qpo_profile_pilot import collect_scan_pilot, prepare_normal_pilot, prepare_scan_pilot
from pipeline.prepare_official_qpo_profile_smoke import SMOKE_LC_IDS
from utils.project_paths import DATA_DIR


def _fake_program_root(tmp_path: Path) -> Path:
    root = tmp_path / "v1.0"
    (root / "config" / "Data" / "WCDA" / "Cod" / "LC" / "2Days").mkdir(parents=True)
    (root / "Src_Main").write_text("fake binary\n", encoding="utf-8")
    for lc_id, period in zip(SMOKE_LC_IDS, ("001", "048", "083")):
        (root / "config" / "Data" / "WCDA" / "Cod" / "LC" / "2Days" / f"Data_LC_{lc_id:04d}.yaml").write_text(
            f"Responsefile1: root://example/Group2/T{period}/Response.root\nResponsefile2: root://example/Group1/T{period}/Response.root\n",
            encoding="utf-8",
        )
    return root


def test_normal_profile_pilot_is_headerless_and_not_submitted(tmp_path: Path) -> None:
    registry = yaml.safe_load((DATA_DIR / "config" / "official_qpo_source_models.yaml").read_text(encoding="utf-8"))
    dge_path = tmp_path / "dge.root"
    dge_path.write_text("fixture\n", encoding="utf-8")
    registry["dge"]["template_path"] = str(dge_path)
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")

    summary = prepare_normal_pilot(registry_path, _fake_program_root(tmp_path), tmp_path / "pilot", overwrite=False)

    assert summary["stage"] == "NORMAL_PREPARED_NOT_SUBMITTED"
    assert summary["expected_normal_jobs"] == 3
    assert summary["expected_scan_jobs_after_normal"] == 15
    args = Path(summary["normal_args"]).read_text(encoding="utf-8").splitlines()
    assert len(args) == 3
    assert not any("source_id" in row for row in args)
    submit = Path(summary["normal_submit"]).read_text(encoding="utf-8")
    assert "request_memory = 4000 MB" in submit
    assert "arguments = $(program_root) $(fit_yaml) $(parinit_yaml) $(fit_log)" in submit
    assert "queue program_root,fit_yaml,parinit_yaml,fit_log" in submit
    with Path(summary["smoke_manifest"]).open(newline="", encoding="utf-8") as handle:
        assert [int(row["lc_id"]) for row in csv.DictReader(handle)] == list(SMOKE_LC_IDS)


def test_collector_requires_exact_scan_coverage_and_writes_profiles(tmp_path: Path) -> None:
    registry = yaml.safe_load((DATA_DIR / "config" / "official_qpo_source_models.yaml").read_text(encoding="utf-8"))
    dge_path = tmp_path / "dge.root"
    dge_path.write_text("fixture\n", encoding="utf-8")
    registry["dge"]["template_path"] = str(dge_path)
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    work_root = tmp_path / "pilot"
    summary = prepare_normal_pilot(registry_path, _fake_program_root(tmp_path), work_root, overwrite=False)
    with Path(summary["smoke_manifest"]).open(newline="", encoding="utf-8") as handle:
        normal_rows = list(csv.DictReader(handle))
    for row in normal_rows:
        Path(row["normal_log"]).write_text("STATUS : OK\nTS = 2.0, BIC = 10.0, AIC = 8.0\n", encoding="utf-8")
        Path(row["normal_parres"]).parent.mkdir(parents=True, exist_ok=True)
        Path(row["normal_parres"]).write_text(
            "SRC:\n  Src0:\n    SEDModel:\n      F0: [1.0, 0.0, 500.0, 0, 1e-15]\n",
            encoding="utf-8",
        )
    prepare_scan_pilot(work_root)
    for line in (work_root / "fixed_f0_scan_queue.args").read_text(encoding="utf-8").splitlines():
        program_root, fit_yaml, parinit_yaml, fit_log, lc_id, f0 = line.split()
        del program_root, fit_yaml, parinit_yaml, lc_id
        # The MLE sits at the unit-normalization grid point.
        aic = {0.0625: 16.0, 0.5: 8.0, 1.0: 0.0, 2.0: 8.0, 16.0: 16.0}[float(f0)]
        Path(fit_log).write_text(f"STATUS : OK\nTS = 2.0, BIC = {aic + 2}, AIC = {aic}\n", encoding="utf-8")

    collected = collect_scan_pilot(work_root)

    assert collected["stage"] == "FIXED_F0_SCANS_COLLECTED"
    assert len(collected["profiles"]) == 3
    assert all(Path(row["profile_json"]).is_file() for row in normal_rows)


def test_prepare_scan_allows_only_the_explicit_physical_lower_boundary(tmp_path: Path) -> None:
    registry = yaml.safe_load((DATA_DIR / "config" / "official_qpo_source_models.yaml").read_text(encoding="utf-8"))
    dge_path = tmp_path / "dge.root"
    dge_path.write_text("fixture\n", encoding="utf-8")
    registry["dge"]["template_path"] = str(dge_path)
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    work_root = tmp_path / "pilot"
    summary = prepare_normal_pilot(registry_path, _fake_program_root(tmp_path), work_root, overwrite=False)
    with Path(summary["smoke_manifest"]).open(newline="", encoding="utf-8") as handle:
        normal_rows = list(csv.DictReader(handle))
    for row in normal_rows:
        status = "NotOK" if row["lc_id"] == "402" else "OK"
        Path(row["normal_log"]).write_text(f"STATUS : {status}\nTS = 2.0, BIC = 10.0, AIC = 8.0\n", encoding="utf-8")
        Path(row["normal_parres"]).parent.mkdir(parents=True, exist_ok=True)
        Path(row["normal_parres"]).write_text(
            "SRC:\n  Src0:\n    SEDModel:\n      F0: [1.e-5, 0.0, 500.0, 0, 1e-15]\n",
            encoding="utf-8",
        )
    prepared = prepare_scan_pilot(work_root)
    assert prepared["ordinary_lower_boundary_lc_ids"] == [402]
