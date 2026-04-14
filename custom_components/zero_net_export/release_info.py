"""Release / changelog metadata helpers for Zero Net Export."""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
import re
import subprocess
from typing import Any

from .const import INTEGRATION_VERSION

_CHANGELOG_HEADING_RE = re.compile(r"^## \[(?P<version>[^\]]+)\](?: - (?P<date>.+))?$")
_BULLET_RE = re.compile(r"^[-*]\s+(?P<text>.+)$")
_RELEASE_INFO_CACHE: dict[str, dict[str, Any]] = {}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _changelog_path() -> Path:
    return _repo_root() / "CHANGELOG.md"


def _component_root() -> Path:
    return Path(__file__).resolve().parent


def _safe_file_fingerprint(path: Path) -> tuple[str | None, int | None]:
    try:
        payload = path.read_bytes()
        return hashlib.sha256(payload).hexdigest()[:12], len(payload)
    except OSError:
        return None, None



def _safe_git_output(repo_root: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=repo_root, text=True).strip() or None
    except Exception:
        return None



def _safe_git_commit(repo_root: Path) -> str | None:
    return _safe_git_output(repo_root, "rev-parse", "--short", "HEAD")



def _safe_git_remote_tracking_details(repo_root: Path) -> dict[str, Any]:
    branch = _safe_git_output(repo_root, "branch", "--show-current") or "detached"
    upstream = _safe_git_output(repo_root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    if not upstream:
        return {
            "git_branch": branch,
            "git_upstream": None,
            "git_upstream_commit": None,
            "git_local_vs_upstream": "no_upstream",
            "git_ahead_count": None,
            "git_behind_count": None,
            "git_ahead_commits": [],
            "git_behind_commits": [],
            "git_sync_remediation": None,
        }

    upstream_commit = _safe_git_output(repo_root, "rev-parse", "--short", upstream)
    ahead_behind = _safe_git_output(repo_root, "rev-list", "--left-right", "--count", f"{upstream}...HEAD")
    if not ahead_behind:
        return {
            "git_branch": branch,
            "git_upstream": upstream,
            "git_upstream_commit": upstream_commit,
            "git_local_vs_upstream": "unknown",
            "git_ahead_count": None,
            "git_behind_count": None,
            "git_ahead_commits": [],
            "git_behind_commits": [],
            "git_sync_remediation": None,
        }

    behind_str, ahead_str = ahead_behind.split()
    behind = int(behind_str)
    ahead = int(ahead_str)
    if ahead == 0 and behind == 0:
        relation = "in_sync"
    elif ahead > 0 and behind == 0:
        relation = "ahead"
    elif behind > 0 and ahead == 0:
        relation = "behind"
    else:
        relation = "diverged"

    ahead_commits_raw = _safe_git_output(repo_root, "log", "--format=%h", "--max-count=10", f"{upstream}..HEAD")
    behind_commits_raw = _safe_git_output(repo_root, "log", "--format=%h", "--max-count=10", f"HEAD..{upstream}")
    ahead_commits = [line.strip() for line in (ahead_commits_raw or "").splitlines() if line.strip()]
    behind_commits = [line.strip() for line in (behind_commits_raw or "").splitlines() if line.strip()]

    remote_name = None
    upstream_branch = None
    if "/" in upstream:
        remote_name, upstream_branch = upstream.split("/", 1)

    remediation = None
    if relation == "ahead" and remote_name and upstream_branch:
        remediation = f"git push {remote_name} HEAD:{upstream_branch}"
    elif relation == "behind" and remote_name and upstream_branch:
        remediation = f"git pull --ff-only {remote_name} {upstream_branch}"
    elif relation == "diverged" and remote_name and upstream_branch:
        remediation = f"git fetch {remote_name} {upstream_branch}"
    elif relation == "no_upstream":
        remediation = f"git push --set-upstream origin {branch}"

    return {
        "git_branch": branch,
        "git_upstream": upstream,
        "git_upstream_commit": upstream_commit,
        "git_local_vs_upstream": relation,
        "git_ahead_count": ahead,
        "git_behind_count": behind,
        "git_ahead_commits": ahead_commits,
        "git_behind_commits": behind_commits,
        "git_sync_remediation": remediation,
    }


@lru_cache(maxsize=1)
def _cached_install_provenance() -> dict[str, Any]:
    component_root = _component_root()
    manifest_path = component_root / "manifest.json"
    manifest_version: str | None = None
    manifest_error: str | None = None

    try:
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_version = str(manifest_payload.get("version") or "") or None
    except OSError as err:
        manifest_error = str(err)
    except json.JSONDecodeError as err:
        manifest_error = f"manifest parse error: {err}"

    tracked_files = (
        "manifest.json",
        "config_flow.py",
        "native_support.py",
        "coordinator.py",
        "strings.json",
        "translations/en.json",
    )
    file_fingerprints: dict[str, dict[str, str | int | None]] = {}
    for relative_name in tracked_files:
        path = component_root / relative_name
        exists = path.exists()
        sha256_12, size_bytes = _safe_file_fingerprint(path) if exists else (None, None)
        file_fingerprints[relative_name] = {
            "path": str(path),
            "exists": exists,
            "sha256_12": sha256_12,
            "size_bytes": size_bytes,
        }

    manifest_matches_code_version = manifest_version == INTEGRATION_VERSION if manifest_version else None
    live_validation_safe = manifest_matches_code_version is not False and not manifest_error

    repo_root = _repo_root()
    expected_commit = _safe_git_commit(repo_root)
    git_tracking = _safe_git_remote_tracking_details(repo_root)

    summary = f"Installed package path {component_root}; code version {INTEGRATION_VERSION}"
    if manifest_version:
        summary += f"; manifest version {manifest_version}"
        if manifest_matches_code_version is False:
            summary += " (version mismatch, mixed-build risk)"
    elif manifest_error:
        summary += f"; manifest unavailable ({manifest_error})"

    payload = {
        "component_root": str(component_root),
        "code_version": INTEGRATION_VERSION,
        "manifest_version": manifest_version,
        "manifest_error": manifest_error,
        "manifest_matches_code_version": manifest_matches_code_version,
        "live_validation_safe": live_validation_safe,
        "expected_commit": expected_commit,
        "tracked_files": file_fingerprints,
        "summary": summary,
    }
    payload.update(git_tracking)
    return payload


def build_install_provenance() -> dict[str, Any]:
    """Return install-path and key-file fingerprint details for live-source validation."""
    return dict(_cached_install_provenance())


def build_install_consistency_summary(install_provenance: dict[str, Any] | None = None) -> str:
    """Return operator-facing guidance for whether live validation can be trusted."""
    provenance = install_provenance or build_install_provenance()
    if provenance.get("manifest_matches_code_version") is False:
        return (
            "Installed package version metadata does not match the running code version, so this install may be serving a mixed build. "
            "Deploy one exact intended Zero Net Export build to one install path, then restart Home Assistant core from that synchronized source before trusting validation results."
        )
    if provenance.get("manifest_error"):
        return (
            "Installed package version metadata could not be read. "
            "Confirm the exact live package path and tracked-file fingerprints before trusting validation results."
        )
    return "Installed package version metadata matches the running code version."


def _install_command_targets(install_provenance: dict[str, Any] | None = None) -> tuple[str, str]:
    provenance = install_provenance or build_install_provenance()
    component_root_raw = str(provenance.get("component_root") or "").strip()
    component_root = Path(component_root_raw).expanduser() if component_root_raw else None

    compare_target = component_root.parent if component_root and component_root.name == "zero_net_export" else component_root
    compare_target_str = str(compare_target) if compare_target else "/path/to/home-assistant/config/custom_components"

    deploy_target = None
    if component_root and component_root.name == "zero_net_export" and component_root.parent.name == "custom_components":
        deploy_target = component_root.parent.parent
    elif component_root and component_root.name == "custom_components":
        deploy_target = component_root.parent
    deploy_target_str = str(deploy_target) if deploy_target else "/path/to/home-assistant/config"

    return compare_target_str, deploy_target_str



def _install_expected_commit(install_provenance: dict[str, Any] | None = None) -> str:
    provenance = install_provenance or build_install_provenance()
    raw_commit = str(provenance.get("expected_commit") or "").strip()
    if raw_commit and raw_commit.lower() not in {"unknown", "none", "n/a"}:
        return raw_commit
    return "<intended_commit>"



def build_install_discovery_command() -> str:
    """Return the exact repo helper command for discovering a Home Assistant config path."""
    return "python3 scripts/deploy_exact_repo_build.py --discover-home-assistant-config"



def build_install_validation_command(install_provenance: dict[str, Any] | None = None) -> str:
    """Return the exact repo helper command for validating the active install path."""
    compare_target_str, _ = _install_command_targets(install_provenance)
    return f"python3 scripts/validate_install_fingerprint.py {compare_target_str}"



def build_install_deploy_dry_run_command(install_provenance: dict[str, Any] | None = None) -> str:
    """Return the exact repo helper command for previewing a safe reinstall to this HA config path."""
    _, deploy_target_str = _install_command_targets(install_provenance)
    expected_commit = _install_expected_commit(install_provenance)
    return (
        "python3 scripts/deploy_exact_repo_build.py "
        f"{deploy_target_str} --dry-run --expected-commit {expected_commit} --require-clean --require-upstream-sync"
    )



def build_install_deploy_command(install_provenance: dict[str, Any] | None = None) -> str:
    """Return the exact repo helper command for deploying one synchronized repo build to this HA config path."""
    _, deploy_target_str = _install_command_targets(install_provenance)
    expected_commit = _install_expected_commit(install_provenance)
    return (
        "python3 scripts/deploy_exact_repo_build.py "
        f"{deploy_target_str} --expected-commit {expected_commit} --require-clean --require-upstream-sync"
    )



def build_install_exact_copy_summary(install_provenance: dict[str, Any] | None = None) -> str:
    """Return the operator-facing exact-copy sequence for a trustworthy live install."""
    discovery_command = build_install_discovery_command()
    dry_run_command = build_install_deploy_dry_run_command(install_provenance)
    deploy_command = build_install_deploy_command(install_provenance)
    validation_command = build_install_validation_command(install_provenance)
    return (
        "From the real Home Assistant host or container, first run `pwd` and `ls /config` to confirm whether `/config` is the live Home Assistant config mount. "
        f"If the config path is still unknown, run discovery with `{discovery_command}`. "
        "If the repo branch is ahead, behind, or diverged, push or reconcile it until git_local_vs_upstream=in_sync. "
        f"Then run `{dry_run_command}` until repo_deploy_requirements_passed=true and copy_ready=true, "
        f"run `{deploy_command}`, rerun `{validation_command}`, restart Home Assistant core, and reopen "
        "Configure -> Sensors and source mapping before trusting live control."
    )



def build_install_restart_validation_summary(install_provenance: dict[str, Any] | None = None) -> str:
    """Return the native post-restart path operators should use before trusting live validation."""
    _ = install_provenance
    return (
        "Restart Home Assistant core, then reopen Settings -> Devices & Services -> Integrations -> Zero Net Export -> "
        "Configure -> Sensors and source mapping to confirm the entry loads, mapped roles persist, and any unavailable or stale roles are named clearly before trusting live control."
    )



def build_install_fingerprint_summary(install_provenance: dict[str, Any] | None = None) -> str:
    """Return a concise multiline summary of the live installed package details."""
    provenance = install_provenance or build_install_provenance()
    lines = [
        f"- component_root: {provenance.get('component_root') or 'n/a'}",
        f"- code_version: {provenance.get('code_version') or 'n/a'}",
        f"- manifest_version: {provenance.get('manifest_version') or 'n/a'}",
        f"- manifest_matches_code_version: {provenance.get('manifest_matches_code_version')}",
    ]
    manifest_error = str(provenance.get("manifest_error") or "").strip()
    if manifest_error:
        lines.append(f"- manifest_error: {manifest_error}")

    for name, details in (provenance.get("tracked_files") or {}).items():
        lines.append(
            f"- {name}: sha256_12={details.get('sha256_12') or 'n/a'}, "
            f"size_bytes={details.get('size_bytes') if details.get('size_bytes') is not None else 'n/a'}, "
            f"exists={details.get('exists')}"
        )

    lines.append(f"- discovery_command: {build_install_discovery_command()}")
    lines.append(f"- git_branch: {provenance.get('git_branch') or 'n/a'}")
    lines.append(f"- git_upstream: {provenance.get('git_upstream') or 'n/a'}")
    lines.append(f"- git_local_vs_upstream: {provenance.get('git_local_vs_upstream') or 'unknown'}")
    lines.append(
        f"- git_ahead_commits: {','.join(provenance.get('git_ahead_commits') or []) or 'none'}"
    )
    lines.append(
        f"- git_behind_commits: {','.join(provenance.get('git_behind_commits') or []) or 'none'}"
    )
    lines.append("- deploy_precondition: push or reconcile the repo branch first if git_local_vs_upstream is not in_sync")
    if provenance.get("git_sync_remediation"):
        lines.append(f"- deploy_sync_remediation: {provenance.get('git_sync_remediation')}")
    lines.append(f"- deploy_dry_run_command: {build_install_deploy_dry_run_command(provenance)}")
    lines.append(f"- deploy_command: {build_install_deploy_command(provenance)}")
    lines.append(f"- validation_command: {build_install_validation_command(provenance)}")
    lines.append(f"- exact_copy_sequence: {build_install_exact_copy_summary(provenance)}")
    lines.append(f"- post_restart_validation: {build_install_restart_validation_summary(provenance)}")

    return "\n".join(lines)


def _parse_changelog_text(text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        heading_match = _CHANGELOG_HEADING_RE.match(line)
        if heading_match:
            if current:
                sections.append(current)
            current = {
                "version": heading_match.group("version"),
                "released_on": heading_match.group("date") or None,
                "highlights": [],
            }
            continue

        if current is None:
            continue

        bullet_match = _BULLET_RE.match(line)
        if bullet_match:
            current["highlights"].append(bullet_match.group("text").strip())

    if current:
        sections.append(current)

    return sections


def _parse_changelog_sections() -> list[dict[str, Any]]:
    path = _changelog_path()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []

    return _parse_changelog_text(text)


def build_release_info(version: str = INTEGRATION_VERSION, *, include_changelog: bool = True) -> dict[str, Any]:
    """Return current release metadata plus a previous-release comparison when available."""
    if not include_changelog:
        cached = _RELEASE_INFO_CACHE.get(version)
        if cached is not None:
            return dict(cached)
        return {
            "current_version": version,
            "released_on": None,
            "highlights": [],
            "highlight_count": 0,
            "headline": f"Version {version}",
            "changes_preview": "Release notes deferred until diagnostics/support surfaces request them.",
            "previous_version": None,
            "previous_released_on": None,
            "previous_highlights": [],
            "summary": f"Installed version {version}; changelog parsing deferred outside the startup path.",
            "has_changelog": False,
        }

    sections: list[dict[str, Any]] = []
    path = _changelog_path()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        text = ""
    if text:
        sections = _parse_changelog_text(text)

    current: dict[str, Any] | None = None
    current = next((item for item in sections if item.get("version") == version), None)
    using_unreleased_fallback = False
    if current is None:
        current = next((item for item in sections if item.get("version") == "Unreleased"), None)
        using_unreleased_fallback = current is not None
    if current is None:
        result = {
            "current_version": version,
            "released_on": None,
            "highlights": [],
            "highlight_count": 0,
            "headline": f"Version {version}",
            "changes_preview": "No changelog entry matched this installed version.",
            "previous_version": None,
            "previous_released_on": None,
            "previous_highlights": [],
            "summary": f"Installed version {version}; no matching changelog entry was found.",
            "has_changelog": False,
        }
        _RELEASE_INFO_CACHE[version] = dict(result)
        return result

    index = sections.index(current)
    previous = sections[index + 1] if index + 1 < len(sections) else None
    highlights = current.get("highlights", [])
    highlight_count = len(highlights)
    summary = (
        f"Installed version {version}"
        + (" using current Unreleased changelog notes" if using_unreleased_fallback else "")
        + (f" ({current['released_on']})" if current.get("released_on") else "")
        + (
            f" with {highlight_count} documented change{'s' if highlight_count != 1 else ''}."
            if highlight_count
            else "; changelog entry is present but has no bullet highlights."
        )
    )
    if previous:
        summary += f" Previous documented release: {previous['version']}."

    preview = " • ".join(highlights[:3]) if highlights else "No bullet highlights were documented for this release."

    result = {
        "current_version": version,
        "released_on": current.get("released_on"),
        "highlights": highlights,
        "highlight_count": highlight_count,
        "headline": (
            f"Version {version}"
            + (" · pending release notes" if using_unreleased_fallback else "")
            + (f" · {current['released_on']}" if current.get("released_on") else "")
        ),
        "changes_preview": preview,
        "previous_version": previous.get("version") if previous else None,
        "previous_released_on": previous.get("released_on") if previous else None,
        "previous_highlights": previous.get("highlights", []) if previous else [],
        "summary": summary,
        "has_changelog": True,
    }
    _RELEASE_INFO_CACHE[version] = dict(result)
    return result
