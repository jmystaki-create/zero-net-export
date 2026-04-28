"""Base entity helpers."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import re
from urllib.parse import urlencode

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, INTEGRATION_VERSION


def _legacy_device_identifier_part(value: object) -> str:
    """Return the pre-ZNE-508 registry identifier fragment for upgrade cleanup only."""
    original = str(value or "unknown").strip() or "unknown"
    return re.sub(
        r"[^a-z0-9_]+",
        "_",
        original.lower().replace(".", "_").replace(":", "_").replace("/", "_"),
    ).strip("_") or "unknown"


def _device_identifier_part(value: object) -> str:
    """Return a stable, safe, collision-resistant device-registry identifier fragment."""
    original = str(value or "unknown").strip() or "unknown"
    safe = _legacy_device_identifier_part(original)
    if original == safe:
        return safe
    digest = hashlib.sha1(original.encode("utf-8")).hexdigest()[:8]
    return f"{safe}_{digest}"


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
    fallback_details = getattr(coordinator, "_zne_integration_page_managed_details", {}) or {}
    fallback_detail = managed_load_detail_mapping(
        fallback_details.get(device_key, {}) if isinstance(fallback_details, Mapping) else {}
    )
    for key, value in fallback_detail.items():
        if detail.get(key) in (None, ""):
            detail[key] = value
    if device_name:
        detail.setdefault("name", device_name)
    return detail


def managed_load_configuration_url(coordinator, device_key: str) -> str:
    """Return the native HA configuration URL exposed as the row settings/gear action."""
    entry_id = str(getattr(coordinator.entry, "entry_id", "entry") or "entry").strip() or "entry"
    key = str(device_key or "unknown").strip() or "unknown"
    query = urlencode({"managed_device": f"{entry_id}:{key}"})
    return f"homeassistant://navigate/config/integrations/integration/{DOMAIN}?{query}"


def managed_load_device_info(coordinator, device_key: str, detail: dict | None = None) -> dict:
    """Return device info that makes a managed load appear as its own HA device row."""
    detail = detail or managed_load_detail(coordinator, device_key)
    name = str(detail.get("name") or device_key or "Managed device").strip()
    kind = str(detail.get("kind") or "managed").strip()
    return {
        "identifiers": {(DOMAIN, f"{coordinator.entry.entry_id}:managed-device:{_device_identifier_part(device_key)}")},
        "name": f"Managed Devices — {name}",
        "manufacturer": "OpenClaw",
        "model": f"Managed Devices — {kind.title()} managed load" if kind else "Managed Devices — Managed load",
        "sw_version": INTEGRATION_VERSION,
        "via_device": (DOMAIN, coordinator.entry.entry_id),
        "configuration_url": managed_load_configuration_url(coordinator, device_key),
    }


def legacy_managed_load_device_info(coordinator, device_key: str) -> dict | None:
    """Return legacy managed-row device info when the old identifier differs."""
    current = _device_identifier_part(device_key)
    legacy = _legacy_device_identifier_part(device_key)
    if legacy == current:
        return None
    return {"identifiers": {(DOMAIN, f"{coordinator.entry.entry_id}:managed-device:{legacy}")}}


def attach_managed_load_device(entity, coordinator, device_key: str, device_name: str | None = None) -> None:
    """Attach an entity to its managed-load child device instead of the controller device."""
    entity._attr_device_info = managed_load_device_info(
        coordinator,
        device_key,
        managed_load_detail(coordinator, device_key, device_name),
    )
    entity._zero_net_export_legacy_device_info = legacy_managed_load_device_info(coordinator, device_key)
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



def _integration_page_child_device_registry_entry(hass, device_info: dict | None):
    """Return the registry and device entry for a managed/unmanaged child device."""
    identifier = _integration_page_child_device_identifier(device_info)
    if identifier is None:
        return None, None

    try:
        from homeassistant.helpers import device_registry as dr
    except Exception:
        return None, None

    try:
        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device({identifier})
    except Exception:
        return None, None
    return device_registry, device


def sync_integration_page_child_device_registry(hass, device_info: dict | None, legacy_device_info: dict | None = None) -> None:
    """Refresh device-registry metadata for managed/unmanaged integration-page rows."""
    if legacy_device_info is not None:
        remove_integration_page_child_device_registry(hass, legacy_device_info)

    device_registry, device = _integration_page_child_device_registry_entry(hass, device_info)
    if device_registry is None or device is None:
        return

    updates = {}
    field_map = {
        "configuration_url": "configuration_url",
        "name": "name",
        "manufacturer": "manufacturer",
        "model": "model",
        "sw_version": "sw_version",
    }
    for info_key, update_key in field_map.items():
        value = (device_info or {}).get(info_key)
        if value in (None, ""):
            continue
        device_value = getattr(device, info_key, None)
        update_value = getattr(device, update_key, None)
        if device_value != value and update_value != value:
            updates[update_key] = value

    if updates:
        device_registry.async_update_device(device.id, **updates)


def remove_integration_page_child_device_registry(hass, device_info: dict | None) -> None:
    """Remove a stale managed/unmanaged child device row from the device registry."""
    device_registry, device = _integration_page_child_device_registry_entry(hass, device_info)
    if device_registry is None or device is None:
        return
    remove_device = getattr(device_registry, "async_remove_device", None)
    if remove_device is None:
        return
    try:
        remove_device(device.id)
    except Exception:
        return


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
    }


def legacy_unmanaged_candidate_device_info(coordinator, candidate: dict) -> dict | None:
    """Return legacy unmanaged-row device info when the old identifier differs."""
    entity_id = str(candidate.get("entity_id") or "candidate").strip()
    current = _device_identifier_part(entity_id)
    legacy = _legacy_device_identifier_part(entity_id)
    if legacy == current:
        return None
    return {"identifiers": {(DOMAIN, f"{coordinator.entry.entry_id}:unmanaged-candidate:{legacy}")}}


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

        sync_integration_page_child_device_registry(
            self.hass,
            getattr(self, "_attr_device_info", None),
            getattr(self, "_zero_net_export_legacy_device_info", None),
        )

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
