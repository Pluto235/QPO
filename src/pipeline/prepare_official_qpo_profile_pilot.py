#!/usr/bin/env python3
"""Prepare, but never submit, a two-stage HTCondor profile-likelihood pilot.

Stage one runs the three predeclared normal fits. Stage two is deliberately
blocked until all three normal ``ParRes.yaml`` files validate, then writes one
independent fixed-F0 scan task for each predeclared grid point. This keeps the
slow public ROOT minimization off the IHEP login node while retaining the exact
DGE/profile contract established by the smoke wrapper.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shlex
import stat
import sys
from typing import Any

import yaml

try:
    from pipeline.prepare_official_qpo_profile_smoke import (
        GRID_MULTIPLIERS,
        IHEP_ENV_SCRIPT,
        IHEP_PROGRAM_ROOT,
        SMOKE_LC_IDS,
        _fixed_grid,
        _parse_f0,
        _read_registry,
        _smoke_target,
        _write_yaml,
        build_fit_yaml,
        build_parinit_yaml,
        prepare as prepare_smoke,
        sha256,
    )
    from utils.official_profile import build_fixed_grid_profile, parse_src_main_fit_summary
    from utils.project_paths import DATA_DIR, PROJECT_ROOT
except ModuleNotFoundError:
    from prepare_official_qpo_profile_smoke import (  # type: ignore[no-redef]
        GRID_MULTIPLIERS,
        IHEP_ENV_SCRIPT,
        IHEP_PROGRAM_ROOT,
        SMOKE_LC_IDS,
        _fixed_grid,
        _parse_f0,
        _read_registry,
        _smoke_target,
        _write_yaml,
        build_fit_yaml,
        build_parinit_yaml,
        prepare as prepare_smoke,
        sha256,
    )
    from official_profile import build_fixed_grid_profile, parse_src_main_fit_summary  # type: ignore[no-redef]

    PROJECT_ROOT = Path.cwd()
    DATA_DIR = PROJECT_ROOT / "data"


NORMAL_ARGS_FIELDS = ("program_root", "fit_yaml", "parinit_yaml", "fit_log")
SCAN_ARGS_FIELDS = NORMAL_ARGS_FIELDS + ("lc_id", "f0")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DATA_DIR / "config" / "official_qpo_source_models.yaml")
    parser.add_argument("--program-root", type=Path, default=IHEP_PROGRAM_ROOT)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("/home/lhaaso/liushijie/QPO/JOBs_official_qpo_profile_pilot"),
    )
    parser.add_argument("--prepare-scans", action="store_true", help="Require all normal outputs, then prepare fixed-F0 scan jobs.")
    parser.add_argument("--collect-scans", action="store_true", help="Validate and collect all fixed-F0 pilot outputs into three profiles.")
    parser.add_argument("--overwrite", action="store_true", help="Allow rebuilding only a not-yet-submitted pilot root.")
    return parser.parse_args(argv)


def _write_runner(work_root: Path) -> Path:
    runner = work_root / "run_profile_fit.sh"
    runner.write_text(
        "#!/usr/bin/env bash\n"
        "set -eo pipefail\n"
        f"source {shlex.quote(IHEP_ENV_SCRIPT)}\n"
        "set -u\n"
        "program_root=$1\nfit_yaml=$2\nparinit_yaml=$3\nlog_path=$4\n"
        "cd \"$program_root\"\n"
        "\"$program_root/Src_Main\" \"$fit_yaml\" \"$parinit_yaml\" > \"$log_path\" 2>&1\n",
        encoding="utf-8",
    )
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)
    return runner


def _write_submit(work_root: Path, runner: Path, args_path: Path, *, name: str, extra_args: bool) -> Path:
    submit = work_root / f"{name}.sub"
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
+ProjectName = \"qpo_official_profile_pilot\"
+JobBatchName = \"qpo_official_profile_pilot_{name}\"
output = {work_root}/logs/{name}_$(ClusterId)_$(ProcId).out
error = {work_root}/logs/{name}_$(ClusterId)_$(ProcId).err
log = {work_root}/logs/{name}_$(ClusterId).log
queue program_root,fit_yaml,parinit_yaml,fit_log from {args_path}
""",
        encoding="utf-8",
    )
    return submit


