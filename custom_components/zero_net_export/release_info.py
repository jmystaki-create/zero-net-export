"""Release / changelog metadata helpers for Zero Net Export."""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
import re
import shlex
from typing import Any

from .const import INTEGRATION_VERSION

_CHANGELOG_HEADING_RE = re.compile(r"^## \[(?P<version>[^\]]+)\](?: - (?P<date>.+))?$")
_BULLET_RE = re.compile(r"^[-*]\s+(?P<text>.+)$")
_RELEASE_INFO_CACHE: dict[str, dict[str, Any]] = {}
_INSTALL_PROVENANCE_SNAPSHOT: dict[str, Any] | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _changelog_path() -> Path:
    return _repo_root() / "CHANGELOG.md"


def _component_root() -> Path:
    return Path(__file__).resolve().parent


def _tracked_component_files(component_root: Path | None = None) -> tuple[str, ...]:
    root = component_root or _component_root()
    tracked: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts:
            continue
        if path.suffix not in {".py", ".json"}:
            continue
        tracked.append(path.relative_to(root).as_posix())
    return tuple(tracked)


def _collect_install_provenance() -> dict[str, Any]:
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

    tracked_files = _tracked_component_files(component_root)
    file_fingerprints: dict[str, dict[str, str | int | None]] = {}
    for relative_name in tracked_files:
        path = component_root / relative_name
        exists = path.exists()
        sha256_12: str | None = None
        size_bytes: int | None = None
        if exists:
            try:
                sha256_12 = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
                size_bytes = path.stat().st_size
            except OSError:
                sha256_12 = None
                size_bytes = None
        file_fingerprints[relative_name] = {
            "path": str(path),
            "exists": exists,
            "sha256_12": sha256_12,
            "size_bytes": size_bytes,
        }

    manifest_matches_code_version = manifest_version == INTEGRATION_VERSION if manifest_version else None
    live_validation_safe = manifest_matches_code_version is not False and not manifest_error

    summary = f"Installed package path {component_root}; code version {INTEGRATION_VERSION}"
    if manifest_version:
        summary += f"; manifest version {manifest_version}"
        if manifest_matches_code_version is False:
            summary += " (version mismatch, mixed-build risk)"
    elif manifest_error:
        summary += f"; manifest unavailable ({manifest_error})"

    return {
        "component_root": str(component_root),
        "code_version": INTEGRATION_VERSION,
        "manifest_version": manifest_version,
        "manifest_error": manifest_error,
        "manifest_matches_code_version": manifest_matches_code_version,
        "live_validation_safe": live_validation_safe,
        "tracked_files": file_fingerprints,
        "summary": summary,
    }


@lru_cache(maxsize=1)
def _cached_install_provenance() -> dict[str, Any]:
    return _collect_install_provenance()


def _cache_install_provenance(snapshot: dict[str, Any]) -> dict[str, Any]:
    global _INSTALL_PROVENANCE_SNAPSHOT
    _INSTALL_PROVENANCE_SNAPSHOT = dict(snapshot)
    return dict(_INSTALL_PROVENANCE_SNAPSHOT)


def _build_pending_install_provenance() -> dict[str, Any]:
    component_root = _component_root()
    return {
        "component_root": str(component_root),
        "code_version": INTEGRATION_VERSION,
        "manifest_version": None,
        "manifest_error": None,
        "manifest_matches_code_version": None,
        "live_validation_safe": True,
        "tracked_files": {},
        "summary": (
            f"Installed package path {component_root}; code version {INTEGRATION_VERSION}; "
            "install provenance pending async refresh"
        ),
        "pending_async_refresh": True,
    }


async def async_prime_install_provenance(hass, *, force_refresh: bool = False) -> dict[str, Any]:
    """Warm the install provenance snapshot off the event loop before sync UI helpers use it."""
    if force_refresh or _INSTALL_PROVENANCE_SNAPSHOT is None:
        snapshot = await hass.async_add_executor_job(_collect_install_provenance)
        _cached_install_provenance.cache_clear()
        return _cache_install_provenance(snapshot)
    return build_install_provenance()


