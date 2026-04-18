#!/usr/bin/env python3
"""Clean legacy Zero Net Export discovery artifacts from a Home Assistant custom_components tree."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


COMPONENT_DIRNAME = "zero_net_export"
LEGACY_BACKUP_PREFIXES = (
    f"{COMPONENT_DIRNAME}.backup_",
    f"{COMPONENT_DIRNAME}.backup-",
)
LEGACY_COMPONENT_CHILD_PREFIXES = (
    "backup_",
    "backup-",
)


def normalize_custom_components_root(path: Path) -> Path:
    candidate = path.expanduser().resolve()
    if candidate.name == COMPONENT_DIRNAME:
        return candidate.parent
    if candidate.name == "custom_components":
        return candidate
    return candidate / "custom_components"


def legacy_backup_paths(custom_components_root: Path) -> list[Path]:
    if not custom_components_root.exists():
        return []

    matches: list[Path] = []
    for child in sorted(custom_components_root.iterdir(), key=lambda item: item.name):
        if child.name == COMPONENT_DIRNAME:
            continue
        if any(child.name.startswith(prefix) for prefix in LEGACY_BACKUP_PREFIXES):
            matches.append(child)
    return matches


def legacy_component_child_paths(custom_components_root: Path) -> list[Path]:
    component_root = custom_components_root / COMPONENT_DIRNAME
    if not component_root.exists() or not component_root.is_dir():
        return []

    matches: list[Path] = []
    for child in sorted(component_root.iterdir(), key=lambda item: item.name):
        if any(child.name.startswith(prefix) for prefix in LEGACY_COMPONENT_CHILD_PREFIXES):
            matches.append(child)
    return matches


def stale_zero_net_export_bytecode_paths(custom_components_root: Path) -> list[Path]:
    if not custom_components_root.exists():
        return []

    component_root = custom_components_root / COMPONENT_DIRNAME
    component_pycache_root = component_root / "__pycache__"

    matches: list[Path] = []
    for cache_dir in sorted(custom_components_root.rglob("__pycache__"), key=lambda item: str(item)):
        for artifact in sorted(cache_dir.iterdir(), key=lambda item: item.name):
            if not artifact.is_file():
                continue
            if artifact.name.startswith(f"{COMPONENT_DIRNAME}."):
                matches.append(artifact)
                continue
            if component_pycache_root in artifact.parents and any(
                artifact.name.startswith(prefix) for prefix in LEGACY_COMPONENT_CHILD_PREFIXES
            ):
                matches.append(artifact)
    return matches


def scan_artifacts(custom_components_root: Path) -> dict[str, list[str]]:
    return {
        "legacy_backup_paths": [str(path) for path in legacy_backup_paths(custom_components_root)],
        "legacy_component_child_paths": [str(path) for path in legacy_component_child_paths(custom_components_root)],
        "stale_bytecode_paths": [str(path) for path in stale_zero_net_export_bytecode_paths(custom_components_root)],
    }


def clean_artifacts(custom_components_root: Path) -> dict[str, list[str]]:
    backup_paths = legacy_backup_paths(custom_components_root)
    component_child_paths = legacy_component_child_paths(custom_components_root)
    bytecode_paths = stale_zero_net_export_bytecode_paths(custom_components_root)

    removed_backups: list[str] = []
    removed_component_children: list[str] = []
    removed_bytecode: list[str] = []

    for path in backup_paths + component_child_paths:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        if path in backup_paths:
            removed_backups.append(str(path))
        else:
            removed_component_children.append(str(path))

    for path in bytecode_paths:
        path.unlink(missing_ok=True)
        removed_bytecode.append(str(path))

    return {
        "removed_backup_paths": removed_backups,
        "removed_component_child_paths": removed_component_children,
        "removed_stale_bytecode_paths": removed_bytecode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Remove legacy Zero Net Export backup directories and stale zero_net_export bytecode "
            "artifacts that can pollute Home Assistant custom-component discovery."
        )
    )
    parser.add_argument(
        "install_path",
        help=(
            "Path to the Home Assistant config directory, its custom_components directory, "
            "or the destination custom_components/zero_net_export directory."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report matching legacy artifacts without deleting anything.",
    )
    args = parser.parse_args()

    custom_components_root = normalize_custom_components_root(Path(args.install_path))
    payload = {
        "custom_components_root": str(custom_components_root),
        "component": COMPONENT_DIRNAME,
    }

    if args.dry_run:
        payload.update(scan_artifacts(custom_components_root))
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    payload.update(clean_artifacts(custom_components_root))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
