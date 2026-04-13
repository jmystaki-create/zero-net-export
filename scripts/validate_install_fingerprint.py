#!/usr/bin/env python3
"""Capture the expected repo fingerprint, compare a live install path, and save both JSON artifacts."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_json_command(command: list[str], *, cwd: Path) -> tuple[int, dict[str, object]]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode not in (0, 1):
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
        raise SystemExit(result.returncode)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as err:
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
        raise SystemExit(f"Failed to parse JSON output from {' '.join(command)}: {err}")

    return result.returncode, payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture the expected repo fingerprint and compare it against a Home Assistant install path in one step.",
    )
    parser.add_argument(
        "install_path",
        help="Path to the Home Assistant config directory, custom_components directory, or zero_net_export directory to compare.",
    )
    parser.add_argument(
        "--expected-json",
        default="tmp/expected-install-fingerprint.json",
        help="Where to save the repo fingerprint JSON (default: tmp/expected-install-fingerprint.json).",
    )
    parser.add_argument(
        "--compare-json",
        default="tmp/install-fingerprint-compare.json",
        help="Where to save the comparison JSON (default: tmp/install-fingerprint-compare.json).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    expected_json = Path(args.expected_json).expanduser().resolve()
    compare_json = Path(args.compare_json).expanduser().resolve()

    expected_json.parent.mkdir(parents=True, exist_ok=True)
    compare_json.parent.mkdir(parents=True, exist_ok=True)

    expected_command = [
        sys.executable,
        "scripts/print_expected_install_fingerprint.py",
        "--write-json",
        str(expected_json),
    ]
    compare_command = [
        sys.executable,
        "scripts/compare_install_fingerprint.py",
        args.install_path,
        "--expected-json",
        str(expected_json),
        "--write-json",
        str(compare_json),
    ]

    _, expected_payload = run_json_command(expected_command, cwd=repo_root)
    compare_returncode, compare_payload = run_json_command(compare_command, cwd=repo_root)

    payload = {
        "repo_root": str(repo_root),
        "install_path": str(Path(args.install_path).expanduser().resolve()),
        "expected_json": str(expected_json),
        "compare_json": str(compare_json),
        "expected": expected_payload,
        "comparison_payload": compare_payload,
        "overall_match": bool(
            ((compare_payload.get("comparison") or {}).get("overall_match"))
        ),
        "recommended_next_step": (
            ((compare_payload.get("comparison") or {}).get("recommendation"))
            or "Review the comparison payload."
        ),
        "commands": {
            "expected": " ".join(expected_command),
            "compare": " ".join(compare_command),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return compare_returncode


if __name__ == "__main__":
    raise SystemExit(main())
