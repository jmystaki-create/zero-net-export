"""Base entity helpers."""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, INTEGRATION_VERSION


def _device_identifier_part(value: object) -> str:
    """Return a stable device-registry-safe identifier fragment."""
    text = str(value or "unknown").strip()
    return text.replace(".", "_").replace(":", "_").replace("/", "_") or "unknown"


def zero_net_export_device_info(coordinator) -> dict:
    """Return the integration's primary Home Assistant device info."""
    return {
        "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
        "name": coordinator.entry.title,
        "manufacturer": "OpenClaw",
        "model": "Zero Net Export",
        "sw_version": INTEGRATION_VERSION,
    }


def managed_load_device_info(coordinator, device_key: str, detail: dict | None = None) -> dict:
    """Return device info that makes a managed load appear as its own HA device row."""
    detail = detail or {}
    name = str(detail.get("name") or device_key or "Managed device").strip()
    kind = str(detail.get("kind") or "managed").strip()
    entity_id = str(detail.get("entity_id") or "").strip()
    return {
        "identifiers": {(DOMAIN, f"{coordinator.entry.entry_id}:managed-device:{device_key}")},
        "name": f"Managed Devices — {name}",
        "manufacturer": "OpenClaw",
        "model": f"{kind.title()} managed load" if kind else "Managed load",
        "sw_version": INTEGRATION_VERSION,
        "via_device": (DOMAIN, coordinator.entry.entry_id),
        **({"configuration_url": f"homeassistant://navigate/config/integrations/integration/{DOMAIN}"} if not entity_id else {}),
    }


def unmanaged_candidate_device_info(coordinator, candidate: dict) -> dict:
    """Return device info that makes an unmanaged candidate appear as its own HA device row."""
    entity_id = str(candidate.get("entity_id") or "candidate").strip()
    name = str(candidate.get("name") or entity_id).strip()
    kind = str(candidate.get("kind") or "candidate").strip()
    domain = str(candidate.get("domain") or entity_id.partition(".")[0] or "unknown").strip()
    return {
        "identifiers": {(DOMAIN, f"{coordinator.entry.entry_id}:unmanaged-candidate:{_device_identifier_part(entity_id)}")},
        "name": f"Un Managed — {name}",
        "manufacturer": "OpenClaw",
        "model": f"{kind.title()} unmanaged candidate" if kind else "Unmanaged candidate",
        "sw_version": INTEGRATION_VERSION,
        "via_device": (DOMAIN, coordinator.entry.entry_id),
        "configuration_url": f"homeassistant://navigate/config/entities?entity_id={entity_id}",
        "suggested_area": f"Zero Net Export {domain.title()} candidates",
    }


class ZeroNetExportEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = zero_net_export_device_info(coordinator)

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
