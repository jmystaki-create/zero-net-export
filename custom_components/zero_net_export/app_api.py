"""Application-facing helpers for Zero Net Export."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    APP_MODULE_URL,
    APP_PANEL_COMPONENT_NAME,
    APP_PANEL_ICON,
    APP_PANEL_TITLE,
    APP_PANEL_URL_PATH,
    DOMAIN,
    INTEGRATION_VERSION,
)


def build_app_panel_config(hass: HomeAssistant) -> dict[str, Any]:
    """Return the static bootstrap payload for the Home Assistant app panel."""
    entries: list[ConfigEntry] = hass.config_entries.async_entries(DOMAIN)
    return {
        "domain": DOMAIN,
        "title": APP_PANEL_TITLE,
        "version": INTEGRATION_VERSION,
        "panel_url_path": APP_PANEL_URL_PATH,
        "module_url": APP_MODULE_URL,
        "component_name": APP_PANEL_COMPONENT_NAME,
        "icon": APP_PANEL_ICON,
        "entries": [
            {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "state": str(getattr(entry, "state", "unknown")),
            }
            for entry in entries
        ],
    }
