from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace

from tests.test_button_entity_categories import _load_button_module
from tests.test_sensor_entity_categories import _load_sensor_module


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"


def _coordinator():
    return SimpleNamespace(
        entry=SimpleNamespace(entry_id="entry-1", title="Zero Net Export"),
        data=SimpleNamespace(
            validation_details={},
            device_details={
                "pool": {
                    "name": "Pool Pump",
                    "kind": "fixed",
                    "entity_id": "switch.pool_pump",
                    "effective_enabled": True,
                    "effective_priority": 120,
                    "usable": True,
                }
            },
        ),
    )


def _load_simple_platform_module(module_name: str, component_name: str, entity_base_name: str):
    _load_sensor_module()  # installs the package, const, entity, and common HA helper stubs.

    component_pkg = sys.modules.setdefault(
        f"homeassistant.components.{component_name}",
        types.ModuleType(f"homeassistant.components.{component_name}"),
    )
    setattr(component_pkg, entity_base_name, type(entity_base_name, (), {}))

    const_module = sys.modules.setdefault("homeassistant.const", types.ModuleType("homeassistant.const"))
    const_module.UnitOfPower = types.SimpleNamespace(WATT="W")

    spec = importlib.util.spec_from_file_location(
        f"custom_components.zero_net_export.{module_name}",
        PACKAGE_ROOT / f"{module_name}.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DevicePageManagedSettingsTests(unittest.TestCase):
    def test_managed_device_enable_switch_is_child_device_configuration(self) -> None:
        switch_module = _load_simple_platform_module("switch", "switch", "SwitchEntity")

        switch = switch_module.ZeroNetExportDeviceEnabledSwitch(_coordinator(), "pool", "Pool Pump")

        self.assertEqual(switch._attr_entity_category, switch_module.EntityCategory.CONFIG)
        self.assertEqual(switch._attr_device_info["name"], "Managed Devices — Pool Pump")
        self.assertEqual(switch._attr_device_info["via_device"], ("zero_net_export", "entry-1"))

    def test_managed_device_priority_number_is_child_device_configuration(self) -> None:
        number_module = _load_simple_platform_module("number", "number", "NumberEntity")

        number = number_module.ZeroNetExportDevicePriorityNumber(_coordinator(), "pool", "Pool Pump")

        self.assertEqual(number._attr_entity_category, number_module.EntityCategory.CONFIG)
        self.assertEqual(number._attr_device_info["name"], "Managed Devices — Pool Pump")
        self.assertEqual(number._attr_device_info["via_device"], ("zero_net_export", "entry-1"))

    def test_managed_device_action_buttons_are_child_device_configuration(self) -> None:
        button_module = _load_button_module()

        review = button_module.ZeroNetExportShowManagedDeviceDetailButton(_coordinator(), "pool", "Pool Pump")
        reset = button_module.ZeroNetExportResetDeviceOverridesButton(_coordinator(), "pool", "Pool Pump")

        self.assertEqual(review._attr_entity_category, button_module.EntityCategory.CONFIG)
        self.assertEqual(reset._attr_entity_category, button_module.EntityCategory.CONFIG)
        self.assertEqual(review._attr_device_info["name"], "Managed Devices — Pool Pump")
        self.assertEqual(reset._attr_device_info["name"], "Managed Devices — Pool Pump")


if __name__ == "__main__":
    unittest.main()
