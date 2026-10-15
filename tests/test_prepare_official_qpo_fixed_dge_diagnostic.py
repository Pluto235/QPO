from __future__ import annotations

import csv
from pathlib import Path

import yaml

from pipeline.prepare_official_qpo_fixed_dge_diagnostic import prepare


def test_prepare_fixed_dge_diagnostic_keeps_template_active(tmp_path: Path) -> None:
    program_root = tmp_path / "program"
    program_root.mkdir()
    (program_root / "Src_Main").write_text("fixture\n", encoding="utf-8")
    pilot = tmp_path / "pilot"
    normal = pilot / "LC0402" / "normal"
    normal.joinpath("out").mkdir(parents=True)
    fit = {"WorkDir": str(program_root), "Output": {"Outdir": "old", "fParResu": "ParRes.yaml"}}
    parinit = {
        "DGE": {"Active": 1, "Template0": {"SEDModel": {"F0": [7.0, 0.0, 200.0, 0], "alpha": [2.6, 1.0, 4.0, 0]}}},
        "SRC": {"ParStatus": {"F0": 0}, "Src0": {"SEDModel": {"F0": [1.0, 0.0, 500.0, 0, "1e-12"]}}},
    }
    (normal / "Fit.yaml").write_text(yaml.safe_dump(fit), encoding="utf-8")
    (normal / "ParInit.yaml").write_text(yaml.safe_dump(parinit), encoding="utf-8")
    (normal / "out" / "ParRes.yaml").write_text(yaml.safe_dump({"SRC": {"Src0": {"SEDModel": {"F0": [0.1, 0.0, 500.0, 0, "1e-12"]}}}}), encoding="utf-8")
    with (pilot / "profile_smoke_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("lc_id", "normal_fit_yaml", "normal_parinit_yaml", "normal_parres"))
        writer.writeheader()
        writer.writerow({"lc_id": 402, "normal_fit_yaml": normal / "Fit.yaml", "normal_parinit_yaml": normal / "ParInit.yaml", "normal_parres": normal / "out" / "ParRes.yaml"})

    summary = prepare(pilot, tmp_path / "diagnostic", lc_id=402)

    assert summary["expected_jobs"] == 2
    assert "$(fit_log)" in Path(summary["submit"]).read_text(encoding="utf-8")
    assert "queue program_root,fit_yaml,parinit_yaml,fit_log" in Path(summary["submit"]).read_text(encoding="utf-8")
    normal_parinit = yaml.safe_load((tmp_path / "diagnostic" / "normal" / "ParInit.yaml").read_text(encoding="utf-8"))
    fixed_parinit = yaml.safe_load((tmp_path / "diagnostic" / "fixed_f0" / "ParInit.yaml").read_text(encoding="utf-8"))
    assert normal_parinit["DGE"]["Active"] == 1
    assert normal_parinit["DGE"]["Template0"]["SEDModel"]["F0"][3] == 1
    assert normal_parinit["DGE"]["Template0"]["SEDModel"]["alpha"][3] == 1
    assert fixed_parinit["SRC"]["ParStatus"]["F0"] == 1
    assert fixed_parinit["SRC"]["Src0"]["SEDModel"]["F0"] == [0.1, 0.0, 500.0, 1, "1e-12"]
