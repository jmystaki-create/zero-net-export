#!/usr/bin/env python3
"""Deploy one exact Zero Net Export repo build to a Home Assistant install path."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


COMPONENT_DIRNAME = "zero_net_export"
BACKUP_ROOT_DIRNAME = ".openclaw_backups"
LEGACY_BACKUP_PREFIXES = (
    f"{COMPONENT_DIRNAME}.backup_",
    f"{COMPONENT_DIRNAME}.backup-",
)
LEGACY_COMPONENT_CHILD_PREFIXES = (
    "backup",
    "backup_",
    "backup-",
)


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


def git_commit_full(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
    ).strip()


def git_component_commit(root: Path) -> str:
    return subprocess.check_output(
        ["git", "log", "-n", "1", "--format=%H", "--", str(source_component_root().relative_to(root))],
        cwd=root,
        text=True,
    ).strip()


def ensure_expected_commit(root: Path, expected_commit: str, parser: argparse.ArgumentParser) -> None:
    actual_commit = git_commit_full(root)
    expected = expected_commit.strip()
    if not expected:
        parser.exit(2, "ERROR: --expected-commit requires a non-empty commit value.\n")
    if actual_commit != expected and not actual_commit.startswith(expected):
        parser.exit(
            2,
            f"ERROR: repo HEAD {actual_commit} does not match --expected-commit {expected}.\n",
        )


def ensure_expected_component_commit(root: Path, expected_commit: str, parser: argparse.ArgumentParser) -> None:
    actual_commit = git_component_commit(root)
    expected = expected_commit.strip()
    if not expected:
        parser.exit(2, "ERROR: --expected-component-commit requires a non-empty commit value.\n")
    if actual_commit != expected and not actual_commit.startswith(expected):
        parser.exit(
            2,
            "ERROR: latest custom_components/zero_net_export commit "
            f"{actual_commit} does not match --expected-component-commit {expected}.\n",
        )


def ensure_clean_repo(root: Path, parser: argparse.ArgumentParser) -> None:
    status = subprocess.check_output(
        ["git", "status", "--porcelain"],
        cwd=root,
        text=True,
    )
    if status.strip():
        parser.exit(
            2,
            "ERROR: repo has uncommitted or untracked changes but --require-clean was set.\n",
        )


def ensure_upstream_sync(root: Path, parser: argparse.ArgumentParser) -> None:
    try:
        upstream_ref = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
            cwd=root,
            text=True,
            stderr=subprocess.STDOUT,
        ).strip()
    except subprocess.CalledProcessError as err:
        details = err.output.strip()
        suffix = f" ({details})" if details else ""
        parser.exit(2, f"ERROR: --require-upstream-sync needs a configured upstream branch{suffix}.\n")

    local_commit = git_commit_full(root)
    upstream_commit = subprocess.check_output(
        ["git", "rev-parse", upstream_ref],
        cwd=root,
        text=True,
    ).strip()
    if local_commit != upstream_commit:
        parser.exit(
            2,
            "ERROR: repo HEAD does not match its upstream tracking branch but --require-upstream-sync was set.\n",
        )


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



def _ignore_component_artifacts(_directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name == "__pycache__":
            ignored.add(name)
            continue
        if name.endswith((".pyc", ".pyo")):
            ignored.add(name)
    return ignored


def copy_component(source_root: Path, destination_root: Path) -> None:
    destination_root.parent.mkdir(parents=True, exist_ok=True)
    if destination_root.exists():
        shutil.rmtree(destination_root)
    shutil.copytree(source_root, destination_root, ignore=_ignore_component_artifacts)


def config_root_for_destination(destination_root: Path) -> Path:
    custom_components_root = destination_root.parent
    if custom_components_root.name != "custom_components":
        raise ValueError(
            f"Destination {destination_root} is not nested under a custom_components directory"
        )
    return custom_components_root.parent


def is_legacy_component_child_name(name: str) -> bool:
    return name == "backup" or name.startswith(LEGACY_COMPONENT_CHILD_PREFIXES)


def legacy_artifacts_for_destination(destination_root: Path) -> dict[str, list[Path]]:
    custom_components_root = destination_root.parent
    component_pycache_root = destination_root / "__pycache__"

    backup_paths = [
        child
        for child in sorted(custom_components_root.iterdir(), key=lambda item: item.name)
        if child.name != COMPONENT_DIRNAME
        and any(child.name.startswith(prefix) for prefix in LEGACY_BACKUP_PREFIXES)
    ] if custom_components_root.exists() else []

    component_child_paths = [
        child
        for child in sorted(destination_root.iterdir(), key=lambda item: item.name)
        if is_legacy_component_child_name(child.name)
    ] if destination_root.exists() else []

    stale_bytecode_paths: list[Path] = []
    if custom_components_root.exists():
        for cache_dir in sorted(custom_components_root.rglob("__pycache__"), key=lambda item: str(item)):
            for artifact in sorted(cache_dir.iterdir(), key=lambda item: item.name):
                if not artifact.is_file():
                    continue
                if artifact.name.startswith(f"{COMPONENT_DIRNAME}."):
                    stale_bytecode_paths.append(artifact)
                    continue
                stem = artifact.name.split(".cpython-", 1)[0]
                if component_pycache_root in artifact.parents and is_legacy_component_child_name(stem):
                    stale_bytecode_paths.append(artifact)

    return {
        "legacy_backup_paths": backup_paths,
        "legacy_component_child_paths": component_child_paths,
        "stale_bytecode_paths": stale_bytecode_paths,
    }


def clean_legacy_artifacts_for_destination(destination_root: Path) -> dict[str, list[str]]:
    artifacts = legacy_artifacts_for_destination(destination_root)

    removed_backups: list[str] = []
    removed_component_children: list[str] = []
    removed_bytecode: list[str] = []

    for path in artifacts["legacy_backup_paths"] + artifacts["legacy_component_child_paths"]:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
        if path in artifacts["legacy_backup_paths"]:
            removed_backups.append(str(path))
        else:
            removed_component_children.append(str(path))

    for path in artifacts["stale_bytecode_paths"]:
        path.unlink(missing_ok=True)
        removed_bytecode.append(str(path))

    return {
        "removed_backup_paths": removed_backups,
        "removed_component_child_paths": removed_component_children,
        "removed_stale_bytecode_paths": removed_bytecode,
    }



def planned_backup_path(destination_root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    config_root = config_root_for_destination(destination_root)
    return (
        config_root
        / BACKUP_ROOT_DIRNAME
        / "custom_components"
        / f"{destination_root.name}.backup-{stamp}"
    )


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
        "--expected-commit",
        help="Require the repo HEAD commit to match this full or short commit before deploying.",
    )
    parser.add_argument(
        "--expected-component-commit",
        help=(
            "Require the latest custom_components/zero_net_export commit to match this full or short commit "
            "before deploying. Prefer this when doc-only repo commits should not move the deploy target."
        ),
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="Fail unless the repo has no tracked, staged, or untracked changes.",
    )
    parser.add_argument(
        "--require-upstream-sync",
        action="store_true",
        help="Fail unless the repo HEAD matches the current branch's upstream tracking commit.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help=(
            "Skip creating a timestamped backup copy of the existing destination component. "
            "Default backups are stored outside custom_components under .openclaw_backups/."
        ),
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

    if args.expected_commit:
        ensure_expected_commit(root, args.expected_commit, parser)
    if args.expected_component_commit:
        ensure_expected_component_commit(root, args.expected_component_commit, parser)
    if args.require_clean:
        ensure_clean_repo(root, parser)
    if args.require_upstream_sync:
        ensure_upstream_sync(root, parser)

    ensure_safe_destination(root, source_root, destination_root, parser)

    destination_exists = destination_root.exists()
    backup_root = None if args.no_backup or not destination_exists else planned_backup_path(destination_root)
    planned_legacy_cleanup = {
        key: [str(path) for path in paths]
        for key, paths in legacy_artifacts_for_destination(destination_root).items()
    }

    if args.dry_run:
        print(f"Dry run deploy plan for {COMPONENT_DIRNAME}")
        print(f"Repo:        {root}")
        print(f"Source:      {source_root}")
        print(f"Destination: {destination_root}")
        print(f"Commit:      {git_commit(root)}")
        if args.expected_commit:
            print(f"Expected repo HEAD:      {args.expected_commit}")
        if args.expected_component_commit:
            print(f"Expected component HEAD: {args.expected_component_commit}")
        if args.require_clean:
            print("Require clean: yes")
        if args.require_upstream_sync:
            print("Require upstream sync: yes")
        print(f"Exists now:  {'yes' if destination_exists else 'no'}")
        if backup_root is not None:
            print(f"Backup:      {backup_root} (planned)")
        else:
            print("Backup:      none")
        if any(planned_legacy_cleanup.values()):
            print("Legacy cleanup:")
            print(json.dumps(planned_legacy_cleanup, indent=2, sort_keys=True))
        else:
            print("Legacy cleanup: none")
        if args.no_validate:
            print("Validation:  skipped (--no-validate)")
        else:
            print("Validation:  would run scripts/validate_install_fingerprint.py against the deployed path")
        print("Next step:   rerun without --dry-run to perform the copy, then restart Home Assistant core only after validation succeeds.")
        return 0

    actual_backup_root = None
    if not args.no_backup:
        actual_backup_root = backup_component(destination_root)

    legacy_cleanup = clean_legacy_artifacts_for_destination(destination_root)

    copy_component(source_root, destination_root)

    print(f"Deployed {COMPONENT_DIRNAME} from repo {root}")
    print(f"Source:      {source_root}")
    print(f"Destination: {destination_root}")
    print(f"Commit:      {git_commit(root)}")
    if args.expected_commit:
        print(f"Expected repo HEAD:      {args.expected_commit}")
    if args.expected_component_commit:
        print(f"Expected component HEAD: {args.expected_component_commit}")
    if args.require_clean:
        print("Require clean: yes")
    if args.require_upstream_sync:
        print("Require upstream sync: yes")
    if actual_backup_root is not None:
        print(f"Backup:      {actual_backup_root}")
    else:
        print("Backup:      none")
    if any(legacy_cleanup.values()):
        print(f"Legacy cleanup: {json.dumps(legacy_cleanup, sort_keys=True)}")
    else:
        print("Legacy cleanup: none")

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