def build_install_provenance() -> dict[str, Any]:
    """Return install-path and key-file fingerprint details for live-source validation."""
    if _INSTALL_PROVENANCE_SNAPSHOT is None:
        return _build_pending_install_provenance()
    return dict(_INSTALL_PROVENANCE_SNAPSHOT)


def build_install_consistency_summary(install_provenance: dict[str, Any] | None = None) -> str:
    """Return operator-facing guidance for whether live validation can be trusted."""
    provenance = install_provenance or build_install_provenance()
    if provenance.get("pending_async_refresh"):
        return "Install provenance is still being refreshed asynchronously."
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


def build_install_validation_cli_steps(install_provenance: dict[str, Any] | None = None) -> dict[str, str]:
    """Return exact repo and live-install commands for fingerprint validation."""
    provenance = install_provenance or build_install_provenance()
    component_root_raw = str(provenance.get("component_root") or "").strip()
    component_root = Path(component_root_raw).expanduser() if component_root_raw else None
    compare_target = component_root.parent if component_root and component_root.name == "zero_net_export" else component_root
    compare_target_str = str(compare_target) if compare_target else "/path/to/home-assistant/config/custom_components"

    expected_json = "tmp/expected-install-fingerprint.json"
    compare_json = "tmp/install-fingerprint-compare.json"
    repo_command = (
        "python3 scripts/print_expected_install_fingerprint.py "
        f"--write-json {shlex.quote(expected_json)}"
    )
    compare_command = (
        "python3 scripts/compare_install_fingerprint.py "
        f"{shlex.quote(compare_target_str)} "
        f"--expected-json {shlex.quote(expected_json)} "
        f"--write-json {shlex.quote(compare_json)}"
    )
    combined_command = (
        "python3 scripts/validate_install_fingerprint.py "
        f"{shlex.quote(compare_target_str)} "
        f"--expected-json {shlex.quote(expected_json)} "
        f"--compare-json {shlex.quote(compare_json)}"
    )
    deploy_command = (
        "python3 scripts/deploy_exact_repo_build.py "
        f"{shlex.quote(compare_target_str)}"
    )
    deploy_dry_run_command = f"{deploy_command} --dry-run"
    return {
        "repo_command": repo_command,
        "compare_command": compare_command,
        "combined_command": combined_command,
        "deploy_command": deploy_command,
        "deploy_dry_run_command": deploy_dry_run_command,
        "compare_target": compare_target_str,
    }


def build_install_repair_step(install_provenance: dict[str, Any] | None = None) -> str:
    """Return the next operator action when install provenance blocks trustworthy validation."""
    provenance = install_provenance or build_install_provenance()
    component_root = provenance.get("component_root") or "the active custom_components/zero_net_export path"
    cli_steps = build_install_validation_cli_steps(provenance)
    compare_target = cli_steps["compare_target"]
    if provenance.get("pending_async_refresh"):
        return (
            f"Wait for the async install-provenance refresh to complete for {component_root}, then rerun the exact-build fingerprint check against {compare_target} before treating install provenance as a blocker."
        )
    if provenance.get("manifest_matches_code_version") is False:
        return (
            f"Ask James directly to approve deploy/restart of the exact build for {compare_target} before running release steps. "
            f"After approval, preview the exact repo deploy target with `{cli_steps['deploy_dry_run_command']}` first, then run `{cli_steps['deploy_command']}` and `{cli_steps['combined_command']}` from the repo against that live install path so {component_root} is replaced by one synchronized build before restarting Home Assistant core or trusting live validation."
        )
    if provenance.get("manifest_error"):
        return (
            f"Confirm the exact live Zero Net Export install path at {component_root}, then ask James directly to approve deploy/restart of the exact build for {compare_target} before using release commands. "
            f"After approval, preview the resolved deploy target with `{cli_steps['deploy_dry_run_command']}` before using `{cli_steps['deploy_command']}` if you need to recopy the repo build, and run `{cli_steps['combined_command']}` from the repo against that same live install path before restarting Home Assistant core or trusting live validation."
        )
    return "Installed package provenance looks consistent."


