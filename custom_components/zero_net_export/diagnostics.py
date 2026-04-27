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
from .entity import managed_load_details_mapping, validation_details_mapping
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


def _runtime_attr(data: Any | None, name: str) -> Any:
    """Return a runtime attribute when present, otherwise None."""
    return getattr(data, name, None) if data is not None else None


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data

    safe_validation_details = validation_details_mapping(getattr(data, "validation_details", {}) if data is not None else {})
    validation_details = async_redact_data(deepcopy(safe_validation_details), REDACT_NESTED_KEYS)

    device_details = []
    for index, detail in enumerate(managed_load_details_mapping(getattr(data, "device_details", {}) or {}).values(), start=1):
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
            "mode": _runtime_attr(data, "mode"),
            "enabled": _runtime_attr(data, "enabled"),
            "active": _runtime_attr(data, "active"),
            "safe_mode": _runtime_attr(data, "safe_mode"),
            "status": _runtime_attr(data, "status"),
            "reason": _runtime_attr(data, "reason"),
            "current_native_next_action": _runtime_attr(data, "recommendation"),
            "confidence": _runtime_attr(data, "confidence"),
            "health_status": _runtime_attr(data, "health_status"),
            "health_summary": _runtime_attr(data, "health_summary"),
            "stale_data": _runtime_attr(data, "stale_data"),
            "command_failure": _runtime_attr(data, "command_failure"),
            "source_mismatch": _runtime_attr(data, "source_mismatch"),
            "target_export_w": _runtime_attr(data, "target_export_w"),
            "deadband_w": _runtime_attr(data, "deadband_w"),
            "export_error_w": _runtime_attr(data, "export_error_w"),
            "planned_action_count": _runtime_attr(data, "planned_action_count"),
            "executable_action_count": _runtime_attr(data, "executable_action_count"),
            "blocked_planned_action_count": _runtime_attr(data, "blocked_planned_action_count"),
            "planned_power_delta_w": _runtime_attr(data, "planned_power_delta_w"),
            "control_status": _runtime_attr(data, "control_status"),
            "control_summary": _runtime_attr(data, "control_summary"),
            "control_reason": _runtime_attr(data, "control_reason"),
            "control_guard_summary": _runtime_attr(data, "control_guard_summary"),
        },
        "telemetry": {
            "actions_today": _runtime_attr(data, "actions_today"),
            "successful_actions_today": _runtime_attr(data, "successful_actions_today"),
            "failed_actions_today": _runtime_attr(data, "failed_actions_today"),
            "energy_redirected_today_kwh": _runtime_attr(data, "energy_redirected_today_kwh"),
            "active_controlled_power_w": _runtime_attr(data, "active_controlled_power_w"),
            "successful_action_count": _runtime_attr(data, "successful_action_count"),
            "failed_action_count": _runtime_attr(data, "failed_action_count"),
            "total_successful_action_count": _runtime_attr(data, "total_successful_action_count"),
            "total_failed_action_count": _runtime_attr(data, "total_failed_action_count"),
            "action_history_count": _runtime_attr(data, "action_history_count"),
        },
        "sources": {
            "solar_power_w": _runtime_attr(data, "solar_power_w"),
            "solar_energy_kwh": _runtime_attr(data, "solar_energy_kwh"),
            "grid_import_power_w": _runtime_attr(data, "grid_import_power_w"),
            "grid_export_power_w": _runtime_attr(data, "grid_export_power_w"),
            "grid_import_energy_kwh": _runtime_attr(data, "grid_import_energy_kwh"),
            "grid_export_energy_kwh": _runtime_attr(data, "grid_export_energy_kwh"),
            "home_load_power_w": _runtime_attr(data, "home_load_power_w"),
            "battery_soc": _runtime_attr(data, "battery_soc"),
            "battery_charge_power_w": _runtime_attr(data, "battery_charge_power_w"),
            "battery_discharge_power_w": _runtime_attr(data, "battery_discharge_power_w"),
            "surplus_w": _runtime_attr(data, "surplus_w"),
            "last_reconciliation_error_w": _runtime_attr(data, "last_reconciliation_error_w"),
            "stale_source_count": _runtime_attr(data, "stale_source_count"),
            "stale_source_summary": _runtime_attr(data, "stale_source_summary"),
        },
        "devices": {
            "device_count": _runtime_attr(data, "device_count"),
            "enabled_device_count": _runtime_attr(data, "enabled_device_count"),
            "usable_device_count": _runtime_attr(data, "usable_device_count"),
            "fixed_device_count": _runtime_attr(data, "fixed_device_count"),
            "variable_device_count": _runtime_attr(data, "variable_device_count"),
            "controllable_nominal_power_w": _runtime_attr(data, "controllable_nominal_power_w"),
            "usable_nominal_power_w": _runtime_attr(data, "usable_nominal_power_w"),
            "device_status_summary": _runtime_attr(data, "device_status_summary"),
            "details": device_details,
        },
        "native_surfaces": {
            "configure_path": PRIMARY_CONFIGURE_PATH,
            "device_page_buttons": [
                "Show command center guide",
                "Open Managed Devices workspace",
                "Open Managed Devices review",
                "Per-device Managed Devices review buttons",
                "Review diagnostics",
                "Review diagnostics snapshot",
                "Show setup checklist",
            ],
            "operator_readiness": operator_readiness,
        },
        "validation_details": validation_details,
        "release_info": release_info,
        "install_provenance": install_provenance,
        "release_update": release_update,
    }
