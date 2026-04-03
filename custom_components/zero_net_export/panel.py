"""Panel app support for Zero Net Export."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DEVICE_INVENTORY_JSON,
    CONF_BATTERY_CHARGE_POWER_ENTITY,
    CONF_BATTERY_DISCHARGE_POWER_ENTITY,
    CONF_BATTERY_RESERVE_SOC,
    CONF_BATTERY_SOC_ENTITY,
    CONF_DEADBAND_W,
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
    MODES,
)
from .device_model import (
    ADAPTER_FIXED_TOGGLE,
    ADAPTER_SPECS,
    ADAPTER_VARIABLE_NUMBER,
    DEVICE_KIND_FIXED,
    DEVICE_KIND_VARIABLE,
    parse_device_configs,
)
from .validation import SourceSpec, validate_configured_entities

PANEL_TITLE = "Zero Net Export"
PANEL_ICON = "mdi:transmission-tower-export"
PANEL_URL_PATH = "zero-net-export"
PANEL_COMPONENT_NAME = "zero-net-export-panel"
PANEL_STATIC_DIR = "frontend"
PANEL_BUNDLE_NAME = "zero-net-export-panel.js"
PANEL_WEBSOCKET_GET_STATE = f"{DOMAIN}/panel/get_state"
PANEL_WEBSOCKET_SAVE_CONTROLLER = f"{DOMAIN}/panel/save_controller_settings"
PANEL_WEBSOCKET_RESET_CONTROLLER = f"{DOMAIN}/panel/reset_controller_overrides"
PANEL_WEBSOCKET_SAVE_SOURCES = f"{DOMAIN}/panel/save_sources"
PANEL_WEBSOCKET_ADD_DEVICE = f"{DOMAIN}/panel/add_device"
PANEL_WEBSOCKET_UPDATE_DEVICE = f"{DOMAIN}/panel/update_device"
PANEL_WEBSOCKET_DELETE_DEVICE = f"{DOMAIN}/panel/delete_device"
PANEL_WEBSOCKET_RESET_DEVICE = f"{DOMAIN}/panel/reset_device_overrides"
PANEL_SCHEMA_VERSION = 13

_SOURCE_ROLE_HINTS: dict[str, dict[str, Any]] = {
    CONF_SOLAR_POWER_ENTITY: {
        "quantity": "power",
        "description": "Live solar generation power.",
        "preferred_terms": ("solar", "pv", "inverter", "generation"),
    },
    CONF_SOLAR_ENERGY_ENTITY: {
        "quantity": "energy",
        "description": "Accumulating solar generation energy sensor.",
        "preferred_terms": ("solar", "pv", "inverter", "generation"),
    },
    CONF_GRID_IMPORT_POWER_ENTITY: {
        "quantity": "power",
        "description": "Positive import-from-grid power sensor.",
        "preferred_terms": ("grid", "import", "consumption", "from grid"),
    },
    CONF_GRID_EXPORT_POWER_ENTITY: {
        "quantity": "power",
        "description": "Positive export-to-grid power sensor.",
        "preferred_terms": ("grid", "export", "feed", "to grid"),
    },
    CONF_GRID_IMPORT_ENERGY_ENTITY: {
        "quantity": "energy",
        "description": "Accumulating grid-import energy sensor.",
        "preferred_terms": ("grid", "import", "consumption", "from grid"),
    },
    CONF_GRID_EXPORT_ENERGY_ENTITY: {
        "quantity": "energy",
        "description": "Accumulating grid-export energy sensor.",
        "preferred_terms": ("grid", "export", "feed", "to grid"),
    },
    CONF_HOME_LOAD_POWER_ENTITY: {
        "quantity": "power",
        "description": "Whole-home load / consumption power sensor.",
        "preferred_terms": ("home", "load", "consumption", "house"),
    },
    CONF_BATTERY_SOC_ENTITY: {
        "quantity": "percent",
        "description": "Battery state of charge percent sensor.",
        "preferred_terms": ("battery", "soc", "state of charge"),
    },
    CONF_BATTERY_CHARGE_POWER_ENTITY: {
        "quantity": "power",
        "description": "Positive battery charge power sensor.",
        "preferred_terms": ("battery", "charge", "charging"),
    },
    CONF_BATTERY_DISCHARGE_POWER_ENTITY: {
        "quantity": "power",
        "description": "Positive battery discharge power sensor.",
        "preferred_terms": ("battery", "discharge", "discharging"),
    },
}


def _frontend_dir() -> Path:
    return Path(__file__).parent / PANEL_STATIC_DIR


def _frontend_module_url() -> str:
    return f"/api/{DOMAIN}/{PANEL_BUNDLE_NAME}?v={PANEL_SCHEMA_VERSION}"


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
    websocket_api.async_register_command(hass, websocket_save_sources)
    websocket_api.async_register_command(hass, websocket_add_device)
    websocket_api.async_register_command(hass, websocket_update_device)
    websocket_api.async_register_command(hass, websocket_delete_device)
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
        vol.Required("type"): PANEL_WEBSOCKET_SAVE_SOURCES,
        vol.Optional("entry_id"): str,
        vol.Required(CONF_SOLAR_POWER_ENTITY): str,
        vol.Required(CONF_SOLAR_ENERGY_ENTITY): str,
        vol.Required(CONF_GRID_IMPORT_POWER_ENTITY): str,
        vol.Required(CONF_GRID_EXPORT_POWER_ENTITY): str,
        vol.Required(CONF_GRID_IMPORT_ENERGY_ENTITY): str,
        vol.Required(CONF_GRID_EXPORT_ENERGY_ENTITY): str,
        vol.Required(CONF_HOME_LOAD_POWER_ENTITY): str,
        vol.Optional(CONF_BATTERY_SOC_ENTITY): str,
        vol.Optional(CONF_BATTERY_CHARGE_POWER_ENTITY): str,
        vol.Optional(CONF_BATTERY_DISCHARGE_POWER_ENTITY): str,
        vol.Optional(CONF_REFRESH_SECONDS): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
    }
)
@websocket_api.async_response
async def websocket_save_sources(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Persist source mapping changes from the panel and reload the entry."""
    coordinator = _get_coordinator(hass, msg.get("entry_id"))
    entry = coordinator.entry
    merged_data = dict(entry.data)

    for key in (
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
    ):
        merged_data[key] = msg.get(key) or None

    issues = validate_configured_entities(hass, merged_data, _source_specs_from_config(merged_data))
    blocking_issues = [issue.message for issue in issues if issue.severity == "error"]
    if blocking_issues:
        raise HomeAssistantError("\n".join(blocking_issues[:6]))

    merged_options = dict(entry.options)
    if CONF_REFRESH_SECONDS in msg:
        merged_options[CONF_REFRESH_SECONDS] = msg[CONF_REFRESH_SECONDS]

    hass.config_entries.async_update_entry(entry, data=merged_data, options=merged_options)
    await hass.config_entries.async_reload(entry.entry_id)
    connection.send_result(msg["id"], _build_panel_state(hass))


