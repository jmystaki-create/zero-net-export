"""Zero Net Export integration."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import re
from typing import Any

import voluptuous as vol

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_BATTERY_RESERVE_SOC,
    CONF_DEADBAND_W,
    CONF_DEVICE_INVENTORY_JSON,
    CONF_GRID_EXPORT_ENERGY_ENTITY,
    CONF_GRID_EXPORT_POWER_ENTITY,
    CONF_GRID_IMPORT_ENERGY_ENTITY,
    CONF_GRID_IMPORT_POWER_ENTITY,
    CONF_HOME_LOAD_POWER_ENTITY,
    CONF_REFRESH_SECONDS,
    CONF_SOLAR_ENERGY_ENTITY,
    CONF_SOLAR_POWER_ENTITY,
    CONF_TARGET_EXPORT_W,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_DEADBAND_W,
    DEFAULT_DEVICE_INVENTORY_JSON,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_TARGET_EXPORT_W,
    DOMAIN,
    INTEGRATION_VERSION,
    PLATFORMS,
    REQUIRED_SOURCE_KEYS,
    SOURCE_ROLE_LABELS,
)
from .coordinator import ZeroNetExportCoordinator
from .device_model import parse_device_configs
from .entity import sync_primary_controller_device_registry
from .native_support import (
    DEVICES_CONFIGURE_PATH,
    DIAGNOSTICS_DEVICE_ACTIONS_PATH,
    POLICY_CONFIGURE_PATH,
    PRIMARY_CONFIGURE_PATH,
    SOURCES_CONFIGURE_PATH,
    SUPPORT_CONFIGURE_PATH,
    build_native_operator_readiness,
    build_source_attention_role_summary,
    build_source_selector_fallback_hint,
)
from .release_info import async_prime_install_provenance
from .repairs import async_clear_repairs_issues, async_sync_repairs_issues


STALE_GUIDED_FLOW_BUTTON_SUFFIXES = {
    "open_sensors_guided_flow",
    "open_controls_guided_flow",
    "open_managed_devices_guided_flow",
    "open_diagnostics_guided_flow",
}
STALE_MANAGED_LOAD_BUTTON_SUFFIXES = (
    "_edit_configuration",
    "_remove_from_zne",
)


def _setup_notification_id(entry: ConfigEntry) -> str:
    return f"{DOMAIN}_{entry.entry_id}_native_setup"


def _async_remove_stale_guided_flow_button_entities(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove registry rows for retired device-page launcher buttons."""
    entity_registry = er.async_get(hass)
    unique_id_prefix = f"{entry.entry_id}_"
    for entity_id, entity_entry in list(entity_registry.entities.items()):
        if getattr(entity_entry, "platform", None) != DOMAIN:
            continue
        unique_id = str(getattr(entity_entry, "unique_id", "") or "")
        if not unique_id.startswith(unique_id_prefix):
            continue
        suffix = unique_id.removeprefix(unique_id_prefix)
        if suffix in STALE_GUIDED_FLOW_BUTTON_SUFFIXES or (
            suffix.startswith("device_") and suffix.endswith(STALE_MANAGED_LOAD_BUTTON_SUFFIXES)
        ):
            entity_registry.async_remove(entity_id)


def _missing_required_source_mappings(entry: ConfigEntry) -> list[str]:
    merged = dict(entry.data)
    merged.update(entry.options)
    return [key for key in REQUIRED_SOURCE_KEYS if not merged.get(key)]


