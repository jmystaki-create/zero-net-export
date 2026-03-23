"""Config flow for Zero Net Export."""
from __future__ import annotations

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
)
from .device_model import default_device_blueprint, parse_device_configs
from .validation import SourceSpec, validate_configured_entities


def _source_specs_from_input(user_input: dict) -> list[SourceSpec]:
    return [
        SourceSpec(CONF_SOLAR_POWER_ENTITY, user_input.get(CONF_SOLAR_POWER_ENTITY), "power"),
        SourceSpec(CONF_SOLAR_ENERGY_ENTITY, user_input.get(CONF_SOLAR_ENERGY_ENTITY), "energy"),
        SourceSpec(CONF_GRID_IMPORT_POWER_ENTITY, user_input.get(CONF_GRID_IMPORT_POWER_ENTITY), "power"),
        SourceSpec(CONF_GRID_EXPORT_POWER_ENTITY, user_input.get(CONF_GRID_EXPORT_POWER_ENTITY), "power"),
        SourceSpec(CONF_GRID_IMPORT_ENERGY_ENTITY, user_input.get(CONF_GRID_IMPORT_ENERGY_ENTITY), "energy"),
        SourceSpec(CONF_GRID_EXPORT_ENERGY_ENTITY, user_input.get(CONF_GRID_EXPORT_ENERGY_ENTITY), "energy"),
        SourceSpec(CONF_HOME_LOAD_POWER_ENTITY, user_input.get(CONF_HOME_LOAD_POWER_ENTITY), "power"),
        SourceSpec(CONF_BATTERY_SOC_ENTITY, user_input.get(CONF_BATTERY_SOC_ENTITY), "percent", required=False),
        SourceSpec(CONF_BATTERY_CHARGE_POWER_ENTITY, user_input.get(CONF_BATTERY_CHARGE_POWER_ENTITY), "power", required=False),
        SourceSpec(CONF_BATTERY_DISCHARGE_POWER_ENTITY, user_input.get(CONF_BATTERY_DISCHARGE_POWER_ENTITY), "power", required=False),
    ]


def _entity_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=["sensor"],
        )
    )


def _build_schema(defaults: dict | None = None) -> vol.Schema:
    defaults = defaults or {}

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_SOLAR_POWER_ENTITY, default=defaults.get(CONF_SOLAR_POWER_ENTITY, vol.UNDEFINED)): _entity_selector(),
            vol.Required(CONF_SOLAR_ENERGY_ENTITY, default=defaults.get(CONF_SOLAR_ENERGY_ENTITY, vol.UNDEFINED)): _entity_selector(),
            vol.Required(CONF_GRID_IMPORT_POWER_ENTITY, default=defaults.get(CONF_GRID_IMPORT_POWER_ENTITY, vol.UNDEFINED)): _entity_selector(),
            vol.Required(CONF_GRID_EXPORT_POWER_ENTITY, default=defaults.get(CONF_GRID_EXPORT_POWER_ENTITY, vol.UNDEFINED)): _entity_selector(),
            vol.Required(CONF_GRID_IMPORT_ENERGY_ENTITY, default=defaults.get(CONF_GRID_IMPORT_ENERGY_ENTITY, vol.UNDEFINED)): _entity_selector(),
            vol.Required(CONF_GRID_EXPORT_ENERGY_ENTITY, default=defaults.get(CONF_GRID_EXPORT_ENERGY_ENTITY, vol.UNDEFINED)): _entity_selector(),
            vol.Required(CONF_HOME_LOAD_POWER_ENTITY, default=defaults.get(CONF_HOME_LOAD_POWER_ENTITY, vol.UNDEFINED)): _entity_selector(),
            vol.Optional(CONF_BATTERY_SOC_ENTITY, default=defaults.get(CONF_BATTERY_SOC_ENTITY, vol.UNDEFINED)): _entity_selector(),
            vol.Optional(CONF_BATTERY_CHARGE_POWER_ENTITY, default=defaults.get(CONF_BATTERY_CHARGE_POWER_ENTITY, vol.UNDEFINED)): _entity_selector(),
            vol.Optional(CONF_BATTERY_DISCHARGE_POWER_ENTITY, default=defaults.get(CONF_BATTERY_DISCHARGE_POWER_ENTITY, vol.UNDEFINED)): _entity_selector(),
            vol.Required(CONF_TARGET_EXPORT_W, default=defaults.get(CONF_TARGET_EXPORT_W, DEFAULT_TARGET_EXPORT_W)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-5000, max=10000, step=10, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_DEADBAND_W, default=defaults.get(CONF_DEADBAND_W, DEFAULT_DEADBAND_W)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=2000, step=10, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_BATTERY_RESERVE_SOC, default=defaults.get(CONF_BATTERY_RESERVE_SOC, DEFAULT_BATTERY_RESERVE_SOC)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_REFRESH_SECONDS, default=defaults.get(CONF_REFRESH_SECONDS, DEFAULT_REFRESH_SECONDS)): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=300, step=5, mode=selector.NumberSelectorMode.BOX)
            ),
        }
    )


class ZeroNetExportConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        description_placeholders = {}

        if user_input is not None:
            issues = validate_configured_entities(
                self.hass,
                user_input,
                _source_specs_from_input(user_input),
            )
            blocking_issues = [issue for issue in issues if issue.severity == "error"]
            if blocking_issues:
                errors["base"] = "source_validation_failed"
                description_placeholders["issues"] = "\n".join(
                    f"- {issue.message}" for issue in blocking_issues[:6]
                )
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input),
            errors=errors,
            description_placeholders=description_placeholders,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ZeroNetExportOptionsFlow(config_entry)


class ZeroNetExportOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        description_placeholders = {
            "device_blueprint": default_device_blueprint(),
        }

        if user_input is not None:
            _, device_issues = parse_device_configs(user_input.get(CONF_DEVICE_INVENTORY_JSON))
            if device_issues:
                errors["base"] = "device_inventory_invalid"
                description_placeholders["device_issues"] = "\n".join(
                    f"- {issue}" for issue in device_issues[:6]
                )
            else:
                return self.async_create_entry(title="", data=user_input)
        else:
            description_placeholders["device_issues"] = ""

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_TARGET_EXPORT_W,
                    default=self.config_entry.options.get(CONF_TARGET_EXPORT_W, self.config_entry.data.get(CONF_TARGET_EXPORT_W, DEFAULT_TARGET_EXPORT_W)),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=-5000, max=10000, step=10, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_DEADBAND_W,
                    default=self.config_entry.options.get(CONF_DEADBAND_W, self.config_entry.data.get(CONF_DEADBAND_W, DEFAULT_DEADBAND_W)),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=2000, step=10, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_BATTERY_RESERVE_SOC,
                    default=self.config_entry.options.get(CONF_BATTERY_RESERVE_SOC, self.config_entry.data.get(CONF_BATTERY_RESERVE_SOC, DEFAULT_BATTERY_RESERVE_SOC)),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_REFRESH_SECONDS,
                    default=self.config_entry.options.get(CONF_REFRESH_SECONDS, self.config_entry.data.get(CONF_REFRESH_SECONDS, DEFAULT_REFRESH_SECONDS)),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=300, step=5, mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_DEVICE_INVENTORY_JSON,
                    default=self.config_entry.options.get(
                        CONF_DEVICE_INVENTORY_JSON,
                        self.config_entry.data.get(CONF_DEVICE_INVENTORY_JSON, DEFAULT_DEVICE_INVENTORY_JSON),
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
            step_id="init",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )
