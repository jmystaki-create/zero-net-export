#!/usr/bin/env python3
"""Print the expected Zero Net Export package fingerprint for live-install comparison."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def tracked_component_files(component_root: Path) -> tuple[str, ...]:
    """Return the shipped source files that must match a live install exactly."""
    tracked: list[str] = []
    for path in sorted(component_root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        if path.suffix not in {".py", ".json"}:
            continue
        tracked.append(path.relative_to(component_root).as_posix())
    return tuple(tracked)


def short_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except OSError:
        return None


def build_expected_payload() -> dict[str, object]:
    repo_root = Path(__file__).resolve().parents[1]
    component_root = repo_root / "custom_components" / "zero_net_export"
    tracked_files_list = tracked_component_files(component_root)
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
    for name in tracked_files_list:
        path = component_root / name
        tracked_files[name] = {
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "sha256_12": short_sha256(path) if path.exists() else None,
        }
    payload["tracked_files"] = tracked_files
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print the expected Zero Net Export package fingerprint for live-install comparison.",
    )
    parser.add_argument(
        "--write-json",
        help="Optional path to also save the expected fingerprint JSON for later comparison.",
    )
    args = parser.parse_args()

    payload = build_expected_payload()
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    print(rendered)

    if args.write_json:
        output_path = Path(args.write_json).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
