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
from .native_support import PRIMARY_CONFIGURE_PATH, build_native_operator_readiness
from .release_info import (
    build_install_consistency_summary,
    build_install_provenance,
    build_release_info,
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

    safe_validation_details = (data.validation_details or {}) if data is not None else {}
    validation_details = async_redact_data(deepcopy(safe_validation_details), REDACT_NESTED_KEYS)

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

    release_info = build_release_info(INTEGRATION_VERSION, include_changelog=False)
    install_provenance = build_install_provenance()
    release_update = deepcopy(safe_validation_details.get("release_update") or {})
    operator_readiness = deepcopy(build_native_operator_readiness(coordinator))

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "domain": entry.domain,
            "config_entry_version": entry.version,
            "integration_version": INTEGRATION_VERSION,
            "release_summary": release_info.get("summary"),
            "install_provenance_summary": install_provenance.get("summary"),
            "install_consistency_summary": build_install_consistency_summary(install_provenance),
            "live_validation_safe": install_provenance.get("live_validation_safe"),
            "release_update_summary": release_update.get("summary"),
        },
        "config": async_redact_data(dict(entry.data), REDACT_CONFIG_KEYS),
        "options": async_redact_data(dict(entry.options), REDACT_CONFIG_KEYS),
        "refresh_seconds": entry.options.get(CONF_REFRESH_SECONDS, entry.data.get(CONF_REFRESH_SECONDS)),
        "target_export_w": entry.options.get(CONF_TARGET_EXPORT_W, entry.data.get(CONF_TARGET_EXPORT_W)),
        "deadband_w": entry.options.get(CONF_DEADBAND_W, entry.data.get(CONF_DEADBAND_W)),
        "controller": {
            "mode": data.mode if data is not None else None,
            "enabled": data.enabled if data is not None else None,
            "active": data.active if data is not None else None,
            "safe_mode": data.safe_mode if data is not None else None,
            "status": data.status if data is not None else None,
            "reason": data.reason if data is not None else None,
            "recommendation": data.recommendation if data is not None else None,
            "confidence": data.confidence if data is not None else None,
            "health_status": data.health_status if data is not None else None,
            "health_summary": data.health_summary if data is not None else None,
            "stale_data": data.stale_data if data is not None else None,
            "command_failure": data.command_failure if data is not None else None,
            "source_mismatch": data.source_mismatch if data is not None else None,
            "target_export_w": data.target_export_w if data is not None else None,
            "deadband_w": data.deadband_w if data is not None else None,
            "export_error_w": data.export_error_w if data is not None else None,
            "planned_action_count": data.planned_action_count if data is not None else None,
            "executable_action_count": data.executable_action_count if data is not None else None,
            "blocked_planned_action_count": data.blocked_planned_action_count if data is not None else None,
            "planned_power_delta_w": data.planned_power_delta_w if data is not None else None,
            "control_status": data.control_status if data is not None else None,
            "control_summary": data.control_summary if data is not None else None,
            "control_reason": data.control_reason if data is not None else None,
            "control_guard_summary": data.control_guard_summary if data is not None else None,
        },
        "telemetry": {
            "actions_today": data.actions_today if data is not None else None,
            "successful_actions_today": data.successful_actions_today if data is not None else None,
            "failed_actions_today": data.failed_actions_today if data is not None else None,
            "energy_redirected_today_kwh": data.energy_redirected_today_kwh if data is not None else None,
            "active_controlled_power_w": data.active_controlled_power_w if data is not None else None,
            "successful_action_count": data.successful_action_count if data is not None else None,
            "failed_action_count": data.failed_action_count if data is not None else None,
            "total_successful_action_count": data.total_successful_action_count if data is not None else None,
            "total_failed_action_count": data.total_failed_action_count if data is not None else None,
            "action_history_count": data.action_history_count if data is not None else None,
        },
        "sources": {
            "solar_power_w": data.solar_power_w if data is not None else None,
            "solar_energy_kwh": data.solar_energy_kwh if data is not None else None,
            "grid_import_power_w": data.grid_import_power_w if data is not None else None,
            "grid_export_power_w": data.grid_export_power_w if data is not None else None,
            "grid_import_energy_kwh": data.grid_import_energy_kwh if data is not None else None,
            "grid_export_energy_kwh": data.grid_export_energy_kwh if data is not None else None,
            "home_load_power_w": data.home_load_power_w if data is not None else None,
            "battery_soc": data.battery_soc if data is not None else None,
            "battery_charge_power_w": data.battery_charge_power_w if data is not None else None,
            "battery_discharge_power_w": data.battery_discharge_power_w if data is not None else None,
            "surplus_w": data.surplus_w if data is not None else None,
            "last_reconciliation_error_w": data.last_reconciliation_error_w if data is not None else None,
            "stale_source_count": data.stale_source_count if data is not None else None,
            "stale_source_summary": data.stale_source_summary if data is not None else None,
        },
        "devices": {
            "device_count": data.device_count if data is not None else None,
            "enabled_device_count": data.enabled_device_count if data is not None else None,
            "usable_device_count": data.usable_device_count if data is not None else None,
            "fixed_device_count": data.fixed_device_count if data is not None else None,
            "variable_device_count": data.variable_device_count if data is not None else None,
            "controllable_nominal_power_w": data.controllable_nominal_power_w if data is not None else None,
            "usable_nominal_power_w": data.usable_nominal_power_w if data is not None else None,
            "device_status_summary": data.device_status_summary if data is not None else None,
            "details": device_details,
        },
        "native_surfaces": {
            "configure_path": PRIMARY_CONFIGURE_PATH,
            "device_page_buttons": [
                "Show command center guide",
                "Show support center",
                "Show native diagnostics snapshot",
                "Show setup checklist",
                "Show fleet console",
            ],
            "operator_readiness": operator_readiness,
        },
        "validation_details": validation_details,
        "release_info": release_info,
        "install_provenance": install_provenance,
        "release_update": release_update,
    }