def _source_specs_from_config(config: dict[str, Any]) -> list[SourceSpec]:
    return [
        SourceSpec(CONF_SOLAR_POWER_ENTITY, config.get(CONF_SOLAR_POWER_ENTITY), "power"),
        SourceSpec(CONF_SOLAR_ENERGY_ENTITY, config.get(CONF_SOLAR_ENERGY_ENTITY), "energy"),
        SourceSpec(CONF_GRID_IMPORT_POWER_ENTITY, config.get(CONF_GRID_IMPORT_POWER_ENTITY), "power"),
        SourceSpec(CONF_GRID_EXPORT_POWER_ENTITY, config.get(CONF_GRID_EXPORT_POWER_ENTITY), "power"),
        SourceSpec(CONF_GRID_IMPORT_ENERGY_ENTITY, config.get(CONF_GRID_IMPORT_ENERGY_ENTITY), "energy"),
        SourceSpec(CONF_GRID_EXPORT_ENERGY_ENTITY, config.get(CONF_GRID_EXPORT_ENERGY_ENTITY), "energy"),
        SourceSpec(CONF_HOME_LOAD_POWER_ENTITY, config.get(CONF_HOME_LOAD_POWER_ENTITY), "power"),
        SourceSpec(CONF_BATTERY_SOC_ENTITY, config.get(CONF_BATTERY_SOC_ENTITY), "percent", required=False),
        SourceSpec(CONF_BATTERY_CHARGE_POWER_ENTITY, config.get(CONF_BATTERY_CHARGE_POWER_ENTITY), "power", required=False),
        SourceSpec(CONF_BATTERY_DISCHARGE_POWER_ENTITY, config.get(CONF_BATTERY_DISCHARGE_POWER_ENTITY), "power", required=False),
    ]


