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
    mismatches: list[dict[str, Any]] = []
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
            mismatch_reasons: list[str] = []
            if not exists_match:
                mismatch_reasons.append("exists")
            if not size_match:
                mismatch_reasons.append("size_bytes")
            if not sha_match:
                mismatch_reasons.append("sha256_12")
            mismatches.append(
                {
                    "file": name,
                    "reasons": mismatch_reasons,
                    "expected": expected_details,
                    "actual": actual_details,
                }
            )
        tracked_files[name] = {
            "matches": file_match,
            "sha256_12_matches": sha_match,
            "size_bytes_matches": size_match,
            "exists_matches": exists_match,
            "expected": expected_details,
            "actual": actual_details,
        }

    manifest_version_matches = expected.get("manifest_version") == actual.get("manifest_version")
    manifest_mismatch: dict[str, Any] | None = None
    if not manifest_version_matches:
        manifest_mismatch = {
            "field": "manifest_version",
            "expected": expected.get("manifest_version"),
            "actual": actual.get("manifest_version"),
        }

    overall_match = bool(manifest_version_matches and all_files_match)
    if overall_match:
        recommendation = "Install fingerprint matches the intended repo build. A Home Assistant restart from this install path should now be trustworthy."
    else:
        recommendation = (
            "Install fingerprint does not match the intended repo build. Deploy one exact repo build to one Home Assistant custom_components/zero_net_export path, rerun this comparison until it reports overall_match=true, then restart Home Assistant core before trusting live validation."
        )

    return {
        "manifest_version_matches": manifest_version_matches,
        "manifest_mismatch": manifest_mismatch,
        "all_tracked_files_match": all_files_match,
        "overall_match": overall_match,
        "tracked_files": tracked_files,
        "mismatches": mismatches,
        "recommendation": recommendation,
    }


def load_expected_from_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("expected fingerprint JSON must contain an object at the top level")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare the repo fingerprint against a live Home Assistant install path.",
    )
    parser.add_argument(
        "install_path",
        help="Path to the installed zero_net_export directory, or its parent custom_components directory.",
    )
    parser.add_argument(
        "--expected-json",
        help="Optional path to a previously captured expected fingerprint JSON from print_expected_install_fingerprint.py.",
    )
    parser.add_argument(
        "--write-json",
        help="Optional path to also save the comparison payload JSON for validation evidence.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    actual_component_root = normalize_component_root(Path(args.install_path))

    if args.expected_json:
        expected_json_path = Path(args.expected_json).expanduser().resolve()
        expected = load_expected_from_json(expected_json_path)
        expected_source = str(expected_json_path)
    else:
        expected_component_root = repo_root / "custom_components" / "zero_net_export"
        expected = fingerprint(expected_component_root)
        expected["expected_commit"] = git_commit(repo_root)
        expected["repo_root"] = str(repo_root)
        expected_source = "repo_head"

    actual = fingerprint(actual_component_root)
    comparison = compare(expected, actual)

    payload = {
        "expected": expected,
        "expected_source": expected_source,
        "actual": actual,
        "comparison": comparison,
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    print(rendered)

    if args.write_json:
        output_path = Path(args.write_json).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")

    return 0 if comparison.get("overall_match") else 1


if __name__ == "__main__":
    raise SystemExit(main())
