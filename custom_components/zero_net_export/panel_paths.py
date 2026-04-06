"""Shared panel and launcher URL helpers for Zero Net Export."""
from __future__ import annotations

from urllib.parse import urlencode

from homeassistant.config_entries import ConfigEntry


PANEL_ROUTE = "/zero-net-export"
PANEL_LAUNCHER_ROUTE = "/api/zero_net_export/panel-launch.html"


def panel_setup_path(entry: ConfigEntry | None = None, *, source: str | None = None) -> str:
    """Return the real in-app panel setup route."""
    params: dict[str, str] = {"tab": "setup"}
    if entry is not None:
        params["entry"] = entry.entry_id
    if source:
        params["source"] = source
    return f"{PANEL_ROUTE}?{urlencode(params)}"


def panel_launcher_path(entry: ConfigEntry | None = None, *, source: str | None = None) -> str:
    """Return a same-origin launcher page that redirects into the panel route."""
    target = panel_setup_path(entry, source=source)
    return f"{PANEL_LAUNCHER_ROUTE}?{urlencode({'target': target})}"
