#!/usr/bin/env python3
"""Print the expected Zero Net Export package fingerprint for live-install comparison."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

TRACKED_FILES = (
    "manifest.json",
    "config_flow.py",
    "native_support.py",
    "coordinator.py",
)


def short_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except OSError:
        return None


repo_root = Path(__file__).resolve().parents[1]
component_root = repo_root / "custom_components" / "zero_net_export"
manifest_path = component_root / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

try:
    commit = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        text=True,
    ).strip()
except Exception:
    commit = "unknown"

payload: dict[str, object] = {
    "repo_root": str(repo_root),
    "component_root": str(component_root),
    "expected_commit": commit,
    "manifest_version": str(manifest.get("version") or "unknown"),
    "tracked_files": {},
}

tracked_files: dict[str, object] = {}
for name in TRACKED_FILES:
    path = component_root / name
    tracked_files[name] = {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256_12": short_sha256(path) if path.exists() else None,
    }
payload["tracked_files"] = tracked_files

print(json.dumps(payload, indent=2, sort_keys=True))
