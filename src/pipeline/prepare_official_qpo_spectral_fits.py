#!/usr/bin/env python3
"""Prepare, but never submit, IHEP full-interval spectral-fit jobs.

Run this script on IHEP after syncing the ETO repository. It creates one
HTCondor-ready job per target whose spectrum is still marked ``UNVERIFIED`` in
the frozen source registry. Submission intentionally remains a separate,
reviewed operation.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import sys

import yaml


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.project_paths import DATA_DIR, PROJECT_ROOT


IHEP_PROGRAM_ROOT = Path("/home/lhaaso/hushicong/public/v1.0")
IHEP_ENV_SCRIPT = "/cvmfs/lhaaso.ihep.ac.cn/anysw/slc6_ia64_gcc73/external/envf.sh"
FULL_INTERVAL_DATA_CONFIG = "config/Data/WCDA/Cod/Data_20210305_20250731.yaml"
MANIFEST_FIELDS = (
    "source_id",
    "token",
    "ra_deg",
    "dec_deg",
    "galactic_latitude_deg",
    "dge_max_abs_galactic_latitude_deg",
    "dge_active",
    "dge_decision",
    "response_slot",
    "program_root",
    "data_config",
    "fit_yaml",
    "parinit_yaml",
    "outdir",
    "parres",
    "fit_log",
    "registry_sha256",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DATA_DIR / "config" / "official_qpo_source_models.yaml")
    parser.add_argument("--program-root", type=Path, default=IHEP_PROGRAM_ROOT)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("/home/lhaaso/liushijie/QPO/JOBs_official_qpo_spectral_fits"),
    )
    parser.add_argument("--source-ids", nargs="+", help="Subset of currently unresolved source IDs to prepare.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing prepared work root.")
    return parser.parse_args(argv)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pending_targets(registry: dict[str, object], source_ids: set[str] | None = None) -> list[dict[str, object]]:
    targets = registry.get("targets")
    if not isinstance(targets, list):
        raise ValueError("Registry does not contain a targets list")
    pending = []
    for target in targets:
        if not isinstance(target, dict):
            raise ValueError("Registry contains a non-mapping target")
        spectrum = target.get("spectral_model")
        if not isinstance(spectrum, dict):
            raise ValueError(f"Target {target.get('source_id')} lacks spectral_model metadata")
        if spectrum.get("validation_status") == "UNVERIFIED":
            if spectrum.get("current_action") != "full_interval_fit_required":
                continue
            if source_ids is not None and target.get("source_id") not in source_ids:
                continue
            pending.append(target)
    if source_ids is not None:
        found_ids = {str(target["source_id"]) for target in pending}
        missing_ids = source_ids - found_ids
        if missing_ids:
            raise ValueError(f"Requested source IDs are not unresolved full-interval targets: {sorted(missing_ids)}")
    if not pending:
        raise ValueError("No full-interval spectral-fit targets are pending")
    return pending


def build_fit_yaml(program_root: Path, job_dir: Path, target: dict[str, object]) -> dict[str, object]:
    ra_deg = float(target["ra_deg"])
    dec_deg = float(target["dec_deg"])
    outdir = job_dir / "out"
    return {
        "WorkDir": str(program_root),
        "DataConfig": {"WCDA": FULL_INTERVAL_DATA_CONFIG, "KM2A": "config/Data/KM2A/Data_20210720_20250731.yaml"},
        "CorOpt": 0,
        "DataUsed": {
            "SmoothBkg": 1,
            "WCDA": {"Active": 1, "NbinUsed": [0, 6], "ReBin": {"Active": 0, "Rebin": [2, 2, 1]}},
            "KM2A": {"Active": 0, "12_and_34": 1, "NbinUsed": [1.4, 3.4]},
        },
        "ROI": {
            "ROIfile": "none",
            "Include": [0, 0, ra_deg, dec_deg, 4, 6],
            "Exclude": {"Active": 0, "Region": [0, ra_deg, dec_deg, 1, 1]},
        },
        "FastIteration": 1,
        "Fit": {"Fitting": 1, "FluxPoint": 0, "TS_Src": 0, "TS_Bin": 0, "FluxUL": 0},
        "TSmap": {"Active": 0, "WCDA": [1, 0, 6], "KM2A": [0, 1.4, 3.4], "SrcID": 0, "Subtract": 0, "JOBScript": "JOB_TS.sh"},
        "Output": {
            "DrawOpt": 0,
            "Outdir": os.path.relpath(outdir, program_root),
            "fParResu": "ParRes.yaml",
            "fConExcess": "none",
        },
    }


def _dge_config(target: dict[str, object], dge: dict[str, object]) -> dict[str, object]:
    policy = target.get("dge_policy")
    if not isinstance(policy, dict) or not isinstance(policy.get("active"), bool):
        raise ValueError(f"Target {target.get('source_id')} lacks an explicit DGE policy")
    if not policy["active"]:
        return {"Active": 0}
    dge_model = dge["public_tutorial_model"]
    return {
        "Active": 1,
        "ConvoPSF": 1,
        "Template0": {
            "Name": "dust",
            "Tempfile": dge["template_path"],
            "TempHist": [dge["template_hist"]],
            "Epiv": dge_model["Epiv_TeV"],
            "SEDModel": {
                "type": dge_model["type"],
                "F0": dge_model["F0"],
                "alpha": dge_model["alpha"],
            },
        },
    }


def build_parinit_yaml(target: dict[str, object], dge: dict[str, object]) -> dict[str, object]:
    ra_deg = float(target["ra_deg"])
    dec_deg = float(target["dec_deg"])
    return {
        "DGE": _dge_config(target, dge),
        "SRC": {
            "UseCatalog": 0,
            "Active": 1,
            "Epiv": -1,
            "ParStatus": {"Position": 1, "F0": 0, "Index": 0, "MorPar": 1},
            "Src0": {
                "Name": target["token"],
                "Epiv": 3,
                "SEDModel": {
                    "type": "PL",
                    "F0": [1.0, 0.0, 500.0, 0, "1.e-12"],
                    "alpha": [2.6, 1.0, 4.0, 0],
                },
                "MorModel": {
                    "type": "Point",
                    "ra": [ra_deg, ra_deg - 1.0, ra_deg + 1.0, 1],
                    "dec": [dec_deg, dec_deg - 1.0, dec_deg + 1.0, 1],
                },
            },
        },
    }


def _write_yaml(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_runner(work_root: Path) -> Path:
    runner = work_root / "run_spectral_fit.sh"
    runner.write_text(
        "#!/usr/bin/env bash\n"
        # The public environment script reads an unset ANYSW_LANG_K variable.
        # Enable nounset only after it has completed successfully.
        "set -eo pipefail\n"
        f"source {shlex.quote(IHEP_ENV_SCRIPT)}\n"
        "set -u\n"
        "program_root=$1\n"
        "fit_yaml=$2\n"
        "parinit_yaml=$3\n"
        "log_path=$4\n"
        "cd \"$program_root\"\n"
        "\"$program_root/Src_Main\" \"$fit_yaml\" \"$parinit_yaml\" > \"$log_path\" 2>&1\n",
        encoding="utf-8",
    )
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)
    return runner


def _write_condor_submit(work_root: Path, queue_args_path: Path, runner: Path) -> Path:
    submit = work_root / "spectral_fits.sub"
    submit.write_text(
        f"""universe = vanilla
