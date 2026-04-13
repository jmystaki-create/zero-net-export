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
    candidate = path.expanduser().resolve()
    if candidate.name == COMPONENT_DIRNAME:
        return candidate
    if candidate.name == "custom_components":
        return candidate / COMPONENT_DIRNAME
    return candidate / "custom_components" / COMPONENT_DIRNAME


def git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def ensure_safe_destination(
    repo_root: Path,
    source_root: Path,
    destination_root: Path,
    parser: argparse.ArgumentParser,
) -> None:
    if destination_root == source_root:
        parser.exit(
            2,
            "ERROR: destination resolves to this repo's source component directory. "
            "Choose a Home Assistant install path outside the repo so the source build is not deleted.\n",
        )

    if source_root in destination_root.parents:
        parser.exit(
            2,
            "ERROR: destination is nested inside this repo's source component directory. "
            "Choose a Home Assistant install path outside the repo.\n",
        )

    if destination_root == repo_root or repo_root in destination_root.parents:
        parser.exit(
            2,
            "ERROR: destination resolves inside this repo. "
            "Choose the real Home Assistant config/custom_components/zero_net_export path outside the repo so repo-local dry runs cannot be mistaken for a live deploy.\n",
        )



def copy_component(source_root: Path, destination_root: Path) -> None:
    destination_root.parent.mkdir(parents=True, exist_ok=True)
    if destination_root.exists():
        shutil.rmtree(destination_root)
    shutil.copytree(source_root, destination_root)


def planned_backup_path(destination_root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return destination_root.parent / f"{destination_root.name}.backup-{stamp}"


def backup_component(destination_root: Path) -> Path | None:
    if not destination_root.exists():
        return None

    backup_root = planned_backup_path(destination_root)
    if backup_root.exists():
        raise FileExistsError(f"Backup path already exists: {backup_root}")
    shutil.copytree(destination_root, backup_root)
    return backup_root


def validate_install(destination_root: Path) -> int:
    return subprocess.call(
        [
            sys.executable,
            "scripts/validate_install_fingerprint.py",
            str(destination_root),
        ],
        cwd=repo_root(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Copy this repo's custom_components/zero_net_export into one explicit Home "
            "Assistant install path, replacing any existing component directory first."
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
        "--no-backup",
        action="store_true",
        help="Skip creating a timestamped backup copy of the existing destination component.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip the post-copy fingerprint validation step.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved deploy plan without copying, backing up, or validating anything.",
    )
    args = parser.parse_args()

    root = repo_root()
    source_root = source_component_root()
    destination_root = normalize_destination(Path(args.install_path))

    if not source_root.exists():
        parser.exit(2, f"ERROR: repo component source is missing: {source_root}\n")

    ensure_safe_destination(root, source_root, destination_root, parser)

    destination_exists = destination_root.exists()
    backup_root = None if args.no_backup or not destination_exists else planned_backup_path(destination_root)

    if args.dry_run:
        print(f"Dry run deploy plan for {COMPONENT_DIRNAME}")
        print(f"Repo:        {root}")
        print(f"Source:      {source_root}")
        print(f"Destination: {destination_root}")
        print(f"Commit:      {git_commit(root)}")
        print(f"Exists now:  {'yes' if destination_exists else 'no'}")
        if backup_root is not None:
            print(f"Backup:      {backup_root} (planned)")
        else:
            print("Backup:      none")
        if args.no_validate:
            print("Validation:  skipped (--no-validate)")
        else:
            print("Validation:  would run scripts/validate_install_fingerprint.py against the deployed path")
        print("Next step:   rerun without --dry-run to perform the copy, then restart Home Assistant core only after validation succeeds.")
        return 0

    actual_backup_root = None
    if not args.no_backup:
        actual_backup_root = backup_component(destination_root)

    copy_component(source_root, destination_root)

    print(f"Deployed {COMPONENT_DIRNAME} from repo {root}")
    print(f"Source:      {source_root}")
    print(f"Destination: {destination_root}")
    print(f"Commit:      {git_commit(root)}")
    if actual_backup_root is not None:
        print(f"Backup:      {actual_backup_root}")
    else:
        print("Backup:      none")

    if args.no_validate:
        print("Validation:  skipped (--no-validate)")
        print("Next step:   restart Home Assistant core only after validating the destination install path.")
        return 0

    print("Validation:  running scripts/validate_install_fingerprint.py against the deployed path...")
    validation_exit = validate_install(destination_root)
    if validation_exit == 0:
        print("Next step:   restart Home Assistant core from this synchronized install path.")
        return 0

    print(
        "Next step:   fix the deployed install path until validation reports overall_match=true, "
        "then restart Home Assistant core.",
        file=sys.stderr,
    )
    return validation_exit


if __name__ == "__main__":
    raise SystemExit(main())
