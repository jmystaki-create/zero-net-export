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
    CONF_HOME_LOAD_POWER_ENTITY,
    CONF_NAME,
    CONF_REFRESH_SECONDS,
    CONF_SOLAR_ENERGY_ENTITY,
    CONF_SOLAR_POWER_ENTITY,
    CONF_TARGET_EXPORT_W,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_DEADBAND_W,
    DEFAULT_DEVICE_INVENTORY_JSON,
    DEFAULT_NAME,
    DEFAULT_REFRESH_SECONDS,
    DEFAULT_TARGET_EXPORT_W,
    DOMAIN,
    REQUIRED_SOURCE_KEYS,
    SOURCE_ROLE_LABELS,
)
from .device_model import (
    ADAPTER_FIXED_TOGGLE,
    ADAPTER_VARIABLE_NUMBER,
    DEVICE_KIND_FIXED,
    DEVICE_KIND_VARIABLE,
    default_device_blueprint,
    parse_device_configs,
)
from .native_support import PRIMARY_CONFIGURE_PATH, _source_specs_from_config
from .validation import validate_configured_entities

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
        self._pending_device_kind: str | None = None

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

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init",
            menu_options=["native_setup", "devices", "advanced"],
        )

    async def async_step_native_setup(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            merged_data = dict(self._config_entry.data)
            merged_options = dict(self._config_entry.options)

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
                merged_data[key] = user_input.get(key) or None

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
                return self.async_create_entry(title="", data=merged_options)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SOLAR_POWER_ENTITY,
                    default=_entry_default_text(self._config_entry, CONF_SOLAR_POWER_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(
                    CONF_SOLAR_ENERGY_ENTITY,
                    default=_entry_default_text(self._config_entry, CONF_SOLAR_ENERGY_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(
                    CONF_GRID_IMPORT_POWER_ENTITY,
                    default=_entry_default_text(self._config_entry, CONF_GRID_IMPORT_POWER_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(
                    CONF_GRID_EXPORT_POWER_ENTITY,
                    default=_entry_default_text(self._config_entry, CONF_GRID_EXPORT_POWER_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(
                    CONF_GRID_IMPORT_ENERGY_ENTITY,
                    default=_entry_default_text(self._config_entry, CONF_GRID_IMPORT_ENERGY_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(
                    CONF_GRID_EXPORT_ENERGY_ENTITY,
                    default=_entry_default_text(self._config_entry, CONF_GRID_EXPORT_ENERGY_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Required(
                    CONF_HOME_LOAD_POWER_ENTITY,
                    default=_entry_default_text(self._config_entry, CONF_HOME_LOAD_POWER_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Optional(
                    CONF_BATTERY_SOC_ENTITY,
                    default=_entry_default_text(self._config_entry, CONF_BATTERY_SOC_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Optional(
                    CONF_BATTERY_CHARGE_POWER_ENTITY,
                    default=_entry_default_text(self._config_entry, CONF_BATTERY_CHARGE_POWER_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
                ),
                vol.Optional(
                    CONF_BATTERY_DISCHARGE_POWER_ENTITY,
                    default=_entry_default_text(self._config_entry, CONF_BATTERY_DISCHARGE_POWER_ENTITY, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor"])
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

        missing_sources = [
            SOURCE_ROLE_LABELS.get(key, key)
            for key in REQUIRED_SOURCE_KEYS
            if not self._config_entry.options.get(key, self._config_entry.data.get(key))
        ]
        return self.async_show_form(
            step_id="native_setup",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "missing_sources": ", ".join(missing_sources) if missing_sources else "None",
                "configure_path": PRIMARY_CONFIGURE_PATH,
            },
        )

    async def async_step_devices(self, user_input=None):
        devices, issues = self._load_devices()
        if user_input is not None:
            choice = user_input.get("device_action")
            if choice == "add_fixed":
                self._pending_device_kind = DEVICE_KIND_FIXED
                return await self.async_step_device_add()
            if choice == "add_variable":
                self._pending_device_kind = DEVICE_KIND_VARIABLE
                return await self.async_step_device_add()
            if choice == "remove" and devices:
                return await self.async_step_device_remove()
            if choice == "json":
                return await self.async_step_devices_json()

        choices = [
            selector.SelectOptionDict(value="add_fixed", label="Add fixed load device"),
            selector.SelectOptionDict(value="add_variable", label="Add variable load device"),
        ]
        if devices:
            choices.append(selector.SelectOptionDict(value="remove", label="Remove configured device"))
        choices.append(selector.SelectOptionDict(value="json", label="Advanced JSON editor / recovery"))
        summary = ", ".join(f"{item['name']} ({item['kind']})" for item in devices[:5]) if devices else "None"
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

    async def async_step_device_add(self, user_input=None):
        errors: dict[str, str] = {}
        kind = self._pending_device_kind or DEVICE_KIND_FIXED

        if user_input is not None:
            devices, _ = self._load_devices()
            name = str(user_input["name"]).strip()
            new_device = {
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
            if kind == DEVICE_KIND_FIXED:
                new_device["min_power_w"] = new_device["nominal_power_w"]
                new_device["max_power_w"] = new_device["nominal_power_w"]
                new_device["step_w"] = new_device["nominal_power_w"]
            else:
                new_device["min_power_w"] = float(user_input["min_power_w"])
                new_device["max_power_w"] = float(user_input["max_power_w"])
                new_device["step_w"] = float(user_input["step_w"])

            candidate_devices = [*devices, new_device]
            raw_inventory = _device_options_json(candidate_devices)
            _, device_issues = parse_device_configs(raw_inventory)
            if device_issues:
                errors["base"] = "device_inventory_invalid"
            else:
                return await self._save_devices(candidate_devices)

        entity_domain = ["switch", "input_boolean"] if kind == DEVICE_KIND_FIXED else ["number", "input_number"]
        schema_dict: dict[Any, Any] = {
            vol.Required("name"): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)),
            vol.Required("entity_id"): selector.EntitySelector(selector.EntitySelectorConfig(domain=entity_domain)),
            vol.Required("nominal_power_w", default=2400 if kind == DEVICE_KIND_FIXED else 3600): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=50000, step=10, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("priority", default=100): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=1000, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("enabled", default=True): selector.BooleanSelector(),
            vol.Required("min_on_seconds", default=900 if kind == DEVICE_KIND_FIXED else 300): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=86400, step=30, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("min_off_seconds", default=900 if kind == DEVICE_KIND_FIXED else 60): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=86400, step=30, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("cooldown_seconds", default=60 if kind == DEVICE_KIND_FIXED else 30): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=3600, step=5, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required("max_active_seconds", default=14400 if kind == DEVICE_KIND_FIXED else 28800): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=172800, step=60, mode=selector.NumberSelectorMode.BOX)
            ),
        }
        if kind == DEVICE_KIND_VARIABLE:
            schema_dict.update(
                {
                    vol.Required("min_power_w", default=1400): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=50000, step=10, mode=selector.NumberSelectorMode.BOX)
                    ),
                    vol.Required("max_power_w", default=7200): selector.NumberSelector(
                        selector.NumberSelectorConfig(min=1, max=50000, step=10, mode=selector.NumberSelectorMode.BOX)
                    ),
                    vol.Required("step_w", default=100): selector.NumberSelector(
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
            },
        )

    async def async_step_device_remove(self, user_input=None):
        devices, _ = self._load_devices()
        if user_input is not None:
            remove_name = user_input["device_key"]
            remaining = [device for device in devices if device.get("key") != remove_name]
            return await self._save_devices(remaining)

        options = [
            selector.SelectOptionDict(value=device["key"], label=f"{device['name']} ({device['kind']})")
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

    async def async_step_advanced(self, user_input=None):
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

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
            step_id="advanced",
            data_schema=schema,
            errors=errors,
        )
