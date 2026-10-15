from __future__ import annotations

import csv
from pathlib import Path

import yaml

from pipeline.prepare_official_qpo_spectral_fits import FULL_INTERVAL_DATA_CONFIG, prepare
from utils.project_paths import DATA_DIR


def _fake_program_root(tmp_path: Path) -> Path:
    program_root = tmp_path / "v1.0"
    (program_root / "config" / "Data" / "WCDA" / "Cod").mkdir(parents=True)
    (program_root / "Src_Main").write_text("fake binary for manifest test\n", encoding="utf-8")
    (program_root / FULL_INTERVAL_DATA_CONFIG).write_text("Version: Cod\n", encoding="utf-8")
    return program_root


def test_prepare_creates_three_unverified_spectral_fit_jobs(tmp_path: Path) -> None:
    program_root = _fake_program_root(tmp_path)
    work_root = tmp_path / "jobs"

    summary = prepare(
        DATA_DIR / "config" / "official_qpo_source_models.yaml",
        program_root,
        work_root,
        overwrite=False,
        source_ids={"bllac", "ngc1275", "4c_p42d22"},
    )

    assert summary["expected_jobs"] == 3
    assert summary["submission_status"] == "PREPARED_NOT_SUBMITTED"
    with (work_root / "spectral_fit_manifest.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["source_id"] for row in rows} == {"bllac", "ngc1275", "4c_p42d22"}
    assert len((work_root / "spectral_fit_queue.args").read_text(encoding="utf-8").splitlines()) == 3
    assert "spectral_fit_queue.args" in (work_root / "spectral_fits.sub").read_text(encoding="utf-8")
    assert "source_id," not in (work_root / "spectral_fits.sub").read_text(encoding="utf-8")
    assert "$(fit_log)" in (work_root / "spectral_fits.sub").read_text(encoding="utf-8")
    assert "$(log)" not in (work_root / "spectral_fits.sub").read_text(encoding="utf-8")
    runner = (work_root / "run_spectral_fit.sh").read_text(encoding="utf-8")
    assert "set -eo pipefail\nsource " in runner
    assert "envf.sh\nset -u\n" in runner
    assert all(row["response_slot"] == "Responsefile2" for row in rows)
    parinits = {
        row["source_id"]: yaml.safe_load(Path(row["parinit_yaml"]).read_text(encoding="utf-8")) for row in rows
    }
    assert parinits["ngc1275"]["DGE"]["Active"] == 1
    assert parinits["bllac"]["DGE"]["Active"] == 1
    assert parinits["4c_p42d22"]["DGE"]["Active"] == 0
    dge_rows = {row["source_id"]: row for row in rows}
    assert dge_rows["ngc1275"]["dge_active"] == "1"
    assert dge_rows["bllac"]["dge_active"] == "1"
    assert dge_rows["4c_p42d22"]["dge_active"] == "0"
    assert dge_rows["4c_p42d22"]["dge_max_abs_galactic_latitude_deg"] == "15.0"
    assert dge_rows["4c_p42d22"]["dge_decision"] == "disabled_by_user_accepted_public_src_main_high_latitude_guard"
    assert all(parinit["SRC"]["ParStatus"] == {"Position": 1, "F0": 0, "Index": 0, "MorPar": 1} for parinit in parinits.values())
    assert all(parinit["SRC"]["Src0"]["SEDModel"]["alpha"][-1] == 0 for parinit in parinits.values())
    fit = yaml.safe_load(Path(rows[0]["fit_yaml"]).read_text(encoding="utf-8"))
    assert fit["DataUsed"]["WCDA"]["NbinUsed"] == [0, 6]


def test_prepare_refuses_to_replace_existing_work_without_flag(tmp_path: Path) -> None:
    program_root = _fake_program_root(tmp_path)
    work_root = tmp_path / "jobs"
    prepare(
        DATA_DIR / "config" / "official_qpo_source_models.yaml",
        program_root,
        work_root,
        overwrite=False,
        source_ids={"bllac", "ngc1275", "4c_p42d22"},
    )

    try:
        prepare(
            DATA_DIR / "config" / "official_qpo_source_models.yaml",
            program_root,
            work_root,
            overwrite=False,
            source_ids={"bllac", "ngc1275", "4c_p42d22"},
        )
    except FileExistsError:
        return
    raise AssertionError("prepare unexpectedly replaced an existing work root")
