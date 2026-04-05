"""Release / changelog metadata helpers for Zero Net Export."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .const import INTEGRATION_VERSION

_CHANGELOG_HEADING_RE = re.compile(r"^## \[(?P<version>[^\]]+)\](?: - (?P<date>.+))?$")
_BULLET_RE = re.compile(r"^[-*]\s+(?P<text>.+)$")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _changelog_path() -> Path:
    return _repo_root() / "CHANGELOG.md"


def _parse_changelog_sections() -> list[dict[str, Any]]:
    path = _changelog_path()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []

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


def build_release_info(version: str = INTEGRATION_VERSION) -> dict[str, Any]:
    """Return current release metadata plus a previous-release comparison when available."""
    sections = _parse_changelog_sections()
    current = next((item for item in sections if item.get("version") == version), None)
    if current is None:
        return {
            "current_version": version,
            "released_on": None,
            "highlights": [],
            "previous_version": None,
            "previous_released_on": None,
            "previous_highlights": [],
            "summary": f"Installed version {version}; no matching changelog entry was found.",
            "has_changelog": False,
        }

    index = sections.index(current)
    previous = sections[index + 1] if index + 1 < len(sections) else None
    highlight_count = len(current.get("highlights") or [])
    summary = (
        f"Installed version {version}"
        + (f" ({current['released_on']})" if current.get("released_on") else "")
        + (
            f" with {highlight_count} documented change{'s' if highlight_count != 1 else ''}."
            if highlight_count
            else "; changelog entry is present but has no bullet highlights."
        )
    )
    if previous:
        summary += f" Previous documented release: {previous['version']}."

    return {
        "current_version": version,
        "released_on": current.get("released_on"),
        "highlights": current.get("highlights", []),
        "previous_version": previous.get("version") if previous else None,
        "previous_released_on": previous.get("released_on") if previous else None,
        "previous_highlights": previous.get("highlights", []) if previous else [],
        "summary": summary,
        "has_changelog": True,
    }
