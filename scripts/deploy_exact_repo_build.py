#!/usr/bin/env python3
"""Deploy one exact Zero Net Export repo build to a Home Assistant install path."""
from __future__ import annotations

import argparse
import os
import shlex
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
        git_remote_tracking_details,
        git_status_details,
    )
except ModuleNotFoundError:  # pragma: no cover - script execution fallback
    from compare_install_fingerprint import (  # type: ignore[no-redef]
        build_default_expected,
        compare as compare_fingerprints,
        fingerprint as build_fingerprint,
        git_remote_tracking_details,
        git_status_details,
    )

COMPONENT_DIRNAME = "zero_net_export"
COMMON_CONFIG_ENV_KEYS = (
    "HOME_ASSISTANT_CONFIG",
    "HASS_CONFIG",
    "HA_CONFIG",
    "HOMEASSISTANT_CONFIG",
    "HASSIO_HOMEASSISTANT",
)
COMMON_CONFIG_CANDIDATE_PATHS = (
    Path("/config"),
    Path("/homeassistant"),
    Path("/usr/share/hassio/homeassistant"),
    Path("/mnt/data/supervisor/homeassistant"),
    Path("/var/lib/homeassistant"),
    Path("/srv/homeassistant"),
    Path("~/.homeassistant"),
    Path("~/homeassistant"),
    Path("~/config/homeassistant"),
)


def configured_discovery_hints() -> dict[str, list[str]]:
    return {
        "env_keys": list(COMMON_CONFIG_ENV_KEYS),
        "candidate_paths": [str(path.expanduser()) for path in COMMON_CONFIG_CANDIDATE_PATHS],
    }


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def source_component_root() -> Path:
    return repo_root() / "custom_components" / COMPONENT_DIRNAME


def normalize_destination(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.name == COMPONENT_DIRNAME and resolved.parent.name == "custom_components":
        return resolved
    if resolved.name == "custom_components":
        return resolved / COMPONENT_DIRNAME
    return resolved / "custom_components" / COMPONENT_DIRNAME


def git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=root, text=True).strip()
    except Exception:
        return "unknown"


def _candidate_config_root(path: Path) -> Path:
    if path.name == COMPONENT_DIRNAME and path.parent.name == "custom_components":
        return path.parent.parent
    if path.name == "custom_components":
        return path.parent
    return path


def _looks_like_home_assistant_config_root(path: Path) -> bool:
    return (
        (path / "configuration.yaml").exists()
        or (path / ".storage").is_dir()
        or (path / "custom_components").is_dir()
    )


def discover_home_assistant_config_roots() -> list[Path]:
    candidates: list[Path] = []

    def add_candidate(path: Path | None) -> None:
        if path is None:
            return
        try:
            resolved = _candidate_config_root(path.expanduser().resolve())
        except Exception:
            return
        if not _looks_like_home_assistant_config_root(resolved):
            return
        if resolved not in candidates:
            candidates.append(resolved)

    for env_key in COMMON_CONFIG_ENV_KEYS:
        env_value = os.environ.get(env_key)
        if env_value:
            add_candidate(Path(env_value))

    for candidate in COMMON_CONFIG_CANDIDATE_PATHS:
        add_candidate(candidate)

    return candidates


def shell_command(*parts: str | Path) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def recommended_deploy_command(
    target_path: Path,
    *,
    dry_run: bool,
    expected_commit: str | None = None,
    require_clean: bool = True,
    require_upstream_sync: bool = True,
) -> str:
    command: list[str | Path] = ["python3", "scripts/deploy_exact_repo_build.py", target_path]
    if dry_run:
        command.append("--dry-run")
    if expected_commit:
        command.extend(["--expected-commit", expected_commit])
    if require_clean:
        command.append("--require-clean")
    if require_upstream_sync:
        command.append("--require-upstream-sync")
    return shell_command(*command)


