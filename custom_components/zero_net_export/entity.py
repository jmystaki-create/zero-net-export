"""Base entity helpers."""
from __future__ import annotations

import json
from pathlib import Path

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, INTEGRATION_VERSION


def _device_surface_version() -> str:
    """Return the version shown on the HA device surface."""
    manifest_path = Path(__file__).with_name("manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return INTEGRATION_VERSION
    version = manifest.get("version")
    return str(version) if version is not None else INTEGRATION_VERSION


class ZeroNetExportEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
            "name": coordinator.entry.title,
            "manufacturer": "OpenClaw",
            "model": "Zero Net Export",
            "sw_version": _device_surface_version(),
        }

    @property
    def _state(self):
        return self.coordinator.data

    @property
    def _validation_details(self) -> dict:
        state = self._state
        if state is None:
            return {}
        return state.validation_details or {}

    @property
    def available(self) -> bool:
        return self._state is not None
