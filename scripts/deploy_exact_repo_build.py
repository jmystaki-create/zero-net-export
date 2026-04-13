#!/usr/bin/env python3
"""Deploy one exact Zero Net Export repo build to a Home Assistant install path."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

COMPONENT_DIRNAME = "zero_net_export"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def source_component_root() -> Path:
    return repo_root() / "custom_components" / COMPONENT_DIRNAME


def normalize_destination(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.name == COMPONENT_DIRNAME and resolved.parent.name == "custom_components":
        return resolved
    return resolved / "custom_components" / COMPONENT_DIRNAME


def git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=root, text=True).strip()
    except Exception:
        return "unknown"


def ensure_safe_destination(destination_root: Path) -> None:
    source_root = source_component_root().resolve()
    if destination_root == source_root:
        raise SystemExit(
            "Refusing to deploy into the repo source directory itself. Point at the Home Assistant config directory or installed custom_components/zero_net_export path instead."
        )
    if destination_root.name != COMPONENT_DIRNAME or destination_root.parent.name != "custom_components":
        raise SystemExit(
            f"Resolved destination {destination_root} is not a custom_components/zero_net_export path."
        )


def copy_component(source_root: Path, destination_root: Path) -> None:
    if destination_root.exists():
        shutil.rmtree(destination_root)
    shutil.copytree(
        source_root,
        destination_root,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )


def planned_backup_path(destination_root: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return destination_root.parent / f"{COMPONENT_DIRNAME}.backup-{timestamp}"


def backup_component(destination_root: Path) -> Path | None:
    if not destination_root.exists():
        return None
    backup_path = planned_backup_path(destination_root)
    shutil.move(str(destination_root), str(backup_path))
    return backup_path


def validate_install(destination_root: Path) -> int:
    script = repo_root() / "scripts" / "validate_install_fingerprint.py"
    result = subprocess.run([sys.executable, str(script), str(destination_root)], cwd=repo_root())
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Home Assistant config directory or installed custom_components/zero_net_export path")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved deploy target and planned actions without copying files")
    args = parser.parse_args()

    root = repo_root()
    source_root = source_component_root().resolve()
    destination_root = normalize_destination(args.path)
    ensure_safe_destination(destination_root)

    commit = git_commit(root)
    if args.dry_run:
        print(f"repo_root={root}")
        print(f"source_component_root={source_root}")
        print(f"resolved_destination={destination_root}")
        print(f"git_commit={commit}")
        print(f"destination_exists={destination_root.exists()}")
        if destination_root.exists():
            print(f"planned_backup_path={planned_backup_path(destination_root)}")
        print("action=preview_only")
        return 0

    destination_root.parent.mkdir(parents=True, exist_ok=True)
    backup_path = backup_component(destination_root)
    copy_component(source_root, destination_root)

    print(f"deployed_commit={commit}")
    print(f"source_component_root={source_root}")
    print(f"resolved_destination={destination_root}")
    print(f"backup_path={backup_path if backup_path else 'none'}")

    validation_rc = validate_install(destination_root)
    if validation_rc != 0:
        print("post_copy_validation=failed", file=sys.stderr)
        return validation_rc

    print("post_copy_validation=passed")
    print("next_step=restart Home Assistant core from this synchronized install path")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
