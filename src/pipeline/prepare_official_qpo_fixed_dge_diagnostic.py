#!/usr/bin/env python3
"""Prepare a two-row fixed-DGE HTCondor diagnostic for one profile-pilot bin.

This is a numerical-boundary diagnostic only.  It keeps the public DGE template
active, while fixing its tutorial spectrum to test whether an unconstrained DGE
nuisance is solely responsible for a low-flux ``STATUS: NotOK`` result.  It is
not a production light-curve generator and never submits jobs itself.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

import yaml


IHEP_ENV_SCRIPT = "/cvmfs/lhaaso.ihep.ac.cn/anysw/slc6_ia64_gcc73/external/envf.sh"
FIELDS = ("kind", "program_root", "fit_yaml", "parinit_yaml", "fit_log")
QUEUE_FIELDS = FIELDS[1:]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-root", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--lc-id", type=int, default=402)
    return parser.parse_args(argv)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_yaml(path: Path) -> dict[str, object]:
    result = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return result


def _write_yaml(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _freeze_dge(parinit: dict[str, object]) -> None:
    try:
        sed = parinit["DGE"]["Template0"]["SEDModel"]  # type: ignore[index]
        for name in ("F0", "alpha"):
            values = sed[name]
            if not isinstance(values, list) or len(values) < 4:
                raise ValueError(f"DGE {name} has an invalid public-template schema")
            values[3] = 1
    except (KeyError, TypeError) as exc:
        raise ValueError("ParInit lacks the public Template0 DGE spectrum") from exc


def _source_f0(parres: dict[str, object]) -> tuple[float, str]:
    try:
        values = parres["SRC"]["Src0"]["SEDModel"]["F0"]  # type: ignore[index]
        return float(values[0]), str(values[4])
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise ValueError("Ordinary pilot ParRes lacks source F0") from exc


def _fix_source_f0(parinit: dict[str, object], f0: float, order: str) -> None:
    try:
        parinit["SRC"]["ParStatus"]["F0"] = 1  # type: ignore[index]
        parinit["SRC"]["Src0"]["SEDModel"]["F0"] = [f0, 0.0, 500.0, 1, order]  # type: ignore[index]
    except (KeyError, TypeError) as exc:
        raise ValueError("ParInit lacks source F0 configuration") from exc


def _set_outdir(fit: dict[str, object], program_root: Path, output_dir: Path) -> None:
    try:
        fit["Output"]["Outdir"] = os.path.relpath(output_dir, program_root)  # type: ignore[index]
    except (KeyError, TypeError) as exc:
        raise ValueError("Fit YAML lacks Output.Outdir") from exc


def _write_runner(work_root: Path) -> Path:
    path = work_root / "run_fixed_dge_diagnostic.sh"
    path.write_text(
        "#!/usr/bin/env bash\n"
        "set -eo pipefail\n"
        f"source {IHEP_ENV_SCRIPT}\n"
        "set -u\n"
        "program_root=$1\nfit_yaml=$2\nparinit_yaml=$3\nfit_log=$4\n"
        "cd \"$program_root\"\n"
        "\"$program_root/Src_Main\" \"$fit_yaml\" \"$parinit_yaml\" > \"$fit_log\" 2>&1\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)
    return path


def prepare(pilot_root: Path, work_root: Path, *, lc_id: int) -> dict[str, object]:
    if work_root.exists() and any(work_root.iterdir()):
        raise FileExistsError(f"Refusing to replace diagnostic root: {work_root}")
    with (pilot_root / "profile_smoke_manifest.csv").open(newline="", encoding="utf-8") as handle:
        normal = next((row for row in csv.DictReader(handle) if int(row["lc_id"]) == lc_id), None)
    if normal is None:
        raise ValueError(f"Pilot manifest lacks LC{lc_id:04d}")
    fit = _read_yaml(Path(normal["normal_fit_yaml"]))
    parinit = _read_yaml(Path(normal["normal_parinit_yaml"]))
    parres = _read_yaml(Path(normal["normal_parres"]))
    program_root = Path(str(fit["WorkDir"]))
    if not (program_root / "Src_Main").is_file():
        raise FileNotFoundError(f"Src_Main missing under {program_root}")
    f0, order = _source_f0(parres)
    work_root.mkdir(parents=True)
    rows: list[dict[str, str]] = []
    for kind in ("normal", "fixed_f0"):
        job_dir = work_root / kind
        output = job_dir / "out"
        output.mkdir(parents=True)
        fit_value = json.loads(json.dumps(fit))
        parinit_value = json.loads(json.dumps(parinit))
        _set_outdir(fit_value, program_root, output)
        _freeze_dge(parinit_value)
        if kind == "fixed_f0":
            _fix_source_f0(parinit_value, f0, order)
        fit_path, parinit_path = job_dir / "Fit.yaml", job_dir / "ParInit.yaml"
        _write_yaml(fit_path, fit_value)
        _write_yaml(parinit_path, parinit_value)
        rows.append({
            "kind": kind,
            "program_root": str(program_root),
            "fit_yaml": str(fit_path),
            "parinit_yaml": str(parinit_path),
            "fit_log": str(job_dir / "fit.log"),
        })
    args = work_root / "fixed_dge_diagnostic.args"
    args.write_text("".join(" ".join(row[field] for field in QUEUE_FIELDS) + "\n" for row in rows), encoding="utf-8")
    runner = _write_runner(work_root)
    submit = work_root / "fixed_dge_diagnostic.sub"
    submit.write_text(
        f"""universe = vanilla
executable = {runner}
arguments = $(program_root) $(fit_yaml) $(parinit_yaml) $(fit_log)
should_transfer_files = NO
getenv = True
request_cpus = 1
request_memory = 4000 MB
request_disk = 4000 MB
accounting_group = LHAASO.lhaaso.default
+HepJob_Experiment = \"LHAASO\"
+HepJob_RealGroup = \"lhaaso\"
+HepJob_RequestOS = \"AlmaLinux9\"
+IHEP_RealGroup = \"lhaaso\"
+ProjectName = \"qpo_official_fixed_dge_diagnostic\"
+JobBatchName = \"qpo_official_fixed_dge_diagnostic\"
output = {work_root}/logs/$(ClusterId)_$(ProcId).out
error = {work_root}/logs/$(ClusterId)_$(ProcId).err
log = {work_root}/logs/$(ClusterId).log
queue program_root,fit_yaml,parinit_yaml,fit_log from {args}
""",
        encoding="utf-8",
    )
    (work_root / "logs").mkdir()
    summary = {
        "purpose": "non-production LC0402 DGE-boundary diagnostic",
        "lc_id": lc_id,
        "ordinary_pilot_root": str(pilot_root),
        "ordinary_f0": f0,
        "dge_template_active": True,
        "dge_f0_and_alpha_fixed_to_public_template": True,
        "expected_jobs": len(rows),
        "args": str(args),
        "args_sha256": _sha256(args),
        "submit": str(submit),
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (work_root / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    summary = prepare(args.pilot_root, args.work_root, lc_id=args.lc_id)
    print(f"[OK] prepared {summary['expected_jobs']} fixed-DGE diagnostic jobs; not submitted")


if __name__ == "__main__":
    main()
