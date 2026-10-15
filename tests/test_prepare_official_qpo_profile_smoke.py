from __future__ import annotations

import csv
from pathlib import Path

import yaml

from pipeline.prepare_official_qpo_profile_smoke import GRID_MULTIPLIERS, SMOKE_LC_IDS, build_parinit_yaml, prepare
from utils.project_paths import DATA_DIR


def _fake_program_root(tmp_path: Path) -> Path:
    root = tmp_path / "v1.0"
    (root / "config" / "Data" / "WCDA" / "Cod" / "LC" / "2Days").mkdir(parents=True)
    (root / "Src_Main").write_text("fake binary\n", encoding="utf-8")
    for lc_id, period in zip(SMOKE_LC_IDS, ("001", "048", "083")):
        (root / "config" / "Data" / "WCDA" / "Cod" / "LC" / "2Days" / f"Data_LC_{lc_id:04d}.yaml").write_text(
            "Responsefile1: root://example/Group2/T" + period + "/Response.root\n"
            "Responsefile2: root://example/Group1/T" + period + "/Response.root\n",
            encoding="utf-8",
        )
    return root


def _registry_with_local_dge(tmp_path: Path) -> Path:
    registry = yaml.safe_load((DATA_DIR / "config" / "official_qpo_source_models.yaml").read_text(encoding="utf-8"))
    dge_path = tmp_path / "dge.root"
    dge_path.write_text("fixture\n", encoding="utf-8")
    registry["dge"]["template_path"] = str(dge_path)
    path = tmp_path / "registry.yaml"
    path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    return path


def test_prepare_creates_exact_three_bin_profile_smoke(tmp_path: Path) -> None:
    program_root = _fake_program_root(tmp_path)
    registry = _registry_with_local_dge(tmp_path)
    summary = prepare(registry, program_root, tmp_path / "smoke", overwrite=False)

    assert summary["expected_profiles"] == 3
    assert summary["lc_ids"] == list(SMOKE_LC_IDS)
    assert summary["grid_multipliers"] == list(GRID_MULTIPLIERS) == [0.0625, 0.5, 1.0, 2.0, 16.0]
    assert Path(summary["registry"]).is_file()
    assert (tmp_path / "smoke" / "official_profile.py").is_file()
    with Path(summary["manifest"]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [int(row["lc_id"]) for row in rows] == list(SMOKE_LC_IDS)
    assert [row["response_period"] for row in rows] == ["T001", "T048", "T083"]
    parinit = yaml.safe_load(Path(rows[0]["normal_parinit_yaml"]).read_text(encoding="utf-8"))
    assert parinit["DGE"]["Active"] == 1
    assert parinit["SRC"]["ParStatus"] == {"Position": 1, "F0": 0, "Index": 1, "MorPar": 1}
    assert "--execute" in Path(summary["runner"]).read_text(encoding="utf-8")
    fit = yaml.safe_load(Path(rows[0]["normal_fit_yaml"]).read_text(encoding="utf-8"))
    assert not fit["Output"]["Outdir"].startswith("/")


def test_fixed_f0_parinit_has_fixed_source_normalization(tmp_path: Path) -> None:
    registry = yaml.safe_load((DATA_DIR / "config" / "official_qpo_source_models.yaml").read_text(encoding="utf-8"))
    target = next(item for item in registry["targets"] if item["source_id"] == "1es2344p514")

    parinit = build_parinit_yaml(target, registry["dge"], f0=2.5, fixed_f0=True)

    assert parinit["SRC"]["ParStatus"]["F0"] == 1
    assert parinit["SRC"]["Src0"]["SEDModel"]["F0"] == [2.5, 0.0, 500.0, 1, "1e-15"]