def build_install_fingerprint_summary(install_provenance: dict[str, Any] | None = None) -> str:
    """Return a concise multiline summary of the live installed package details."""
    provenance = install_provenance or build_install_provenance()
    lines = [
        f"- component_root: {provenance.get('component_root') or 'n/a'}",
        f"- code_version: {provenance.get('code_version') or 'n/a'}",
        f"- manifest_version: {provenance.get('manifest_version') or 'n/a'}",
        f"- manifest_matches_code_version: {provenance.get('manifest_matches_code_version')}",
    ]
    if provenance.get("pending_async_refresh"):
        lines.append("- pending_async_refresh: true")
    manifest_error = str(provenance.get("manifest_error") or "").strip()
    if manifest_error:
        lines.append(f"- manifest_error: {manifest_error}")

    for name, details in (provenance.get("tracked_files") or {}).items():
        lines.append(
            f"- {name}: sha256_12={details.get('sha256_12') or 'n/a'}, "
            f"size_bytes={details.get('size_bytes') if details.get('size_bytes') is not None else 'n/a'}, "
            f"exists={details.get('exists')}"
        )

    cli_steps = build_install_validation_cli_steps(provenance)
    lines.extend(
        [
            "- validation_compare_target: " + cli_steps["compare_target"],
            "- deploy_exact_build_dry_run_command: " + cli_steps["deploy_dry_run_command"],
            "- deploy_exact_build_command: " + cli_steps["deploy_command"],
            "- repo_fingerprint_command: " + cli_steps["repo_command"],
            "- live_compare_command: " + cli_steps["compare_command"],
            "- combined_validation_command: " + cli_steps["combined_command"],
        ]
    )

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

        bullet_match = _BULLET_RE.match(line.strip())
        if bullet_match:
            current["highlights"].append(bullet_match.group("text"))

    if current:
        sections.append(current)

    return sections


def _load_changelog() -> list[dict[str, Any]]:
    cache_key = "changelog"
    cached = _RELEASE_INFO_CACHE.get(cache_key)
    if cached is not None:
        return cached.get("sections", [])

    path = _changelog_path()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        sections: list[dict[str, Any]] = []
    else:
        sections = _parse_changelog_text(text)

    _RELEASE_INFO_CACHE[cache_key] = {"sections": sections}
    return sections


def _section_for_version(version: str) -> dict[str, Any] | None:
    for section in _load_changelog():
        if str(section.get("version")) == version:
            return section
    return None


def build_release_info(current_version: str, *, include_changelog: bool = True) -> dict[str, Any]:
    """Return release metadata for the currently installed version."""
    section = _section_for_version(current_version) if include_changelog else None
    if section is None and include_changelog:
        section = _section_for_version("Unreleased")

    highlights = list(section.get("highlights", [])) if section else []
    released_on = section.get("released_on") if section else None
    has_changelog = section is not None
    headline_version = current_version if current_version else "Unknown"
    summary = (
        f"Installed version {headline_version}; changelog parsing deferred outside the startup path."
        if not include_changelog
        else f"Installed version {headline_version}"
    )
    if include_changelog and released_on:
        summary += f" released {released_on}"
    if include_changelog and not has_changelog:
        summary += "; no matching changelog entry found"
    elif include_changelog and not highlights:
        summary += "; no highlights recorded"

    preview = (
        "Release notes deferred until Diagnostics surfaces request them."
        if not include_changelog
        else ("; ".join(highlights[:3]) if highlights else "No release highlights recorded.")
    )

    return {
        "current_version": headline_version,
        "released_on": released_on,
        "highlights": highlights,
        "highlight_count": len(highlights),
        "headline": f"Version {headline_version}",
        "release_summary": preview,
        "changes_preview": preview,
        "summary": summary,
        "has_changelog": has_changelog,
    }
