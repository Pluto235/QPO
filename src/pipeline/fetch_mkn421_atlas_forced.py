#!/usr/bin/env python3
"""Fetch Mrk 421 ATLAS forced photometry for the LHAASO/WCDA window."""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests


SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.project_paths import MULTIWAVELENGTH_DIR, PROJECT_ROOT  # noqa: E402


BASEURL = "https://fallingstar-data.com/forcedphot"
DEFAULT_RA_DEG = 166.11383
DEFAULT_DEC_DEG = 38.20883
DEFAULT_MJD_MIN = 59281.0
DEFAULT_MJD_MAX = 61129.0
OUTPUT_DIR = MULTIWAVELENGTH_DIR / "mkn421" / "optical_lhaaso_2021_2026"
OUTPUT_CSV = OUTPUT_DIR / "atlas_forced_photometry.csv"
RAW_OUTPUT = OUTPUT_DIR / "atlas_forced_photometry_raw.txt"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ra-deg", type=float, default=DEFAULT_RA_DEG)
    parser.add_argument("--dec-deg", type=float, default=DEFAULT_DEC_DEG)
    parser.add_argument("--mjd-min", type=float, default=DEFAULT_MJD_MIN)
    parser.add_argument("--mjd-max", type=float, default=DEFAULT_MJD_MAX)
    parser.add_argument(
        "--omit-mjd-max",
        action="store_true",
        help="Do not send mjd_max; useful if the ATLAS queue rejects that optional field.",
    )
    parser.add_argument("--output-csv", type=Path, default=OUTPUT_CSV)
    parser.add_argument("--raw-output", type=Path, default=RAW_OUTPUT)
    parser.add_argument("--username-env", default="ATLAS_USERNAME")
    parser.add_argument("--password-env", default="ATLAS_PASSWORD")
    parser.add_argument("--token-env", default="ATLAS_TOKEN")
    parser.add_argument(
        "--token-only",
        action="store_true",
        help="Print a new ATLAS API token from username/password env vars and exit.",
    )
    parser.add_argument("--poll-seconds", type=float, default=10.0)
    parser.add_argument("--max-poll-minutes", type=float, default=60.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    output_csv = _project_path(args.output_csv)
    raw_output = _project_path(args.raw_output)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    raw_output.parent.mkdir(parents=True, exist_ok=True)

    token = os.environ.get(args.token_env)
    if not token:
        token = fetch_token(args.username_env, args.password_env)
        if args.token_only:
            print(token)
            return
        print(f"[INFO] fetched ATLAS token from {args.username_env}/{args.password_env} env vars.")

    headers = {"Authorization": f"Token {token}", "Accept": "application/json"}
    task_url = queue_request(args, headers)
    result_url = wait_for_result(task_url, headers, args.poll_seconds, args.max_poll_minutes)

    with requests.Session() as session:
        response = session.get(result_url, headers=headers, timeout=120)
    response.raise_for_status()
    raw_text = response.text
    raw_output.write_text(raw_text, encoding="utf-8")

    parsed = parse_result_text(raw_text)
    parsed.to_csv(output_csv, index=False)
    print(f"[OK] ATLAS raw output: {raw_output.relative_to(PROJECT_ROOT)}")
    print(f"[OK] ATLAS CSV: {output_csv.relative_to(PROJECT_ROOT)}")
    print(f"[OK] rows={len(parsed)}")


def fetch_token(username_env: str, password_env: str) -> str:
    username = os.environ.get(username_env)
    password = os.environ.get(password_env)
    if not username or not password:
        raise SystemExit(
            f"Set {username_env}/{password_env}, or set ATLAS_TOKEN directly. "
            "Do not commit credentials."
        )
    response = requests.post(
        f"{BASEURL}/api-token-auth/",
        data={"username": username, "password": password},
        timeout=60,
    )
    if response.status_code != 200:
        raise RuntimeError(f"ATLAS token request failed: HTTP {response.status_code}: {response.text}")
    return response.json()["token"]


def queue_request(args: argparse.Namespace, headers: dict[str, str]) -> str:
    payload = {
        "ra": args.ra_deg,
        "dec": args.dec_deg,
        "mjd_min": args.mjd_min,
    }
    if not args.omit_mjd_max:
        payload["mjd_max"] = args.mjd_max
    while True:
        with requests.Session() as session:
            response = session.post(f"{BASEURL}/queue/", headers=headers, data=payload, timeout=60)
        if response.status_code == 201:
            task_url = response.json()["url"]
            print(f"[OK] queued ATLAS task: {task_url}")
            return task_url
        if response.status_code == 429:
            wait_seconds = throttle_wait_seconds(response.json().get("detail", ""))
            print(f"[INFO] ATLAS throttled request; waiting {wait_seconds} s.")
            time.sleep(wait_seconds)
            continue
        raise RuntimeError(f"ATLAS queue request failed: HTTP {response.status_code}: {response.text}")


def wait_for_result(
    task_url: str,
    headers: dict[str, str],
    poll_seconds: float,
    max_poll_minutes: float,
) -> str:
    deadline = time.monotonic() + max_poll_minutes * 60
    while time.monotonic() < deadline:
        with requests.Session() as session:
            response = session.get(task_url, headers=headers, timeout=60)
        if response.status_code != 200:
            raise RuntimeError(f"ATLAS task status failed: HTTP {response.status_code}: {response.text}")
        payload = response.json()
        if payload.get("finishtimestamp"):
            result_url = payload["result_url"]
            print(f"[OK] ATLAS task complete: {result_url}")
            return result_url
        if payload.get("starttimestamp"):
            print(f"[INFO] ATLAS task running since {payload['starttimestamp']}; polling again.")
        else:
            print("[INFO] ATLAS task waiting in queue; polling again.")
        time.sleep(poll_seconds)
    raise TimeoutError(f"ATLAS task did not finish within {max_poll_minutes:g} minutes: {task_url}")


def throttle_wait_seconds(message: str) -> int:
    seconds = re.findall(r"available in (\d+) seconds", message)
    minutes = re.findall(r"available in (\d+) minutes", message)
    if seconds:
        return int(seconds[0])
    if minutes:
        return int(minutes[0]) * 60
    return 10


def parse_result_text(raw_text: str) -> pd.DataFrame:
    cleaned = raw_text.replace("###", "")
    frame = pd.read_csv(io.StringIO(cleaned), sep=r"\s+")
    if "MJD" in frame.columns and "mjd" not in frame.columns:
        frame = frame.rename(columns={"MJD": "mjd"})
    frame.insert(0, "source_id", "mkn421")
    frame.insert(1, "survey", "ATLAS")
    return frame


def _project_path(path: Path) -> Path:
    path = path.expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


if __name__ == "__main__":
    main()
