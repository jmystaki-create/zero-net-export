"""Shared panel and launcher URL helpers for Zero Net Export."""
from __future__ import annotations

from urllib.parse import urlencode

from homeassistant.config_entries import ConfigEntry


PANEL_ROUTE = "/zero-net-export"


def panel_setup_path(entry: ConfigEntry | None = None, *, source: str | None = None) -> str:
    """Return the real in-app panel setup route."""
    params: dict[str, str] = {"tab": "setup"}
    if entry is not None:
        params["entry"] = entry.entry_id
    if source:
        params["source"] = source
    return f"{PANEL_ROUTE}?{urlencode(params)}"


def panel_launcher_path(entry: ConfigEntry | None = None, *, source: str | None = None) -> str:
    """Return the direct in-app setup route.

    Older builds used a launcher HTML trampoline here, but Home Assistant can treat
    that as an external-site handoff on some clients. Returning the real panel route
    keeps Configure -> setup inside Home Assistant.
    """
    return panel_setup_path(entry, source=source)
