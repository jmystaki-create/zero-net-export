#!/usr/bin/env python3
"""Compare the intended repo build fingerprint against a Home Assistant install path."""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
from pathlib import Path
from typing import Any

TRACKED_FILES = (
    "manifest.json",
    "__init__.py",
    "config_flow.py",
    "coordinator.py",
    "native_support.py",
    "release_info.py",
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
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return str(payload.get("version") or "") or None


def git_commit(repo_root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
        ).strip()
    except Exception:
        return None


def normalize_component_root(path: Path) -> Path:
    candidate = path.expanduser().resolve()
    if candidate.name == "zero_net_export":
        return candidate

    nested_component = candidate / "zero_net_export"
    if nested_component.exists():
        return nested_component

    custom_components_component = candidate / "custom_components" / "zero_net_export"
    if custom_components_component.exists():
        return custom_components_component

    return candidate


def validate_component_root(
    component_root: Path,
    input_path: Path,
    repo_root: Path,
    repo_component_root: Path,
) -> None:
    manifest_path = component_root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            "Could not find zero_net_export/manifest.json from "
            f"install path '{input_path.expanduser().resolve()}'. "
            "Pass either the zero_net_export component directory itself, its "
            "parent custom_components directory, or the Home Assistant config "
            "directory that contains custom_components/zero_net_export."
        )

    if component_root == repo_component_root:
        raise ValueError(
            "Install path resolves to this repo's source component directory instead of a live Home Assistant install. "
            "Point the comparison at the Home Assistant config directory, its custom_components directory, "
            "or the installed custom_components/zero_net_export directory outside this repo."
        )

    if component_root == repo_root or repo_root in component_root.parents:
        raise ValueError(
            "Install path resolves inside this repo instead of a live Home Assistant install. "
            "Point the comparison at the Home Assistant config directory, its custom_components directory, "
            "or the installed custom_components/zero_net_export directory outside this repo so repo-local copies cannot be mistaken for live validation."
        )


def fingerprint(component_root: Path) -> dict[str, Any]:
    manifest_path = component_root / "manifest.json"
    payload: dict[str, Any] = {
        "component_root": str(component_root),
        "manifest_version": read_manifest_version(manifest_path),
        "tracked_files": {},
    }

    tracked_files: dict[str, Any] = {}
    for name in TRACKED_FILES:
        path = component_root / name
        exists = path.exists()
        tracked_files[name] = {
            "path": str(path),
            "exists": exists,
            "size_bytes": path.stat().st_size if exists else None,
            "sha256_12": short_sha256(path) if exists else None,
        }
    payload["tracked_files"] = tracked_files
    return payload


def ssh_command_base(ssh_host: str, ssh_port: int | None) -> list[str]:
    command = ["ssh"]
    if ssh_port is not None:
        command.extend(["-p", str(ssh_port)])
    command.append(ssh_host)
    return command