def _normalize_source_mapping_case_drift(text: str) -> str:
    """Catch title-case source-mapping fallback text before persistent notices render."""
    text = re.sub(
        r"\bOpen Configure and finish (?:required )?(?:source[- ]mappings?|source[- ]roles?)\b",
        f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bOpen Configure to finish (?:required )?(?:source[- ]mappings?|source[- ]roles?)\b",
        f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bOpen(?: the)? Source[- ]Mappings? Step\b",
        f"Open {SOURCES_CONFIGURE_PATH}",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bMissing Required Source Mappings\b",
        lambda match: "Missing required source roles" if match.group(0)[0].isupper() else "missing required source roles",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bRequired Source Mapping\b",
        lambda match: "Required source roles" if match.group(0)[0].isupper() else "required source roles",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bFinish Source Mapping\b",
        lambda match: "Finish source roles" if match.group(0)[0].isupper() else "finish source roles",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\bSource[- ]Mappings? Step\b",
        "Sensors source roles",
        text,
        flags=re.IGNORECASE,
    )
    return re.sub(
        r"\bSource[- ]Mappings?\b",
        lambda match: "Source roles" if match.group(0)[0].isupper() else "source roles",
        text,
        flags=re.IGNORECASE,
    )


def _normalize_native_setup_notice_text(value: Any) -> str:
    """Keep setup notifications on the operator-facing source-role wording."""
    text = str(value or "")
    replacements = {
        "Open Configure and finish required source roles": f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        "Open Configure and finish source mapping": f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        "Open Configure and finish source roles": f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        "Open Configure and finish source role": f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        "Open Configure to finish required source roles": f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        "Open Configure to finish source mapping": f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        "Open Configure to finish source roles": f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        "Open Configure to finish source role": f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        "Open the Source-mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the source-mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open Source-mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open source-mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the Source-mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the source-mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open Source-mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open source-mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the Source mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the source mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open Source mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open source mapping step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the Source mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open the source mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open Source mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open source mappings step": f"Open {SOURCES_CONFIGURE_PATH}",
        "Missing required source mappings": "Missing required source roles",
        "missing required source mappings": "missing required source roles",
        "Missing source mappings": "Missing source roles",
        "missing source mappings": "missing source roles",
        "Finish source mapping": "Finish source roles",
        "finish source mapping": "finish source roles",
        "Required source mapping": "Required source roles",
        "required source mapping": "required source roles",
        "Open Sensors and": f"Open {SOURCES_CONFIGURE_PATH} and",
        "Open Sensors to": f"Open {SOURCES_CONFIGURE_PATH} to",
        "Open Sources and": f"Open {SOURCES_CONFIGURE_PATH} and",
        "Open Sources to": f"Open {SOURCES_CONFIGURE_PATH} to",
        "Open Controls and": f"Open {POLICY_CONFIGURE_PATH} and",
        "Open Controls to": f"Open {POLICY_CONFIGURE_PATH} to",
        "Open Managed Devices and": f"Open {DEVICES_CONFIGURE_PATH} and",
        "Open Managed Devices to": f"Open {DEVICES_CONFIGURE_PATH} to",
        "Open Diagnostics and": f"Open {SUPPORT_CONFIGURE_PATH} and",
        "Open Diagnostics to": f"Open {SUPPORT_CONFIGURE_PATH} to",
        "Mapped-source blockers": "Source blockers",
        "Mapped-source blocker": "Source blocker",
        "mapped-source blockers": "source blockers",
        "mapped-source blocker": "source blocker",
        "Mapped source blockers": "Source blockers",
        "Mapped source blocker": "Source blocker",
        "mapped source blockers": "source blockers",
        "mapped source blocker": "source blocker",
        "Mapped-source roles": "Source roles",
        "Mapped-source role": "Source role",
        "mapped-source roles": "source roles",
        "mapped-source role": "source role",
        "Mapped source roles": "Source roles",
        "Mapped source role": "Source role",
        "mapped source roles": "source roles",
        "mapped source role": "source role",
        "Mapped-role blockers": "Source blockers",
        "Mapped-role blocker": "Source blocker",
        "Mapped role blockers": "Source blockers",
        "Mapped role blocker": "Source blocker",
        "mapped-role blockers": "source blockers",
        "mapped-role blocker": "source blocker",
        "mapped role blockers": "source blockers",
        "mapped role blocker": "source blocker",
        "Mapped-roles": "Source roles",
        "Mapped-role": "Source role",
        "mapped-roles": "source roles",
        "mapped-role": "source role",
        "Mapped roles": "Source roles",
        "Mapped role": "Source role",
        "mapped roles": "source roles",
        "mapped role": "source role",
        "Mapped sources": "Source roles",
        "Mapped source": "Source role",
        "mapped sources": "source roles",
        "mapped source": "source role",
        "Source-mapping step": "Sensors source roles",
        "source-mapping step": "Sensors source roles",
        "Source-mappings step": "Sensors source roles",
        "source-mappings step": "Sensors source roles",
        "Source-mappings": "Source roles",
        "source-mappings": "source roles",
        "Source-mapping": "Source roles",
        "source-mapping": "source roles",
        "Source mapping step": "Sensors source roles",
        "source mapping step": "Sensors source roles",
        "Source mappings": "Source roles",
        "source mappings": "source roles",
        "Source mapping": "Source roles",
        "source mapping": "source roles",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = _normalize_source_mapping_case_drift(text)
    arrow_paths = {
        "Sensors": SOURCES_CONFIGURE_PATH,
        "Controls": POLICY_CONFIGURE_PATH,
        "Managed Devices": DEVICES_CONFIGURE_PATH,
        "Diagnostics": SUPPORT_CONFIGURE_PATH,
    }
    for section_label, section_path in arrow_paths.items():
        escaped_section = re.escape(section_label)
        text = re.sub(
            rf"{re.escape(PRIMARY_CONFIGURE_PATH)}\s*(?:->|→|>)\s*{escaped_section}(?!; device-page diagnostics)",
            section_path,
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            rf"(?<!Integrations -> )Zero Net Export\s*->\s*Configure\s*(?:->|→|>)\s*{escaped_section}(?!; device-page diagnostics)",
            section_path,
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            rf"(?<!Zero Net Export -> )Configure\s*(?:->|→|>)\s*{escaped_section}(?!; device-page diagnostics)",
            section_path,
            text,
            flags=re.IGNORECASE,
        )
    section_paths = {
        "Sensors": SOURCES_CONFIGURE_PATH,
        "Sources": SOURCES_CONFIGURE_PATH,
        "Controls": POLICY_CONFIGURE_PATH,
        "Managed Devices": DEVICES_CONFIGURE_PATH,
        "Diagnostics": SUPPORT_CONFIGURE_PATH,
    }
    for section_label, section_path in section_paths.items():
        text = re.sub(
            rf"\bOpen {re.escape(section_label)}(?!(?:\s+path)\b)(?=(?:\s|[.,;:]|$))",
            f"Open {section_path}",
            text,
            flags=re.IGNORECASE,
        )
    return text


async def _async_update_native_setup_notice(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: ZeroNetExportCoordinator | None = None,
) -> None:
    missing_sources = _missing_required_source_mappings(entry)
    raw_inventory = entry.options.get(
        CONF_DEVICE_INVENTORY_JSON,
        entry.data.get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
    )
    devices, device_issues = parse_device_configs(raw_inventory)
    state = coordinator.data if coordinator is not None else None
    merged = dict(entry.data)
    merged.update(entry.options)
    readiness = build_native_operator_readiness(coordinator) if coordinator is not None else {}
    source_attention_roles = build_source_attention_role_summary(state, merged, limit=4)

    if not missing_sources and devices and not device_issues and source_attention_roles == "None":
        persistent_notification.async_dismiss(hass, _setup_notification_id(entry))
        return

    readable_roles = [SOURCE_ROLE_LABELS.get(key, key) for key in missing_sources]
    fallback_hint = build_source_selector_fallback_hint(role_keys=missing_sources) or "Not needed right now."
    readiness_summary = _normalize_native_setup_notice_text(
        readiness.get("summary") or "Setup incomplete."
    )
    missing_lines = [
        f"• Source roles: {', '.join(readable_roles) if readable_roles else 'None'}",
        f"• Managed devices: {len(devices)}",
    ]
    if device_issues:
        missing_lines.append(f"• Device issues: {'; '.join(device_issues[:3])}")
    elif not devices:
        missing_lines.append("• Device issues: No controllable devices added yet.")
    if source_attention_roles != "None":
        missing_lines.append(f"• Blockers: {source_attention_roles}")

    next_step = _normalize_native_setup_notice_text(
        readiness.get("next_step") or f"Open {PRIMARY_CONFIGURE_PATH} and continue setup."
    )
    if fallback_hint != "Not needed right now.":
        next_step = next_step.replace(f" {fallback_hint}", "").replace(fallback_hint, "").strip()

    message = (
        "Setup incomplete — control is paused until setup is finished.\n\n"
        "Do this first\n"
        + f"• {next_step}"
        + "\n\nMissing\n"
        + "\n".join(missing_lines)
        + "\n\nOpen\n"
        + f"• Sensors: {SOURCES_CONFIGURE_PATH}\n"
        + f"• Managed Devices: {DEVICES_CONFIGURE_PATH}\n"
        + f"• Controls: {POLICY_CONFIGURE_PATH}\n"
        + f"• Diagnostics: {SUPPORT_CONFIGURE_PATH}"
        + "\n\nFallback only if Home Assistant rejects a valid selector choice\n"
        + f"• {fallback_hint}"
    )
    persistent_notification.async_create(
        hass,
        message,
        title=f"{entry.title}: setup incomplete",
        notification_id=_setup_notification_id(entry),
    )


def _managed_device_identifier_part(value: object) -> str:
    """Return the same safe managed-device identifier fragment used by entity.py."""
    original = str(value or "unknown").strip() or "unknown"
    safe = re.sub(r"[^a-zA-Z0-9_]+", "_", original).strip("_").lower() or "unknown"
    if original == safe:
        return safe
    digest = hashlib.sha1(original.encode("utf-8")).hexdigest()[:8]
    return f"{safe}_{digest}"


def _coerce_number(value: Any, fallback: int | float) -> int | float:
    if value in (None, ""):
        return fallback
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    if isinstance(fallback, int) and not isinstance(fallback, bool):
        return int(parsed)
    return parsed


UPDATE_MANAGED_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): str,
        vol.Required("device_key"): str,
        vol.Optional("name"): str,
        vol.Optional("entity_id"): str,
        vol.Optional("enabled"): bool,
        vol.Optional("priority"): int,
        vol.Optional("nominal_power_w"): float,
        vol.Optional("min_power_w"): float,
        vol.Optional("max_power_w"): float,
        vol.Optional("step_w"): float,
        vol.Optional("min_on_seconds"): int,
        vol.Optional("min_off_seconds"): int,
        vol.Optional("cooldown_seconds"): int,
        vol.Optional("max_active_seconds"): int,
    }
)


