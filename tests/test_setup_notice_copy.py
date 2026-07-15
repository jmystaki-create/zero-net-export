import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export" / "__init__.py"


def _load_init_module(notification_calls: list[dict], dismiss_calls: list[dict]):
    package_name = "custom_components.zero_net_export"

    for name in [package_name, "custom_components"]:
        sys.modules.pop(name, None)

    custom_components_pkg = types.ModuleType("custom_components")
    custom_components_pkg.__path__ = [str(MODULE_PATH.parents[1])]
    sys.modules[custom_components_pkg.__name__] = custom_components_pkg

    persistent_notification = types.ModuleType("homeassistant.components.persistent_notification")

    def _record_create(*args, **kwargs):
        notification_calls.append({"args": args, "kwargs": kwargs})

    def _record_dismiss(*args, **kwargs):
        dismiss_calls.append({"args": args, "kwargs": kwargs})

    persistent_notification.async_create = _record_create
    persistent_notification.async_dismiss = _record_dismiss

    voluptuous_module = types.ModuleType("voluptuous")
    voluptuous_module.Schema = lambda value: value
    voluptuous_module.Required = lambda key, default=None: key
    voluptuous_module.Optional = lambda key, default=None: key
    voluptuous_module.Coerce = lambda typ: typ
    sys.modules[voluptuous_module.__name__] = voluptuous_module

    homeassistant_pkg = types.ModuleType("homeassistant")
    homeassistant_pkg.__path__ = []
    sys.modules[homeassistant_pkg.__name__] = homeassistant_pkg

    components_pkg = types.ModuleType("homeassistant.components")
    components_pkg.persistent_notification = persistent_notification
    sys.modules[components_pkg.__name__] = components_pkg
    sys.modules[persistent_notification.__name__] = persistent_notification
    homeassistant_pkg.components = components_pkg

    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = object
    sys.modules[config_entries.__name__] = config_entries
    homeassistant_pkg.config_entries = config_entries

    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = object
    sys.modules[core.__name__] = core
    homeassistant_pkg.core = core

    typing_module = types.ModuleType("homeassistant.helpers.typing")
    typing_module.ConfigType = dict
    entity_registry_module = types.ModuleType("homeassistant.helpers.entity_registry")
    entity_registry_module.async_get = lambda hass: hass.entity_registry
    helpers_pkg = types.ModuleType("homeassistant.helpers")
    helpers_pkg.typing = typing_module
    helpers_pkg.entity_registry = entity_registry_module
    sys.modules[helpers_pkg.__name__] = helpers_pkg
    sys.modules[typing_module.__name__] = typing_module
    sys.modules[entity_registry_module.__name__] = entity_registry_module
    homeassistant_pkg.helpers = helpers_pkg

    const_module = types.ModuleType(f"{package_name}.const")
    const_module.CONF_BATTERY_RESERVE_SOC = "battery_reserve_soc"
    const_module.CONF_DEADBAND_W = "deadband_w"
    const_module.CONF_DEVICE_INVENTORY_JSON = "device_inventory_json"
    const_module.CONF_GRID_EXPORT_ENERGY_ENTITY = "grid_export_energy_entity"
    const_module.CONF_GRID_EXPORT_POWER_ENTITY = "grid_export_power_entity"
    const_module.CONF_GRID_IMPORT_ENERGY_ENTITY = "grid_import_energy_entity"
    const_module.CONF_GRID_IMPORT_POWER_ENTITY = "grid_import_power_entity"
    const_module.CONF_HOME_LOAD_POWER_ENTITY = "home_load_power_entity"
    const_module.CONF_REFRESH_SECONDS = "refresh_seconds"
    const_module.CONF_SOLAR_ENERGY_ENTITY = "solar_energy_entity"
    const_module.CONF_SOLAR_POWER_ENTITY = "solar_power_entity"
    const_module.CONF_TARGET_EXPORT_W = "target_export_w"
    const_module.DEFAULT_BATTERY_RESERVE_SOC = 20
    const_module.DEFAULT_DEADBAND_W = 50
    const_module.DEFAULT_DEVICE_INVENTORY_JSON = "[]"
    const_module.DEFAULT_REFRESH_SECONDS = 30
    const_module.DEFAULT_TARGET_EXPORT_W = 0
    const_module.DOMAIN = "zero_net_export"
    const_module.APP_MODULE_URL = "/zero_net_export_static/zero-net-export-app.js"
    const_module.APP_PANEL_COMPONENT_NAME = "zero-net-export-app"
    const_module.APP_PANEL_ICON = "mdi:transmission-tower-export"
    const_module.APP_PANEL_TITLE = "Zero Net Export"
    const_module.APP_PANEL_URL_PATH = "zero-net-export"
    const_module.APP_STATIC_URL_PATH = "/zero_net_export_static"
    const_module.INTEGRATION_VERSION = "0.1.90"
    const_module.PLATFORMS = []
    const_module.REQUIRED_SOURCE_KEYS = ["solar_power_entity", "home_load_power_entity"]
    const_module.SOURCE_ROLE_LABELS = {
        "solar_power_entity": "Solar power",
        "home_load_power_entity": "Home load power",
    }
    sys.modules[const_module.__name__] = const_module

    coordinator_module = types.ModuleType(f"{package_name}.coordinator")
    coordinator_module.ZeroNetExportCoordinator = object
    sys.modules[coordinator_module.__name__] = coordinator_module

    entity_module = types.ModuleType(f"{package_name}.entity")
    entity_module.sync_primary_controller_device_registry = lambda *args, **kwargs: None
    entity_module.sync_fleet_workspace_entity_registry = lambda *args, **kwargs: None
    sys.modules[entity_module.__name__] = entity_module

    device_model_module = types.ModuleType(f"{package_name}.device_model")
    device_model_module.parse_device_configs = lambda raw: ([], [])
    sys.modules[device_model_module.__name__] = device_model_module

    native_support_module = types.ModuleType(f"{package_name}.native_support")
    native_support_module.PRIMARY_CONFIGURE_PATH = "configure path"
    native_support_module.SOURCES_CONFIGURE_PATH = "sensors path"
    native_support_module.POLICY_CONFIGURE_PATH = "controls path"
    native_support_module.DEVICES_CONFIGURE_PATH = "devices path"
    native_support_module.SUPPORT_CONFIGURE_PATH = "diagnostics path"
    native_support_module.DIAGNOSTICS_DEVICE_ACTIONS_PATH = "device path -> Review diagnostics / Show setup checklist / Review diagnostics snapshot"
    native_support_module.build_native_operator_readiness = lambda coordinator: {
        "summary": "Setup still blocked by missing source mappings; mapped sources are stale.",
        "next_step": "Repair mapped-role blockers, then review mapped sources before relying on control. Capture the validation error, then paste the same entity id into the matching fallback field.",
    }
    native_support_module.build_source_attention_role_summary = lambda state, merged, limit=4: "Solar power"
    native_support_module.build_source_selector_fallback_hint = lambda role_keys=None: "Capture the validation error, then paste the same entity id into the matching fallback field."
    sys.modules[native_support_module.__name__] = native_support_module

    release_info_module = types.ModuleType(f"{package_name}.release_info")
    async def _prime(*args, **kwargs):
        return None
    release_info_module.async_prime_install_provenance = _prime
    sys.modules[release_info_module.__name__] = release_info_module

    repairs_module = types.ModuleType(f"{package_name}.repairs")
    repairs_module.async_clear_repairs_issues = lambda *args, **kwargs: None
    repairs_module.async_sync_repairs_issues = lambda *args, **kwargs: None
    sys.modules[repairs_module.__name__] = repairs_module

    spec = importlib.util.spec_from_file_location(
        package_name,
        MODULE_PATH,
        submodule_search_locations=[str(MODULE_PATH.parent)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = module
    custom_components_pkg.zero_net_export = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SetupNoticeCopyTests(unittest.TestCase):
    def test_stale_guided_flow_button_registry_rows_are_removed_for_current_entry(self) -> None:
        module = _load_init_module([], [])

        class FakeEntityRegistry:
            def __init__(self):
                self.entities = {
                    "button.winter_plan_open_sensors_setup": SimpleNamespace(
                        platform="zero_net_export",
                        unique_id="entry-1_open_sensors_guided_flow",
                    ),
                    "button.winter_plan_open_controls_setup": SimpleNamespace(
                        platform="zero_net_export",
                        unique_id="entry-1_open_controls_guided_flow",
                    ),
                    "button.winter_plan_open_managed_devices_setup": SimpleNamespace(
                        platform="zero_net_export",
                        unique_id="entry-1_open_managed_devices_guided_flow",
                    ),
                    "button.winter_plan_open_diagnostics_setup": SimpleNamespace(
                        platform="zero_net_export",
                        unique_id="entry-1_open_diagnostics_guided_flow",
                    ),
                    "button.summer_plan_open_sensors_setup": SimpleNamespace(
                        platform="zero_net_export",
                        unique_id="other-entry_open_sensors_guided_flow",
                    ),
                    "button.pool_edit_zero_net_export_configuration": SimpleNamespace(
                        platform="zero_net_export",
                        unique_id="entry-1_device_pool_edit_configuration",
                    ),
                    "button.pool_remove_from_zero_net_export": SimpleNamespace(
                        platform="zero_net_export",
                        unique_id="entry-1_device_pool_remove_from_zne",
                    ),
                    "button.summer_pool_remove_from_zero_net_export": SimpleNamespace(
                        platform="zero_net_export",
                        unique_id="other-entry_device_pool_remove_from_zne",
                    ),
                    "button.winter_plan_show_command_center_guide": SimpleNamespace(
                        platform="zero_net_export",
                        unique_id="entry-1_show_native_command_center",
                    ),
                    "button.unrelated": SimpleNamespace(
                        platform="other_integration",
                        unique_id="entry-1_open_sensors_guided_flow",
                    ),
                }
                self.removed = []

            def async_remove(self, entity_id):
                self.removed.append(entity_id)
                self.entities.pop(entity_id, None)

        registry = FakeEntityRegistry()
        hass = SimpleNamespace(entity_registry=registry)
        entry = SimpleNamespace(entry_id="entry-1")

        module._async_remove_stale_guided_flow_button_entities(hass, entry)

        self.assertEqual(
            registry.removed,
            [
                "button.winter_plan_open_sensors_setup",
                "button.winter_plan_open_controls_setup",
                "button.winter_plan_open_managed_devices_setup",
                "button.winter_plan_open_diagnostics_setup",
                "button.pool_edit_zero_net_export_configuration",
                "button.pool_remove_from_zero_net_export",
            ],
        )
        self.assertIn("button.summer_plan_open_sensors_setup", registry.entities)
        self.assertIn("button.summer_pool_remove_from_zero_net_export", registry.entities)
        self.assertIn("button.winter_plan_show_command_center_guide", registry.entities)
        self.assertIn("button.unrelated", registry.entities)

    def test_setup_notice_is_short_and_action_first(self) -> None:
        notification_calls: list[dict] = []
        dismiss_calls: list[dict] = []
        module = _load_init_module(notification_calls, dismiss_calls)

        entry = SimpleNamespace(
            entry_id="entry-1",
            title="Test Entry",
            data={},
            options={},
        )
        coordinator = SimpleNamespace(data=SimpleNamespace())

        asyncio.run(module._async_update_native_setup_notice(SimpleNamespace(), entry, coordinator))

        self.assertEqual(dismiss_calls, [])
        self.assertEqual(len(notification_calls), 1)
        self.assertEqual(notification_calls[0]["kwargs"]["title"], "Test Entry: setup incomplete")
        message = notification_calls[0]["args"][1]
        self.assertIn("Setup incomplete — control is paused until setup is finished.", message)
        self.assertIn("\n\nDo this first\n• Repair source blockers, then review source roles before relying on control.", message)
        self.assertIn("\n\nMissing\n• Source roles: Solar power, Home load power", message)
        self.assertIn("\n• Managed devices: 0", message)
        self.assertIn("\n• Device issues: No controllable devices added yet.", message)
        self.assertIn("\n• Blockers: Solar power", message)
        self.assertIn("\n\nOpen\n• Sensors: sensors path", message)
        self.assertIn("\n• Managed Devices: devices path", message)
        self.assertIn("\n• Controls: controls path", message)
        self.assertIn("\n• Diagnostics: diagnostics path", message)
        self.assertIn(
            "\n\nFallback only if Home Assistant rejects a valid selector choice\n• Capture the validation error, then paste the same entity id into the matching fallback field.",
            message,
        )
        self.assertEqual(message.count("Capture the validation error"), 1)
        self.assertLess(message.index("Do this first"), message.index("Missing"))
        self.assertLess(len(message), 600)
        self.assertNotIn("Zero Net Export still needs a few native setup steps", message)
        self.assertNotIn("Status\n• Summary", message)
        self.assertNotIn("Command center", message)
        self.assertNotIn("Device-page diagnostics actions", message)
        self.assertNotIn("source mappings", message)
        self.assertNotIn("mapped sources", message)
        self.assertNotIn("mapped-role blockers", message)
        self.assertNotIn("Finish setup from Home Assistant's native integration surfaces.", message)
        self.assertNotIn("\n\nNext step:", message)

    def test_setup_notice_normalizes_stale_source_mapping_next_step(self) -> None:
        notification_calls: list[dict] = []
        dismiss_calls: list[dict] = []
        module = _load_init_module(notification_calls, dismiss_calls)

        self.assertEqual(
            module._normalize_native_setup_notice_text("Open the source mapping step before enabling control."),
            "Open sensors path before enabling control.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Open source mapping step before enabling control."),
            "Open sensors path before enabling control.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Open source mappings step before enabling control."),
            "Open sensors path before enabling control.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Open source-mapping step before enabling control."),
            "Open sensors path before enabling control.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Open source-mappings step before enabling control."),
            "Open sensors path before enabling control.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Missing required source mappings. Source mapping step incomplete. Source mappings stale."
            ),
            "Missing required source roles. Sensors source roles incomplete. Source roles stale.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Source-mapping step incomplete. Source-mappings stale. Finish source-mapping before control."
            ),
            "Sensors source roles incomplete. Source roles stale. Finish source roles before control.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Open Source Mapping Step before enabling control. Missing Required Source Mappings. "
                "Source Mapping Step incomplete. Source Mappings stale. Finish Source Mapping before control."
            ),
            "Open sensors path before enabling control. Missing required source roles. "
            "Sensors source roles incomplete. Source roles stale. Finish source roles before control.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Open Configure and finish Source Mapping."),
            "Open sensors path and finish required source roles.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Open Configure to finish Source Roles."),
            "Open sensors path to finish required source roles.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Repair mapped-role blockers, then review mapped sources."),
            "Repair source blockers, then review source roles.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Repair mapped-source blockers, then review mapped-source roles."),
            "Repair source blockers, then review source roles.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Mapped-source blockers: Solar power stale. Review Mapped-source roles."),
            "Source blockers: Solar power stale. Review Source roles.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Mapped source blockers: Solar power stale. Review mapped source roles."),
            "Source blockers: Solar power stale. Review source roles.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Mapped source blocker: Solar power stale. Review mapped source role."),
            "Source blocker: Solar power stale. Review source role.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Mapped-role blocker: Solar power stale. Review Mapped-role."),
            "Source blocker: Solar power stale. Review Source role.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Mapped role blocker: Solar power stale. Review mapped role."),
            "Source blocker: Solar power stale. Review source role.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Mapped role blockers: Solar power stale. Review mapped role blockers."),
            "Source blockers: Solar power stale. Review source blockers.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Open Sensors and finish the missing source roles. Open Sources to review source health."
            ),
            "Open sensors path and finish the missing source roles. Open sensors path to review source health.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Open Controls to adjust live mode."),
            "Open controls path to adjust live mode.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text("Open Managed Devices to review candidates."),
            "Open devices path to review candidates.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Open Sensors first. Open Sources next. Open Controls after that. Open Managed Devices for review. Open Diagnostics with install evidence."
            ),
            "Open sensors path first. Open sensors path next. Open controls path after that. Open devices path for review. Open diagnostics path with install evidence.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Open Configure > Sensors. Open Configure > Controls. Open Configure > Managed Devices. Open Configure > Diagnostics."
            ),
            "Open sensors path. Open controls path. Open devices path. Open diagnostics path.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Open Configure -> Sensors. Open Configure -> Controls. Open Configure -> Managed Devices. Open Configure -> Diagnostics."
            ),
            "Open sensors path. Open controls path. Open devices path. Open diagnostics path.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Open Configure → Sensors. Open Configure → Controls. Open Configure → Managed Devices. Open Configure → Diagnostics."
            ),
            "Open sensors path. Open controls path. Open devices path. Open diagnostics path.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Path: Configure > Sensors. Next: Configure -> Managed Devices. Then Configure → Controls and Configure > Diagnostics."
            ),
            "Path: sensors path. Next: devices path. Then controls path and diagnostics path.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Open configure -> sensors. Path: CONFIGURE > managed devices. Then configure → controls and open diagnostics."
            ),
            "Open sensors path. Path: devices path. Then controls path and Open diagnostics path.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Path: Zero Net Export -> Configure → Sensors. Next: Zero Net Export -> Configure → Managed Devices."
            ),
            "Path: sensors path. Next: devices path.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Path: Zero Net Export -> Configure > Sensors. Next: Zero Net Export -> Configure > Managed Devices."
            ),
            "Path: sensors path. Next: devices path.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Open Configure and finish source mapping. Open Configure to finish required source roles."
            ),
            "Open sensors path and finish required source roles. Open sensors path to finish required source roles.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Open Configure and finish source role. Open Configure to finish Source Role."
            ),
            "Open sensors path and finish required source roles. Open sensors path to finish required source roles.",
        )
        self.assertEqual(
            module._normalize_native_setup_notice_text(
                "Open Configure and finish required source-role. Open Configure to finish source-roles."
            ),
            "Open sensors path and finish required source roles. Open sensors path to finish required source roles.",
        )


if __name__ == "__main__":
    unittest.main()
