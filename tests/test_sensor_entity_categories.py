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

    ha_pkg = sys.modules.setdefault("homeassistant", types.ModuleType("homeassistant"))

    sensor_component_module = types.ModuleType("homeassistant.components.sensor")
    sensor_component_module.SensorEntity = type("SensorEntity", (), {})
    sensor_component_module.SensorDeviceClass = types.SimpleNamespace(TIMESTAMP="timestamp")
    sensor_component_module.SensorStateClass = types.SimpleNamespace(MEASUREMENT="measurement")
    sys.modules[sensor_component_module.__name__] = sensor_component_module

    const_module = types.ModuleType("homeassistant.const")
    const_module.PERCENTAGE = "%"
    const_module.UnitOfEnergy = types.SimpleNamespace(KILO_WATT_HOUR="kWh")
    const_module.UnitOfPower = types.SimpleNamespace(WATT="W")
    const_module.UnitOfTime = types.SimpleNamespace(SECONDS="s")
    sys.modules[const_module.__name__] = const_module

    entity_helper_module = types.ModuleType("homeassistant.helpers.entity")
    entity_helper_module.EntityCategory = types.SimpleNamespace(DIAGNOSTIC="diagnostic")
    sys.modules[entity_helper_module.__name__] = entity_helper_module

    update_coordinator_module = types.ModuleType("homeassistant.helpers.update_coordinator")

    class CoordinatorEntity:
        def __init__(self, coordinator) -> None:
            self.coordinator = coordinator

    update_coordinator_module.CoordinatorEntity = CoordinatorEntity
    sys.modules[update_coordinator_module.__name__] = update_coordinator_module

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

    native_support_module = types.ModuleType("custom_components.zero_net_export.native_support")
    native_support_module.DEVICES_CONFIGURE_PATH = "devices path"
    native_support_module.POLICY_CONFIGURE_PATH = "policy path"
    native_support_module.SOURCES_CONFIGURE_PATH = "sources path"
    native_support_module.build_native_command_center_summary = lambda coordinator: {}
    native_support_module.build_native_operator_readiness = lambda coordinator: {}
    native_support_module.build_source_attention_details = lambda state: {}
    native_support_module.build_source_attention_brief = lambda state, merged, limit=3: "None"
    native_support_module.build_source_attention_role_summary = lambda state, merged, limit=6: "None"
    native_support_module.build_source_attention_summary = lambda state, merged, limit=4: "None"
    native_support_module.summarize_validation_issue_messages = lambda state, severities=None, limit=3: "None"
    sys.modules[native_support_module.__name__] = native_support_module

    release_info_module = types.ModuleType("custom_components.zero_net_export.release_info")
    release_info_module.build_release_info = lambda *args, **kwargs: {}
    sys.modules[release_info_module.__name__] = release_info_module

    candidate_utils_module = types.ModuleType("custom_components.zero_net_export.candidate_utils")
    candidate_utils_module.assess_candidate = lambda candidate: {
        "confidence": "medium",
        "summary": "Looks like a plausible controllable candidate, but review before promotion.",
        "warnings": [],
    }
    candidate_utils_module.build_candidate_name_summary = lambda candidates, **kwargs: "candidate names"
    candidate_utils_module.build_candidate_preview = lambda candidate, **kwargs: "candidate preview"
    candidate_utils_module.discover_candidate_devices = lambda states, managed_entity_ids: []
    sys.modules[candidate_utils_module.__name__] = candidate_utils_module

    sensor_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.sensor", SENSOR_PATH)
    assert sensor_spec and sensor_spec.loader
    sensor_module = importlib.util.module_from_spec(sensor_spec)
    sys.modules[sensor_spec.name] = sensor_module
    sensor_spec.loader.exec_module(sensor_module)
    return sensor_module


class SensorEntityCategoryTests(unittest.TestCase):
    def test_fleet_workspace_sensors_are_primary_entities(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=None,
        )

        managed_overview = sensor_module.ZeroNetExportSensor(
            coordinator,
            "managed_fleet_overview",
            "Managed fleet overview",
        )
        shortlist = sensor_module.ZeroNetExportSensor(
            coordinator,
            "candidate_shortlist",
            "Candidate shortlist",
        )

        self.assertIsNone(managed_overview.entity_category)
        self.assertIsNone(shortlist.entity_category)

    def test_telemetry_sensor_stays_uncategorized(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=None,
        )

        telemetry = sensor_module.ZeroNetExportSensor(coordinator, "solar_power_w", "Solar power")

        self.assertIsNone(telemetry.entity_category)

    def test_managed_device_summary_stays_primary_while_secondary_runtime_details_become_diagnostic(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "status": "Ready for control",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "priority": 90,
                        "current_power_w": 1185,
                        "planned_action": "turn_on",
                    }
                }
            ),
        )

        summary = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "pool", "Pool pump")
        current_power = sensor_module.ZeroNetExportDevicePowerSensor(
            coordinator,
            "pool",
            "Pool pump",
            "current_power_w",
            "Current power",
        )
        status = sensor_module.ZeroNetExportDeviceStatusSensor(coordinator, "pool", "Pool pump")
        plan = sensor_module.ZeroNetExportDevicePlanSensor(coordinator, "pool", "Pool pump")
        guard = sensor_module.ZeroNetExportDeviceGuardSensor(coordinator, "pool", "Pool pump")
        planned_delta = sensor_module.ZeroNetExportDevicePowerSensor(
            coordinator,
            "pool",
            "Pool pump",
            "planned_power_delta_w",
            "Planned power delta",
            entity_category=sensor_module.EntityCategory.DIAGNOSTIC,
        )
        runtime = sensor_module.ZeroNetExportDeviceDurationSensor(
            coordinator,
            "pool",
            "Pool pump",
            "current_active_seconds",
            "Current active runtime",
        )
        last_requested = sensor_module.ZeroNetExportDevicePowerSensor(
            coordinator,
            "pool",
            "Pool pump",
            "last_requested_power_w",
            "Last requested power",
            entity_category=sensor_module.EntityCategory.DIAGNOSTIC,
        )

        self.assertEqual(summary._attr_name, "Pool pump managed summary")
        self.assertEqual(
            summary.native_value,
            "Ready for control | usable | enabled | priority 90 | power 1185 W | plan turn_on",
        )
        self.assertIsNone(getattr(summary, "_attr_entity_category", None))
        self.assertIsNone(getattr(current_power, "_attr_entity_category", None))
        self.assertEqual(status._attr_entity_category, sensor_module.EntityCategory.DIAGNOSTIC)
        self.assertEqual(plan._attr_entity_category, sensor_module.EntityCategory.DIAGNOSTIC)
        self.assertEqual(guard._attr_entity_category, sensor_module.EntityCategory.DIAGNOSTIC)
        self.assertEqual(planned_delta._attr_entity_category, sensor_module.EntityCategory.DIAGNOSTIC)
        self.assertEqual(runtime._attr_entity_category, sensor_module.EntityCategory.DIAGNOSTIC)
        self.assertEqual(last_requested._attr_entity_category, sensor_module.EntityCategory.DIAGNOSTIC)


if __name__ == "__main__":
    unittest.main()
