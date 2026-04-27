from pathlib import Path
import importlib.util
import sys
import types
import unittest
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"
DIAGNOSTICS_PATH = PACKAGE_ROOT / "diagnostics.py"


def _load_diagnostics_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    ha_pkg = sys.modules.setdefault("homeassistant", types.ModuleType("homeassistant"))
    ha_pkg.__path__ = []

    components_pkg = types.ModuleType("homeassistant.components")
    components_pkg.__path__ = []
    sys.modules[components_pkg.__name__] = components_pkg

    diagnostics_component = types.ModuleType("homeassistant.components.diagnostics")
    diagnostics_component.async_redact_data = lambda data, keys: data
    sys.modules[diagnostics_component.__name__] = diagnostics_component

    config_entries_module = types.ModuleType("homeassistant.config_entries")
    config_entries_module.ConfigEntry = type("ConfigEntry", (), {})
    sys.modules[config_entries_module.__name__] = config_entries_module

    const_module = types.ModuleType("homeassistant.const")
    const_module.CONF_NAME = "name"
    sys.modules[const_module.__name__] = const_module

    core_module = types.ModuleType("homeassistant.core")
    core_module.HomeAssistant = type("HomeAssistant", (), {})
    sys.modules[core_module.__name__] = core_module

    integration_const = types.ModuleType("custom_components.zero_net_export.const")
    for name in [
        "CONF_BATTERY_CHARGE_POWER_ENTITY",
        "CONF_BATTERY_DISCHARGE_POWER_ENTITY",
        "CONF_BATTERY_SOC_ENTITY",
        "CONF_DEADBAND_W",
        "CONF_DEVICE_INVENTORY_JSON",
        "CONF_GRID_EXPORT_ENERGY_ENTITY",
        "CONF_GRID_EXPORT_POWER_ENTITY",
        "CONF_GRID_IMPORT_ENERGY_ENTITY",
        "CONF_GRID_IMPORT_POWER_ENTITY",
        "CONF_HOME_LOAD_POWER_ENTITY",
        "CONF_REFRESH_SECONDS",
        "CONF_SOLAR_ENERGY_ENTITY",
        "CONF_SOLAR_POWER_ENTITY",
        "CONF_TARGET_EXPORT_W",
    ]:
        setattr(integration_const, name, name.lower())
    integration_const.DOMAIN = "zero_net_export"
    integration_const.INTEGRATION_VERSION = "0.1.94"
    sys.modules[integration_const.__name__] = integration_const

    native_support = types.ModuleType("custom_components.zero_net_export.native_support")
    native_support.PRIMARY_CONFIGURE_PATH = "configure path"
    native_support.build_native_operator_readiness = lambda coordinator: {"summary": "ready"}
    sys.modules[native_support.__name__] = native_support

    release_info = types.ModuleType("custom_components.zero_net_export.release_info")
    release_info.build_install_consistency_summary = lambda provenance: "consistent"
    release_info.build_install_provenance = lambda: {"summary": "repo", "live_validation_safe": False}
    release_info.build_release_info = lambda *args, **kwargs: {"summary": "release"}
    sys.modules[release_info.__name__] = release_info

    spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.diagnostics", DIAGNOSTICS_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _SparseRuntimeState:
    validation_details = {}

    def __getattr__(self, name):
        if name == "device_details":
            raise AttributeError(name)
        return None


class TestDiagnosticsPayloadCopy(unittest.TestCase):
    def test_controller_diagnostics_use_current_next_action_key(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export" / "diagnostics.py").read_text(encoding="utf-8")

        self.assertIn('"current_native_next_action": _runtime_attr(data, "recommendation")', source)
        self.assertNotIn('"recommendation": data.recommendation', source)

    def test_native_surface_button_metadata_matches_managed_devices_actions(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export" / "diagnostics.py").read_text(encoding="utf-8")

        self.assertIn('"Open Managed Devices workspace"', source)
        self.assertIn('"Open Managed Devices review"', source)
        self.assertIn('"Per-device Managed Devices review buttons"', source)
        self.assertNotIn('"Review managed devices",', source)
        self.assertNotIn('"Review managed devices workspace",', source)
        self.assertNotIn('"Review each managed device",', source)

    def test_diagnostics_snapshot_tolerates_missing_runtime_controller_fields(self) -> None:
        diagnostics = _load_diagnostics_module()
        entry = SimpleNamespace(
            entry_id="entry-1",
            title="Zero Net Export",
            domain="zero_net_export",
            version=1,
            data={},
            options={},
        )
        coordinator = SimpleNamespace(entry=entry, data=SimpleNamespace(validation_details={}))
        hass = SimpleNamespace(data={"zero_net_export": {"entry-1": coordinator}})

        payload = diagnostics.async_get_config_entry_diagnostics(hass, entry)
        if hasattr(payload, "__await__"):
            import asyncio

            payload = asyncio.run(payload)

        self.assertIsNone(payload["controller"]["current_native_next_action"])
        self.assertIsNone(payload["controller"]["active"])
        self.assertIsNone(payload["telemetry"]["actions_today"])
        self.assertIsNone(payload["sources"]["grid_export_power_w"])
        self.assertIsNone(payload["devices"]["device_count"])
        self.assertEqual(payload["devices"]["details"], [])

    def test_diagnostics_snapshot_tolerates_missing_runtime_device_details(self) -> None:
        diagnostics = _load_diagnostics_module()
        entry = SimpleNamespace(
            entry_id="entry-1",
            title="Zero Net Export",
            domain="zero_net_export",
            version=1,
            data={},
            options={},
        )
        coordinator = SimpleNamespace(entry=entry, data=_SparseRuntimeState())
        hass = SimpleNamespace(data={"zero_net_export": {"entry-1": coordinator}})

        payload = diagnostics.async_get_config_entry_diagnostics(hass, entry)
        if hasattr(payload, "__await__"):
            import asyncio

            payload = asyncio.run(payload)

        self.assertEqual(payload["devices"]["details"], [])
        self.assertEqual(payload["validation_details"]["action_history"], [])
        self.assertEqual(payload["validation_details"]["source_diagnostics"], {})
        self.assertEqual(payload["validation_details"]["source_freshness"], {})

    def test_diagnostics_snapshot_tolerates_malformed_validation_details(self) -> None:
        diagnostics = _load_diagnostics_module()
        entry = SimpleNamespace(
            entry_id="entry-1",
            title="Zero Net Export",
            domain="zero_net_export",
            version=1,
            data={},
            options={},
        )
        coordinator = SimpleNamespace(entry=entry, data=SimpleNamespace(validation_details=["temporarily malformed"]))
        hass = SimpleNamespace(data={"zero_net_export": {"entry-1": coordinator}})

        payload = diagnostics.async_get_config_entry_diagnostics(hass, entry)
        if hasattr(payload, "__await__"):
            import asyncio

            payload = asyncio.run(payload)

        self.assertEqual(payload["validation_details"]["action_history"], [])
        self.assertEqual(payload["validation_details"]["source_diagnostics"], {})
        self.assertEqual(payload["validation_details"]["source_freshness"], {})
        self.assertIsNone(payload["entry"]["release_update_summary"])


if __name__ == "__main__":
    unittest.main()
