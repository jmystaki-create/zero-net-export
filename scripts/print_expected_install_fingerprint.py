#!/usr/bin/env python3
"""Print the expected Zero Net Export package fingerprint for live-install comparison."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


def git_status_details(root: Path) -> tuple[bool | None, list[str]]:
    try:
        output = subprocess.check_output(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=root,
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


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def component_root() -> Path:
    return repo_root() / "custom_components" / "zero_net_export"


def manifest_version(path: Path) -> str | None:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    version = manifest.get("version")
    return str(version) if version else None


def git_commit(root: Path) -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=root, text=True)
            .strip()
        )
    except Exception:
        return "unknown"


def main() -> int:
    root = repo_root()
    component = component_root()
    working_tree_dirty, working_tree_changes = git_status_details(root)
    payload: dict[str, object] = {
        "repo_root": str(root),
        "component_root": str(component),
        "expected_commit": git_commit(root),
        "working_tree_dirty": working_tree_dirty,
        "working_tree_changes": working_tree_changes,
        "manifest_version": manifest_version(component / "manifest.json"),
        "tracked_files": {},
    }

    tracked_files: dict[str, object] = {}
    for name in TRACKED_FILES:
        path = component / name
        exists = path.exists()
        tracked_files[name] = {
            "path": str(path),
            "exists": exists,
            "sha256_12": short_sha256(path) if exists else None,
            "size_bytes": path.stat().st_size if exists else None,
        }
    payload["tracked_files"] = tracked_files

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
