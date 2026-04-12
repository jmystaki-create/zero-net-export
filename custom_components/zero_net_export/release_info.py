"""Release / changelog metadata helpers for Zero Net Export."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
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


def _short_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except OSError:
        return None


def build_install_provenance() -> dict[str, Any]:
    """Return install-path and key-file fingerprint details for live-source validation."""
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

    tracked_files = ("manifest.json", "config_flow.py", "native_support.py", "coordinator.py")
    file_fingerprints: dict[str, dict[str, str | int | None]] = {}
    for relative_name in tracked_files:
        path = component_root / relative_name
        exists = path.exists()
        file_fingerprints[relative_name] = {
            "path": str(path),
            "exists": exists,
            "sha256_12": _short_sha256(path) if exists else None,
            "size_bytes": path.stat().st_size if exists else None,
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


def build_install_repair_step(install_provenance: dict[str, Any] | None = None) -> str:
    """Return the next operator action when install provenance blocks trustworthy validation."""
    provenance = install_provenance or build_install_provenance()
    component_root = provenance.get("component_root") or "the active custom_components/zero_net_export path"
    if provenance.get("manifest_matches_code_version") is False:
        return (
            f"Deploy one exact intended Zero Net Export build to {component_root}, confirm manifest.json and the tracked files all come from that same build, "
            "then restart Home Assistant core before trusting live validation or source diagnostics."
        )
    if provenance.get("manifest_error"):
        return (
            f"Confirm the exact live Zero Net Export install path at {component_root}, compare manifest.json and the tracked-file fingerprints from that path, "
            "then restart Home Assistant core from one synchronized build before trusting live validation or source diagnostics."
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
    manifest_error = str(provenance.get("manifest_error") or "").strip()
    if manifest_error:
        lines.append(f"- manifest_error: {manifest_error}")

    for name, details in (provenance.get("tracked_files") or {}).items():
        lines.append(
            f"- {name}: sha256_12={details.get('sha256_12') or 'n/a'}, "
            f"size_bytes={details.get('size_bytes') if details.get('size_bytes') is not None else 'n/a'}, "
            f"exists={details.get('exists')}"
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
