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
    helpers_pkg = types.ModuleType("homeassistant.helpers")
    helpers_pkg.typing = typing_module
    sys.modules[helpers_pkg.__name__] = helpers_pkg
    sys.modules[typing_module.__name__] = typing_module
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
    const_module.INTEGRATION_VERSION = "0.1.88"
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

    device_model_module = types.ModuleType(f"{package_name}.device_model")
    device_model_module.parse_device_configs = lambda raw: ([], [])
    sys.modules[device_model_module.__name__] = device_model_module

    native_support_module = types.ModuleType(f"{package_name}.native_support")
    native_support_module.PRIMARY_CONFIGURE_PATH = "configure path"
    native_support_module.SOURCES_CONFIGURE_PATH = "sensors path"
    native_support_module.DEVICES_CONFIGURE_PATH = "devices path"
    native_support_module.SUPPORT_CONFIGURE_PATH = "diagnostics path"
    native_support_module.DIAGNOSTICS_DEVICE_ACTIONS_PATH = "device path -> Review diagnostics / Show setup checklist / Review diagnostics snapshot"
    native_support_module.build_native_operator_readiness = lambda coordinator: {
        "summary": "Setup still blocked by missing source mappings.",
        "next_step": "Open configure path -> Sensors and map Solar power first.",
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
    def test_setup_notice_uses_compact_sections(self) -> None:
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
        self.assertEqual(notification_calls[0]["kwargs"]["title"], "Test Entry: finish native Zero Net Export setup")
        message = notification_calls[0]["args"][1]
        self.assertIn("Zero Net Export still needs a few native setup steps.", message)
        self.assertIn("\n\nStatus\n• Summary: Setup still blocked by missing source roles.", message)
        self.assertNotIn("source mappings", message)
        self.assertIn("\n• Missing required source roles: Solar power, Home load power", message)
        self.assertIn("\n• Managed Devices: 0", message)
        self.assertIn("\n• Managed-device issues: No controllable devices have been added yet.", message)
        self.assertIn("\n• Active blockers: Solar power", message)
        self.assertIn("\n\nDo next\n• Open configure path -> Sensors and map Solar power first.", message)
        self.assertIn(
            "\n\nFallback, only if Home Assistant rejects a valid choice\n• Capture the validation error, then paste the same entity id into the matching fallback field.",
            message,
        )
        self.assertIn("\n\nOpen\n• Command center: configure path", message)
        self.assertIn("\n• Sensors: sensors path", message)
        self.assertIn("\n• Managed Devices: devices path", message)
        self.assertIn("\n• Diagnostics: diagnostics path", message)
        self.assertIn(
            "\n• Device-page diagnostics actions: device path -> Review diagnostics / Show setup checklist / Review diagnostics snapshot",
            message,
        )
        self.assertNotIn("Finish setup from Home Assistant's native integration surfaces.", message)
        self.assertNotIn("\n\nNext step:", message)
        self.assertNotIn("\n\nUse device path -> Review diagnostics / Show setup checklist / Review diagnostics snapshot for deeper diagnostics", message)

    def test_setup_notice_normalizes_stale_source_mapping_next_step(self) -> None:
        notification_calls: list[dict] = []
        dismiss_calls: list[dict] = []
        module = _load_init_module(notification_calls, dismiss_calls)

        self.assertEqual(
            module._normalize_native_setup_notice_text("Open the source mapping step before enabling control."),
            "Open the Sensors source roles step before enabling control.",
        )


if __name__ == "__main__":
    unittest.main()
