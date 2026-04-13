#!/usr/bin/env python3
"""Deploy one exact Zero Net Export repo build to a Home Assistant install path."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.compare_install_fingerprint import (
        build_default_expected,
        compare as compare_fingerprints,
        fingerprint as build_fingerprint,
    )
except ModuleNotFoundError:  # pragma: no cover - script execution fallback
    from compare_install_fingerprint import (  # type: ignore[no-redef]
        build_default_expected,
        compare as compare_fingerprints,
        fingerprint as build_fingerprint,
    )

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


def restore_backup(destination_root: Path, backup_path: Path | None) -> None:
    if destination_root.exists():
        shutil.rmtree(destination_root)
    if backup_path and backup_path.exists():
        shutil.move(str(backup_path), str(destination_root))


def validate_install(destination_root: Path) -> int:
    script = repo_root() / "scripts" / "validate_install_fingerprint.py"
    result = subprocess.run([sys.executable, str(script), str(destination_root)], cwd=repo_root())
    return result.returncode


def pre_deploy_install_summary(destination_root: Path, *, root: Path) -> dict[str, Any]:
    if not destination_root.exists():
        return {
            "existing_install_present": False,
            "current_install_manifest_version": None,
            "current_install_matches_repo": None,
            "current_install_mismatches": [],
        }

    expected = build_default_expected(root)
    actual = build_fingerprint(destination_root)
    comparison = compare_fingerprints(expected, actual)
    mismatch_files = [item.get("file") for item in comparison.get("mismatches", []) if item.get("file")]
    manifest_mismatch = comparison.get("manifest_mismatch") or {}
    manifest_actual = actual.get("manifest_version")
    if manifest_mismatch.get("field") == "manifest_version":
        manifest_actual = manifest_mismatch.get("actual")

    return {
        "existing_install_present": True,
        "current_install_manifest_version": manifest_actual,
        "current_install_matches_repo": comparison.get("overall_match"),
        "current_install_mismatches": mismatch_files,
    }


def emit_pre_deploy_install_summary(summary: dict[str, Any]) -> None:
    print(f"existing_install_present={str(bool(summary.get('existing_install_present'))).lower()}")
    manifest_version = summary.get("current_install_manifest_version")
    print(f"current_install_manifest_version={manifest_version if manifest_version else 'unknown'}")

    matches_repo = summary.get("current_install_matches_repo")
    if matches_repo is None:
        print("current_install_matches_repo=unknown")
    else:
        print(f"current_install_matches_repo={str(bool(matches_repo)).lower()}")

    mismatches = summary.get("current_install_mismatches") or []
    print(f"current_install_mismatches={','.join(mismatches) if mismatches else 'none'}")


def perform_deploy(destination_root: Path, *, source_root: Path, commit: str, validate_fn=validate_install) -> int:
    root = repo_root()
    destination_root.parent.mkdir(parents=True, exist_ok=True)
    existing_install_summary = pre_deploy_install_summary(destination_root, root=root)
    backup_path = backup_component(destination_root)
    try:
        copy_component(source_root, destination_root)
    except Exception:
        restore_backup(destination_root, backup_path)
        raise

    print(f"deployed_commit={commit}")
    print(f"source_component_root={source_root}")
    print(f"resolved_destination={destination_root}")
    print(f"backup_path={backup_path if backup_path else 'none'}")
    emit_pre_deploy_install_summary(existing_install_summary)

    validation_rc = validate_fn(destination_root)
    if validation_rc != 0:
        restore_backup(destination_root, backup_path)
        print("post_copy_validation=failed", file=sys.stderr)
        print(f"restored_backup={backup_path if backup_path and backup_path.exists() else 'none'}", file=sys.stderr)
        return validation_rc

    print("post_copy_validation=passed")
    print("next_step=restart Home Assistant core from this synchronized install path")
    return 0


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
        emit_pre_deploy_install_summary(pre_deploy_install_summary(destination_root, root=root))
        if destination_root.exists():
            print(f"planned_backup_path={planned_backup_path(destination_root)}")
        print("action=preview_only")
        return 0

    return perform_deploy(destination_root, source_root=source_root, commit=commit)


if __name__ == "__main__":
    raise SystemExit(main())