executable = {runner}
arguments = $(program_root) $(fit_yaml) $(parinit_yaml) $(fit_log)
should_transfer_files = NO
getenv = True
request_cpus = 1
request_memory = 2500 MB
request_disk = 2000 MB
accounting_group = LHAASO.lhaaso.default
+HepJob_Experiment = \"LHAASO\"
+HepJob_RealGroup = \"lhaaso\"
+HepJob_RequestOS = \"AlmaLinux9\"
+IHEP_RealGroup = \"lhaaso\"
+ProjectName = \"qpo_official_spectral_fit\"
+JobBatchName = \"qpo_official_spectral_fit\"
output = {work_root}/logs/fit_$(ClusterId)_$(ProcId).out
error = {work_root}/logs/fit_$(ClusterId)_$(ProcId).err
log = {work_root}/logs/fit_$(ClusterId).log
queue program_root,fit_yaml,parinit_yaml,fit_log from {queue_args_path}
""",
        encoding="utf-8",
    )
    return submit


def prepare(
    registry_path: Path,
    program_root: Path,
    work_root: Path,
    *,
    overwrite: bool,
    source_ids: set[str] | None = None,
) -> dict[str, object]:
    registry_path = registry_path.resolve()
    program_root = program_root.resolve()
    if not (program_root / "Src_Main").is_file():
        raise FileNotFoundError(f"Official Src_Main is missing under {program_root}")
    if not (program_root / FULL_INTERVAL_DATA_CONFIG).is_file():
        raise FileNotFoundError(f"Official full-interval WCDA DataConfig is missing under {program_root}")
    if work_root.exists() and any(work_root.iterdir()) and not overwrite:
        raise FileExistsError(f"Refusing to overwrite prepared work root without --overwrite: {work_root}")

    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        raise ValueError(f"Registry is not a mapping: {registry_path}")
    dge = registry.get("dge")
    if not isinstance(dge, dict) or not dge.get("template_path"):
        raise ValueError("Registry does not provide the public DGE template")
    targets = pending_targets(registry, source_ids)
    registry_hash = sha256(registry_path)

    work_root.mkdir(parents=True, exist_ok=True)
    (work_root / "logs").mkdir(exist_ok=True)
    rows: list[dict[str, str]] = []
    for target in targets:
        source_id = str(target["source_id"])
        job_dir = work_root / "fits" / source_id
        outdir = job_dir / "out"
        outdir.mkdir(parents=True, exist_ok=True)
        fit_path = job_dir / "Fit.yaml"
        parinit_path = job_dir / "ParInit.yaml"
        _write_yaml(fit_path, build_fit_yaml(program_root, job_dir, target))
        _write_yaml(parinit_path, build_parinit_yaml(target, dge))
        response_slot = "Responsefile1" if float(target["dec_deg"]) < 28 else "Responsefile2"
        dge_policy = target.get("dge_policy")
        if not isinstance(dge_policy, dict):
            raise ValueError(f"Target {source_id} lacks an explicit DGE policy")
        rows.append(
            {
                "source_id": source_id,
                "token": str(target["token"]),
                "ra_deg": str(target["ra_deg"]),
                "dec_deg": str(target["dec_deg"]),
                "galactic_latitude_deg": str(dge_policy["galactic_latitude_deg"]),
                "dge_max_abs_galactic_latitude_deg": str(dge_policy["public_src_main_max_abs_galactic_latitude_deg"]),
                "dge_active": str(int(dge_policy["active"])),
                "dge_decision": str(dge_policy["decision"]),
                "response_slot": response_slot,
                "program_root": str(program_root),
                "data_config": str(program_root / FULL_INTERVAL_DATA_CONFIG),
                "fit_yaml": str(fit_path),
                "parinit_yaml": str(parinit_path),
                "outdir": str(outdir),
                "parres": str(outdir / "ParRes.yaml"),
                "fit_log": str(job_dir / "fit.log"),
                "registry_sha256": registry_hash,
            }
        )
    manifest_path = work_root / "spectral_fit_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    queue_args_path = work_root / "spectral_fit_queue.args"
    queue_args_path.write_text(
        "".join(
            " ".join(row[field] for field in ("program_root", "fit_yaml", "parinit_yaml", "fit_log"))
            + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )
    runner = _write_runner(work_root)
    submit = _write_condor_submit(work_root, queue_args_path, runner)
    summary = {
        "schema_version": "official_qpo_full_interval_spectral_fit_manifest_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "purpose": "prepare only; submission requires separate review",
        "expected_jobs": len(rows),
        "registry": str(registry_path),
        "registry_sha256": registry_hash,
        "program_root": str(program_root),
        "src_main_sha256": sha256(program_root / "Src_Main"),
        "data_config": str(program_root / FULL_INTERVAL_DATA_CONFIG),
        "data_config_sha256": sha256(program_root / FULL_INTERVAL_DATA_CONFIG),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256(manifest_path),
        "queue_args": str(queue_args_path),
        "queue_args_sha256": sha256(queue_args_path),
        "submit_file": str(submit),
        "submission_status": "PREPARED_NOT_SUBMITTED",
    }
    (work_root / "spectral_fit_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    registry_path = args.registry if args.registry.is_absolute() else PROJECT_ROOT / args.registry
    summary = prepare(
        registry_path,
        args.program_root,
        args.work_root,
        overwrite=args.overwrite,
        source_ids=set(args.source_ids) if args.source_ids else None,
    )
    print(f"[OK] prepared {summary['expected_jobs']} full-interval spectral fits; not submitted")
    print(f"[OK] manifest sha256={summary['manifest_sha256']}")


if __name__ == "__main__":
    main()
