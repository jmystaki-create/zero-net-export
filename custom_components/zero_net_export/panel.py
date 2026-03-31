"""Panel app support for Zero Net Export."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .const import DOMAIN, MODES

PANEL_TITLE = "Zero Net Export"
PANEL_ICON = "mdi:transmission-tower-export"
PANEL_URL_PATH = "zero-net-export"
PANEL_COMPONENT_NAME = "zero-net-export-panel"
PANEL_STATIC_DIR = "frontend"
PANEL_BUNDLE_NAME = "zero-net-export-panel.js"
PANEL_WEBSOCKET_GET_STATE = f"{DOMAIN}/panel/get_state"
PANEL_WEBSOCKET_SAVE_CONTROLLER = f"{DOMAIN}/panel/save_controller_settings"
PANEL_WEBSOCKET_RESET_CONTROLLER = f"{DOMAIN}/panel/reset_controller_overrides"
PANEL_WEBSOCKET_UPDATE_DEVICE = f"{DOMAIN}/panel/update_device"
PANEL_WEBSOCKET_RESET_DEVICE = f"{DOMAIN}/panel/reset_device_overrides"
PANEL_SCHEMA_VERSION = 2


def _frontend_dir() -> Path:
    return Path(__file__).parent / PANEL_STATIC_DIR


def _frontend_module_url() -> str:
    return f"/api/{DOMAIN}/{PANEL_BUNDLE_NAME}"


def _coordinators(hass: HomeAssistant) -> dict[str, Any]:
    entries = hass.data.get(DOMAIN, {})
    return {
        entry_id: coordinator
        for entry_id, coordinator in entries.items()
        if entry_id != "panel_registered"
    }


def _get_coordinator(hass: HomeAssistant, entry_id: str | None = None) -> Any:
    coordinators = _coordinators(hass)
    if not coordinators:
        raise HomeAssistantError("Zero Net Export is not configured yet.")

    if entry_id:
        coordinator = coordinators.get(entry_id)
        if coordinator is None:
            raise HomeAssistantError(f"Unknown Zero Net Export entry: {entry_id}")
        return coordinator

    return next(iter(coordinators.values()))


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Register the Zero Net Export panel shell and websocket API."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("panel_registered"):
        return

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                url_path=f"/api/{DOMAIN}",
                path=str(_frontend_dir()),
                cache_headers=False,
            )
        ]
    )

    panel_custom.async_register_panel(
        hass,
        webcomponent_name=PANEL_COMPONENT_NAME,
        frontend_url_path=PANEL_URL_PATH,
        module_url=_frontend_module_url(),
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        require_admin=False,
        config={"version": PANEL_SCHEMA_VERSION},
    )

    websocket_api.async_register_command(hass, websocket_get_panel_state)
    websocket_api.async_register_command(hass, websocket_save_controller_settings)
    websocket_api.async_register_command(hass, websocket_reset_controller_overrides)
    websocket_api.async_register_command(hass, websocket_update_device)
    websocket_api.async_register_command(hass, websocket_reset_device_overrides)
    domain_data["panel_registered"] = True


@websocket_api.websocket_command({vol.Required("type"): PANEL_WEBSOCKET_GET_STATE})
@websocket_api.async_response
async def websocket_get_panel_state(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the normalized panel bootstrap state."""
    connection.send_result(msg["id"], _build_panel_state(hass))