def _write_args(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.write_text("".join(" ".join(row[field] for field in fields) + "\n" for row in rows), encoding="utf-8")


def _is_physical_lower_boundary_normal(normal_fit: Any, normal_parres: Path) -> bool:
    """Identify only the public-Minuit F0=0 boundary status for one-sided scans."""

    if normal_fit.status != "NotOK":
        return False
    data = yaml.safe_load(normal_parres.read_text(encoding="utf-8"))
    try:
        f0 = data["SRC"]["Src0"]["SEDModel"]["F0"]
        value, lower, upper = (float(f0[index]) for index in range(3))
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise ValueError(f"Cannot inspect ordinary-fit F0 bounds in {normal_parres}") from exc
    if not all(math.isfinite(item) for item in (value, lower, upper)) or upper <= lower:
        raise ValueError(f"Ordinary-fit F0 bounds are invalid in {normal_parres}")
    # The public executable prints values near, rather than exactly at, zero.
    tolerance = max(1e-8, abs(upper - lower) * 1e-6)
    return lower == 0.0 and lower <= value <= lower + tolerance


def prepare_normal_pilot(registry_path: Path, program_root: Path, work_root: Path, *, overwrite: bool) -> dict[str, Any]:
    """Create exactly three normal-fit pilot jobs without submitting them."""

    smoke = prepare_smoke(registry_path, program_root, work_root, overwrite=overwrite)
    manifest = Path(smoke["manifest"])
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if [int(row["lc_id"]) for row in rows] != list(SMOKE_LC_IDS):
        raise ValueError("Normal pilot must contain exactly the frozen smoke bins")
    normal_rows = [
        {
            "program_root": str(program_root.resolve()),
            "fit_yaml": row["normal_fit_yaml"],
            "parinit_yaml": row["normal_parinit_yaml"],
            "fit_log": row["normal_log"],
        }
        for row in rows
    ]
    (work_root / "logs").mkdir(exist_ok=True)
    args_path = work_root / "normal_fit_queue.args"
    _write_args(args_path, NORMAL_ARGS_FIELDS, normal_rows)
    runner = _write_runner(work_root)
    submit = _write_submit(work_root, runner, args_path, name="normal_profile_pilot", extra_args=False)
    summary_path = work_root / "profile_pilot_summary.json"
    summary = {
        "schema_version": "official_qpo_profile_pilot_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "purpose": "three-bin Phase 3 HTCondor pilot; not full LC production",
        "stage": "NORMAL_PREPARED_NOT_SUBMITTED",
        "expected_normal_jobs": len(normal_rows),
        "expected_scan_jobs_after_normal": len(normal_rows) * len(GRID_MULTIPLIERS),
        "smoke_manifest": str(manifest),
        "smoke_manifest_sha256": sha256(manifest),
        "normal_args": str(args_path),
        "normal_args_sha256": sha256(args_path),
        "normal_submit": str(submit),
        "src_main_sha256": smoke["src_main_sha256"],
        "grid_multipliers": list(GRID_MULTIPLIERS),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def prepare_scan_pilot(work_root: Path) -> dict[str, Any]:
    """Generate scan jobs only after every normal pilot result validates."""

    summary_path = work_root / "profile_pilot_summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(f"Normal pilot summary missing: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = Path(summary["smoke_manifest"])
    if sha256(manifest) != summary["smoke_manifest_sha256"]:
        raise RuntimeError("Normal smoke manifest hash changed before scan preparation")
    with manifest.open(newline="", encoding="utf-8") as handle:
        normal_rows = list(csv.DictReader(handle))
    registry = _read_registry(work_root / "registry.yaml")
    target = _smoke_target(registry)
    dge = registry["dge"]
    program_root = Path(json.loads((work_root / "profile_smoke_summary.json").read_text(encoding="utf-8"))["program_root"])
    scan_rows: list[dict[str, str]] = []
    lower_boundary_lc_ids: list[int] = []
    for normal in normal_rows:
        normal_log = Path(normal["normal_log"])
        normal_parres = Path(normal["normal_parres"])
        if not normal_log.is_file() or not normal_parres.is_file():
            raise FileNotFoundError(f"Normal pilot output is incomplete for LC{int(normal['lc_id']):04d}")
        normal_fit = parse_src_main_fit_summary(normal_log.read_text(encoding="utf-8"))
        lower_boundary = _is_physical_lower_boundary_normal(normal_fit, normal_parres)
        if normal_fit.status != "OK" and not lower_boundary:
            raise RuntimeError(f"Normal pilot is not STATUS: OK for LC{int(normal['lc_id']):04d}")
        if lower_boundary:
            lower_boundary_lc_ids.append(int(normal["lc_id"]))
        ordinary_f0, _ = _parse_f0(normal_parres)
        job_dir = Path(normal["normal_fit_yaml"]).parents[1]
        data_config = Path(normal["data_config"])
        for point_id, f0 in enumerate(_fixed_grid(ordinary_f0)):
            point_dir = job_dir / "scan" / f"p{point_id:02d}"
            point_dir.joinpath("out").mkdir(parents=True, exist_ok=True)
            fit_yaml = point_dir / "Fit.yaml"
            parinit_yaml = point_dir / "ParInit.yaml"
            _write_yaml(fit_yaml, build_fit_yaml(program_root, point_dir, target, data_config))
            _write_yaml(parinit_yaml, build_parinit_yaml(target, dge, f0=f0, fixed_f0=True))
            scan_rows.append({
                "program_root": str(program_root), "fit_yaml": str(fit_yaml), "parinit_yaml": str(parinit_yaml),
                "fit_log": str(point_dir / "scan.log"), "lc_id": normal["lc_id"], "f0": repr(f0),
            })
    expected = len(SMOKE_LC_IDS) * len(GRID_MULTIPLIERS)
    if len(scan_rows) != expected:
        raise AssertionError(f"Expected {expected} fixed-F0 pilot jobs, generated {len(scan_rows)}")
    args_path = work_root / "fixed_f0_scan_queue.args"
    _write_args(args_path, SCAN_ARGS_FIELDS, scan_rows)
    runner = work_root / "run_profile_fit.sh"
    submit = _write_submit(work_root, runner, args_path, name="fixed_f0_profile_pilot", extra_args=True)
    summary.update({
        "stage": "FIXED_F0_SCANS_PREPARED_NOT_SUBMITTED",
        "expected_scan_jobs": len(scan_rows),
        "scan_args": str(args_path),
        "scan_args_sha256": sha256(args_path),
        "scan_submit": str(submit),
        "ordinary_lower_boundary_lc_ids": lower_boundary_lc_ids,
    })
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def collect_scan_pilot(work_root: Path) -> dict[str, Any]:
    """Require exact scan coverage and emit only finite, bracketed profiles."""

    summary_path = work_root / "profile_pilot_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("stage") != "FIXED_F0_SCANS_PREPARED_NOT_SUBMITTED":
        raise ValueError("Fixed-F0 scan manifest has not been prepared")
    manifest = Path(summary["smoke_manifest"])
    with manifest.open(newline="", encoding="utf-8") as handle:
        normal_rows = {row["lc_id"]: row for row in csv.DictReader(handle)}
    args_path = Path(summary["scan_args"])
    if sha256(args_path) != summary["scan_args_sha256"]:
        raise RuntimeError("Fixed-F0 scan args hash changed before collection")
    scan_rows: list[dict[str, str]] = []
    for line in args_path.read_text(encoding="utf-8").splitlines():
        values = line.split()
        if len(values) != len(SCAN_ARGS_FIELDS):
            raise ValueError("Fixed-F0 scan args row has an unexpected column count")
        scan_rows.append(dict(zip(SCAN_ARGS_FIELDS, values)))
    expected = len(SMOKE_LC_IDS) * len(GRID_MULTIPLIERS)
    if len(scan_rows) != expected:
        raise ValueError(f"Fixed-F0 scan coverage is {len(scan_rows)}, expected {expected}")

    profiles: dict[str, str] = {}
    lower_boundary_lc_ids = {int(item) for item in summary.get("ordinary_lower_boundary_lc_ids", [])}
    for lc_id in map(str, SMOKE_LC_IDS):
        normal = normal_rows[lc_id]
        ordinary_log = Path(normal["normal_log"])
        ordinary_parres = Path(normal["normal_parres"])
        ordinary_summary = parse_src_main_fit_summary(ordinary_log.read_text(encoding="utf-8"))
        lower_boundary = int(lc_id) in lower_boundary_lc_ids
        if ordinary_summary.status != "OK" and not (lower_boundary and _is_physical_lower_boundary_normal(ordinary_summary, ordinary_parres)):
            raise RuntimeError(f"Normal pilot is not STATUS: OK for LC{int(lc_id):04d}")
        ordinary_f0, f0_order = _parse_f0(ordinary_parres)
        items = sorted((row for row in scan_rows if row["lc_id"] == lc_id), key=lambda row: float(row["f0"]))
        if len(items) != len(GRID_MULTIPLIERS):
            raise ValueError(f"LC{int(lc_id):04d} scan coverage is incomplete")
        f0_values = [float(item["f0"]) for item in items]
        expected_grid = _fixed_grid(ordinary_f0)
        if f0_values != expected_grid:
            raise RuntimeError(f"LC{int(lc_id):04d} fixed-F0 grid differs from the immutable ordinary MLE grid")
        parsed = []
        for item in items:
            log = Path(item["fit_log"])
            if not log.is_file():
                raise FileNotFoundError(f"Fixed-F0 log missing: {log}")
            point = parse_src_main_fit_summary(log.read_text(encoding="utf-8"))
            if point.status != "OK":
                raise RuntimeError(f"Fixed-F0 scan is not STATUS: OK: {log}")
            parsed.append(point)
        profile = build_fixed_grid_profile(f0_values, parsed, allow_lower_boundary_mle=lower_boundary)
        mle_f0 = min(profile, key=lambda point: point.delta_log_likelihood).f0
        result = {
            "schema_version": "official_qpo_fixed_f0_profile_v1",
            "source_id": normal["source_id"], "cadence_days": int(normal["cadence_days"]),
            "lc_id": int(lc_id), "mjd": float(normal["mjd"]), "response_period": normal["response_period"],
            "response_slot": normal["response_slot"], "response_file": normal["response_file"], "data_config": normal["data_config"],
            "ordinary_fit": {"f0": ordinary_f0, "f0_order": f0_order, "aic": ordinary_summary.aic, "bic": ordinary_summary.bic, "ts": ordinary_summary.ts, "status": ordinary_summary.status, "physical_lower_boundary": lower_boundary, "log": str(ordinary_log)},
            "profile_mle_f0": mle_f0, "profile_mle_matches_ordinary": mle_f0 == ordinary_f0,
            "profile_physical_lower_boundary": lower_boundary and mle_f0 == f0_values[0],
            "points": [{**asdict(point), "log": item["fit_log"], "fit_yaml_sha256": sha256(Path(item["fit_yaml"])), "parinit_yaml_sha256": sha256(Path(item["parinit_yaml"]))} for item, point in zip(items, profile)],
        }
        output = Path(normal["profile_json"])
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        profiles[lc_id] = sha256(output)
    summary.update({"stage": "FIXED_F0_SCANS_COLLECTED", "profiles": profiles, "collected_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.prepare_scans and args.collect_scans:
        raise ValueError("Choose only one pilot transition at a time")
    if args.collect_scans:
        summary = collect_scan_pilot(args.work_root)
        print(f"[OK] collected {len(summary['profiles'])} validated fixed-F0 pilot profiles")
        return
    if args.prepare_scans:
        summary = prepare_scan_pilot(args.work_root)
        print(f"[OK] prepared {summary['expected_scan_jobs']} fixed-F0 pilot jobs; not submitted")
        return
    registry = args.registry if args.registry.is_absolute() else PROJECT_ROOT / args.registry
    summary = prepare_normal_pilot(registry, args.program_root, args.work_root, overwrite=args.overwrite)
    print(f"[OK] prepared {summary['expected_normal_jobs']} normal pilot jobs; not submitted")


if __name__ == "__main__":
    main()
