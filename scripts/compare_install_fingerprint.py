#!/usr/bin/env python3
"""Compare the intended repo build fingerprint against a Home Assistant install path."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def git_status_details(repo_root: Path) -> tuple[bool | None, list[str]]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=repo_root,
            text=True,
        )
    except Exception:
        return None, []

    changed_files: list[str] = []
    for raw_line in output.splitlines():
        if not raw_line.strip():
            continue
        path_part = raw_line[3:] if len(raw_line) > 3 else raw_line
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1]
        changed_files.append(path_part)

    return bool(changed_files), changed_files

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
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    version = manifest.get("version")
    return str(version) if version else None


def git_commit(repo_root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, text=True).strip()
    except Exception:
        return "unknown"


def normalize_component_root(input_path: Path, *, repo_component_root: Path | None = None) -> Path:
    resolved = input_path.expanduser().resolve()
    if resolved.name == "zero_net_export" and resolved.parent.name == "custom_components":
        return resolved
    candidate = resolved / "custom_components" / "zero_net_export"
    if candidate.exists():
        return candidate
    if repo_component_root is not None and resolved == repo_component_root:
        return resolved
    return resolved


def validate_component_root(component_root: Path, *, repo_component_root: Path | None = None) -> None:
    if repo_component_root is not None and component_root == repo_component_root:
        raise SystemExit(
            "Refusing to compare against the repo source tree itself. Point at the Home Assistant config directory or installed custom_components/zero_net_export path instead."
        )
    if component_root.name != "zero_net_export":
        raise SystemExit(
            f"Resolved install path {component_root} is not a custom_components/zero_net_export directory."
        )


def fingerprint(component_root: Path) -> dict[str, Any]:
    tracked_files: dict[str, Any] = {}
    for name in TRACKED_FILES:
        path = component_root / name
        exists = path.exists()
        tracked_files[name] = {
            "path": str(path),
            "exists": exists,
            "sha256_12": short_sha256(path) if exists else None,
            "size_bytes": path.stat().st_size if exists else None,
        }
    return {
        "component_root": str(component_root),
        "manifest_version": read_manifest_version(component_root / "manifest.json"),
        "tracked_files": tracked_files,
    }


def compare(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    expected_manifest = expected.get("manifest_version")
    actual_manifest = actual.get("manifest_version")
    mismatches: list[dict[str, Any]] = []
    tracked: dict[str, Any] = {}

    for name, expected_details in (expected.get("tracked_files") or {}).items():
        actual_details = (actual.get("tracked_files") or {}).get(name, {})
        reasons = []
        if actual_details.get("exists") != expected_details.get("exists"):
            reasons.append("exists")
        if actual_details.get("size_bytes") != expected_details.get("size_bytes"):
            reasons.append("size_bytes")
        if actual_details.get("sha256_12") != expected_details.get("sha256_12"):
            reasons.append("sha256_12")
        matches = not reasons
        tracked[name] = {
            "expected": expected_details,
            "actual": actual_details,
            "exists_matches": actual_details.get("exists") == expected_details.get("exists"),
            "size_bytes_matches": actual_details.get("size_bytes") == expected_details.get("size_bytes"),
            "sha256_12_matches": actual_details.get("sha256_12") == expected_details.get("sha256_12"),
            "matches": matches,
        }
        if not matches:
            mismatches.append({
                "file": name,
                "expected": expected_details,
                "actual": actual_details,
                "reasons": reasons,
            })

    manifest_version_matches = actual_manifest == expected_manifest
    manifest_mismatch = None if manifest_version_matches else {
        "field": "manifest_version",
        "expected": expected_manifest,
        "actual": actual_manifest,
    }
    all_tracked_files_match = not mismatches
    overall_match = manifest_version_matches and all_tracked_files_match
    recommendation = (
        "Install fingerprint matches the intended repo build. A Home Assistant restart from this install path should now be trustworthy."
        if overall_match
        else "Install fingerprint does not match the intended repo build. Deploy one exact repo build to one Home Assistant custom_components/zero_net_export path, rerun this comparison until it reports overall_match=true, then restart Home Assistant core before trusting live validation."
    )

    return {
        "manifest_version_matches": manifest_version_matches,
        "manifest_mismatch": manifest_mismatch,
        "all_tracked_files_match": all_tracked_files_match,
        "mismatches": mismatches,
        "overall_match": overall_match,
        "recommendation": recommendation,
        "tracked_files": tracked,
    }


def load_expected_from_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_default_expected(repo_root: Path) -> dict[str, Any]:
    component = repo_root / "custom_components" / "zero_net_export"
    working_tree_dirty, working_tree_changes = git_status_details(repo_root)
    return {
        "repo_root": str(repo_root),
        "component_root": str(component),
        "expected_commit": git_commit(repo_root),
        "working_tree_dirty": working_tree_dirty,
        "working_tree_changes": working_tree_changes,
        "manifest_version": read_manifest_version(component / "manifest.json"),
        "tracked_files": fingerprint(component)["tracked_files"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Home Assistant config directory or installed custom_components/zero_net_export path")
    parser.add_argument("--expected-json", type=Path, help="Optional precomputed expected fingerprint JSON")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    repo_component_root = root / "custom_components" / "zero_net_export"
    expected = load_expected_from_json(args.expected_json) if args.expected_json else build_default_expected(root)
    expected_source = str(args.expected_json.resolve()) if args.expected_json else None

    component_root = normalize_component_root(args.path, repo_component_root=repo_component_root)
    validate_component_root(component_root, repo_component_root=repo_component_root)
    actual = fingerprint(component_root)

    payload: dict[str, Any] = {
        "expected": expected,
        "actual": actual,
        "comparison": compare(expected, actual),
        "input_install_path": str(args.path.expanduser().resolve()),
    }
    if expected_source:
        payload["expected_source"] = expected_source

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["comparison"]["overall_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
