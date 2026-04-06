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
)
from .coordinator import ZeroNetExportCoordinator
from .device_model import parse_device_configs
from .panel import async_setup_panel


def _panel_notification_id(entry: ConfigEntry) -> str:
    return f"{DOMAIN}_{entry.entry_id}_panel_onboarding"


def _missing_required_source_mappings(entry: ConfigEntry) -> list[str]:
    merged = dict(entry.data)
    merged.update(entry.options)
    required_keys = (
        CONF_SOLAR_POWER_ENTITY,
        CONF_SOLAR_ENERGY_ENTITY,
        CONF_GRID_IMPORT_POWER_ENTITY,
        CONF_GRID_EXPORT_POWER_ENTITY,
        CONF_GRID_IMPORT_ENERGY_ENTITY,
        CONF_GRID_EXPORT_ENERGY_ENTITY,
        CONF_HOME_LOAD_POWER_ENTITY,
    )
    return [key for key in required_keys if not merged.get(key)]


async def _async_update_panel_onboarding_notice(hass: HomeAssistant, entry: ConfigEntry) -> None:
    missing_sources = _missing_required_source_mappings(entry)
    raw_inventory = entry.options.get(
        CONF_DEVICE_INVENTORY_JSON,
        entry.data.get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
    )
    devices, device_issues = parse_device_configs(raw_inventory)

    if not missing_sources and devices and not device_issues:
        persistent_notification.async_dismiss(hass, _panel_notification_id(entry))
        return

    bullets: list[str] = []
    if missing_sources:
        bullets.append("Missing required source mappings: " + ", ".join(missing_sources))
    if device_issues:
        bullets.append("Device inventory validation issues: " + "; ".join(device_issues[:3]))
    elif not devices:
        bullets.append("No controllable devices have been added yet.")

    message = (
        "Finish setup in the Zero Net Export panel: [Open panel](/zero-net-export).\n\n"
        "Use the panel for source mapping, device onboarding, readiness checks, and the installed -> mapped -> operational workflow.\n\n"
        + "\n".join(f"- {item}" for item in bullets)
        + "\n\nThe raw Configure/options path is advanced recovery only."
    )
    persistent_notification.async_create(
        hass,
        message,
        title=f"{entry.title}: finish setup in Zero Net Export panel",
        notification_id=_panel_notification_id(entry),
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
    """Set up the integration domain and panel shell."""
    hass.data.setdefault(DOMAIN, {})
    await async_setup_panel(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await async_setup_panel(hass)
    await _async_update_panel_onboarding_notice(hass, entry)

    coordinator = ZeroNetExportCoordinator(hass, entry)
    await coordinator.async_initialize()
    await coordinator.async_note_current_integration_version(INTEGRATION_VERSION)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        persistent_notification.async_dismiss(hass, _panel_notification_id(entry))
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

    await _async_update_panel_onboarding_notice(hass, entry)

    return True
