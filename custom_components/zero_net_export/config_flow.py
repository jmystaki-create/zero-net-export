"""Config flow for Zero Net Export."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BATTERY_CHARGE_POWER_ENTITY,
    CONF_BATTERY_DISCHARGE_POWER_ENTITY,
    CONF_BATTERY_RESERVE_SOC,
    CONF_BATTERY_SOC_ENTITY,
    CONF_DEADBAND_W,
    CONF_DEVICE_INVENTORY_JSON,
    CONF_GRID_EXPORT_ENERGY_ENTITY,
    CONF_GRID_EXPORT_POWER_ENTITY,
    CONF_GRID_IMPORT_ENERGY_ENTITY,
    CONF_GRID_IMPORT_POWER_ENTITY,
    CONF_GRID_SENSOR_MODE,
    CONF_HOME_LOAD_POWER_ENTITY,
    CONF_NAME,
    CONF_REFRESH_SECONDS,
    CONF_SOLAR_ENERGY_ENTITY,
    CONF_SOLAR_POWER_ENTITY,
    CONF_TARGET_EXPORT_W,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_DEADBAND_W,
    DEFAULT_DEVICE_INVENTORY_JSON,
    DEFAULT_GRID_SENSOR_MODE,
    DEFAULT_NAME,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_TARGET_EXPORT_W,
    DOMAIN,
    GRID_SENSOR_MODE_COMBINED,
    GRID_SENSOR_MODE_SEPARATE,
    SOURCE_ROLE_LABELS,
)
from .device_model import (
    ADAPTER_FIXED_TOGGLE,
    ADAPTER_VARIABLE_NUMBER,
    DEVICE_KIND_FIXED,
    DEVICE_KIND_VARIABLE,
    default_device_blueprint,
    get_device_template,
    get_device_templates,
    parse_device_configs,
)
from .native_support import PRIMARY_CONFIGURE_PATH, _source_specs_from_config, build_native_operator_readiness
from .validation import (
    DERIVED_SOURCE_MODE_DIRECT,
    DERIVED_SOURCE_MODE_NEGATIVE_ABS,
    DERIVED_SOURCE_MODE_POSITIVE,
    DERIVED_SOURCE_PREFIX,
    parse_source_binding,
    validate_configured_entities,
)

_LOGGER = logging.getLogger(__name__)


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


def _coerce_text(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value
    return str(value)


def _entry_default_number(config_entry, key: str, fallback: int | float) -> int | float:
    return _coerce_number(config_entry.options.get(key, config_entry.data.get(key, fallback)), fallback)


def _entry_default_text(config_entry, key: str, fallback: str) -> str:
    return _coerce_text(config_entry.options.get(key, config_entry.data.get(key, fallback)), fallback)


def _build_bootstrap_schema(defaults: dict | None = None) -> vol.Schema:
    defaults = defaults or {}

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
        }
    )


def _build_bootstrap_entry_data(user_input: dict[str, str]) -> dict[str, str | int | float | None]:
    return {
        CONF_NAME: user_input[CONF_NAME],
        CONF_SOLAR_POWER_ENTITY: None,
        CONF_SOLAR_ENERGY_ENTITY: None,
        CONF_GRID_IMPORT_POWER_ENTITY: None,
        CONF_GRID_EXPORT_POWER_ENTITY: None,
        CONF_GRID_IMPORT_ENERGY_ENTITY: None,
        CONF_GRID_EXPORT_ENERGY_ENTITY: None,
        CONF_HOME_LOAD_POWER_ENTITY: None,
        CONF_BATTERY_SOC_ENTITY: None,
        CONF_BATTERY_CHARGE_POWER_ENTITY: None,
        CONF_BATTERY_DISCHARGE_POWER_ENTITY: None,
        CONF_TARGET_EXPORT_W: DEFAULT_TARGET_EXPORT_W,
        CONF_DEADBAND_W: DEFAULT_DEADBAND_W,
        CONF_BATTERY_RESERVE_SOC: DEFAULT_BATTERY_RESERVE_SOC,
        CONF_REFRESH_SECONDS: DEFAULT_REFRESH_SECONDS,
        CONF_DEVICE_INVENTORY_JSON: DEFAULT_DEVICE_INVENTORY_JSON,
    }


def _device_options_json(devices: list[dict[str, Any]]) -> str:
    import json

    return json.dumps(devices, indent=2)


COMBINED_GRID_ENERGY_FALLBACK_KEY = "grid_energy_entity_manual"
BATTERY_SOC_FALLBACK_KEY = "battery_soc_entity_manual"


def _build_derived_binding(mode: str, entity_id: str | None) -> str | None:
    if not entity_id:
        return None
    return f"{DERIVED_SOURCE_PREFIX}:{mode}:{entity_id}"


def _normalize_selector_entity_value(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("entity_id", "value", "id"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate:
                return candidate
    return str(value)


def _normalize_entity_selector_input(user_input: dict[str, Any] | None, key: str) -> str | None:
    if not user_input:
        return None
    value = _normalize_selector_entity_value(user_input.get(key))
    if value:
        return value
    alt_key = f"{key}.entity_id"
    alt_value = _normalize_selector_entity_value(user_input.get(alt_key))
    if alt_value:
        return alt_value
    selector_value = user_input.get(key)
    if isinstance(selector_value, dict):
        for nested_key in ("entity_id", "value", "id"):
            nested_value = _normalize_selector_entity_value(selector_value.get(nested_key))
            if nested_value:
                return nested_value
    return None


def _selector_entity_default(raw: str | None, *, allow_derived: bool = False) -> str:
    binding = parse_source_binding(raw)
    if not binding.valid or not binding.entity_id:
        return ""
    if binding.mode == DERIVED_SOURCE_MODE_DIRECT:
        return binding.entity_id
    return binding.entity_id if allow_derived else ""


def _infer_grid_sensor_mode(config: dict[str, Any]) -> str:
    import_power = parse_source_binding(config.get(CONF_GRID_IMPORT_POWER_ENTITY))
    export_power = parse_source_binding(config.get(CONF_GRID_EXPORT_POWER_ENTITY))
    import_energy = parse_source_binding(config.get(CONF_GRID_IMPORT_ENERGY_ENTITY))
    export_energy = parse_source_binding(config.get(CONF_GRID_EXPORT_ENERGY_ENTITY))

    power_combined = (
        import_power.valid
        and export_power.valid
        and import_power.entity_id
        and import_power.entity_id == export_power.entity_id
        and import_power.mode == DERIVED_SOURCE_MODE_POSITIVE
        and export_power.mode == DERIVED_SOURCE_MODE_NEGATIVE_ABS
    )
    energy_combined = (
        import_energy.valid
        and export_energy.valid
        and import_energy.entity_id
        and import_energy.entity_id == export_energy.entity_id
        and import_energy.mode == DERIVED_SOURCE_MODE_POSITIVE
        and export_energy.mode == DERIVED_SOURCE_MODE_NEGATIVE_ABS
    )
    if power_combined and energy_combined:
        return GRID_SENSOR_MODE_COMBINED
    if not any(
        config.get(key)
        for key in (
            CONF_GRID_IMPORT_POWER_ENTITY,
            CONF_GRID_EXPORT_POWER_ENTITY,
            CONF_GRID_IMPORT_ENERGY_ENTITY,
            CONF_GRID_EXPORT_ENERGY_ENTITY,
        )
    ):
        return DEFAULT_GRID_SENSOR_MODE
    return GRID_SENSOR_MODE_SEPARATE


def _grid_mode_default(config_entry) -> str:
    configured = config_entry.options.get(CONF_GRID_SENSOR_MODE, config_entry.data.get(CONF_GRID_SENSOR_MODE))
    if configured in {GRID_SENSOR_MODE_COMBINED, GRID_SENSOR_MODE_SEPARATE}:
        return str(configured)
    snapshot = dict(config_entry.data)
    snapshot.update(config_entry.options)
    return _infer_grid_sensor_mode(snapshot)


def _grid_mode_missing_sources(config: dict[str, Any], grid_mode: str) -> list[str]:
    required_keys = [
        CONF_SOLAR_POWER_ENTITY,
        CONF_SOLAR_ENERGY_ENTITY,
    ]
    if grid_mode == GRID_SENSOR_MODE_COMBINED:
        required_keys.extend(
            [
                CONF_GRID_IMPORT_POWER_ENTITY,
                CONF_GRID_IMPORT_ENERGY_ENTITY,
            ]
        )
    else:
        required_keys.extend(
            [
                CONF_GRID_IMPORT_POWER_ENTITY,
                CONF_GRID_EXPORT_POWER_ENTITY,
                CONF_GRID_IMPORT_ENERGY_ENTITY,
                CONF_GRID_EXPORT_ENERGY_ENTITY,
            ]
        )
    return [SOURCE_ROLE_LABELS.get(key, key) for key in required_keys if not config.get(key)]


class ZeroNetExportConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            entry_data = _build_bootstrap_entry_data(user_input)
            return self.async_create_entry(title=user_input[CONF_NAME], data=entry_data)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_bootstrap_schema(user_input),
            errors={},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ZeroNetExportOptionsFlow(config_entry)


class ZeroNetExportOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        super().__init__()
        self._config_entry = config_entry
        self._pending_grid_sensor_mode: str | None = None
        self._pending_device_kind: str | None = None
        self._pending_device_key: str | None = None
        self._pending_device_template_key: str | None = None

    @staticmethod
    def _device_status_label(device: dict[str, Any]) -> str:
        state = "enabled" if device.get("enabled", True) else "disabled"
        priority = int(device.get("priority", 0) or 0)
        power = int(float(device.get("nominal_power_w", 0) or 0))
        return (
            f"{device.get('name', 'Unnamed device')} "
            f"({device.get('kind', 'unknown')}, {state}, priority {priority}, {power} W, {device.get('entity_id', 'unknown entity')})"
        )

    def _fleet_summary_lines(self, devices: list[dict[str, Any]]) -> list[str]:
        if not devices:
            return ["- None"]
        ordered = sorted(
            devices,
            key=lambda item: (
                0 if item.get("enabled", True) else 1,
                int(item.get("priority", 0) or 0),
                str(item.get("name", "")).lower(),
            ),
        )
        enabled_count = sum(1 for device in devices if device.get("enabled", True))
        fixed_count = sum(1 for device in devices if device.get("kind") == DEVICE_KIND_FIXED)
        variable_count = sum(1 for device in devices if device.get("kind") == DEVICE_KIND_VARIABLE)
        total_power = int(sum(float(device.get("nominal_power_w", 0) or 0) for device in devices))
        lines = [
            f"- Fleet summary: {len(devices)} device(s), {enabled_count} enabled, {fixed_count} fixed, {variable_count} variable, {total_power} W nominal controllable power",
        ]
        lines.extend(f"- {self._device_status_label(device)}" for device in ordered)
        return lines

    def _load_devices(self) -> tuple[list[dict[str, Any]], list[str]]:
        raw_inventory = _entry_default_text(
            self._config_entry,
            CONF_DEVICE_INVENTORY_JSON,
            DEFAULT_DEVICE_INVENTORY_JSON,
        )
        devices, issues = parse_device_configs(raw_inventory)
        return [
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
            for device in devices
        ], issues

    async def _save_devices(self, devices: list[dict[str, Any]]):
        merged_options = dict(self._config_entry.options)
        merged_options[CONF_DEVICE_INVENTORY_JSON] = _device_options_json(devices)
        self.hass.config_entries.async_update_entry(self._config_entry, options=merged_options)
        await self.hass.config_entries.async_reload(self._config_entry.entry_id)
        return self.async_create_entry(title="", data=merged_options)

    @staticmethod
    def _build_device_payload(user_input: dict[str, Any], kind: str, *, key: str | None = None) -> dict[str, Any]:
        name = str(user_input["name"]).strip()
        payload: dict[str, Any] = {
            "name": name,
            "kind": kind,
            "entity_id": user_input["entity_id"],
            "adapter": ADAPTER_FIXED_TOGGLE if kind == DEVICE_KIND_FIXED else ADAPTER_VARIABLE_NUMBER,
            "nominal_power_w": float(user_input["nominal_power_w"]),
            "priority": int(user_input["priority"]),
            "enabled": bool(user_input.get("enabled", True)),
            "min_on_seconds": int(user_input["min_on_seconds"]),
            "min_off_seconds": int(user_input["min_off_seconds"]),
            "cooldown_seconds": int(user_input["cooldown_seconds"]),
            "max_active_seconds": int(user_input["max_active_seconds"]) or None,
        }
        if key:
            payload["key"] = key
        if kind == DEVICE_KIND_FIXED:
            payload["min_power_w"] = payload["nominal_power_w"]
            payload["max_power_w"] = payload["nominal_power_w"]
            payload["step_w"] = payload["nominal_power_w"]
        else:
            payload["min_power_w"] = float(user_input["min_power_w"])
            payload["max_power_w"] = float(user_input["max_power_w"])
            payload["step_w"] = float(user_input["step_w"])
        return payload

    @staticmethod
    def _device_form_defaults(
        device: dict[str, Any] | None,
        kind: str,
        template_defaults: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        defaults = {
            "name": "",
            "entity_id": "",
            "nominal_power_w": 2400 if kind == DEVICE_KIND_FIXED else 3600,
            "priority": 100,
            "enabled": True,
            "min_on_seconds": 900 if kind == DEVICE_KIND_FIXED else 300,
            "min_off_seconds": 900 if kind == DEVICE_KIND_FIXED else 60,
            "cooldown_seconds": 60 if kind == DEVICE_KIND_FIXED else 30,
            "max_active_seconds": 14400 if kind == DEVICE_KIND_FIXED else 28800,
            "min_power_w": 1400,
            "max_power_w": 7200,
            "step_w": 100,
        }
        if template_defaults:
            defaults.update(template_defaults)
        if device is None:
            return defaults
        defaults.update(
            {
                "name": device.get("name", defaults["name"]),
                "entity_id": device.get("entity_id", defaults["entity_id"]),
                "nominal_power_w": device.get("nominal_power_w", defaults["nominal_power_w"]),
                "priority": device.get("priority", defaults["priority"]),
                "enabled": device.get("enabled", defaults["enabled"]),
                "min_on_seconds": device.get("min_on_seconds", defaults["min_on_seconds"]),
                "min_off_seconds": device.get("min_off_seconds", defaults["min_off_seconds"]),
                "cooldown_seconds": device.get("cooldown_seconds", defaults["cooldown_seconds"]),
                "max_active_seconds": device.get("max_active_seconds") or 0,
                "min_power_w": device.get("min_power_w", defaults["min_power_w"]),
                "max_power_w": device.get("max_power_w", defaults["max_power_w"]),
                "step_w": device.get("step_w", defaults["step_w"]),
            }
        )
        return defaults

    def _coordinator(self):
        return self.hass.data.get(DOMAIN, {}).get(self._config_entry.entry_id)

    @staticmethod
    def _format_source_role_names(source_keys: list[str]) -> str:
        named_roles = [SOURCE_ROLE_LABELS.get(key, key) for key in source_keys if key]
        return ", ".join(named_roles[:6]) if named_roles else "None"

    def _source_placeholders(
        self,
        *,
        effective_config: dict[str, Any] | None = None,
        grid_mode: str | None = None,
    ) -> dict[str, str]:
        effective = effective_config or {**self._config_entry.data, **self._config_entry.options}
        resolved_grid_mode = grid_mode or _grid_mode_default(self._config_entry)
        missing_source_keys = _grid_mode_missing_sources(effective, resolved_grid_mode)
        coordinator = self._coordinator()
        state = getattr(coordinator, "data", None) if coordinator is not None else None
        readiness = build_native_operator_readiness(coordinator) if coordinator is not None else {}
        validation_details = getattr(state, "validation_details", {}) or {}
        source_diagnostics = validation_details.get("source_diagnostics", {}) or {}
        unavailable_source_keys = [
            key for key, details in source_diagnostics.items() if details.get("status") == "unavailable"
        ]
        stale_source_keys = [
            key for key, details in source_diagnostics.items() if details.get("stale") or (details.get("age_seconds") or 0) > 120
        ]

        missing_sources = self._format_source_role_names(missing_source_keys)
        unavailable_sources = self._format_source_role_names(unavailable_source_keys)
        stale_sources = self._format_source_role_names(stale_source_keys)

        if missing_source_keys:
            source_health = f"Missing required sources: {missing_sources}"
            source_next_step = "Finish the missing required source roles here, then save and reload the integration."
        elif unavailable_source_keys or stale_source_keys:
            issue_parts = []
            if unavailable_source_keys:
                issue_parts.append(f"unavailable: {unavailable_sources}")
            if stale_source_keys:
                issue_parts.append(f"stale: {stale_sources}")
            source_health = "Mapped source roles need attention, " + "; ".join(issue_parts)
            source_next_step = str(
                readiness.get("next_step")
                or "Repair the unavailable or stale mapped source roles, then save and reload the integration."
            )
        elif state is None:
            source_health = "Source health will appear here after the integration loads."
            source_next_step = "Save source mapping, reload the integration, then reopen Configure to confirm live source health."
        else:
            source_health = str(
                readiness.get("summary")
                or state.health_summary
                or state.diagnostic_summary
                or "Mapped sources currently look healthy."
            )
            source_next_step = str(
                readiness.get("next_step") or "Source mapping looks healthy; continue to managed devices or policy."
            )

        return {
            "missing_sources": missing_sources,
            "source_health": source_health,
            "source_next_step": source_next_step,
            "unavailable_sources": unavailable_sources,
            "stale_sources": stale_sources,
        }

    def _support_placeholders(self) -> dict[str, str]:
        coordinator = self._coordinator()
        state = getattr(coordinator, "data", None) if coordinator is not None else None
        readiness = build_native_operator_readiness(coordinator) if coordinator is not None else {}
        health_summary = "Integration state not loaded yet"
        if state is not None:
            health_summary = state.health_summary or state.diagnostic_summary or health_summary
        return {
            "support_status": readiness.get("summary") or health_summary,
            "support_next_step": readiness.get("next_step") or "Open the device page support actions or Repairs to continue troubleshooting.",
            "support_path": "Configure -> Support and troubleshooting; deeper support: integration device page -> Show support center / Show setup checklist / Show native diagnostics snapshot; Settings -> Repairs",
            "readiness_phase": str(readiness.get("phase") or "unknown"),
            "health_status": health_summary,
        }

    async def async_step_init(self, user_input=None):
        effective_config = dict(self._config_entry.data)
        effective_config.update(self._config_entry.options)
        devices, device_issues = self._load_devices()
        grid_mode = _grid_mode_default(self._config_entry)
        source_placeholders = self._source_placeholders(effective_config=effective_config, grid_mode=grid_mode)
        missing_sources = _grid_mode_missing_sources(effective_config, grid_mode)

        if missing_sources:
            source_status = source_placeholders["source_health"]
            recommended_section = "Sources and source mapping"
        else:
            source_status = source_placeholders["source_health"]
            recommended_section = "Managed devices" if not devices else "Policy and controller settings"

        if device_issues:
            device_status = f"{len(devices)} configured, with {len(device_issues)} issue(s) to repair"
            recommended_section = "Managed devices"
        elif devices:
            device_status = f"{len(devices)} configured"
        else:
            device_status = "No managed devices configured yet"
            if not missing_sources:
                recommended_section = "Managed devices"

        next_action_summary = "Open Sources and source mapping first to finish required entity mapping."
        if missing_sources:
            next_action_summary = "Finish source mapping first, then return here to add devices and tune policy."
        elif device_issues:
            next_action_summary = "Repair the managed-device configuration next so control actions can be trusted."
        elif not devices:
            next_action_summary = "Add at least one managed device next so Zero Net Export has a controllable load."
        else:
            next_action_summary = "Sources and devices are in place, so policy tuning or support review are the next useful steps."

        placeholders = {
            "configure_path": PRIMARY_CONFIGURE_PATH,
            "source_status": source_status,
            "device_status": device_status,
            "policy_status": (
                f"Target {int(_entry_default_number(self._config_entry, CONF_TARGET_EXPORT_W, DEFAULT_TARGET_EXPORT_W))} W, "
                f"deadband {int(_entry_default_number(self._config_entry, CONF_DEADBAND_W, DEFAULT_DEADBAND_W))} W, "
                f"battery reserve {int(_entry_default_number(self._config_entry, CONF_BATTERY_RESERVE_SOC, DEFAULT_BATTERY_RESERVE_SOC))}%"
            ),
            "recommended_section": recommended_section,
            "next_action_summary": next_action_summary,
        }
        placeholders.update(self._support_placeholders())

        return self.async_show_menu(
            step_id="init",
            menu_options=["native_setup", "policy", "devices", "support", "advanced"],
            description_placeholders=placeholders,
        )

    async def async_step_native_setup(self, user_input=None):
        current_mode = self._pending_grid_sensor_mode or _grid_mode_default(self._config_entry)
        if user_input is not None:
            self._pending_grid_sensor_mode = user_input[CONF_GRID_SENSOR_MODE]
            return await self.async_step_native_setup_sources()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_GRID_SENSOR_MODE,
                    default=current_mode,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(value=GRID_SENSOR_MODE_COMBINED, label="Combined / net sensors"),
                            selector.SelectOptionDict(value=GRID_SENSOR_MODE_SEPARATE, label="Separate import and export sensors"),
                        ],
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )

        effective_config = dict(self._config_entry.data)
        effective_config.update(self._config_entry.options)
        source_placeholders = self._source_placeholders(effective_config=effective_config, grid_mode=current_mode)
        return self.async_show_form(
            step_id="native_setup",
            data_schema=schema,
            errors={},
            description_placeholders={
                "configure_path": PRIMARY_CONFIGURE_PATH,
                **source_placeholders,
            },
        )

    async def async_step_native_setup_sources(self, user_input=None):
        errors: dict[str, str] = {}
        grid_mode = self._pending_grid_sensor_mode or _grid_mode_default(self._config_entry)

        if user_input is not None:
            merged_data = dict(self._config_entry.data)
            merged_options = dict(self._config_entry.options)

            merged_data[CONF_SOLAR_POWER_ENTITY] = _normalize_entity_selector_input(user_input, CONF_SOLAR_POWER_ENTITY)
            merged_data[CONF_SOLAR_ENERGY_ENTITY] = _normalize_entity_selector_input(user_input, CONF_SOLAR_ENERGY_ENTITY)
            merged_data[CONF_HOME_LOAD_POWER_ENTITY] = _normalize_entity_selector_input(user_input, CONF_HOME_LOAD_POWER_ENTITY)
            merged_data[CONF_BATTERY_SOC_ENTITY] = (
                _normalize_entity_selector_input(user_input, BATTERY_SOC_FALLBACK_KEY)
                or _normalize_entity_selector_input(user_input, CONF_BATTERY_SOC_ENTITY)
            )
            merged_data[CONF_BATTERY_CHARGE_POWER_ENTITY] = _normalize_entity_selector_input(user_input, CONF_BATTERY_CHARGE_POWER_ENTITY)
            merged_data[CONF_BATTERY_DISCHARGE_POWER_ENTITY] = _normalize_entity_selector_input(user_input, CONF_BATTERY_DISCHARGE_POWER_ENTITY)

            if grid_mode == GRID_SENSOR_MODE_COMBINED:
                combined_power = _normalize_entity_selector_input(user_input, "grid_power_entity")
                combined_energy = (
                    _normalize_entity_selector_input(user_input, COMBINED_GRID_ENERGY_FALLBACK_KEY)
                    or _normalize_entity_selector_input(user_input, "grid_energy_entity")
                )
                merged_data[CONF_GRID_IMPORT_POWER_ENTITY] = _build_derived_binding(DERIVED_SOURCE_MODE_POSITIVE, combined_power)
                merged_data[CONF_GRID_EXPORT_POWER_ENTITY] = _build_derived_binding(DERIVED_SOURCE_MODE_NEGATIVE_ABS, combined_power)
                merged_data[CONF_GRID_IMPORT_ENERGY_ENTITY] = _build_derived_binding(DERIVED_SOURCE_MODE_POSITIVE, combined_energy)
                merged_data[CONF_GRID_EXPORT_ENERGY_ENTITY] = _build_derived_binding(DERIVED_SOURCE_MODE_NEGATIVE_ABS, combined_energy)
            else:
                merged_data[CONF_GRID_IMPORT_POWER_ENTITY] = _normalize_entity_selector_input(user_input, CONF_GRID_IMPORT_POWER_ENTITY)
                merged_data[CONF_GRID_EXPORT_POWER_ENTITY] = _normalize_entity_selector_input(user_input, CONF_GRID_EXPORT_POWER_ENTITY)
                merged_data[CONF_GRID_IMPORT_ENERGY_ENTITY] = _normalize_entity_selector_input(user_input, CONF_GRID_IMPORT_ENERGY_ENTITY)
                merged_data[CONF_GRID_EXPORT_ENERGY_ENTITY] = _normalize_entity_selector_input(user_input, CONF_GRID_EXPORT_ENERGY_ENTITY)

            merged_options[CONF_GRID_SENSOR_MODE] = grid_mode
            merged_options[CONF_REFRESH_SECONDS] = int(
                _coerce_number(user_input.get(CONF_REFRESH_SECONDS), DEFAULT_REFRESH_SECONDS)
            )

            issues = validate_configured_entities(
                self.hass,
                merged_data,
                _source_specs_from_config(merged_data),
            )
            blocking_issues = [issue.message for issue in issues if issue.severity == "error"]
            if blocking_issues:
                errors["base"] = "source_entities_invalid"
            else:
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data=merged_data,
                    options=merged_options,
                )
                await self.hass.config_entries.async_reload(self._config_entry.entry_id)
                self._pending_grid_sensor_mode = None
                return self.async_create_entry(title="", data=merged_options)

        grid_import_power_raw = _entry_default_text(self._config_entry, CONF_GRID_IMPORT_POWER_ENTITY, "")
        grid_import_energy_raw = _entry_default_text(self._config_entry, CONF_GRID_IMPORT_ENERGY_ENTITY, "")

        power_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor"], device_class=["power"])
        )
        energy_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor"], device_class=["energy"])
        )
        battery_soc_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor"], device_class=["battery"])
        )

        fields: dict[Any, Any] = {
            vol.Required(
                CONF_SOLAR_POWER_ENTITY,
                default=_entry_default_text(self._config_entry, CONF_SOLAR_POWER_ENTITY, ""),
            ): power_selector,
            vol.Required(
                CONF_SOLAR_ENERGY_ENTITY,
                default=_entry_default_text(self._config_entry, CONF_SOLAR_ENERGY_ENTITY, ""),
            ): energy_selector,
        }
        if grid_mode == GRID_SENSOR_MODE_COMBINED:
            fields[
                vol.Required(
                    "grid_power_entity",
                    default=_selector_entity_default(grid_import_power_raw, allow_derived=True),
                )
            ] = power_selector
            fields[
                vol.Required(
                    "grid_energy_entity",
                    default=_selector_entity_default(grid_import_energy_raw, allow_derived=True),
                )
            ] = energy_selector
            fields[
                vol.Optional(
                    COMBINED_GRID_ENERGY_FALLBACK_KEY,
                    default="",
                )
            ] = selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            )
        else:
            fields[
                vol.Required(
                    CONF_GRID_IMPORT_POWER_ENTITY,
                    default=_selector_entity_default(_entry_default_text(self._config_entry, CONF_GRID_IMPORT_POWER_ENTITY, "")),
                )
            ] = power_selector
            fields[
                vol.Required(
                    CONF_GRID_EXPORT_POWER_ENTITY,
                    default=_selector_entity_default(_entry_default_text(self._config_entry, CONF_GRID_EXPORT_POWER_ENTITY, "")),
                )
            ] = power_selector
            fields[
                vol.Required(
                    CONF_GRID_IMPORT_ENERGY_ENTITY,
                    default=_selector_entity_default(_entry_default_text(self._config_entry, CONF_GRID_IMPORT_ENERGY_ENTITY, "")),
                )
            ] = energy_selector
            fields[
                vol.Required(
                    CONF_GRID_EXPORT_ENERGY_ENTITY,
                    default=_selector_entity_default(_entry_default_text(self._config_entry, CONF_GRID_EXPORT_ENERGY_ENTITY, "")),
                )
            ] = energy_selector
        fields[
            vol.Optional(
                CONF_HOME_LOAD_POWER_ENTITY,
                default=_entry_default_text(self._config_entry, CONF_HOME_LOAD_POWER_ENTITY, ""),
            )
        ] = power_selector
        fields[
            vol.Optional(
                CONF_BATTERY_SOC_ENTITY,
                default=_entry_default_text(self._config_entry, CONF_BATTERY_SOC_ENTITY, ""),
            )
        ] = battery_soc_selector
        fields[
            vol.Optional(
                BATTERY_SOC_FALLBACK_KEY,
                default="",
            )
        ] = selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        )
        fields[
            vol.Optional(
                CONF_BATTERY_CHARGE_POWER_ENTITY,
                default=_entry_default_text(self._config_entry, CONF_BATTERY_CHARGE_POWER_ENTITY, ""),
            )
        ] = power_selector
        fields[
            vol.Optional(
                CONF_BATTERY_DISCHARGE_POWER_ENTITY,
                default=_entry_default_text(self._config_entry, CONF_BATTERY_DISCHARGE_POWER_ENTITY, ""),
            )
        ] = power_selector
        fields[
            vol.Required(
                CONF_REFRESH_SECONDS,
                default=_entry_default_number(
                    self._config_entry,
                    CONF_REFRESH_SECONDS,
                    DEFAULT_REFRESH_SECONDS,
                ),
            )
        ] = selector.NumberSelector(
            selector.NumberSelectorConfig(min=5, max=300, step=5, mode=selector.NumberSelectorMode.BOX)
        )

        schema = vol.Schema(fields)

        effective_config = dict(self._config_entry.data)
        effective_config.update(self._config_entry.options)
        source_placeholders = self._source_placeholders(effective_config=effective_config, grid_mode=grid_mode)
        fallback_guidance = (
            "If Home Assistant rejects a valid combined grid energy or battery SOC picker choice, leave the selector as-is and paste the same entity ID into the matching fallback field below."
        )
        return self.async_show_form(
            step_id="native_setup_sources",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "grid_mode": "Combined / net sensors" if grid_mode == GRID_SENSOR_MODE_COMBINED else "Separate import and export sensors",
                "configure_path": PRIMARY_CONFIGURE_PATH,
                "fallback_guidance": fallback_guidance,
                **source_placeholders,
            },
        )

    async def async_step_devices(self, user_input=None):
        devices, issues = self._load_devices()
        if user_input is not None:
            choice = user_input.get("device_action")
            if choice == "add_fixed":
                self._pending_device_kind = DEVICE_KIND_FIXED
                self._pending_device_key = None
                self._pending_device_template_key = None
                return await self.async_step_device_template()
            if choice == "add_variable":
                self._pending_device_kind = DEVICE_KIND_VARIABLE
                self._pending_device_key = None
                self._pending_device_template_key = None
                return await self.async_step_device_template()
            if choice == "bulk_enable" and devices:
                return await self.async_step_device_bulk_enable()
            if choice == "edit" and devices:
                return await self.async_step_device_edit_pick()
            if choice == "remove" and devices:
                return await self.async_step_device_remove()
            if choice == "json":
                return await self.async_step_devices_json()

        choices = [
            selector.SelectOptionDict(value="add_fixed", label="Add fixed load device"),
            selector.SelectOptionDict(value="add_variable", label="Add variable load device"),
        ]
        if devices:
            choices.append(selector.SelectOptionDict(value="bulk_enable", label="Review fleet / enable or disable devices"))
            choices.append(selector.SelectOptionDict(value="edit", label="Edit configured device"))
            choices.append(selector.SelectOptionDict(value="remove", label="Remove configured device"))
        choices.append(selector.SelectOptionDict(value="json", label="Advanced JSON editor / recovery"))
        summary = "\n".join(self._fleet_summary_lines(devices))
        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(
                {
                    vol.Required("device_action"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=choices, mode=selector.SelectSelectorMode.LIST)
                    )
                }
            ),
            errors={"base": "device_inventory_invalid"} if issues else {},
            description_placeholders={
                "configure_path": PRIMARY_CONFIGURE_PATH,
                "device_count": str(len(devices)),
                "device_summary": summary,
                "device_issues": "\n".join(f"- {issue}" for issue in issues[:6]) if issues else "None",
            },
        )

    async def async_step_device_template(self, user_input=None):
        kind = self._pending_device_kind or DEVICE_KIND_FIXED
        templates = get_device_templates(kind)
        if user_input is not None:
            self._pending_device_template_key = user_input.get("device_template")
            return await self.async_step_device_add()

        options = [
            selector.SelectOptionDict(value=template.key, label=template.label)
            for template in templates
        ]
        return self.async_show_form(
            step_id="device_template",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "device_template",
                        default=self._pending_device_template_key or (templates[0].key if templates else ""),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.LIST)
                    )
                }
            ),
            errors={},
            description_placeholders={
                "device_kind": "fixed load" if kind == DEVICE_KIND_FIXED else "variable load",
                "template_summary": "\n".join(
                    f"- {template.label}: {template.description}" for template in templates
                ),
            },
        )

    async def async_step_device_add(self, user_input=None):
        errors: dict[str, str] = {}
        kind = self._pending_device_kind or DEVICE_KIND_FIXED
        editing_key = self._pending_device_key
        devices, _ = self._load_devices()
        existing_device = next((device for device in devices if device.get("key") == editing_key), None)

        if editing_key and existing_device is None:
            return await self.async_step_devices()

        if user_input is not None:
            new_device = self._build_device_payload(user_input, kind, key=editing_key)
            candidate_devices = [
                new_device if editing_key and device.get("key") == editing_key else device for device in devices
            ]
            if not editing_key:
                candidate_devices.append(new_device)
            raw_inventory = _device_options_json(candidate_devices)
            _, device_issues = parse_device_configs(raw_inventory)
            if device_issues:
                errors["base"] = "device_inventory_invalid"
            else:
                self._pending_device_key = None
                self._pending_device_template_key = None
                return await self._save_devices(candidate_devices)

        selected_template = get_device_template(kind, self._pending_device_template_key)
        defaults = self._device_form_defaults(
            existing_device,
            kind,
            template_defaults=selected_template.defaults if selected_template and not editing_key else None,
        )
        entity_domain = ["switch", "input_boolean", "light"] if kind == DEVICE_KIND_FIXED else ["number", "input_number"]
        schema_dict: dict[Any, Any] = {
            vol.Required("name", default=defaults["name"]): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            ),
            vol.Required("entity_id", default=defaults["entity_id"]): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=entity_domain)
            ),
            vol.Required("nominal_power_w", default=defaults["nominal_power_w"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=50000, step=10, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("priority", default=defaults["priority"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=1000, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("enabled", default=defaults["enabled"]): selector.BooleanSelector(),
            vol.Required("min_on_seconds", default=defaults["min_on_seconds"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=86400, step=30, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("min_off_seconds", default=defaults["min_off_seconds"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=86400, step=30, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("cooldown_seconds", default=defaults["cooldown_seconds"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=3600, step=5, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("max_active_seconds", default=defaults["max_active_seconds"]): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=172800, step=60, mode=selector.NumberSelectorMode.BOX)
            ),
        }
        if kind == DEVICE_KIND_VARIABLE:
            schema_dict.update(
                {
                    vol.Required("min_power_w", default=defaults["min_power_w"]): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=50000, step=10, mode=selector.NumberSelectorMode.BOX)
                    ),
                    vol.Required("max_power_w", default=defaults["max_power_w"]): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=50000, step=10, mode=selector.NumberSelectorMode.BOX)
                    ),
                    vol.Required("step_w", default=defaults["step_w"]): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=5000, step=10, mode=selector.NumberSelectorMode.BOX)
                    ),
                }
            )

        return self.async_show_form(
            step_id="device_add",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
            description_placeholders={
                "device_kind": "fixed load" if kind == DEVICE_KIND_FIXED else "variable load",
                "configure_path": PRIMARY_CONFIGURE_PATH,
                "device_mode": "Edit" if editing_key else "Add",
                "device_template": selected_template.label if selected_template else "Custom",
                "template_description": selected_template.description if selected_template else "Use manual values for this device.",
            },
        )

    async def async_step_device_bulk_enable(self, user_input=None):
        devices, _ = self._load_devices()
        if not devices:
            return await self.async_step_devices()

        enabled_keys = [device["key"] for device in devices if device.get("enabled", True)]
        if user_input is not None:
            selected_keys = {str(key) for key in user_input.get("enabled_devices", [])}
            updated_devices = [
                {**device, "enabled": device.get("key") in selected_keys}
                for device in devices
            ]
            return await self._save_devices(updated_devices)

        options = [
            selector.SelectOptionDict(value=device["key"], label=self._device_status_label(device))
            for device in sorted(devices, key=lambda item: str(item.get("name", "")).lower())
        ]
        return self.async_show_form(
            step_id="device_bulk_enable",
            data_schema=vol.Schema(
                {
                    vol.Required("enabled_devices", default=enabled_keys): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors={},
            description_placeholders={
                "device_summary": "\n".join(self._fleet_summary_lines(devices)),
                "enabled_count": str(len(enabled_keys)),
                "device_count": str(len(devices)),
            },
        )

    async def async_step_device_edit_pick(self, user_input=None):
        devices, _ = self._load_devices()
        if user_input is not None:
            selected_key = user_input["device_key"]
            selected_device = next((device for device in devices if device.get("key") == selected_key), None)
            if selected_device is None:
                return await self.async_step_devices()
            self._pending_device_key = selected_key
            self._pending_device_kind = str(selected_device.get("kind", DEVICE_KIND_FIXED))
            self._pending_device_template_key = None
            return await self.async_step_device_add()

        options = [
            selector.SelectOptionDict(value=device["key"], label=self._device_status_label(device))
            for device in devices
        ]
        return self.async_show_form(
            step_id="device_edit_pick",
            data_schema=vol.Schema(
                {
                    vol.Required("device_key"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
                    )
                }
            ),
            errors={},
        )

    async def async_step_device_remove(self, user_input=None):
        devices, _ = self._load_devices()
        if user_input is not None:
            remove_name = user_input["device_key"]
            remaining = [device for device in devices if device.get("key") != remove_name]
            return await self._save_devices(remaining)

        options = [
            selector.SelectOptionDict(value=device["key"], label=self._device_status_label(device))
            for device in devices
        ]
        return self.async_show_form(
            step_id="device_remove",
            data_schema=vol.Schema(
                {
                    vol.Required("device_key"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
                    )
                }
            ),
            errors={},
        )

    async def async_step_devices_json(self, user_input=None):
        errors = {}
        description_placeholders = {
            "device_blueprint": default_device_blueprint(),
            "configure_path": PRIMARY_CONFIGURE_PATH,
            "device_issues": "",
        }

        if user_input is not None:
            raw_inventory = user_input.get(CONF_DEVICE_INVENTORY_JSON)
            _, device_issues = parse_device_configs(raw_inventory)
            if device_issues:
                errors["base"] = "device_inventory_invalid"
                description_placeholders["device_issues"] = "\n".join(
                    f"- {issue}" for issue in device_issues[:6]
                )
            else:
                merged_options = dict(self._config_entry.options)
                merged_options[CONF_DEVICE_INVENTORY_JSON] = _coerce_text(
                    raw_inventory,
                    DEFAULT_DEVICE_INVENTORY_JSON,
                )
                self.hass.config_entries.async_update_entry(self._config_entry, options=merged_options)
                await self.hass.config_entries.async_reload(self._config_entry.entry_id)
                return self.async_create_entry(title="", data=merged_options)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_DEVICE_INVENTORY_JSON,
                    default=_entry_default_text(
                        self._config_entry,
                        CONF_DEVICE_INVENTORY_JSON,
                        DEFAULT_DEVICE_INVENTORY_JSON,
                    ),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        multiline=True,
                        type=selector.TextSelectorType.TEXT,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="devices_json",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    async def async_step_policy(self, user_input=None):
        errors = {}

        if user_input is not None:
            merged_options = dict(self._config_entry.options)
            merged_options.update(user_input)
            self.hass.config_entries.async_update_entry(self._config_entry, options=merged_options)
            await self.hass.config_entries.async_reload(self._config_entry.entry_id)
            return self.async_create_entry(title="", data=merged_options)

        effective_config = dict(self._config_entry.data)
        effective_config.update(self._config_entry.options)
        devices, device_issues = self._load_devices()
        grid_mode = _grid_mode_default(self._config_entry)
        missing_sources = _grid_mode_missing_sources(effective_config, grid_mode)
        if missing_sources:
            policy_readiness = "Finish source mapping first: " + ", ".join(missing_sources)
        elif device_issues:
            policy_readiness = f"Managed-device issues still need repair before policy tuning can be trusted ({len(device_issues)} issue(s))."
        elif not devices:
            policy_readiness = "No managed devices are configured yet. You can tune policy now, but control will not act until devices are added."
        else:
            policy_readiness = f"Sources are mapped and {len(devices)} managed device(s) are configured, so policy changes are actionable now."

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_TARGET_EXPORT_W,
                    default=_entry_default_number(
                        self._config_entry,
                        CONF_TARGET_EXPORT_W,
                        DEFAULT_TARGET_EXPORT_W,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=-5000, max=10000, step=10, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_DEADBAND_W,
                    default=_entry_default_number(
                        self._config_entry,
                        CONF_DEADBAND_W,
                        DEFAULT_DEADBAND_W,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=2000, step=10, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_BATTERY_RESERVE_SOC,
                    default=_entry_default_number(
                        self._config_entry,
                        CONF_BATTERY_RESERVE_SOC,
                        DEFAULT_BATTERY_RESERVE_SOC,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_REFRESH_SECONDS,
                    default=_entry_default_number(
                        self._config_entry,
                        CONF_REFRESH_SECONDS,
                        DEFAULT_REFRESH_SECONDS,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=300, step=5, mode=selector.NumberSelectorMode.BOX)
                ),
            }
        )
        return self.async_show_form(
            step_id="policy",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "configure_path": PRIMARY_CONFIGURE_PATH,
                "policy_readiness": policy_readiness,
            },
        )

    async def async_step_support(self, user_input=None):
        if user_input is not None:
            return await self.async_step_init()

        return self.async_show_form(
            step_id="support",
            data_schema=vol.Schema({}),
            errors={},
            description_placeholders={
                "configure_path": PRIMARY_CONFIGURE_PATH,
                **self._support_placeholders(),
            },
        )

    async def async_step_advanced(self, user_input=None):
        return await self.async_step_devices_json(user_input)
