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
BINARY_SENSOR_PATH = PACKAGE_ROOT / "binary_sensor.py"


def _load_binary_sensor_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    ha_pkg = sys.modules.setdefault("homeassistant", types.ModuleType("homeassistant"))

    binary_sensor_component_module = types.ModuleType("homeassistant.components.binary_sensor")
    binary_sensor_component_module.BinarySensorEntity = type("BinarySensorEntity", (), {})
    sys.modules[binary_sensor_component_module.__name__] = binary_sensor_component_module

    entity_helper_module = types.ModuleType("homeassistant.helpers.entity")
    entity_helper_module.EntityCategory = types.SimpleNamespace(CONFIG="config", DIAGNOSTIC="diagnostic")
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

    binary_sensor_spec = importlib.util.spec_from_file_location(
        "custom_components.zero_net_export.binary_sensor",
        BINARY_SENSOR_PATH,
    )
    assert binary_sensor_spec and binary_sensor_spec.loader
    binary_sensor_module = importlib.util.module_from_spec(binary_sensor_spec)
    sys.modules[binary_sensor_spec.name] = binary_sensor_module
    binary_sensor_spec.loader.exec_module(binary_sensor_module)
    return binary_sensor_module


class BinarySensorEntityCategoryTests(unittest.TestCase):
    def test_runtime_health_and_source_stale_binaries_are_diagnostic(self) -> None:
        binary_sensor_module = _load_binary_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=None,
        )

        active = binary_sensor_module.ZeroNetExportBinarySensor(coordinator, "active", "Active")
        safe_mode = binary_sensor_module.ZeroNetExportBinarySensor(
            coordinator,
            "safe_mode",
            "Safe mode",
            entity_category=binary_sensor_module.EntityCategory.DIAGNOSTIC,
        )
        source_stale = binary_sensor_module.ZeroNetExportSourceStaleBinarySensor(
            coordinator,
            "solar_power",
            "Solar power",
        )

        self.assertIsNone(getattr(active, "_attr_entity_category", None))
        self.assertEqual(safe_mode._attr_entity_category, binary_sensor_module.EntityCategory.DIAGNOSTIC)
        self.assertEqual(source_stale._attr_entity_category, binary_sensor_module.EntityCategory.DIAGNOSTIC)

    def test_base_binary_sensor_tolerates_missing_runtime_value_attributes(self) -> None:
        binary_sensor_module = _load_binary_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(validation_details={}),
        )

        active = binary_sensor_module.ZeroNetExportBinarySensor(coordinator, "active", "Active")

        self.assertIsNone(active.is_on)

    def test_device_usable_binary_becomes_diagnostic_because_summary_already_carries_readiness(self) -> None:
        binary_sensor_module = _load_binary_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "usable": True,
                    }
                }
            ),
        )

        usable = binary_sensor_module.ZeroNetExportDeviceUsableBinarySensor(coordinator, "pool", "Pool pump")

        self.assertEqual(usable._attr_name, "Pool pump usable")
        self.assertTrue(usable.is_on)
        self.assertEqual(usable._attr_entity_category, binary_sensor_module.EntityCategory.DIAGNOSTIC)


if __name__ == "__main__":
    unittest.main()
