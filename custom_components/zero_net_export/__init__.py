"""Zero Net Export integration."""
from __future__ import annotations

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
from .native_support import INTEGRATION_DEVICE_PATH, PRIMARY_CONFIGURE_PATH
from .native_support import build_native_operator_readiness, build_source_attention_role_summary
from .repairs import async_clear_repairs_issues, async_sync_repairs_issues


def _setup_notification_id(entry: ConfigEntry) -> str:
    return f"{DOMAIN}_{entry.entry_id}_native_setup"


def _missing_required_source_mappings(entry: ConfigEntry) -> list[str]:
    merged = dict(entry.data)
    merged.update(entry.options)
    return [key for key in REQUIRED_SOURCE_KEYS if not merged.get(key)]


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

    bullets: list[str] = []
    if missing_sources:
        readable_roles = [SOURCE_ROLE_LABELS.get(key, key) for key in missing_sources]
        bullets.append("Missing required source mappings: " + ", ".join(readable_roles))
    if device_issues:
        bullets.append(
            "Managed-device configuration issues in Configure: "
            + "; ".join(device_issues[:3])
            + ". Use the advanced JSON recovery editor only if the native forms cannot repair it."
        )
    elif not devices:
        bullets.append("No controllable devices have been added yet.")
    if source_attention_roles != "None":
        bullets.append("Mapped source blockers right now: " + source_attention_roles)

    next_step = str(readiness.get("next_step") or f"Open {PRIMARY_CONFIGURE_PATH} and continue setup.")

    message = (
        f"Finish setup from Home Assistant's native integration surfaces. Open {PRIMARY_CONFIGURE_PATH} as the Zero Net Export command center for Sensors, Managed Devices, Controls, and Diagnostics.\n\n"
        + "\n".join(f"- {item}" for item in bullets)
        + f"\n\nNext step: {next_step}"
        + f"\n\nUse {INTEGRATION_DEVICE_PATH} support actions for a combined support center, setup checklist, and detailed diagnostics snapshot."
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
    async_sync_repairs_issues(hass, entry)

    return True
