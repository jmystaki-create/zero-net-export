from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"
CONST_PATH = PACKAGE_ROOT / "const.py"
ENTITY_PATH = PACKAGE_ROOT / "entity.py"
SENSOR_PATH = PACKAGE_ROOT / "sensor.py"


def _load_sensor_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    homeassistant_pkg = sys.modules.setdefault("homeassistant", types.ModuleType("homeassistant"))
    homeassistant_pkg.__path__ = []

    components_pkg = sys.modules.setdefault("homeassistant.components", types.ModuleType("homeassistant.components"))
    components_pkg.__path__ = []
    homeassistant_pkg.components = components_pkg

    helpers_pkg = sys.modules.setdefault("homeassistant.helpers", types.ModuleType("homeassistant.helpers"))
    helpers_pkg.__path__ = []
    homeassistant_pkg.helpers = helpers_pkg

    sensor_component_module = types.ModuleType("homeassistant.components.sensor")
    sensor_component_module.SensorEntity = type("SensorEntity", (), {})
    sensor_component_module.SensorDeviceClass = types.SimpleNamespace(TIMESTAMP="timestamp")
    sensor_component_module.SensorStateClass = types.SimpleNamespace(MEASUREMENT="measurement")
    sys.modules[sensor_component_module.__name__] = sensor_component_module
    components_pkg.sensor = sensor_component_module

    const_module = types.ModuleType("homeassistant.const")
    const_module.PERCENTAGE = "%"
    const_module.UnitOfEnergy = types.SimpleNamespace(KILO_WATT_HOUR="kWh")
    const_module.UnitOfPower = types.SimpleNamespace(WATT="W")
    const_module.UnitOfTime = types.SimpleNamespace(SECONDS="s")
    sys.modules[const_module.__name__] = const_module
    homeassistant_pkg.const = const_module

    entity_helper_module = types.ModuleType("homeassistant.helpers.entity")
    entity_helper_module.EntityCategory = types.SimpleNamespace(DIAGNOSTIC="diagnostic")
    sys.modules[entity_helper_module.__name__] = entity_helper_module
    helpers_pkg.entity = entity_helper_module

    update_coordinator_module = types.ModuleType("homeassistant.helpers.update_coordinator")

    class CoordinatorEntity:
        def __init__(self, coordinator) -> None:
            self.coordinator = coordinator

    update_coordinator_module.CoordinatorEntity = CoordinatorEntity
    sys.modules[update_coordinator_module.__name__] = update_coordinator_module
    helpers_pkg.update_coordinator = update_coordinator_module

    candidate_utils_module = types.ModuleType("custom_components.zero_net_export.candidate_utils")
    candidate_utils_module.assess_candidate = lambda candidate: {"confidence": "high", "summary": "good", "warnings": []}
    candidate_utils_module.build_candidate_fit_summary = lambda *args, **kwargs: "fit"
    candidate_utils_module.build_candidate_name_summary = lambda *args, **kwargs: "summary"
    candidate_utils_module.build_candidate_overview_summary = lambda *args, **kwargs: "overview"
    candidate_utils_module.build_candidate_preview = lambda *args, **kwargs: "preview"
    candidate_utils_module.build_candidate_compact_preview = lambda *args, **kwargs: "compact preview"
    candidate_utils_module.build_candidate_review_hint = lambda *args, **kwargs: "likely useful"
    candidate_utils_module.candidate_needs_review = lambda fit: False
    candidate_utils_module.discover_candidate_devices = lambda *args, **kwargs: []
    candidate_utils_module.first_review_candidate = lambda candidates: None
    sys.modules[candidate_utils_module.__name__] = candidate_utils_module

    native_support_module = types.ModuleType("custom_components.zero_net_export.native_support")
    native_support_module.DEVICES_CONFIGURE_PATH = "devices path"
    native_support_module.POLICY_CONFIGURE_PATH = "policy path"
    native_support_module.SOURCES_CONFIGURE_PATH = "sources path"
    native_support_module.build_native_command_center_summary = lambda coordinator: {}
    native_support_module.build_native_operator_readiness = lambda coordinator: {}
    native_support_module.build_source_attention_details = lambda state=None: {}
    native_support_module.build_source_attention_brief = lambda state=None: "brief"
    native_support_module.build_source_attention_role_summary = lambda *args, **kwargs: "roles"
    native_support_module.build_source_attention_summary = lambda *args, **kwargs: "summary"
    native_support_module.summarize_validation_issue_messages = lambda *args, **kwargs: "issues"
    sys.modules[native_support_module.__name__] = native_support_module

    release_info_module = types.ModuleType("custom_components.zero_net_export.release_info")
    release_info_module.build_release_info = lambda *args, **kwargs: {}
    sys.modules[release_info_module.__name__] = release_info_module

    const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", CONST_PATH)
    assert const_spec and const_spec.loader
    integration_const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = integration_const_module
    const_spec.loader.exec_module(integration_const_module)

    entity_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.entity", ENTITY_PATH)
    assert entity_spec and entity_spec.loader
    integration_entity_module = importlib.util.module_from_spec(entity_spec)
    sys.modules[entity_spec.name] = integration_entity_module
    entity_spec.loader.exec_module(integration_entity_module)

    sensor_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.sensor", SENSOR_PATH)
    assert sensor_spec and sensor_spec.loader
    sensor_module = importlib.util.module_from_spec(sensor_spec)
    sys.modules[sensor_spec.name] = sensor_module
    sensor_spec.loader.exec_module(sensor_module)
    return sensor_module


class SourceIssueCountSensorTests(unittest.TestCase):
    def test_issue_count_sensor_uses_measurement_state_class(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                validation_details={
                    "source_diagnostics": {
                        "solar_power": {
                            "issue_counts": {"error": 2, "warning": 1, "info": 3},
                        }
                    }
                }
            ),
        )

        sensor = sensor_module.ZeroNetExportSourceIssueCountSensor(coordinator, "solar_power", "Solar power")

        self.assertEqual(sensor._attr_state_class, sensor_module.SensorStateClass.MEASUREMENT)
        self.assertEqual(sensor.native_value, 6)


if __name__ == "__main__":
    unittest.main()
