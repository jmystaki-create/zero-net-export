"""Zero Net Export integration."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_BATTERY_RESERVE_SOC,
    CONF_DEADBAND_W,
    CONF_DEVICE_INVENTORY_JSON,
    CONF_REFRESH_SECONDS,
    CONF_TARGET_EXPORT_W,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_DEADBAND_W,
    DEFAULT_DEVICE_INVENTORY_JSON,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_TARGET_EXPORT_W,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import ZeroNetExportCoordinator
from .panel import async_setup_panel


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

    coordinator = ZeroNetExportCoordinator(hass, entry)
    await coordinator.async_initialize()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
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

    return True
