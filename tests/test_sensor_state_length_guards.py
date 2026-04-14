from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"
SENSOR_PATH = PACKAGE_ROOT / "sensor.py"


def _load_sensor_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    sensor_component = sys.modules.setdefault(
        "homeassistant.components.sensor",
        types.ModuleType("homeassistant.components.sensor"),
    )
    sensor_component.SensorDeviceClass = types.SimpleNamespace(TIMESTAMP="timestamp")

    class _SensorEntity:
        pass

    sensor_component.SensorEntity = _SensorEntity

    ha_const = sys.modules.setdefault("homeassistant.const", types.ModuleType("homeassistant.const"))
    ha_const.PERCENTAGE = "%"
    ha_const.UnitOfEnergy = types.SimpleNamespace(KILO_WATT_HOUR="kWh")
    ha_const.UnitOfPower = types.SimpleNamespace(WATT="W")
    ha_const.UnitOfTime = types.SimpleNamespace(SECONDS="s")

    entity_helper = sys.modules.setdefault(
        "homeassistant.helpers.entity",
        types.ModuleType("homeassistant.helpers.entity"),
    )
    entity_helper.EntityCategory = types.SimpleNamespace(DIAGNOSTIC="diagnostic")

    const_module = types.ModuleType("custom_components.zero_net_export.const")
    const_module.DEVICE_CANDIDATE_DOMAINS = set()
    const_module.DEVICE_CANDIDATE_FIXED_DOMAINS = set()
    const_module.DOMAIN = "zero_net_export"
    const_module.INTEGRATION_VERSION = "0.1.82"
    sys.modules[const_module.__name__] = const_module

    entity_module = types.ModuleType("custom_components.zero_net_export.entity")

    class _ZeroNetExportEntity:
        pass

    entity_module.ZeroNetExportEntity = _ZeroNetExportEntity
    sys.modules[entity_module.__name__] = entity_module

    native_support_module = types.ModuleType("custom_components.zero_net_export.native_support")
    native_support_module.DEVICES_CONFIGURE_PATH = "Settings -> Devices"
    native_support_module.POLICY_CONFIGURE_PATH = "Settings -> Controls"
    native_support_module.SOURCES_CONFIGURE_PATH = "Settings -> Sensors"
    native_support_module._truncate_state_summary = lambda text, *, fallback: text if len(" ".join(str(text).split())) <= 255 else fallback
    native_support_module.build_native_command_center_summary = lambda coordinator: {
        "recommended_path": "Settings -> Sensors"
    }
    native_support_module.build_native_operator_readiness = lambda coordinator: {}
    native_support_module.build_source_attention_details = lambda state: {
        "unavailable_source_keys": [],
        "stale_source_keys": [],
    }
    native_support_module.build_source_attention_role_summary = lambda *args, **kwargs: "None"
    native_support_module.build_source_attention_summary = lambda *args, **kwargs: "None"
    native_support_module.build_source_repair_step = lambda *args, **kwargs: "Repair sources"
    native_support_module.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
    sys.modules[native_support_module.__name__] = native_support_module

    release_info_module = types.ModuleType("custom_components.zero_net_export.release_info")
    release_info_module.build_release_info = lambda *args, **kwargs: {}
    sys.modules[release_info_module.__name__] = release_info_module

    spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.sensor", SENSOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SensorStateLengthGuardTests(unittest.TestCase):
    def test_command_center_next_step_falls_back_when_value_exceeds_native_limit(self) -> None:
        sensor_module = _load_sensor_module()
        long_value = (
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Sensors and source mapping, "
            "repair Solar power, Solar energy, Grid import power, Grid export power, Battery state of charge, then save, reload, "
            "and confirm everything recovers before continuing."
        )
        trimmed = sensor_module._trim_sensor_state("command_center_next_step", long_value)
        self.assertLessEqual(len(trimmed), 255)
        self.assertEqual(
            trimmed,
            "Open Settings -> Sensors or the recommended native section and continue the highlighted step.",
        )

    def test_candidate_shortlist_falls_back_to_attribute_hint_when_preview_is_too_long(self) -> None:
        sensor_module = _load_sensor_module()
        long_value = "; ".join(
            f"Very Long Candidate Device Name Number {index} (input_number.very_long_candidate_device_name_number_{index})"
            for index in range(1, 6)
        )
        trimmed = sensor_module._trim_sensor_state("candidate_shortlist", long_value)
        self.assertLessEqual(len(trimmed), 255)
        self.assertEqual(
            trimmed,
            "See candidate_devices in the sensor attributes for the current shortlist.",
        )


if __name__ == "__main__":
    unittest.main()