REMOVE_MANAGED_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): str,
        vol.Required("device_key"): str,
        vol.Required("confirm"): bool,
    }
)


def _device_config_to_payload(device) -> dict[str, Any]:
    payload = asdict(device)
    if payload.get("max_active_seconds") is None:
        payload["max_active_seconds"] = 0
    return payload


def _managed_device_entry_and_payloads(hass: HomeAssistant, call: Any) -> tuple[ConfigEntry, str, list[dict[str, Any]]]:
    """Return the selected ZNE entry, requested managed-device key, and inventory payloads."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise ValueError("Zero Net Export has no configured entries")
    requested_entry_id = str(call.data.get("entry_id") or "")
    entry = next((candidate for candidate in entries if candidate.entry_id == requested_entry_id), None) if requested_entry_id else entries[0]
    if entry is None:
        raise ValueError(f"Zero Net Export entry '{requested_entry_id}' was not found")
    device_key = str(call.data["device_key"])
    raw_inventory = entry.options.get(
        CONF_DEVICE_INVENTORY_JSON,
        entry.data.get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
    )
    devices, issues = parse_device_configs(raw_inventory)
    if issues:
        raise ValueError("Managed-device inventory is invalid: " + "; ".join(issues[:3]))
    return entry, device_key, [_device_config_to_payload(device) for device in devices]


async def _async_update_managed_device_from_panel(hass: HomeAssistant, call: Any) -> None:
    """Update a managed device from a native Home Assistant action/service."""
    entry, device_key, payloads = _managed_device_entry_and_payloads(hass, call)
    target = next((payload for payload in payloads if payload.get("key") == device_key), None)
    if target is None:
        raise ValueError(f"Managed device '{device_key}' was not found")

    editable_fields = {
        "name",
        "entity_id",
        "enabled",
        "priority",
        "nominal_power_w",
        "min_power_w",
        "max_power_w",
        "step_w",
        "min_on_seconds",
        "min_off_seconds",
        "cooldown_seconds",
        "max_active_seconds",
    }
    for field in editable_fields:
        if field in call.data:
            target[field] = call.data[field]
    if target.get("max_active_seconds") == 0:
        target["max_active_seconds"] = None

    _validated_devices, validation_issues = parse_device_configs(json.dumps(payloads))
    if validation_issues:
        raise ValueError("Managed-device settings are invalid: " + "; ".join(validation_issues[:3]))

    merged_options = dict(entry.options)
    merged_options[CONF_DEVICE_INVENTORY_JSON] = json.dumps(payloads, indent=2, sort_keys=True)
    hass.config_entries.async_update_entry(entry, options=merged_options)
    await hass.config_entries.async_reload(entry.entry_id)
    persistent_notification.async_create(
        hass,
        f"Updated managed-device settings for {target.get('name') or device_key}. Original Home Assistant devices and entities were not modified.",
        title=f"{entry.title}: managed device settings saved",
        notification_id=f"{DOMAIN}_{entry.entry_id}_managed_device_panel_update",
    )


async def _async_remove_managed_device_payload(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device_key: str,
    payloads: list[dict[str, Any]],
) -> bool:
    """Remove one managed device from one ZNE entry only."""
    removed = next((payload for payload in payloads if payload.get("key") == device_key), None)
    if removed is None:
        return False
    remaining = [payload for payload in payloads if payload.get("key") != device_key]
    _validated_devices, validation_issues = parse_device_configs(json.dumps(remaining))
    if validation_issues:
        raise ValueError("Managed-device settings are invalid after removal: " + "; ".join(validation_issues[:3]))

    merged_options = dict(entry.options)
    merged_options[CONF_DEVICE_INVENTORY_JSON] = json.dumps(remaining, indent=2, sort_keys=True)
    hass.config_entries.async_update_entry(entry, options=merged_options)
    await hass.config_entries.async_reload(entry.entry_id)
    persistent_notification.async_create(
        hass,
        (
            f"Removed {removed.get('name') or device_key} from Zero Net Export management. "
            "This only removed the ZNE managed-load record and its ZNE child-device rows; the original Home Assistant device/entity was left untouched."
        ),
        title=f"{entry.title}: managed device removed",
        notification_id=f"{DOMAIN}_{entry.entry_id}_managed_device_removed",
    )
    return True


async def _async_remove_managed_device(hass: HomeAssistant, call: Any) -> None:
    """Remove one managed device from ZNE configuration only."""
    if call.data.get("confirm") is not True:
        raise ValueError("Set confirm=true to remove a managed device from Zero Net Export")
    entry, device_key, payloads = _managed_device_entry_and_payloads(hass, call)
    if not await _async_remove_managed_device_payload(hass, entry, device_key, payloads):
        raise ValueError(f"Managed device '{device_key}' was not found")


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    device_entry: Any,
) -> bool:
    """Support Home Assistant's native integration-row Delete device action.

    HA exposes `supports_remove_device` from this backend hook and calls it
    only after its own native confirmation.  Remove the selected ZNE
    managed-load record from this config entry and leave the original/source
    Home Assistant device and entity untouched.
    """
    identifiers = getattr(device_entry, "identifiers", set()) or set()
    managed_identifier_prefix = f"{config_entry.entry_id}:managed-device:"
    raw_inventory = config_entry.options.get(
        CONF_DEVICE_INVENTORY_JSON,
        config_entry.data.get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
    )
    devices, issues = parse_device_configs(raw_inventory)
    if issues:
        raise ValueError("Managed-device inventory is invalid: " + "; ".join(issues[:3]))
    payloads = [_device_config_to_payload(device) for device in devices]
    device_key_by_identifier = {
        f"{config_entry.entry_id}:managed-device:{_managed_device_identifier_part(payload.get('key'))}": str(payload.get("key"))
        for payload in payloads
        if payload.get("key")
    }

    for domain, identifier in identifiers:
        if domain != DOMAIN:
            continue
        identifier = str(identifier)
        if not identifier.startswith(managed_identifier_prefix):
            continue
        device_key = device_key_by_identifier.get(identifier)
        if device_key is None:
            return False
        return await _async_remove_managed_device_payload(hass, config_entry, device_key, payloads)
    return False


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, "update_managed_device"):
        return

    async def _handle_update_managed_device(call: Any) -> None:
        await _async_update_managed_device_from_panel(hass, call)

    async def _handle_remove_managed_device(call: Any) -> None:
        await _async_remove_managed_device(hass, call)

    hass.services.async_register(
        DOMAIN,
        "update_managed_device",
        _handle_update_managed_device,
        schema=UPDATE_MANAGED_DEVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        "remove_managed_device",
        _handle_remove_managed_device,
        schema=REMOVE_MANAGED_DEVICE_SCHEMA,
    )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration domain."""
    hass.data.setdefault(DOMAIN, {})
    _register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    sync_primary_controller_device_registry(hass, entry)
    _async_remove_stale_guided_flow_button_entities(hass, entry)
    await _async_update_native_setup_notice(hass, entry)
    await async_prime_install_provenance(hass, force_refresh=True)

    coordinator = ZeroNetExportCoordinator(hass, entry)
    await coordinator.async_initialize()
    await coordinator.async_note_current_integration_version(INTEGRATION_VERSION)
    await coordinator.async_config_entry_first_refresh()
    await _async_update_native_setup_notice(hass, entry, coordinator)
    async_sync_repairs_issues(hass, entry, coordinator)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    sync_primary_controller_device_registry(hass, entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        persistent_notification.async_dismiss(hass, _setup_notification_id(entry))
        async_clear_repairs_issues(hass, entry)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Normalize legacy entry data so upgraded installs do not crash newer flows."""
    data = dict(entry.data)
    changed = False

    normalized_defaults: dict[str, Any] = {
        CONF_TARGET_EXPORT_W: _coerce_number(data.get(CONF_TARGET_EXPORT_W), DEFAULT_TARGET_EXPORT_W),
        CONF_DEADBAND_W: _coerce_number(data.get(CONF_DEADBAND_W), DEFAULT_DEADBAND_W),
        CONF_BATTERY_RESERVE_SOC: _coerce_number(data.get(CONF_BATTERY_RESERVE_SOC), DEFAULT_BATTERY_RESERVE_SOC),
        CONF_REFRESH_SECONDS: _coerce_number(data.get(CONF_REFRESH_SECONDS), DEFAULT_REFRESH_SECONDS),
        CONF_DEVICE_INVENTORY_JSON: data.get(CONF_DEVICE_INVENTORY_JSON),
    }
    if normalized_defaults[CONF_DEVICE_INVENTORY_JSON] in (None, ""):
        normalized_defaults[CONF_DEVICE_INVENTORY_JSON] = DEFAULT_DEVICE_INVENTORY_JSON
    elif not isinstance(normalized_defaults[CONF_DEVICE_INVENTORY_JSON], str):
        normalized_defaults[CONF_DEVICE_INVENTORY_JSON] = str(normalized_defaults[CONF_DEVICE_INVENTORY_JSON])

    for key, normalized in normalized_defaults.items():
        if data.get(key) != normalized:
            data[key] = normalized
            changed = True

    if changed:
        hass.config_entries.async_update_entry(entry, data=data)

    _async_remove_stale_guided_flow_button_entities(hass, entry)
    await _async_update_native_setup_notice(hass, entry)
    await async_prime_install_provenance(hass, force_refresh=True)
    async_sync_repairs_issues(hass, entry)

    return True