def run_ssh_command(ssh_host: str, ssh_port: int | None, remote_command: str) -> str:
    result = subprocess.run(
        [*ssh_command_base(ssh_host, ssh_port), f"sh -c {shlex.quote(remote_command)}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"SSH command failed for {ssh_host}: {result.stderr.strip() or result.stdout.strip() or 'unknown error'}"
        )
    return result.stdout.strip()


def normalize_remote_component_root(install_path: str, ssh_host: str, ssh_port: int | None) -> str:
    quoted = shlex.quote(install_path)
    remote_command = (
        f"candidate=$(realpath {quoted}); "
        'if [ "$(basename "$candidate")" = "zero_net_export" ]; then component="$candidate"; '
        'elif [ -f "$candidate/zero_net_export/manifest.json" ]; then component="$candidate/zero_net_export"; '
        'elif [ -f "$candidate/custom_components/zero_net_export/manifest.json" ]; then component="$candidate/custom_components/zero_net_export"; '
        'else component="$candidate"; fi; '
        'readlink -f "$component"'
    )
    return run_ssh_command(ssh_host, ssh_port, remote_command)


def validate_remote_component_root(component_root: str, input_path: str, ssh_host: str, ssh_port: int | None) -> None:
    remote_command = f"[ -f {shlex.quote(component_root + '/manifest.json')} ]"
    try:
        run_ssh_command(ssh_host, ssh_port, remote_command)
    except RuntimeError as err:
        raise FileNotFoundError(
            "Could not find zero_net_export/manifest.json from "
            f"remote install path '{input_path}'. Pass either the remote zero_net_export component "
            "directory itself, its parent custom_components directory, or the Home Assistant config "
            "directory that contains custom_components/zero_net_export."
        ) from err


def remote_fingerprint(component_root: str, ssh_host: str, ssh_port: int | None) -> dict[str, Any]:
    manifest_path = f"{component_root}/manifest.json"
    manifest_command = (
        f"sed -n 's/.*\"version\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p' {shlex.quote(manifest_path)} | head -n 1"
    )
    manifest_version = run_ssh_command(ssh_host, ssh_port, manifest_command) or None

    tracked_files: dict[str, Any] = {}
    for name in TRACKED_FILES:
        remote_path = f"{component_root}/{name}"
        remote_command = (
            f"if [ -e {shlex.quote(remote_path)} ]; then "
            f"size=$(wc -c < {shlex.quote(remote_path)} | tr -d '[:space:]'); "
            f"sha=$(sha256sum {shlex.quote(remote_path)} | awk '{{print substr($1,1,12)}}'); "
            f"printf '1\\t%s\\t%s\\t%s' \"$size\" \"$sha\" {shlex.quote(remote_path)}; "
            f"else printf '0\\t\\t\\t%s' {shlex.quote(remote_path)}; fi"
        )
        raw = run_ssh_command(ssh_host, ssh_port, remote_command)
        exists_raw, size_raw, sha_raw, path_raw = (raw.split("\t", 3) + [""] * 4)[:4]
        tracked_files[name] = {
            "path": path_raw,
            "exists": exists_raw == "1",
            "size_bytes": int(size_raw) if size_raw else None,
            "sha256_12": sha_raw or None,
        }

    return {
        "component_root": component_root,
        "manifest_version": manifest_version,
        "tracked_files": tracked_files,
        "inspection_transport": "ssh",
        "ssh_host": ssh_host,
        "ssh_port": ssh_port,
    }


def compare(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    tracked_files: dict[str, Any] = {}
    mismatches: list[dict[str, Any]] = []
    all_files_match = True

    expected_files = expected.get("tracked_files") or {}
    actual_files = actual.get("tracked_files") or {}
    for name in TRACKED_FILES:
        expected_details = expected_files.get(name) or {}
        actual_details = actual_files.get(name) or {}
        sha_match = expected_details.get("sha256_12") == actual_details.get("sha256_12")
        size_match = expected_details.get("size_bytes") == actual_details.get("size_bytes")
        exists_match = expected_details.get("exists") == actual_details.get("exists")
        file_match = bool(sha_match and size_match and exists_match)
        if not file_match:
            all_files_match = False
            mismatch_reasons: list[str] = []
            if not exists_match:
                mismatch_reasons.append("exists")
            if not size_match:
                mismatch_reasons.append("size_bytes")
            if not sha_match:
                mismatch_reasons.append("sha256_12")
            mismatches.append(
                {
                    "file": name,
                    "reasons": mismatch_reasons,
                    "expected": expected_details,
                    "actual": actual_details,
                }
            )
        tracked_files[name] = {
            "matches": file_match,
            "sha256_12_matches": sha_match,
            "size_bytes_matches": size_match,
            "exists_matches": exists_match,
            "expected": expected_details,
            "actual": actual_details,
        }

    manifest_version_matches = expected.get("manifest_version") == actual.get("manifest_version")
    manifest_mismatch: dict[str, Any] | None = None
    if not manifest_version_matches:
        manifest_mismatch = {
            "field": "manifest_version",
            "expected": expected.get("manifest_version"),
            "actual": actual.get("manifest_version"),
        }

    overall_match = bool(manifest_version_matches and all_files_match)
    if overall_match:
        recommendation = "Install fingerprint matches the intended repo build. A Home Assistant restart from this install path should now be trustworthy."
    else:
        recommendation = (
            "Install fingerprint does not match the intended repo build. Deploy one exact repo build to one Home Assistant custom_components/zero_net_export path, rerun this comparison until it reports overall_match=true, then restart Home Assistant core before trusting live validation."
        )

    return {
        "manifest_version_matches": manifest_version_matches,
        "manifest_mismatch": manifest_mismatch,
        "all_tracked_files_match": all_files_match,
        "overall_match": overall_match,
        "tracked_files": tracked_files,
        "mismatches": mismatches,
        "recommendation": recommendation,
    }


def load_expected_from_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("expected fingerprint JSON must contain an object at the top level")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare the repo fingerprint against a live Home Assistant install path.",
    )
    parser.add_argument(
        "install_path",
        help="Path to the Home Assistant config directory, its custom_components directory, or the installed zero_net_export directory.",
    )
    parser.add_argument(
        "--expected-json",
        help="Optional path to a previously captured expected fingerprint JSON from print_expected_install_fingerprint.py.",
    )
    parser.add_argument(
        "--write-json",
        help="Optional path to also save the comparison payload JSON for validation evidence.",
    )
    parser.add_argument(
        "--ssh-host",
        help="Optional SSH host for inspecting a remote Home Assistant install path without requiring remote python3.",
    )
    parser.add_argument(
        "--ssh-port",
        type=int,
        help="Optional SSH port to use with --ssh-host.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    repo_component_root = repo_root / "custom_components" / "zero_net_export"

    if args.ssh_host:
        input_install_path = args.install_path
        try:
            actual_component_root = normalize_remote_component_root(args.install_path, args.ssh_host, args.ssh_port)
            validate_remote_component_root(actual_component_root, args.install_path, args.ssh_host, args.ssh_port)
        except FileNotFoundError as err:
            parser.exit(2, f"ERROR: {err}\n")
        except RuntimeError as err:
            parser.exit(2, f"ERROR: {err}\n")
    else:
        input_install_path = Path(args.install_path)
        actual_component_root = normalize_component_root(input_install_path)
        try:
            validate_component_root(actual_component_root, input_install_path, repo_root, repo_component_root)
        except (FileNotFoundError, ValueError) as err:
            parser.exit(2, f"ERROR: {err}\n")

    if args.expected_json:
        expected_json_path = Path(args.expected_json).expanduser().resolve()
        expected = load_expected_from_json(expected_json_path)
        expected_source = str(expected_json_path)
    else:
        expected_component_root = repo_component_root
        expected = fingerprint(expected_component_root)
        expected["expected_commit"] = git_commit(repo_root)
        expected["repo_root"] = str(repo_root)
        expected_source = "repo_head"

    actual = remote_fingerprint(actual_component_root, args.ssh_host, args.ssh_port) if args.ssh_host else fingerprint(actual_component_root)
    comparison = compare(expected, actual)

    payload = {
        "input_install_path": str(input_install_path.expanduser().resolve()) if isinstance(input_install_path, Path) else input_install_path,
        "expected": expected,
        "expected_source": expected_source,
        "actual": actual,
        "comparison": comparison,
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    print(rendered)

    if args.write_json:
        output_path = Path(args.write_json).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")

    return 0 if comparison.get("overall_match") else 1


if __name__ == "__main__":
    raise SystemExit(main())