@websocket_api.websocket_command(
    {
        vol.Required("type"): PANEL_WEBSOCKET_SAVE_CONTROLLER,
        vol.Optional("entry_id"): str,
        vol.Optional("enabled"): bool,
        vol.Optional("mode"): vol.In(MODES),
        vol.Optional("target_export_w"): vol.Coerce(float),
        vol.Optional("deadband_w"): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Optional("battery_reserve_soc"): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
    }
)
@websocket_api.async_response
async def websocket_save_controller_settings(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Apply operator-facing controller overrides from the panel."""
    coordinator = _get_coordinator(hass, msg.get("entry_id"))

    if "enabled" in msg:
        await coordinator.async_set_enabled(msg["enabled"])
    if "mode" in msg:
        await coordinator.async_set_mode(msg["mode"])
    if "target_export_w" in msg:
        await coordinator.async_set_target_export_w_override(msg["target_export_w"])
    if "deadband_w" in msg:
        await coordinator.async_set_deadband_w_override(msg["deadband_w"])
    if "battery_reserve_soc" in msg:
        await coordinator.async_set_battery_reserve_soc_override(msg["battery_reserve_soc"])

    connection.send_result(msg["id"], _build_panel_state(hass))


@websocket_api.websocket_command(
    {
        vol.Required("type"): PANEL_WEBSOCKET_RESET_CONTROLLER,
        vol.Optional("entry_id"): str,
    }
)
@websocket_api.async_response
async def websocket_reset_controller_overrides(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Reset controller overrides back to configured defaults."""
    coordinator = _get_coordinator(hass, msg.get("entry_id"))
    await coordinator.async_reset_controller_overrides()
    connection.send_result(msg["id"], _build_panel_state(hass))


@websocket_api.websocket_command(
    {
        vol.Required("type"): PANEL_WEBSOCKET_UPDATE_DEVICE,
        vol.Optional("entry_id"): str,
        vol.Required("device_key"): str,
        vol.Optional("enabled"): bool,
        vol.Optional("priority"): vol.Coerce(int),
    }
)
@websocket_api.async_response
async def websocket_update_device(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Apply operator-facing device overrides from the panel."""
    coordinator = _get_coordinator(hass, msg.get("entry_id"))
    device_key = msg["device_key"]

    if "enabled" in msg:
        await coordinator.async_set_device_enabled_override(device_key, msg["enabled"])
    if "priority" in msg:
        await coordinator.async_set_device_priority_override(device_key, msg["priority"])

    connection.send_result(msg["id"], _build_panel_state(hass))


@websocket_api.websocket_command(
    {
        vol.Required("type"): PANEL_WEBSOCKET_RESET_DEVICE,
        vol.Optional("entry_id"): str,
        vol.Required("device_key"): str,
    }
)
@websocket_api.async_response
async def websocket_reset_device_overrides(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Reset per-device operator overrides back to configured defaults."""
    coordinator = _get_coordinator(hass, msg.get("entry_id"))
    await coordinator.async_reset_device_overrides(msg["device_key"])
    connection.send_result(msg["id"], _build_panel_state(hass))


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return dt_util.as_local(value).isoformat()
    if is_dataclass(value):
        return _serialize_value(asdict(value))
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def _entry_panel_payload(entry_id: str, coordinator: Any) -> dict[str, Any]:
    state = coordinator.data
    if state is None:
        return {
            "entry_id": entry_id,
            "title": coordinator.entry.title,
            "loaded": False,
            "status": "loading",
            "reason": "Coordinator has not produced runtime state yet.",
        }

    overview = {
        "solar_power_w": state.solar_power_w,
        "home_load_power_w": state.home_load_power_w,
        "grid_import_power_w": state.grid_import_power_w,
        "grid_export_power_w": state.grid_export_power_w,
        "battery_soc": state.battery_soc,
        "battery_charge_power_w": state.battery_charge_power_w,
        "battery_discharge_power_w": state.battery_discharge_power_w,
        "surplus_w": state.surplus_w,
        "target_export_w": state.target_export_w,
        "deadband_w": state.deadband_w,
        "battery_reserve_soc": state.battery_reserve_soc,
        "enabled": state.enabled,
        "active": state.active,
        "safe_mode": state.safe_mode,
        "mode": state.mode,
        "status": state.status,
        "reason": state.reason,
        "recommendation": state.recommendation,
        "health_status": state.health_status,
        "health_summary": state.health_summary,
        "confidence": state.confidence,
        "controller_settings": _serialize_value(state.validation_details),
    }

    setup = {
        "source_mismatch": state.source_mismatch,
        "stale_data": state.stale_data,
        "stale_source_count": state.stale_source_count,
        "stale_source_summary": state.stale_source_summary,
        "diagnostic_summary": state.diagnostic_summary,
        "validation": _serialize_value(state.validation_details),
    }

    devices = {
        "device_count": state.device_count,
        "enabled_device_count": state.enabled_device_count,
        "usable_device_count": state.usable_device_count,
        "fixed_device_count": state.fixed_device_count,
        "variable_device_count": state.variable_device_count,
        "controllable_nominal_power_w": state.controllable_nominal_power_w,
        "usable_nominal_power_w": state.usable_nominal_power_w,
        "summary": state.device_status_summary,
        "items": _serialize_value(list(state.device_details.values())),
    }

    diagnostics = {
        "control_status": state.control_status,
        "control_summary": state.control_summary,
        "control_reason": state.control_reason,
        "control_guard_summary": state.control_guard_summary,
        "planned_action_count": state.planned_action_count,
        "executable_action_count": state.executable_action_count,
        "blocked_planned_action_count": state.blocked_planned_action_count,
        "planned_power_delta_w": state.planned_power_delta_w,
        "last_action_status": state.last_action_status,
        "last_action_summary": state.last_action_summary,
        "last_action_at": _serialize_value(state.last_action_at),
        "last_successful_action_at": _serialize_value(state.last_successful_action_at),
        "last_failed_action_at": _serialize_value(state.last_failed_action_at),
        "recent_action_summary": state.recent_action_summary,
        "recent_failure_summary": state.recent_failure_summary,
        "last_successful_action_summary": state.last_successful_action_summary,
    }

    return {
        "entry_id": entry_id,
        "title": coordinator.entry.title,
        "loaded": True,
        "version": coordinator.entry.version,
        "overview": overview,
        "setup": setup,
        "devices": devices,
        "diagnostics": diagnostics,
    }


def _build_panel_state(hass: HomeAssistant) -> dict[str, Any]:
    entries = hass.data.get(DOMAIN, {})
    coordinators = {
        entry_id: coordinator
        for entry_id, coordinator in entries.items()
        if entry_id != "panel_registered"
    }

    panel_entries = [
        _entry_panel_payload(entry_id, coordinator)
        for entry_id, coordinator in coordinators.items()
    ]
    active_entry = panel_entries[0] if panel_entries else None

    return {
        "domain": DOMAIN,
        "panel_schema_version": PANEL_SCHEMA_VERSION,
        "generated_at": dt_util.now().isoformat(),
        "entry_count": len(panel_entries),
        "setup_complete": bool(active_entry),
        "active_entry_id": active_entry["entry_id"] if active_entry else None,
        "active_entry_title": active_entry["title"] if active_entry else None,
        "top_health_summary": active_entry["overview"]["health_summary"] if active_entry else "Zero Net Export is not configured yet.",
        "entries": panel_entries,
    }