def emit_discovered_home_assistant_config_roots() -> int:
    candidates = discover_home_assistant_config_roots()
    hints = configured_discovery_hints()
    print(f"checked_env_keys={','.join(hints['env_keys'])}")
    print(f"checked_candidate_paths={','.join(hints['candidate_paths'])}")
    print(f"discovered_config_count={len(candidates)}")
    if not candidates:
        print("discovered_config_paths=none")
        print(
            "discovery_guidance=run this from the Home Assistant host or container with the real config mounted, or pass the Home Assistant config directory path explicitly"
        )
        print("next_step=pass your Home Assistant config directory path explicitly to this script")
        return 1

    root = repo_root()
    commit = git_commit(root)
    recommended_target = candidates[0]

    print("discovered_config_paths=")
    for candidate in candidates:
        print(str(candidate))
    print(f"git_commit={commit}")
    print(f"example_dry_run_command={shell_command('python3', 'scripts/deploy_exact_repo_build.py', recommended_target, '--dry-run')}")
    print(
        "recommended_dry_run_command="
        + recommended_deploy_command(recommended_target, dry_run=True, expected_commit=commit)
    )
    print(
        "recommended_deploy_command="
        + recommended_deploy_command(recommended_target, dry_run=False, expected_commit=commit)
    )
    print(
        "recommended_validate_command="
        + shell_command("python3", "scripts/validate_install_fingerprint.py", normalize_destination(recommended_target).parent)
    )
    print(
        "next_step=rerun this script with one discovered config path using the recommended dry-run command, confirm repo_deploy_requirements_passed=true and copy_ready=true, then run the recommended deploy command for that exact path"
    )
    return 0


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


def validation_target_path(destination_root: Path) -> Path:
    return destination_root.parent


def validate_install(destination_root: Path) -> int:
    script = repo_root() / "scripts" / "validate_install_fingerprint.py"
    result = subprocess.run([sys.executable, str(script), str(validation_target_path(destination_root))], cwd=repo_root())
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


def repo_build_summary(*, root: Path, commit: str) -> tuple[str, bool | None, list[str]]:
    dirty, changed_files = git_status_details(root)
    return commit, dirty, changed_files


def emit_repo_build_summary(*, root: Path, commit: str) -> tuple[str, bool | None, list[str]]:
    commit, dirty, changed_files = repo_build_summary(root=root, commit=commit)
    print(f"git_commit={commit}")
    if dirty is None:
        print("git_working_tree_dirty=unknown")
    else:
        print(f"git_working_tree_dirty={str(bool(dirty)).lower()}")
    print(f"git_working_tree_changes={','.join(changed_files) if changed_files else 'none'}")
    tracking = git_remote_tracking_details(root)
    print(f"git_branch={tracking.get('git_branch') or 'unknown'}")
    print(f"git_upstream={tracking.get('git_upstream') or 'none'}")
    print(f"git_upstream_commit={tracking.get('git_upstream_commit') or 'unknown'}")
    print(f"git_local_vs_upstream={tracking.get('git_local_vs_upstream') or 'unknown'}")
    ahead = tracking.get('git_ahead_count')
    behind = tracking.get('git_behind_count')
    print(f"git_ahead_count={ahead if ahead is not None else 'unknown'}")
    print(f"git_behind_count={behind if behind is not None else 'unknown'}")
    return commit, dirty, changed_files


def emit_deploy_readiness(*, ready_for_copy: bool, restart_ready: bool = False) -> None:
    print(f"repo_deploy_requirements_passed={str(bool(ready_for_copy)).lower()}")
    print(f"copy_ready={str(bool(ready_for_copy)).lower()}")
    print(f"restart_ready={str(bool(restart_ready)).lower()}")


def emit_success_criteria(*, phase: str, commit: str) -> None:
    if phase == "dry_run":
        print(
            "success_criteria=confirm repo_deploy_requirements_passed=true, copy_ready=true, "
            f"git_commit={commit}, git_working_tree_dirty=false, and git_local_vs_upstream=in_sync before copying"
        )
        return
    if phase == "deploy":
        print(
            "success_criteria=confirm post_copy_validation=passed, restart_ready=true, "
            f"deployed_commit={commit}, then rerun validate_install_fingerprint before restarting Home Assistant core"
        )


def emit_post_restart_checklist() -> None:
    print(
        "post_restart_checklist=after restarting Home Assistant core, confirm the Zero Net Export entry loads, reopen Configure -> Sensors and source mapping, verify the mapped roles still persist, and verify any unavailable or stale mapped roles are named clearly before trusting live control"
    )


