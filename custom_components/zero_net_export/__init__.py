"""Zero Net Export integration."""
from __future__ import annotations

import re
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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


def _setup_notification_id(entry: ConfigEntry) -> str:
    return f"{DOMAIN}_{entry.entry_id}_native_setup"


def _missing_required_source_mappings(entry: ConfigEntry) -> list[str]:
    merged = dict(entry.data)
    merged.update(entry.options)
    return [key for key in REQUIRED_SOURCE_KEYS if not merged.get(key)]


def _normalize_native_setup_notice_text(value: Any) -> str:
    """Keep setup notifications on the operator-facing source-role wording."""
    text = str(value or "")
    replacements = {
        "Open Configure and finish required source roles": f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        "Open Configure and finish source mapping": f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        "Open Configure and finish source roles": f"Open {SOURCES_CONFIGURE_PATH} and finish required source roles",
        "Open Configure to finish required source roles": f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        "Open Configure to finish source mapping": f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        "Open Configure to finish source roles": f"Open {SOURCES_CONFIGURE_PATH} to finish required source roles",
        "missing source mappings": "missing source roles",
        "missing required source mappings": "missing required source roles",
        "finish source mapping": "finish source roles",
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
        "Open Configure > Sensors": f"Open {SOURCES_CONFIGURE_PATH}",
        "Open Configure > Controls": f"Open {POLICY_CONFIGURE_PATH}",
        "Open Configure > Managed Devices": f"Open {DEVICES_CONFIGURE_PATH}",
        "Open Configure > Diagnostics": f"Open {SUPPORT_CONFIGURE_PATH}",
        "mapped-role blockers": "source-role blockers",
        "mapped role blockers": "source role blockers",
        "mapped roles": "source roles",
        "mapped sources": "source roles",
        "source mapping step": "Sensors source roles step",
        "source mappings": "source roles",
        "source mapping": "source roles",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    section_paths = {
        "Sensors": SOURCES_CONFIGURE_PATH,
        "Sources": SOURCES_CONFIGURE_PATH,
        "Controls": POLICY_CONFIGURE_PATH,
        "Managed Devices": DEVICES_CONFIGURE_PATH,
        "Diagnostics": SUPPORT_CONFIGURE_PATH,
    }
    for section_label, section_path in section_paths.items():
        text = re.sub(
            rf"\bOpen {re.escape(section_label)}(?=(?:\s|[.,;:]|$))",
            f"Open {section_path}",
            text,
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
        readiness.get("summary") or "Zero Net Export still needs a few native setup steps."
    )
    status_lines = [
        f"• Summary: {readiness_summary}",
        f"• Missing required source roles: {', '.join(readable_roles) if readable_roles else 'None'}",
        f"• Managed Devices: {len(devices)}",
    ]
    if device_issues:
        status_lines.append(f"• Managed-device issues: {'; '.join(device_issues[:3])}")
    elif not devices:
        status_lines.append("• Managed-device issues: No controllable devices have been added yet.")
    if source_attention_roles != "None":
        status_lines.append(f"• Active blockers: {source_attention_roles}")

    next_step = _normalize_native_setup_notice_text(
        readiness.get("next_step") or f"Open {PRIMARY_CONFIGURE_PATH} and continue setup."
    )

    message = (
        "Zero Net Export still needs a few native setup steps.\n\n"
        "Status\n"
        + "\n".join(status_lines)
        + "\n\nDo next\n"
        + f"• {next_step}"
        + "\n\nFallback, only if Home Assistant rejects a valid choice\n"
        + f"• {fallback_hint}"
        + "\n\nOpen\n"
        + f"• Command center: {PRIMARY_CONFIGURE_PATH}\n"
        + f"• Sensors: {SOURCES_CONFIGURE_PATH}\n"
        + f"• Managed Devices: {DEVICES_CONFIGURE_PATH}\n"
        + f"• Diagnostics: {SUPPORT_CONFIGURE_PATH}\n"
        + f"• Device-page diagnostics actions: {DIAGNOSTICS_DEVICE_ACTIONS_PATH}"
    )
    persistent_notification.async_create(
        hass,
        message,
        title=f"{entry.title}: finish native Zero Net Export setup",
        notification_id=_setup_notification_id(entry),
    )


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


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration domain."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
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

    await _async_update_native_setup_notice(hass, entry)
    await async_prime_install_provenance(hass, force_refresh=True)
    async_sync_repairs_issues(hass, entry)

    return True
