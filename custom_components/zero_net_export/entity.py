"""Base entity helpers."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import re
from urllib.parse import urlencode

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON, DOMAIN, INTEGRATION_VERSION
from .device_model import parse_device_configs


MANAGED_LOAD_SETTINGS_ICON = "mdi:cog-outline"


FLEET_WORKSPACE_SENSOR_KEYS = {
    "managed_devices_surface",
    "managed_fleet_overview",
    "managed_fleet_attention",
    "managed_fleet_ready",
    "unmanaged_candidate_count",
    "unmanaged_candidate_overview",
    "top_unmanaged_candidate",
    "top_candidate_fit",
    "top_candidate_warnings",
    "candidate_shortlist",
    "candidate_shortlist_fit",
    "fleet_console_next_step",
}


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


def configured_managed_load_details(entry) -> dict[str, dict[str, object]]:
    """Return configured managed-load details when runtime has not populated yet."""
    raw_inventory = getattr(entry, "options", {}).get(
        CONF_DEVICE_INVENTORY_JSON,
        getattr(entry, "data", {}).get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
    )
    devices, _issues = parse_device_configs(raw_inventory)
    return {
        device.key: {
            "name": device.name,
            "kind": device.kind,
            "entity_id": device.entity_id,
            "status": "configured",
            "enabled": device.enabled,
            "effective_enabled": device.enabled,
            "priority": device.priority,
            "nominal_power_w": device.nominal_power_w,
            "min_power_w": device.min_power_w,
            "max_power_w": device.max_power_w,
            "step_w": device.step_w,
        }
        for device in devices
    }


def integration_page_managed_load_details(entry, state) -> dict[str, dict[str, object]]:
    """Return managed rows for native surfaces, merging config inventory with runtime details."""
    configured_details = configured_managed_load_details(entry)
    runtime_details = managed_load_details_mapping(getattr(state, "device_details", {}) or {}) if state is not None else {}
    if not runtime_details:
        return configured_details
    merged_details = {device_key: dict(detail) for device_key, detail in configured_details.items()}
    for device_key, detail in runtime_details.items():
        merged_detail = dict(merged_details.get(device_key, {}))
        merged_detail.update(detail)
        merged_details[device_key] = merged_detail
    return merged_details


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


def managed_load_settings_action_name(device_name: str, action: str) -> str:
    """Return a visible managed-device settings/action label for native HA rows."""
    name = str(device_name or "Managed device").strip() or "Managed device"
    action_label = str(action or "settings").strip() or "settings"
    return f"⚙ Settings — {name} {action_label}"


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
        "name": f"Managed Devices — ⚙ Settings — {name}",
        "manufacturer": "OpenClaw",
        "model": f"Managed Devices — ⚙ Settings — {kind.title()} managed load" if kind else "Managed Devices — ⚙ Settings — Managed load",
        "sw_version": INTEGRATION_VERSION,
        "via_device": (DOMAIN, coordinator.entry.entry_id),
        "configuration_url": managed_load_configuration_url(coordinator, device_key),
    }


def legacy_managed_load_device_info(coordinator, device_key: str) -> list[dict]:
    """Return legacy managed-row device infos when old identifiers differ."""
    entry_id = coordinator.entry.entry_id
    current_identifier = f"{entry_id}:managed-device:{_device_identifier_part(device_key)}"
    legacy_identifiers = []

    # ZNE-507 removed the pre-hardening raw device-key identifier. Existing installs
    # may still have that device-registry row after upgrade when the key contained
    # separators, spaces, or other unsafe punctuation.
    raw_key = str(device_key or "unknown").strip() or "unknown"
    legacy_identifiers.append(f"{entry_id}:managed-device:{raw_key}")

    # ZNE-508 then added hash differentiators for normalized fragments. Keep cleaning
    # up that intermediate unhashed identifier too so upgrades converge to one row.
    legacy_identifiers.append(f"{entry_id}:managed-device:{_legacy_device_identifier_part(device_key)}")

    return [
        {"identifiers": {(DOMAIN, identifier)}}
        for identifier in dict.fromkeys(legacy_identifiers)
        if identifier != current_identifier
    ]


def attach_managed_load_device(entity, coordinator, device_key: str, device_name: str | None = None) -> None:
    """Attach an entity to its managed-load child device instead of the controller device."""
    entity._attr_device_info = managed_load_device_info(
        coordinator,
        device_key,
        managed_load_detail(coordinator, device_key, device_name),
    )
    entity._attr_icon = MANAGED_LOAD_SETTINGS_ICON
    entity._zero_net_export_legacy_device_info = legacy_managed_load_device_info(coordinator, device_key)
    entity._zero_net_export_managed_device_key = device_key


def refresh_managed_load_entity(hass, entity, coordinator, device_key: str, detail: dict[str, object]) -> None:
    """Refresh a native managed-load entity after config/runtime detail changes."""
    device_name = managed_load_display_name(device_key, detail)
    suffix = getattr(entity, "_zero_net_export_managed_name_suffix", None)
    if suffix:
        entity._attr_name = managed_load_settings_action_name(device_name, suffix)
    attach_managed_load_device(entity, coordinator, device_key, device_name)
    sync_integration_page_child_device_registry(
        hass,
        getattr(entity, "_attr_device_info", None),
        getattr(entity, "_zero_net_export_legacy_device_info", None),
    )
    write_state = getattr(entity, "async_write_ha_state", None)
    if write_state is not None:
        write_state()


def schedule_entity_removal(hass, entity) -> None:
    """Remove a stale HA entity, tolerating test and older-HA shims."""
    remove = getattr(entity, "async_remove", None)
    if remove is None:
        return
    try:
        result = remove(force_remove=True)
    except TypeError:
        result = remove()
    if result is None:
        return
    create_task = getattr(hass, "async_create_task", None)
    if create_task is not None:
        create_task(result)
        return
    close = getattr(result, "close", None)
    if close is not None:
        close()


def register_managed_load_platform_sync(hass, entry, coordinator, async_add_entities, known_entities, entity_factory) -> None:
    """Keep per-managed-device platform entities aligned after setup."""

    def _sync_managed_load_entities() -> None:
        state = getattr(coordinator, "data", None)
        managed_details = integration_page_managed_load_details(entry, state)
        coordinator._zne_integration_page_managed_details = managed_details
        current_device_keys = set(managed_details)
        for stale_key in sorted(set(known_entities) - current_device_keys):
            stale_entities = known_entities.pop(stale_key)
            for stale_entity in stale_entities:
                schedule_entity_removal(hass, stale_entity)
        new_entities = []
        for device_key, detail in managed_details.items():
            existing_entities = known_entities.get(device_key)
            if existing_entities is not None:
                for entity in existing_entities:
                    refresh_managed_load_entity(hass, entity, coordinator, device_key, detail)
                continue
            device_entities = list(entity_factory(device_key, detail))
            known_entities[device_key] = device_entities
            new_entities.extend(device_entities)
        if new_entities:
            async_add_entities(new_entities)

    add_listener = getattr(coordinator, "async_add_listener", None)
    if add_listener is None:
        return
    unsubscribe = add_listener(_sync_managed_load_entities)
    async_on_unload = getattr(entry, "async_on_unload", None)
    if unsubscribe is not None and async_on_unload is not None:
        async_on_unload(unsubscribe)


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


def sync_integration_page_child_device_registry(hass, device_info: dict | None, legacy_device_info: object = None) -> None:
    """Refresh device-registry metadata for managed/unmanaged integration-page rows."""
    if legacy_device_info is not None:
        legacy_infos = legacy_device_info if isinstance(legacy_device_info, list) else [legacy_device_info]
        for legacy_info in legacy_infos:
            remove_integration_page_child_device_registry(hass, legacy_info)

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
    identifier = _integration_page_child_device_identifier(device_info)
    device_registry, device = _integration_page_child_device_registry_entry(hass, device_info)
    if device_registry is None or device is None:
        return
    remove_device = getattr(device_registry, "async_remove_device", None)
    if remove_device is None:
        return
    device_id = str(getattr(device, "id", "") or "")
    try:
        remove_device(device.id)
    except Exception:
        return
    if identifier is None or not device_id:
        return
    if ":unmanaged-candidate:" in identifier[1]:
        entry_id = identifier[1].split(":unmanaged-candidate:", 1)[0]
        remove_unmanaged_candidate_entity_registry_entries_for_entry(hass, entry_id, {device_id})
    elif ":managed-device:" in identifier[1]:
        entry_id = identifier[1].split(":managed-device:", 1)[0]
        _remove_entity_registry_entries_attached_to_devices(
            hass,
            entry_id,
            {device_id},
            preserve_current_workflow_entries=False,
        )


def _device_entry_identifiers(device) -> set[tuple[str, str]]:
    """Return registry identifiers from real HA entries and test doubles."""
    identifiers = getattr(device, "identifiers", None)
    if identifiers is None:
        identifier = getattr(device, "identifier", None)
        identifiers = {identifier} if identifier is not None else set()
    normalized: set[tuple[str, str]] = set()
    for identifier in identifiers or set():
        if not isinstance(identifier, tuple) or len(identifier) != 2:
            continue
        domain, value = identifier
        normalized.add((str(domain), str(value)))
    return normalized


def _entity_registry_entries(entity_registry) -> list[object]:
    """Return entity-registry entries from real HA registries and test doubles."""
    entities = getattr(entity_registry, "entities", None)
    if entities is None:
        return []
    try:
        return list(entities.values() if isinstance(entities, Mapping) else entities)
    except Exception:
        return []


def _remove_entity_registry_entry(entity_registry, entity) -> None:
    """Remove one entity-registry entry, tolerating HA/test-double API shapes."""
    remove = getattr(entity_registry, "async_remove", None)
    entity_id = getattr(entity, "entity_id", None)
    if remove is None or not entity_id:
        return
    try:
        remove(entity_id)
    except Exception:
        return


def _is_current_fleet_workspace_entity_registry_entry(entity, entry_id: str) -> bool:
    """Return True for current Managed Devices workflow/backlog/review entries."""
    unique_id = str(getattr(entity, "unique_id", "") or "")
    current_workspace_unique_ids = {f"{entry_id}_{key}" for key in FLEET_WORKSPACE_SENSOR_KEYS}
    if unique_id in current_workspace_unique_ids:
        return True

    entity_id = str(getattr(entity, "entity_id", "") or "")
    return any(
        entity_id.endswith(f"_{key}") or re.search(rf"_{re.escape(key)}_\d+$", entity_id)
        for key in FLEET_WORKSPACE_SENSOR_KEYS
    )


def _is_legacy_unmanaged_candidate_entity_registry_entry(
    entity,
    entry_id: str,
    *,
    require_entry_scoped_unique_id: bool = False,
) -> bool:
    """Return True for old peer-row unmanaged-candidate entity-registry entries."""
    unique_id = str(getattr(entity, "unique_id", "") or "")
    if _is_current_fleet_workspace_entity_registry_entry(entity, entry_id):
        return False

    # When config-entry ownership is missing, only current-entry-scoped legacy
    # unique IDs are safe to remove.  A bare ``*_unmanaged_candidate`` entity id is
    # not enough to distinguish another Zero Net Export config entry's orphan.
    if not require_entry_scoped_unique_id:
        entity_id = str(getattr(entity, "entity_id", "") or "")
        if entity_id.endswith("_unmanaged_candidate"):
            return True
        if unique_id.endswith("_unmanaged_candidate"):
            return True

    # Older peer-row entities commonly used ``<entry>_unmanaged_candidate_<entity>``
    # unique IDs.  Do not treat controller/backlog sensors such as
    # ``<entry>_unmanaged_candidate_count`` as peer rows when they have already
    # lost their device id; only candidate-domain suffixes belong to legacy rows.
    prefix = f"{entry_id}_unmanaged_candidate_"
    if not unique_id.startswith(prefix):
        return False
    candidate_part = unique_id[len(prefix) :]
    candidate_domain_prefixes = (
        "switch_",
        "input_boolean_",
        "light_",
        "number_",
        "input_number_",
    )
    return candidate_part.startswith(candidate_domain_prefixes)


def _entity_registry_entry_config_entry_ids(entity) -> set[str]:
    """Return config-entry ids from old and new HA entity-registry shapes."""
    ids: set[str] = set()
    config_entry_id = str(getattr(entity, "config_entry_id", "") or "")
    if config_entry_id:
        ids.add(config_entry_id)
    config_entry_ids = getattr(entity, "config_entry_ids", None)
    if isinstance(config_entry_ids, str):
        ids.add(config_entry_ids)
    else:
        try:
            ids.update(str(item) for item in (config_entry_ids or set()) if item)
        except Exception:
            pass
    return ids


def _remove_entity_registry_entries_attached_to_devices(
    hass,
    entry_id: str,
    child_device_ids: set[str] | None,
    *,
    preserve_current_workflow_entries: bool,
) -> None:
    """Remove entity-registry entries attached to removed current-entry child devices."""
    try:
        from homeassistant.helpers import entity_registry as er
    except Exception:
        return
    try:
        entity_registry = er.async_get(hass)
    except Exception:
        return
    device_ids = {str(device_id) for device_id in (child_device_ids or set()) if device_id}
    if not device_ids:
        return
    expected_entry_id = str(entry_id)
    for entity in _entity_registry_entries(entity_registry):
        entity_entry_ids = _entity_registry_entry_config_entry_ids(entity)
        if entity_entry_ids and expected_entry_id not in entity_entry_ids:
            continue
        if preserve_current_workflow_entries and _is_current_fleet_workspace_entity_registry_entry(entity, entry_id):
            continue
        if str(getattr(entity, "device_id", "") or "") in device_ids:
            _remove_entity_registry_entry(entity_registry, entity)


def remove_unmanaged_candidate_entity_registry_entries_for_entry(
    hass,
    entry_id: str,
    child_device_ids: set[str] | None = None,
) -> None:
    """Remove stale entity-registry entries attached to legacy unmanaged peer devices."""
    try:
        from homeassistant.helpers import entity_registry as er
    except Exception:
        return
    try:
        entity_registry = er.async_get(hass)
    except Exception:
        return
    device_ids = {str(device_id) for device_id in (child_device_ids or set()) if device_id}
    expected_entry_id = str(entry_id)
    for entity in _entity_registry_entries(entity_registry):
        entity_entry_ids = _entity_registry_entry_config_entry_ids(entity)
        if entity_entry_ids and expected_entry_id not in entity_entry_ids:
            continue
        if _is_current_fleet_workspace_entity_registry_entry(entity, entry_id):
            continue
        device_id = str(getattr(entity, "device_id", "") or "")
        if device_id in device_ids or (
            not device_id
            and (expected_entry_id in entity_entry_ids or not entity_entry_ids)
            and _is_legacy_unmanaged_candidate_entity_registry_entry(
                entity,
                entry_id,
                require_entry_scoped_unique_id=not entity_entry_ids,
            )
        ):
            _remove_entity_registry_entry(entity_registry, entity)


def remove_stale_managed_child_devices_for_entry(hass, entry_id: str, current_device_infos: object) -> set[str]:
    """Remove managed child-device rows that no longer belong to the current managed fleet."""
    removed_device_ids: set[str] = set()
    current_identifiers: set[tuple[str, str]] = set()
    for device_info in current_device_infos or []:
        identifier = _integration_page_child_device_identifier(device_info)
        if identifier is not None and ":managed-device:" in identifier[1]:
            current_identifiers.add(identifier)
    try:
        from homeassistant.helpers import device_registry as dr
    except Exception:
        return removed_device_ids
    try:
        device_registry = dr.async_get(hass)
    except Exception:
        return removed_device_ids
    remove_device = getattr(device_registry, "async_remove_device", None)
    devices = getattr(device_registry, "devices", None)
    if remove_device is None or devices is None:
        return removed_device_ids
    prefix = f"{entry_id}:managed-device:"
    try:
        device_values = list(devices.values() if isinstance(devices, Mapping) else devices)
    except Exception:
        return removed_device_ids
    for device in device_values:
        managed_identifiers = {
            (domain, value)
            for domain, value in _device_entry_identifiers(device)
            if domain == DOMAIN and value.startswith(prefix)
        }
        if not managed_identifiers or managed_identifiers & current_identifiers:
            continue
        device_id = str(getattr(device, "id", "") or "")
        try:
            remove_device(device.id)
            if device_id:
                removed_device_ids.add(device_id)
        except Exception:
            continue
    _remove_entity_registry_entries_attached_to_devices(
        hass,
        entry_id,
        removed_device_ids,
        preserve_current_workflow_entries=False,
    )
    return removed_device_ids


def remove_unmanaged_candidate_child_devices_for_entry(hass, entry_id: str) -> set[str]:
    """Remove all legacy peer `Un Managed` child-device rows for one config entry."""
    removed_device_ids: set[str] = set()
    try:
        from homeassistant.helpers import device_registry as dr
    except Exception:
        return removed_device_ids
    try:
        device_registry = dr.async_get(hass)
    except Exception:
        return removed_device_ids
    remove_device = getattr(device_registry, "async_remove_device", None)
    devices = getattr(device_registry, "devices", None)
    if remove_device is None or devices is None:
        remove_unmanaged_candidate_entity_registry_entries_for_entry(hass, entry_id, removed_device_ids)
        return removed_device_ids
    prefix = f"{entry_id}:unmanaged-candidate:"
    try:
        device_values = list(devices.values() if isinstance(devices, Mapping) else devices)
    except Exception:
        remove_unmanaged_candidate_entity_registry_entries_for_entry(hass, entry_id, removed_device_ids)
        return removed_device_ids
    for device in device_values:
        if any(domain == DOMAIN and value.startswith(prefix) for domain, value in _device_entry_identifiers(device)):
            device_id = str(getattr(device, "id", "") or "")
            try:
                remove_device(device.id)
                if device_id:
                    removed_device_ids.add(device_id)
            except Exception:
                continue
    remove_unmanaged_candidate_entity_registry_entries_for_entry(hass, entry_id, removed_device_ids)
    return removed_device_ids


def unmanaged_candidate_cleanup_device_info(coordinator, candidate: dict) -> dict:
    """Return current unmanaged peer-row identifiers for cleanup only.

    Riley's current scope suppresses native peer `Un Managed — ...` rows.  Keep only
    enough device-info shape to find and remove stale registry devices; do not expose
    names, models, or configuration URLs that could be reused to recreate those rows.
    """
    entity_id = str(candidate.get("entity_id") or "candidate").strip()
    return {
        "identifiers": {(DOMAIN, f"{coordinator.entry.entry_id}:unmanaged-candidate:{_device_identifier_part(entity_id)}")},
    }


def legacy_unmanaged_candidate_device_info(coordinator, candidate: dict) -> dict | None:
    """Return legacy unmanaged-row identifiers for cleanup when the old identifier differs."""
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