def _configured_device_payloads(entry: Any) -> tuple[list[dict[str, Any]], list[str]]:
    raw = entry.options.get(CONF_DEVICE_INVENTORY_JSON, entry.data.get(CONF_DEVICE_INVENTORY_JSON))
    devices, issues = parse_device_configs(raw)
    payloads: list[dict[str, Any]] = []
    for device in devices:
        payloads.append(
            {
                "key": device.key,
                "name": device.name,
                "kind": device.kind,
                "entity_id": device.entity_id,
                "adapter": device.adapter,
                "nominal_power_w": device.nominal_power_w,
                "min_power_w": device.min_power_w,
                "max_power_w": device.max_power_w,
                "step_w": device.step_w,
                "priority": device.priority,
                "enabled": device.enabled,
                "min_on_seconds": device.min_on_seconds,
                "min_off_seconds": device.min_off_seconds,
                "cooldown_seconds": device.cooldown_seconds,
                "max_active_seconds": device.max_active_seconds,
            }
        )
    return payloads, issues


def _device_form_payload(msg: dict[str, Any], existing_key: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": str(msg["name"]).strip(),
        "kind": str(msg["kind"]).strip(),
        "entity_id": str(msg["entity_id"]).strip(),
        "adapter": str(msg.get("adapter") or "").strip() or None,
        "nominal_power_w": float(msg["nominal_power_w"]),
        "priority": int(msg.get("priority", 100)),
        "enabled": bool(msg.get("enabled", True)),
        "min_on_seconds": int(msg.get("min_on_seconds", 300)),
        "min_off_seconds": int(msg.get("min_off_seconds", 300)),
        "cooldown_seconds": int(msg.get("cooldown_seconds", 30)),
        "max_active_seconds": int(msg["max_active_seconds"]) if msg.get("max_active_seconds") not in (None, "") else None,
    }
    if existing_key:
        payload["key"] = existing_key

    if payload["kind"] == DEVICE_KIND_FIXED:
        payload["adapter"] = payload["adapter"] or ADAPTER_FIXED_TOGGLE
        payload["min_power_w"] = float(msg.get("min_power_w", payload["nominal_power_w"]))
        payload["max_power_w"] = float(msg.get("max_power_w", payload["nominal_power_w"]))
        payload["step_w"] = float(msg.get("step_w", payload["nominal_power_w"]))
    else:
        payload["adapter"] = payload["adapter"] or ADAPTER_VARIABLE_NUMBER
        payload["min_power_w"] = float(msg["min_power_w"])
        payload["max_power_w"] = float(msg["max_power_w"])
        payload["step_w"] = float(msg["step_w"])

    return payload


def _validate_device_inventory(payloads: list[dict[str, Any]]) -> None:
    _, issues = parse_device_configs(json.dumps(payloads, indent=2))
    if issues:
        raise HomeAssistantError("\n".join(issues[:6]))


