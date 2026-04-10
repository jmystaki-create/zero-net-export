"""Release / changelog metadata helpers for Zero Net Export."""
from __future__ import annotations

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
