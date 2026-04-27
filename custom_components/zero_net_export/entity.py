"""Base entity helpers."""
from __future__ import annotations

from collections.abc import Mapping
from urllib.parse import urlencode

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, INTEGRATION_VERSION


def _device_identifier_part(value: object) -> str:
    """Return a stable device-registry-safe identifier fragment."""
    text = str(value or "unknown").strip()
    return text.replace(".", "_").replace(":", "_").replace("/", "_") or "unknown"


def managed_load_detail_mapping(value: object) -> dict:
    """Return a managed-load detail mapping, tolerating malformed runtime entries."""
    return dict(value) if isinstance(value, Mapping) else {}


def managed_load_details_mapping(value: object) -> dict[str, dict]:
    """Return all managed-load details, tolerating malformed runtime containers."""
    if not isinstance(value, Mapping):
        return {}
    return {str(device_key): managed_load_detail_mapping(detail) for device_key, detail in value.items()}


def validation_details_mapping(value: object) -> dict:
    """Return validation details, tolerating malformed runtime containers."""
    return dict(value) if isinstance(value, Mapping) else {}


def zero_net_export_device_info(coordinator) -> dict:
    """Return the integration's primary Home Assistant device info."""
    return {
        "identifiers": {(DOMAIN, coordinator.entry.entry_id)},
        "name": coordinator.entry.title,
        "manufacturer": "OpenClaw",
        "model": "Zero Net Export",
        "sw_version": INTEGRATION_VERSION,
    }


def managed_load_display_name(device_key: str, details: dict | None = None) -> str:
    """Return a stable display name for sparse managed-load details."""
    detail = managed_load_detail_mapping(details)
    return str(detail.get("name") or device_key or "Managed device")


def managed_load_detail(coordinator, device_key: str, device_name: str | None = None) -> dict:
    """Return the latest coordinator detail for a managed load."""
    state = getattr(coordinator, "data", None)
    details = getattr(state, "device_details", {}) or {}
    detail = managed_load_detail_mapping(details.get(device_key, {}) if isinstance(details, Mapping) else {})
    if device_name:
        detail.setdefault("name", device_name)
    return detail


def managed_load_configuration_url(coordinator, device_key: str) -> str:
    """Return the native HA configuration URL exposed as the row settings/gear action."""
    entry_id = _device_identifier_part(getattr(coordinator.entry, "entry_id", "entry"))
    key = _device_identifier_part(device_key)
    query = urlencode({"managed_device": f"{entry_id}:{key}"})
    return f"homeassistant://navigate/config/integrations/integration/{DOMAIN}?{query}"


def managed_load_device_info(coordinator, device_key: str, detail: dict | None = None) -> dict:
    """Return device info that makes a managed load appear as its own HA device row."""
    detail = detail or managed_load_detail(coordinator, device_key)
    name = str(detail.get("name") or device_key or "Managed device").strip()
    kind = str(detail.get("kind") or "managed").strip()
    return {
        "identifiers": {(DOMAIN, f"{coordinator.entry.entry_id}:managed-device:{device_key}")},
        "name": f"Managed Devices — {name}",
        "manufacturer": "OpenClaw",
        "model": f"Managed Devices — {kind.title()} managed load" if kind else "Managed Devices — Managed load",
        "sw_version": INTEGRATION_VERSION,
        "via_device": (DOMAIN, coordinator.entry.entry_id),
        "configuration_url": managed_load_configuration_url(coordinator, device_key),
        "suggested_area": "Zero Net Export Managed Devices",
    }


def attach_managed_load_device(entity, coordinator, device_key: str, device_name: str | None = None) -> None:
    """Attach an entity to its managed-load child device instead of the controller device."""
    entity._attr_device_info = managed_load_device_info(
        coordinator,
        device_key,
        managed_load_detail(coordinator, device_key, device_name),
    )
    entity._zero_net_export_managed_device_key = device_key


def _integration_page_child_device_identifier(device_info: dict | None) -> tuple[str, str] | None:
    """Return the managed/unmanaged integration-page child-device identifier, if present."""
    for identifier in (device_info or {}).get("identifiers", set()) or set():
        if len(identifier) != 2:
            continue
        domain, value = identifier
        value = str(value)
        if domain == DOMAIN and (":managed-device:" in value or ":unmanaged-candidate:" in value):
            return (domain, value)
    return None


def unmanaged_candidate_device_info(coordinator, candidate: dict) -> dict:
    """Return device info that makes an unmanaged candidate appear as its own HA device row."""
    entity_id = str(candidate.get("entity_id") or "candidate").strip()
    name = str(candidate.get("name") or entity_id).strip()
    kind = str(candidate.get("kind") or "candidate").strip()
    return {
        "identifiers": {(DOMAIN, f"{coordinator.entry.entry_id}:unmanaged-candidate:{_device_identifier_part(entity_id)}")},
        "name": f"Un Managed — {name}",
        "manufacturer": "OpenClaw",
        "model": f"Un Managed — {kind.title()} unmanaged candidate" if kind else "Un Managed — Unmanaged candidate",
        "sw_version": INTEGRATION_VERSION,
        "via_device": (DOMAIN, coordinator.entry.entry_id),
        "configuration_url": f"homeassistant://navigate/config/entities?{urlencode({'entity_id': entity_id})}",
        "suggested_area": "Zero Net Export Un Managed",
    }


class ZeroNetExportEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = zero_net_export_device_info(coordinator)

    async def async_added_to_hass(self) -> None:
        """Keep existing integration-page child devices updated with their settings/gear URL."""
        parent = getattr(super(), "async_added_to_hass", None)
        if parent is not None:
            await parent()

        device_info = getattr(self, "_attr_device_info", None)
        config_url = (device_info or {}).get("configuration_url")
        identifier = _integration_page_child_device_identifier(device_info)
        if not config_url or identifier is None:
            return

        from homeassistant.helpers import device_registry as dr

        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get_device({identifier})
        if device is not None and getattr(device, "configuration_url", None) != config_url:
            device_registry.async_update_device(device.id, configuration_url=config_url)

    @property
    def _state(self):
        return self.coordinator.data

    @property
    def _validation_details(self) -> dict:
        state = self._state
        if state is None:
            return {}
        return validation_details_mapping(getattr(state, "validation_details", {}) or {})

    @property
    def available(self) -> bool:
        return self._state is not None