async def _save_device_inventory(hass: HomeAssistant, entry: Any, payloads: list[dict[str, Any]]) -> None:
    _validate_device_inventory(payloads)
    merged_options = dict(entry.options)
    merged_options[CONF_DEVICE_INVENTORY_JSON] = json.dumps(payloads, indent=2)
    hass.config_entries.async_update_entry(entry, options=merged_options)
    await hass.config_entries.async_reload(entry.entry_id)


@websocket_api.websocket_command(
    {
        vol.Required("type"): PANEL_WEBSOCKET_ADD_DEVICE,
        vol.Optional("entry_id"): str,
        vol.Required("name"): str,
        vol.Required("kind"): vol.In([DEVICE_KIND_FIXED, DEVICE_KIND_VARIABLE]),
        vol.Required("entity_id"): str,
        vol.Optional("adapter"): vol.In(list(ADAPTER_SPECS.keys())),
        vol.Required("nominal_power_w"): vol.Coerce(float),
        vol.Optional("min_power_w"): vol.Coerce(float),
        vol.Optional("max_power_w"): vol.Coerce(float),
        vol.Optional("step_w"): vol.Coerce(float),
        vol.Optional("priority"): vol.Coerce(int),
        vol.Optional("enabled"): bool,
        vol.Optional("min_on_seconds"): vol.Coerce(int),
        vol.Optional("min_off_seconds"): vol.Coerce(int),
        vol.Optional("cooldown_seconds"): vol.Coerce(int),
        vol.Optional("max_active_seconds"): vol.Any(None, vol.Coerce(int)),
    }
)
@websocket_api.async_response
async def websocket_add_device(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Add a configured device through the panel."""
    coordinator = _get_coordinator(hass, msg.get("entry_id"))
    entry = coordinator.entry
    payloads, _ = _configured_device_payloads(entry)
    payloads.append(_device_form_payload(msg))
    await _save_device_inventory(hass, entry, payloads)
    connection.send_result(msg["id"], _build_panel_state(hass))


@websocket_api.websocket_command(
    {
        vol.Required("type"): PANEL_WEBSOCKET_UPDATE_DEVICE,
        vol.Optional("entry_id"): str,
        vol.Required("device_key"): str,
        vol.Optional("save_config"): bool,
        vol.Optional("name"): str,
        vol.Optional("kind"): vol.In([DEVICE_KIND_FIXED, DEVICE_KIND_VARIABLE]),
        vol.Optional("entity_id"): str,
        vol.Optional("adapter"): vol.In(list(ADAPTER_SPECS.keys())),
        vol.Optional("nominal_power_w"): vol.Coerce(float),
        vol.Optional("min_power_w"): vol.Coerce(float),
        vol.Optional("max_power_w"): vol.Coerce(float),
        vol.Optional("step_w"): vol.Coerce(float),
        vol.Optional("enabled"): bool,
        vol.Optional("priority"): vol.Coerce(int),
        vol.Optional("configured_enabled"): bool,
        vol.Optional("min_on_seconds"): vol.Coerce(int),
        vol.Optional("min_off_seconds"): vol.Coerce(int),
        vol.Optional("cooldown_seconds"): vol.Coerce(int),
        vol.Optional("max_active_seconds"): vol.Any(None, vol.Coerce(int)),
    }
)
@websocket_api.async_response
async def websocket_update_device(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Apply operator overrides or persist config edits for a device from the panel."""
    coordinator = _get_coordinator(hass, msg.get("entry_id"))
    device_key = msg["device_key"]

    config_fields = {
        "name",
        "kind",
        "entity_id",
        "adapter",
        "nominal_power_w",
        "min_power_w",
        "max_power_w",
        "step_w",
        "configured_enabled",
        "priority",
        "min_on_seconds",
        "min_off_seconds",
        "cooldown_seconds",
        "max_active_seconds",
    }
    if msg.get("save_config"):
        entry = coordinator.entry
        payloads, _ = _configured_device_payloads(entry)
        updated = False
        for index, payload in enumerate(payloads):
            if payload.get("key") != device_key:
                continue
            merged = dict(payload)
            if "configured_enabled" in msg:
                merged["enabled"] = bool(msg["configured_enabled"])
            for field in config_fields - {"configured_enabled"}:
                if field in msg:
                    merged[field] = msg[field]
            payloads[index] = _device_form_payload(merged, existing_key=device_key)
            updated = True
            break

        if not updated:
            raise HomeAssistantError(f"Unknown device: {device_key}")

        await _save_device_inventory(hass, entry, payloads)
        connection.send_result(msg["id"], _build_panel_state(hass))
        return

    if "enabled" in msg:
        await coordinator.async_set_device_enabled_override(device_key, msg["enabled"])
    if "priority" in msg:
        await coordinator.async_set_device_priority_override(device_key, msg["priority"])

    connection.send_result(msg["id"], _build_panel_state(hass))


@websocket_api.websocket_command(
    {
        vol.Required("type"): PANEL_WEBSOCKET_DELETE_DEVICE,
        vol.Optional("entry_id"): str,
        vol.Required("device_key"): str,
    }
)
@websocket_api.async_response
async def websocket_delete_device(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete a configured device through the panel."""
    coordinator = _get_coordinator(hass, msg.get("entry_id"))
    entry = coordinator.entry
    payloads, _ = _configured_device_payloads(entry)
    filtered = [payload for payload in payloads if payload.get("key") != msg["device_key"]]
    if len(filtered) == len(payloads):
        raise HomeAssistantError(f"Unknown device: {msg['device_key']}")
    await _save_device_inventory(hass, entry, filtered)
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
        "source_diagnostics": _serialize_value(state.validation_details.get("source_diagnostics", {})),
        "calibration_hints": list(state.validation_details.get("calibration_hints", [])),
        "source_mapping": {
            CONF_SOLAR_POWER_ENTITY: coordinator.entry.data.get(CONF_SOLAR_POWER_ENTITY),
            CONF_SOLAR_ENERGY_ENTITY: coordinator.entry.data.get(CONF_SOLAR_ENERGY_ENTITY),
            CONF_GRID_IMPORT_POWER_ENTITY: coordinator.entry.data.get(CONF_GRID_IMPORT_POWER_ENTITY),
            CONF_GRID_EXPORT_POWER_ENTITY: coordinator.entry.data.get(CONF_GRID_EXPORT_POWER_ENTITY),
            CONF_GRID_IMPORT_ENERGY_ENTITY: coordinator.entry.data.get(CONF_GRID_IMPORT_ENERGY_ENTITY),
            CONF_GRID_EXPORT_ENERGY_ENTITY: coordinator.entry.data.get(CONF_GRID_EXPORT_ENERGY_ENTITY),
            CONF_HOME_LOAD_POWER_ENTITY: coordinator.entry.data.get(CONF_HOME_LOAD_POWER_ENTITY),
            CONF_BATTERY_SOC_ENTITY: coordinator.entry.data.get(CONF_BATTERY_SOC_ENTITY),
            CONF_BATTERY_CHARGE_POWER_ENTITY: coordinator.entry.data.get(CONF_BATTERY_CHARGE_POWER_ENTITY),
            CONF_BATTERY_DISCHARGE_POWER_ENTITY: coordinator.entry.data.get(CONF_BATTERY_DISCHARGE_POWER_ENTITY),
            CONF_REFRESH_SECONDS: coordinator.entry.options.get(
                CONF_REFRESH_SECONDS,
                coordinator.entry.data.get(CONF_REFRESH_SECONDS),
            ),
        },
        "available_entities": _available_sensor_entities(hass),
        "entity_suggestions": _source_entity_suggestions(hass),
    }

    configured_devices, device_parse_issues = _configured_device_payloads(coordinator.entry)

    devices = {
        "device_count": state.device_count,
        "enabled_device_count": state.enabled_device_count,
        "usable_device_count": state.usable_device_count,
        "fixed_device_count": state.fixed_device_count,
        "variable_device_count": state.variable_device_count,
        "controllable_nominal_power_w": state.controllable_nominal_power_w,
        "usable_nominal_power_w": state.usable_nominal_power_w,
        "summary": state.device_status_summary,
        "parse_issues": device_parse_issues,
        "configured_items": configured_devices,
        "items": _serialize_value(list(state.device_details.values())),
        "available_entities": _available_device_entities(hass),
        "adapter_options": [
            {
                "key": spec.key,
                "label": spec.label,
                "kind": spec.kind,
                "description": spec.description,
            }
            for spec in ADAPTER_SPECS.values()
        ],
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
        "last_failed_action_message": state.last_failed_action_message,
        "last_action_device": state.last_action_device,
        "last_failed_action_device": state.last_failed_action_device,
        "health_status": state.health_status,
        "health_summary": state.health_summary,
        "stale_data": state.stale_data,
        "stale_source_summary": state.stale_source_summary,
        "source_mismatch": state.source_mismatch,
        "battery_below_reserve": state.battery_below_reserve,
        "action_history_count": state.action_history_count,
        "action_history": _serialize_value(state.validation_details.get("action_history", [])),
        "source_diagnostics": _serialize_value(state.validation_details.get("source_diagnostics", {})),
        "source_freshness": _serialize_value(state.validation_details.get("source_freshness", {})),
        "calibration_hints": list(state.validation_details.get("calibration_hints", [])),
        "device_items": _serialize_value(list(state.device_details.values())),
    }

    settings = {
        "controller_defaults": {
            "target_export_w": coordinator.entry.options.get(
                CONF_TARGET_EXPORT_W,
                coordinator.entry.data.get(CONF_TARGET_EXPORT_W),
            ),
            "deadband_w": coordinator.entry.options.get(
                CONF_DEADBAND_W,
                coordinator.entry.data.get(CONF_DEADBAND_W),
            ),
            "battery_reserve_soc": coordinator.entry.options.get(
                CONF_BATTERY_RESERVE_SOC,
                coordinator.entry.data.get(CONF_BATTERY_RESERVE_SOC),
            ),
            "refresh_seconds": coordinator.entry.options.get(
                CONF_REFRESH_SECONDS,
                coordinator.entry.data.get(CONF_REFRESH_SECONDS),
            ),
        },
        "operator_summary": {
            "entry_title": coordinator.entry.title,
            "config_entry_version": coordinator.entry.version,
            "integration_version": INTEGRATION_VERSION,
            "device_count": state.device_count,
            "enabled_device_count": state.enabled_device_count,
            "usable_device_count": state.usable_device_count,
            "safe_mode": state.safe_mode,
            "health_status": state.health_status,
            "health_summary": state.health_summary,
            "source_mismatch": state.source_mismatch,
            "stale_data": state.stale_data,
        },
        "workflow": {
            "panel_primary": True,
            "dashboard_fallback_only": True,
            "json_options_fallback_only": True,
            "normal_operator_path": [
                "Setup tab for source mapping",
                "Devices tab for add/edit/remove device onboarding",
                "Overview tab for daily operation",
                "Diagnostics tab for explanation and troubleshooting",
            ],
        },
        "links": {
            "documentation": "https://github.com/jmystaki-create/zero-net-export#readme",
            "changelog": "https://github.com/jmystaki-create/zero-net-export/blob/main/CHANGELOG.md",
            "panel_rebuild_plan": "https://github.com/jmystaki-create/zero-net-export/blob/main/docs/PANEL_APP_REBUILD_PLAN.md",
            "release_process": "https://github.com/jmystaki-create/zero-net-export/blob/main/docs/RELEASE_PROCESS.md",
            "issues": "https://github.com/jmystaki-create/zero-net-export/issues",
        },
    }

    return {
        "entry_id": entry_id,
        "title": coordinator.entry.title,
        "loaded": True,
        "config_entry_version": coordinator.entry.version,
        "integration_version": INTEGRATION_VERSION,
        "overview": overview,
        "setup": setup,
        "devices": devices,
        "diagnostics": diagnostics,
        "settings": settings,
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
        "integration_version": INTEGRATION_VERSION,
        "panel_schema_version": PANEL_SCHEMA_VERSION,
        "generated_at": dt_util.now().isoformat(),
        "entry_count": len(panel_entries),
        "setup_complete": bool(active_entry),
        "active_entry_id": active_entry["entry_id"] if active_entry else None,
        "active_entry_title": active_entry["title"] if active_entry else None,
        "top_health_summary": active_entry["overview"]["health_summary"] if active_entry else "Zero Net Export is not configured yet.",
        "entries": panel_entries,
    }


def _available_sensor_entities(hass: HomeAssistant) -> list[dict[str, str]]:
    entities: list[dict[str, str | None]] = []
    for state in sorted(hass.states.async_all("sensor"), key=lambda item: item.entity_id):
        label = state.attributes.get("friendly_name") or state.entity_id
        unit = state.attributes.get("unit_of_measurement")
        device_class = state.attributes.get("device_class")
        state_class = state.attributes.get("state_class")
        if unit:
            label = f"{label} ({unit})"
        metadata: list[str] = []
        if device_class:
            metadata.append(str(device_class))
        if state_class:
            metadata.append(str(state_class))
        if metadata:
            label = f"{label} — {', '.join(metadata)}"
        entities.append(
            {
                "entity_id": state.entity_id,
                "label": label,
                "unit": unit,
                "device_class": device_class,
                "state_class": state_class,
            }
        )
    return entities


def _score_source_candidate(entity: dict[str, Any], quantity: str, preferred_terms: tuple[str, ...]) -> int:
    score = 0
    unit = entity.get("unit")
    device_class = entity.get("device_class")
    state_class = entity.get("state_class")
    haystack = f"{entity.get('entity_id', '')} {entity.get('label', '')}".lower()

    if quantity == "power":
        if unit in {"W", "kW"}:
            score += 50
        if device_class == "power":
            score += 25
        if state_class == "measurement":
            score += 10
    elif quantity == "energy":
        if unit in {"Wh", "kWh"}:
            score += 50
        if device_class == "energy":
            score += 25
        if state_class in {"total", "total_increasing"}:
            score += 10
    elif quantity == "percent":
        if unit == "%":
            score += 50
        if device_class in {"battery", "power_factor"}:
            score += 15
        if state_class == "measurement":
            score += 10

    for term in preferred_terms:
        if term in haystack:
            score += 8

    return score


def _source_entity_suggestions(hass: HomeAssistant) -> dict[str, Any]:
    available = _available_sensor_entities(hass)
    suggestions: dict[str, Any] = {}

    for key, hint in _SOURCE_ROLE_HINTS.items():
        ranked = sorted(
            (
                {
                    **entity,
                    "score": _score_source_candidate(entity, hint["quantity"], hint["preferred_terms"]),
                }
                for entity in available
            ),
            key=lambda item: (-item["score"], item["entity_id"]),
        )
        suggestions[key] = {
            "description": hint["description"],
            "quantity": hint["quantity"],
            "items": [item for item in ranked[:5] if item["score"] > 0],
        }

    return suggestions


def _available_device_entities(hass: HomeAssistant) -> list[dict[str, str]]:
    entities: list[dict[str, str]] = []
    for domain in ("switch", "input_boolean", "number", "input_number"):
        for state in sorted(hass.states.async_all(domain), key=lambda item: item.entity_id):
            label = state.attributes.get("friendly_name") or state.entity_id
            unit = state.attributes.get("unit_of_measurement")
            if unit:
                label = f"{label} ({unit})"
            entities.append({"entity_id": state.entity_id, "label": label, "domain": domain})
    return entities
