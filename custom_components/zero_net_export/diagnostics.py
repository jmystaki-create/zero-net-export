"""Diagnostics support for Zero Net Export."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from .const import (
    CONF_BATTERY_CHARGE_POWER_ENTITY,
    CONF_BATTERY_DISCHARGE_POWER_ENTITY,
    CONF_BATTERY_SOC_ENTITY,
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
    DOMAIN,
    INTEGRATION_VERSION,
)

REDACT_CONFIG_KEYS = {
    CONF_NAME,
    CONF_SOLAR_POWER_ENTITY,
    CONF_SOLAR_ENERGY_ENTITY,
    CONF_GRID_IMPORT_POWER_ENTITY,
    CONF_GRID_EXPORT_POWER_ENTITY,
    CONF_GRID_IMPORT_ENERGY_ENTITY,
    CONF_GRID_EXPORT_ENERGY_ENTITY,
    CONF_HOME_LOAD_POWER_ENTITY,
    CONF_BATTERY_SOC_ENTITY,
    CONF_BATTERY_CHARGE_POWER_ENTITY,
    CONF_BATTERY_DISCHARGE_POWER_ENTITY,
    CONF_DEVICE_INVENTORY_JSON,
}

REDACT_NESTED_KEYS = {
    "entity_id",
    "name",
    "device_key",
    "last_action_device",
    "last_failed_action_device",
}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data

    validation_details = async_redact_data(deepcopy(data.validation_details), REDACT_NESTED_KEYS)

    device_details = []
    for index, detail in enumerate((data.device_details or {}).values(), start=1):
        redacted_detail = async_redact_data(deepcopy(detail), REDACT_NESTED_KEYS)
        redacted_detail["runtime_slot"] = index
        device_details.append(redacted_detail)

    action_history = []
    for item in validation_details.get("action_history", []):
        action_history.append(
            async_redact_data(
                item,
                {"entity_id", "name", "device_key"},
            )
        )
    validation_details["action_history"] = action_history

    source_diagnostics = {}
    for key, detail in (validation_details.get("source_diagnostics") or {}).items():
        source_diagnostics[key] = async_redact_data(detail, {"entity_id"})
    validation_details["source_diagnostics"] = source_diagnostics

    source_freshness = {}
    for key, detail in (validation_details.get("source_freshness") or {}).items():
        source_freshness[key] = async_redact_data(detail, {"entity_id"})
    validation_details["source_freshness"] = source_freshness

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "domain": entry.domain,
            "config_entry_version": entry.version,
            "integration_version": INTEGRATION_VERSION,
        },
        "config": async_redact_data(dict(entry.data), REDACT_CONFIG_KEYS),
        "options": async_redact_data(dict(entry.options), REDACT_CONFIG_KEYS),
        "refresh_seconds": entry.options.get(CONF_REFRESH_SECONDS, entry.data.get(CONF_REFRESH_SECONDS)),
        "target_export_w": entry.options.get(CONF_TARGET_EXPORT_W, entry.data.get(CONF_TARGET_EXPORT_W)),
        "deadband_w": entry.options.get(CONF_DEADBAND_W, entry.data.get(CONF_DEADBAND_W)),
        "controller": {
            "mode": data.mode,
            "enabled": data.enabled,
            "active": data.active,
            "safe_mode": data.safe_mode,
            "status": data.status,
            "reason": data.reason,
            "recommendation": data.recommendation,
            "confidence": data.confidence,
            "health_status": data.health_status,
            "health_summary": data.health_summary,
            "stale_data": data.stale_data,
            "command_failure": data.command_failure,
            "source_mismatch": data.source_mismatch,
            "target_export_w": data.target_export_w,
            "deadband_w": data.deadband_w,
            "export_error_w": data.export_error_w,
            "planned_action_count": data.planned_action_count,
            "executable_action_count": data.executable_action_count,
            "blocked_planned_action_count": data.blocked_planned_action_count,
            "planned_power_delta_w": data.planned_power_delta_w,
            "control_status": data.control_status,
            "control_summary": data.control_summary,
            "control_reason": data.control_reason,
            "control_guard_summary": data.control_guard_summary,
        },
        "telemetry": {
            "actions_today": data.actions_today,
            "successful_actions_today": data.successful_actions_today,
            "failed_actions_today": data.failed_actions_today,
            "energy_redirected_today_kwh": data.energy_redirected_today_kwh,
            "active_controlled_power_w": data.active_controlled_power_w,
            "successful_action_count": data.successful_action_count,
            "failed_action_count": data.failed_action_count,
            "total_successful_action_count": data.total_successful_action_count,
            "total_failed_action_count": data.total_failed_action_count,
            "action_history_count": data.action_history_count,
        },
        "sources": {
            "solar_power_w": data.solar_power_w,
            "solar_energy_kwh": data.solar_energy_kwh,
            "grid_import_power_w": data.grid_import_power_w,
            "grid_export_power_w": data.grid_export_power_w,
            "grid_import_energy_kwh": data.grid_import_energy_kwh,
            "grid_export_energy_kwh": data.grid_export_energy_kwh,
            "home_load_power_w": data.home_load_power_w,
            "battery_soc": data.battery_soc,
            "battery_charge_power_w": data.battery_charge_power_w,
            "battery_discharge_power_w": data.battery_discharge_power_w,
            "surplus_w": data.surplus_w,
            "last_reconciliation_error_w": data.last_reconciliation_error_w,
            "stale_source_count": data.stale_source_count,
            "stale_source_summary": data.stale_source_summary,
        },
        "devices": {
            "device_count": data.device_count,
            "enabled_device_count": data.enabled_device_count,
            "usable_device_count": data.usable_device_count,
            "fixed_device_count": data.fixed_device_count,
            "variable_device_count": data.variable_device_count,
            "controllable_nominal_power_w": data.controllable_nominal_power_w,
            "usable_nominal_power_w": data.usable_nominal_power_w,
            "device_status_summary": data.device_status_summary,
            "details": device_details,
        },
        "validation_details": validation_details,
    }
