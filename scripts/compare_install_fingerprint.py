#!/usr/bin/env python3
"""Compare the intended repo build fingerprint against a Home Assistant install path."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

TRACKED_FILES = (
    "manifest.json",
    "config_flow.py",
    "native_support.py",
    "coordinator.py",
    "strings.json",
    "translations/en.json",
)


def short_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except OSError:
        return None


def read_manifest_version(path: Path) -> str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return str(payload.get("version") or "") or None


def git_commit(repo_root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
        ).strip()
    except Exception:
        return None


def normalize_component_root(path: Path) -> Path:
    candidate = path.expanduser().resolve()
    if candidate.name == "zero_net_export":
        return candidate
    nested = candidate / "zero_net_export"
    if nested.exists():
        return nested
    return candidate


def fingerprint(component_root: Path) -> dict[str, Any]:
    manifest_path = component_root / "manifest.json"
    payload: dict[str, Any] = {
        "component_root": str(component_root),
        "manifest_version": read_manifest_version(manifest_path),
        "tracked_files": {},
    }

    tracked_files: dict[str, Any] = {}
    for name in TRACKED_FILES:
        path = component_root / name
        exists = path.exists()
        tracked_files[name] = {
            "path": str(path),
            "exists": exists,
            "size_bytes": path.stat().st_size if exists else None,
            "sha256_12": short_sha256(path) if exists else None,
        }
    payload["tracked_files"] = tracked_files
    return payload


def compare(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    tracked_files: dict[str, Any] = {}
    all_files_match = True

    expected_files = expected.get("tracked_files") or {}
    actual_files = actual.get("tracked_files") or {}
    for name in TRACKED_FILES:
        expected_details = expected_files.get(name) or {}
        actual_details = actual_files.get(name) or {}
        sha_match = expected_details.get("sha256_12") == actual_details.get("sha256_12")
        size_match = expected_details.get("size_bytes") == actual_details.get("size_bytes")
        exists_match = expected_details.get("exists") == actual_details.get("exists")
        file_match = bool(sha_match and size_match and exists_match)
        if not file_match:
            all_files_match = False
        tracked_files[name] = {
            "matches": file_match,
            "sha256_12_matches": sha_match,
            "size_bytes_matches": size_match,
            "exists_matches": exists_match,
            "expected": expected_details,
            "actual": actual_details,
        }

    manifest_version_matches = expected.get("manifest_version") == actual.get("manifest_version")
    overall_match = bool(manifest_version_matches and all_files_match)
    if overall_match:
        recommendation = "Install fingerprint matches the intended repo build. A Home Assistant restart from this install path should now be trustworthy."
    else:
        recommendation = (
            "Install fingerprint does not match the intended repo build. Deploy one exact repo build to one Home Assistant custom_components/zero_net_export path, then restart Home Assistant core before trusting live validation."
        )

    return {
        "manifest_version_matches": manifest_version_matches,
        "all_tracked_files_match": all_files_match,
        "overall_match": overall_match,
        "tracked_files": tracked_files,
        "recommendation": recommendation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare the repo fingerprint against a live Home Assistant install path.",
    )
    parser.add_argument(
        "install_path",
        help="Path to the installed zero_net_export directory, or its parent custom_components directory.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    expected_component_root = repo_root / "custom_components" / "zero_net_export"
    actual_component_root = normalize_component_root(Path(args.install_path))

    expected = fingerprint(expected_component_root)
    expected["expected_commit"] = git_commit(repo_root)
    expected["repo_root"] = str(repo_root)

    actual = fingerprint(actual_component_root)

    payload = {
        "expected": expected,
        "actual": actual,
        "comparison": compare(expected, actual),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
