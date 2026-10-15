#!/usr/bin/env python3
"""Prepare or run the three-bin DGE/profile-likelihood smoke gate on IHEP.

This wrapper is deliberately limited to the predeclared T001/T048/T083
two-day bins for 1ES 2344+514, the only target with a directly runnable public
v1.0 PL spectrum before the pending full-interval fits finish.  It is not a
production light-curve generator.  Each smoke bin first obtains an ordinary
free-F0 fit, then evaluates a deterministic fixed-F0 grid containing that MLE.
The public ``Src_Main`` executable is never modified.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from typing import Any

import yaml


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from utils.official_profile import build_fixed_grid_profile, parse_src_main_fit_summary
    from utils.project_paths import DATA_DIR, PROJECT_ROOT
except ModuleNotFoundError:
    # The prepared IHEP smoke directory deliberately carries only this helper.
    from official_profile import build_fixed_grid_profile, parse_src_main_fit_summary

    PROJECT_ROOT = Path.cwd()
    DATA_DIR = PROJECT_ROOT / "data"


IHEP_PROGRAM_ROOT = Path("/home/lhaaso/hushicong/public/v1.0")
IHEP_ENV_SCRIPT = "/cvmfs/lhaaso.ihep.ac.cn/anysw/slc6_ia64_gcc73/external/envf.sh"
SMOKE_SOURCE_ID = "1es2344p514"
SMOKE_CADENCE_DAYS = 2
SMOKE_LC_IDS = (1, 402, 803)
SMOKE_MANIFEST_FIELDS = (
    "source_id",
    "cadence_days",
    "lc_id",
    "mjd",
    "response_period",
    "response_slot",
    "response_file",
    "data_config",
    "normal_fit_yaml",
    "normal_parinit_yaml",
    "normal_log",
    "normal_parres",
    "profile_json",
)
# Exact F0=0 causes a public-v1.0 DGE/Minuit boundary stall in the smoke
# environment. The profile schema still permits zero, but this numerical
# interface check starts at a strictly positive, predeclared lower grid point.
GRID_MULTIPLIERS = (0.0625, 0.5, 1.0, 2.0, 16.0)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DATA_DIR / "config" / "official_qpo_source_models.yaml")
    parser.add_argument("--program-root", type=Path, default=IHEP_PROGRAM_ROOT)
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("/home/lhaaso/liushijie/QPO/JOBs_official_qpo_profile_smoke"),
    )
    parser.add_argument("--execute", action="store_true", help="Run only the predeclared three local smoke bins on IHEP.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing prepared smoke directory.")
    return parser.parse_args(argv)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smoke_data_config(program_root: Path, lc_id: int) -> Path:
    return program_root / "config" / "Data" / "WCDA" / "Cod" / "LC" / "2Days" / f"Data_LC_{lc_id:04d}.yaml"


def _read_registry(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Registry is not a mapping: {path}")
    return data


def _smoke_target(registry: dict[str, Any]) -> dict[str, Any]:
    targets = registry.get("targets")
    if not isinstance(targets, list):
        raise ValueError("Registry does not contain target records")
    target = next((item for item in targets if isinstance(item, dict) and item.get("source_id") == SMOKE_SOURCE_ID), None)
    if target is None:
        raise ValueError(f"Registry lacks required smoke source {SMOKE_SOURCE_ID}")
    spectrum = target.get("spectral_model")
    if not isinstance(spectrum, dict) or spectrum.get("validation_status") != "VERIFIED":
        raise ValueError("The fixed smoke source spectrum is not verified")
    if spectrum.get("model_type") != "PL":
        raise ValueError("The smoke wrapper currently supports only the verified public PL model")
    if not isinstance(spectrum.get("parameters"), dict):
        raise ValueError("The smoke source lacks public PL parameters")
    return target


def _source_sed(target: dict[str, Any], *, f0: float | None, fixed_f0: bool) -> dict[str, Any]:
    spectrum = target["spectral_model"]
    parameters = spectrum["parameters"]
    norm = parameters["norm"]
    index = parameters["index"]
    if not isinstance(norm, list) or len(norm) < 4 or not isinstance(index, list) or not index:
        raise ValueError("Verified PL source parameters have an unexpected catalog schema")
    f0_value = float(norm[0]) if f0 is None else float(f0)
    if f0_value < 0:
        raise ValueError("Fixed F0 must be non-negative")
    return {
        "type": "PL",
        "F0": [f0_value, 0.0, 500.0, int(fixed_f0), str(norm[3])],
        "alpha": [float(index[0]), 1.0, 4.0, 1],
    }


def build_fit_yaml(program_root: Path, job_dir: Path, target: dict[str, Any], data_config: Path) -> dict[str, Any]:
    return {
        "WorkDir": str(program_root),
        "DataConfig": {
            "WCDA": str(data_config.relative_to(program_root)),
            "KM2A": "config/Data/KM2A/Data_20210720_20250731.yaml",
        },
        "CorOpt": 0,
        "DataUsed": {
            "SmoothBkg": 1,
            "WCDA": {"Active": 1, "NbinUsed": [0, 6], "ReBin": {"Active": 0, "Rebin": [2, 2, 1]}},
            "KM2A": {"Active": 0, "12_and_34": 1, "NbinUsed": [1.4, 3.4]},
        },
        "ROI": {
            "ROIfile": "none",
            "Include": [0, 0, float(target["ra_deg"]), float(target["dec_deg"]), 4, 6],
            "Exclude": {"Active": 0, "Region": [0, float(target["ra_deg"]), float(target["dec_deg"]), 1, 1]},
        },
        "FastIteration": 1,
        "Fit": {"Fitting": 1, "FluxPoint": 0, "TS_Src": 0, "TS_Bin": 0, "FluxUL": 0},
        "TSmap": {"Active": 0, "WCDA": [1, 0, 6], "KM2A": [0, 1.4, 3.4], "SrcID": 0, "Subtract": 0, "JOBScript": "JOB_TS.sh"},
        "Output": {
            "DrawOpt": 0,
            "Outdir": os.path.relpath(job_dir / "out", program_root),
            "fParResu": "ParRes.yaml",
            "fConExcess": "none",
        },
    }


def _dge_config(target: dict[str, Any], dge: dict[str, Any]) -> dict[str, Any]:
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
            "SEDModel": {"type": dge_model["type"], "F0": dge_model["F0"], "alpha": dge_model["alpha"]},
        },
    }


def build_parinit_yaml(target: dict[str, Any], dge: dict[str, Any], *, f0: float | None = None, fixed_f0: bool = False) -> dict[str, Any]:
    return {
        "DGE": _dge_config(target, dge),
        "SRC": {
            "UseCatalog": 0,
            "Active": 1,
            "Epiv": -1,
            "ParStatus": {"Position": 1, "F0": int(fixed_f0), "Index": 1, "MorPar": 1},
            "Src0": {
                "Name": target["token"],
                "Epiv": float(target["spectral_model"]["parameters"]["E_0"]),
                "SEDModel": _source_sed(target, f0=f0, fixed_f0=fixed_f0),
                "MorModel": {
                    "type": "Point",
                    "ra": [float(target["ra_deg"]), float(target["ra_deg"]) - 1.0, float(target["ra_deg"]) + 1.0, 1],
                    "dec": [float(target["dec_deg"]), float(target["dec_deg"]) - 1.0, float(target["dec_deg"]) + 1.0, 1],
                },
            },
        },
    }


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _response_metadata(data_config: Path, declination_deg: float) -> tuple[str, str, str]:
    data = yaml.safe_load(data_config.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Official DataConfig is not a mapping: {data_config}")
    slot = "Responsefile1" if declination_deg < 28.0 else "Responsefile2"
    response = str(data[slot])
    marker = "/T"
    if marker not in response:
        raise ValueError(f"Official response path lacks a period marker: {response}")
    period = "T" + response.split(marker, 1)[1][:3]
    return period, slot, response


def _write_runner(work_root: Path) -> Path:
    runner = work_root / "run_profile_smoke.sh"
    runner.write_text(
        "#!/usr/bin/env bash\n"
        "set -eo pipefail\n"
        f"source {IHEP_ENV_SCRIPT}\n"
        "set -u\n"
        "exec \"${PROFILE_PYTHON:-python3}\" \"$(dirname \"$0\")/prepare_official_qpo_profile_smoke.py\" --execute --work-root \"$(dirname \"$0\")\"\n",
        encoding="utf-8",
    )
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)
    return runner


def prepare(registry_path: Path, program_root: Path, work_root: Path, *, overwrite: bool) -> dict[str, Any]:
    registry_path = registry_path.resolve()
    program_root = program_root.resolve()
    if not (program_root / "Src_Main").is_file():
        raise FileNotFoundError(f"Official Src_Main is missing under {program_root}")
    if work_root.exists() and any(work_root.iterdir()) and not overwrite:
        raise FileExistsError(f"Refusing to overwrite prepared profile smoke root without --overwrite: {work_root}")
    registry = _read_registry(registry_path)
    target = _smoke_target(registry)
    dge = registry.get("dge")
    if not isinstance(dge, dict) or not dge.get("active") or not Path(str(dge.get("template_path", ""))).is_file():
        raise ValueError("The public active DGE template is not available")

    work_root.mkdir(parents=True, exist_ok=True)
    frozen_registry = work_root / "registry.yaml"
    shutil.copy2(registry_path, frozen_registry)
    shutil.copy2(Path(__file__), work_root / Path(__file__).name)
    profile_helper = SRC_DIR / "utils" / "official_profile.py"
    if not profile_helper.is_file():
        profile_helper = Path(__file__).with_name("official_profile.py")
    shutil.copy2(profile_helper, work_root / "official_profile.py")
    rows: list[dict[str, str]] = []
    for lc_id in SMOKE_LC_IDS:
        data_config = smoke_data_config(program_root, lc_id)
        if not data_config.is_file():
            raise FileNotFoundError(f"Official smoke DataConfig is missing: {data_config}")
        job_dir = work_root / f"LC{lc_id:04d}"
        normal_dir = job_dir / "normal"
        normal_dir.joinpath("out").mkdir(parents=True, exist_ok=True)
        fit_path = normal_dir / "Fit.yaml"
        parinit_path = normal_dir / "ParInit.yaml"
        _write_yaml(fit_path, build_fit_yaml(program_root, normal_dir, target, data_config))
        _write_yaml(parinit_path, build_parinit_yaml(target, dge))
        period, slot, response = _response_metadata(data_config, float(target["dec_deg"]))
        rows.append(
            {
                "source_id": SMOKE_SOURCE_ID,
                "cadence_days": str(SMOKE_CADENCE_DAYS),
                "lc_id": str(lc_id),
                "mjd": f"{59280.6666666667 + (lc_id - 0.5) * SMOKE_CADENCE_DAYS:.10f}",
                "response_period": period,
                "response_slot": slot,
                "response_file": response,
                "data_config": str(data_config),
                "normal_fit_yaml": str(fit_path),
                "normal_parinit_yaml": str(parinit_path),
                "normal_log": str(normal_dir / "normal.log"),
                "normal_parres": str(normal_dir / "out" / "ParRes.yaml"),
                "profile_json": str(job_dir / "profile.json"),
            }
        )
    manifest = work_root / "profile_smoke_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SMOKE_MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    runner = _write_runner(work_root)
    summary = {
        "schema_version": "official_qpo_profile_smoke_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "purpose": "three-bin local Phase 3 smoke only; not production",
        "source_id": SMOKE_SOURCE_ID,
        "cadence_days": SMOKE_CADENCE_DAYS,
        "lc_ids": list(SMOKE_LC_IDS),
        "expected_profiles": len(rows),
        "grid_multipliers": list(GRID_MULTIPLIERS),
        "registry": str(frozen_registry),
        "registry_sha256": sha256(frozen_registry),
        "program_root": str(program_root),
        "src_main_sha256": sha256(program_root / "Src_Main"),
        "manifest": str(manifest),
        "manifest_sha256": sha256(manifest),
        "runner": str(runner),
        "execution_status": "PREPARED_NOT_EXECUTED",
    }
    (work_root / "profile_smoke_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _parse_f0(parres_path: Path) -> tuple[float, str]:
    data = yaml.safe_load(parres_path.read_text(encoding="utf-8"))
    try:
        f0 = data["SRC"]["Src0"]["SEDModel"]["F0"]
        value, order = float(f0[0]), str(f0[4])
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise ValueError(f"Cannot parse Src0 F0 from {parres_path}") from exc
    if value <= 0:
        raise ValueError(f"Ordinary-fit F0 must be positive for the two-sided smoke grid: {value}")
    return value, order


def _run_src_main(program_root: Path, fit_yaml: Path, parinit_yaml: Path, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        subprocess.run(
            [str(program_root / "Src_Main"), str(fit_yaml), str(parinit_yaml)],
            cwd=program_root,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=True,
        )


def _fixed_grid(mle_f0: float) -> list[float]:
    return [mle_f0 * multiplier for multiplier in GRID_MULTIPLIERS]


def execute(work_root: Path) -> list[dict[str, Any]]:
    manifest = work_root / "profile_smoke_manifest.csv"
    if not manifest.is_file():
        raise FileNotFoundError(f"Prepared smoke manifest is missing: {manifest}")
    registry_path = work_root / "registry.yaml"
    summary_path = work_root / "profile_smoke_summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(f"Prepared smoke summary is missing: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    program_root = Path(summary["program_root"])
    if sha256(program_root / "Src_Main") != summary["src_main_sha256"]:
        raise RuntimeError("Src_Main hash differs from the prepared smoke manifest")
    source_registry = Path(summary["registry"])
    if not source_registry.is_file():
        raise FileNotFoundError(f"Original registry is unavailable: {source_registry}")
    if sha256(source_registry) != summary["registry_sha256"]:
        raise RuntimeError("Registry hash differs from the prepared smoke manifest")
    registry = _read_registry(source_registry)
    target = _smoke_target(registry)
    dge = registry["dge"]

    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(SMOKE_LC_IDS) or [int(row["lc_id"]) for row in rows] != list(SMOKE_LC_IDS):
        raise ValueError("Smoke manifest does not contain exactly the predeclared three bins")

    results: list[dict[str, Any]] = []
    for row in rows:
        normal_fit = Path(row["normal_fit_yaml"])
        normal_parinit = Path(row["normal_parinit_yaml"])
        normal_log = Path(row["normal_log"])
        normal_parres = Path(row["normal_parres"])
        _run_src_main(program_root, normal_fit, normal_parinit, normal_log)
        normal_summary = parse_src_main_fit_summary(normal_log.read_text(encoding="utf-8"))
        if normal_summary.status != "OK" or not normal_parres.is_file():
            raise RuntimeError(f"Ordinary fit failed for LC{int(row['lc_id']):04d}")
        ordinary_f0, f0_order = _parse_f0(normal_parres)
        scan_points = []
        job_dir = normal_fit.parents[1]
        data_config = Path(row["data_config"])
        for index, f0 in enumerate(_fixed_grid(ordinary_f0)):
            point_dir = job_dir / "scan" / f"p{index:02d}"
            point_dir.joinpath("out").mkdir(parents=True, exist_ok=True)
            fit_path = point_dir / "Fit.yaml"
            parinit_path = point_dir / "ParInit.yaml"
            _write_yaml(fit_path, build_fit_yaml(program_root, point_dir, target, data_config))
            _write_yaml(parinit_path, build_parinit_yaml(target, dge, f0=f0, fixed_f0=True))
            log_path = point_dir / "scan.log"
            _run_src_main(program_root, fit_path, parinit_path, log_path)
            parsed = parse_src_main_fit_summary(log_path.read_text(encoding="utf-8"))
            if parsed.status != "OK":
                raise RuntimeError(f"Fixed-F0 scan failed for LC{int(row['lc_id']):04d}, point {index}")
            scan_points.append((f0, parsed, str(log_path), sha256(fit_path), sha256(parinit_path)))
        profile = build_fixed_grid_profile([item[0] for item in scan_points], [item[1] for item in scan_points])
        profile_mle_f0 = min(profile, key=lambda point: point.delta_log_likelihood).f0
        result = {
            "schema_version": "official_qpo_fixed_f0_profile_v1",
            "source_id": row["source_id"],
            "cadence_days": int(row["cadence_days"]),
            "lc_id": int(row["lc_id"]),
            "mjd": float(row["mjd"]),
            "response_period": row["response_period"],
            "response_slot": row["response_slot"],
            "response_file": row["response_file"],
            "data_config": row["data_config"],
            "ordinary_fit": {"f0": ordinary_f0, "f0_order": f0_order, "aic": normal_summary.aic, "bic": normal_summary.bic, "ts": normal_summary.ts, "log": str(normal_log)},
            "profile_mle_f0": profile_mle_f0,
            "profile_mle_matches_ordinary": profile_mle_f0 == ordinary_f0,
            "points": [{**asdict(point), "log": scan_points[index][2], "fit_yaml_sha256": scan_points[index][3], "parinit_yaml_sha256": scan_points[index][4]} for index, point in enumerate(profile)],
        }
        profile_path = Path(row["profile_json"])
        profile_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        results.append(result)
    summary["execution_status"] = "COMPLETED"
    summary["completed_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summary["profile_sha256"] = {str(result["lc_id"]): sha256(Path(rows[index]["profile_json"])) for index, result in enumerate(results)}
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return results


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    work_root = args.work_root
    if args.execute:
        results = execute(work_root)
        print(f"[OK] completed {len(results)} validated fixed-F0 profile smoke bins")
        return
    registry = args.registry if args.registry.is_absolute() else PROJECT_ROOT / args.registry
    summary = prepare(registry, args.program_root, work_root, overwrite=args.overwrite)
    print(f"[OK] prepared {summary['expected_profiles']} profile smoke bins; not executed")
    print(f"[OK] manifest sha256={summary['manifest_sha256']}")


if __name__ == "__main__":
    main()