def enforce_repo_build_requirements(
    *,
    root: Path,
    commit: str,
    expected_commit: str | None,
    require_clean: bool,
    require_upstream_sync: bool,
) -> tuple[str, bool | None, list[str]]:
    commit, dirty, changed_files = repo_build_summary(root=root, commit=commit)

    if expected_commit and commit != expected_commit:
        raise SystemExit(
            f"Refusing to deploy: expected git commit {expected_commit} but repo HEAD is {commit}."
        )

    if require_clean:
        if dirty is None:
            raise SystemExit("Refusing to deploy: could not verify git working tree cleanliness.")
        if dirty:
            changed = ", ".join(changed_files) if changed_files else "unknown changes"
            raise SystemExit(
                f"Refusing to deploy: git working tree is dirty ({changed}). Commit or stash changes, then retry."
            )

    if require_upstream_sync:
        tracking = git_remote_tracking_details(root)
        relation = tracking.get("git_local_vs_upstream") or "unknown"
        upstream = tracking.get("git_upstream") or "none"
        upstream_commit = tracking.get("git_upstream_commit") or "unknown"
        if relation != "in_sync":
            raise SystemExit(
                "Refusing to deploy: repo is not synchronized with its tracked upstream "
                f"({upstream} at {upstream_commit}, relation={relation}). Push or reconcile the branch, then retry."
            )

    return commit, dirty, changed_files


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

    emit_repo_build_summary(root=root, commit=commit)
    emit_deploy_readiness(ready_for_copy=True, restart_ready=False)
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
    emit_deploy_readiness(ready_for_copy=True, restart_ready=True)
    emit_success_criteria(phase="deploy", commit=commit)
    print(f"validate_command={shell_command('python3', 'scripts/validate_install_fingerprint.py', validation_target_path(destination_root))}")
    emit_post_restart_checklist()
    print("next_step=restart Home Assistant core from this synchronized install path")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, help="Home Assistant config directory, custom_components directory, or installed custom_components/zero_net_export path")
    parser.add_argument("--dry-run", action="store_true", help="Print the resolved deploy target and planned actions without copying files")
    parser.add_argument(
        "--discover-home-assistant-config",
        action="store_true",
        help="List likely Home Assistant config directories from common environment variables and paths, then exit.",
    )
    parser.add_argument(
        "--expected-commit",
        help="Refuse to continue unless repo HEAD matches this short or full git commit.",
    )
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="Refuse to continue unless the git working tree is clean.",
    )
    parser.add_argument(
        "--require-upstream-sync",
        action="store_true",
        help="Refuse to continue unless the current branch is fully synchronized with its tracked upstream.",
    )
    args = parser.parse_args()

    if args.discover_home_assistant_config:
        return emit_discovered_home_assistant_config_roots()

    if args.path is None:
        parser.error("path is required unless --discover-home-assistant-config is used")

    root = repo_root()
    source_root = source_component_root().resolve()
    destination_root = normalize_destination(args.path)
    ensure_safe_destination(destination_root)

    commit = git_commit(root)
    enforce_repo_build_requirements(
        root=root,
        commit=commit,
        expected_commit=args.expected_commit,
        require_clean=args.require_clean,
        require_upstream_sync=args.require_upstream_sync,
    )
    if args.dry_run:
        print(f"repo_root={root}")
        print(f"source_component_root={source_root}")
        print(f"resolved_destination={destination_root}")
        emit_repo_build_summary(root=root, commit=commit)
        emit_deploy_readiness(ready_for_copy=True, restart_ready=False)
        print(f"destination_exists={destination_root.exists()}")
        emit_pre_deploy_install_summary(pre_deploy_install_summary(destination_root, root=root))
        if destination_root.exists():
            print(f"planned_backup_path={planned_backup_path(destination_root)}")
        print(
            "next_command="
            + recommended_deploy_command(
                args.path,
                dry_run=False,
                expected_commit=args.expected_commit,
                require_clean=args.require_clean,
                require_upstream_sync=args.require_upstream_sync,
            )
        )
        emit_success_criteria(phase="dry_run", commit=commit)
        print(f"validate_command={shell_command('python3', 'scripts/validate_install_fingerprint.py', validation_target_path(destination_root))}")
        emit_post_restart_checklist()
        print("action=preview_only")
        return 0

    return perform_deploy(destination_root, source_root=source_root, commit=commit)


if __name__ == "__main__":
    raise SystemExit(main())
