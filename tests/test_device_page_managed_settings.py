from __future__ import annotations

import asyncio
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
        self.assertEqual(switch._attr_name, "⚙ Settings — Pool Pump enabled")
        self.assertEqual(switch._attr_device_info["name"], "Managed Devices — ⚙ Settings — Pool Pump")
        self.assertEqual(switch._attr_device_info["via_device"], ("zero_net_export", "entry-1"))

    def test_managed_device_priority_number_is_child_device_configuration(self) -> None:
        number_module = _load_simple_platform_module("number", "number", "NumberEntity")

        number = number_module.ZeroNetExportDevicePriorityNumber(_coordinator(), "pool", "Pool Pump")

        self.assertEqual(number._attr_entity_category, number_module.EntityCategory.CONFIG)
        self.assertEqual(number._attr_name, "⚙ Settings — Pool Pump priority")
        self.assertEqual(number._attr_device_info["name"], "Managed Devices — ⚙ Settings — Pool Pump")
        self.assertEqual(number._attr_device_info["via_device"], ("zero_net_export", "entry-1"))

    def test_managed_device_action_buttons_are_child_device_configuration(self) -> None:
        button_module = _load_button_module()

        review = button_module.ZeroNetExportShowManagedDeviceDetailButton(_coordinator(), "pool", "Pool Pump")
        reset = button_module.ZeroNetExportResetDeviceOverridesButton(_coordinator(), "pool", "Pool Pump")

        self.assertEqual(review._attr_entity_category, button_module.EntityCategory.CONFIG)
        self.assertEqual(reset._attr_entity_category, button_module.EntityCategory.CONFIG)
        self.assertEqual(review._attr_name, "⚙ Settings — Pool Pump review")
        self.assertEqual(reset._attr_name, "⚙ Settings — Pool Pump reset overrides")
        self.assertEqual(review._attr_device_info["name"], "Managed Devices — ⚙ Settings — Pool Pump")
        self.assertEqual(reset._attr_device_info["name"], "Managed Devices — ⚙ Settings — Pool Pump")

    def test_managed_device_usable_binary_sensor_keeps_visible_settings_affordance(self) -> None:
        binary_sensor_module = _load_simple_platform_module("binary_sensor", "binary_sensor", "BinarySensorEntity")

        usable = binary_sensor_module.ZeroNetExportDeviceUsableBinarySensor(_coordinator(), "pool", "Pool Pump")

        self.assertEqual(usable._attr_entity_category, binary_sensor_module.EntityCategory.DIAGNOSTIC)
        self.assertEqual(usable._attr_name, "⚙ Settings — Pool Pump usable")
        self.assertEqual(usable._attr_device_info["name"], "Managed Devices — ⚙ Settings — Pool Pump")

    def test_managed_device_sensor_rows_keep_visible_settings_affordance(self) -> None:
        sensor_module = _load_sensor_module()

        entities = sensor_module._build_managed_device_row_entities(
            _coordinator(),
            "pool",
            {"name": "Pool Pump", "kind": "fixed"},
        )

        self.assertIn("⚙ Settings — Pool Pump managed summary", [entity._attr_name for entity in entities])
        self.assertIn("⚙ Settings — Pool Pump status", [entity._attr_name for entity in entities])
        self.assertIn("⚙ Settings — Pool Pump Current power", [entity._attr_name for entity in entities])
        self.assertTrue(
            all(
                entity._attr_name.startswith("⚙ Settings — Pool Pump ")
                for entity in entities
                if getattr(entity, "_zero_net_export_managed_name_suffix", None)
            )
        )

    def test_managed_device_setup_platforms_keep_sparse_rows_registered(self) -> None:
        coordinator = _coordinator()
        coordinator.data.device_details = {
            "pool": {
                "kind": "fixed",
                "entity_id": "switch.pool_pump",
                "effective_enabled": True,
                "effective_priority": 120,
                "usable": True,
            }
        }
        hass = SimpleNamespace(data={"zero_net_export": {"entry-1": coordinator}})
        entry = SimpleNamespace(entry_id="entry-1")

        platform_specs = [
            (_load_simple_platform_module("switch", "switch", "SwitchEntity"), "switch"),
            (_load_simple_platform_module("number", "number", "NumberEntity"), "number"),
            (_load_simple_platform_module("binary_sensor", "binary_sensor", "BinarySensorEntity"), "binary_sensor"),
            (_load_button_module(), "button"),
        ]

        for module, platform_name in platform_specs:
            with self.subTest(platform=platform_name):
                added = []

                async def run_setup() -> None:
                    await module.async_setup_entry(hass, entry, added.extend)

                asyncio.run(run_setup())
                device_names = [
                    entity._attr_device_info.get("name")
                    for entity in added
                    if getattr(entity, "_attr_device_info", None)
                ]
                self.assertIn("Managed Devices — ⚙ Settings — pool", device_names)

    def test_managed_device_setup_platforms_use_config_inventory_before_runtime_details(self) -> None:
        coordinator = _coordinator()
        coordinator.data = SimpleNamespace(validation_details={})
        hass = SimpleNamespace(data={"zero_net_export": {"entry-1": coordinator}})
        entry = SimpleNamespace(
            entry_id="entry-1",
            data={
                "device_inventory_json": '[{"key":"pool","name":"Pool Pump","kind":"fixed","entity_id":"switch.pool_pump","nominal_power_w":1200,"min_power_w":1200,"max_power_w":1200,"step_w":1200}]'
            },
            options={},
        )

        platform_specs = [
            (_load_simple_platform_module("switch", "switch", "SwitchEntity"), "⚙ Settings — Pool Pump enabled"),
            (_load_simple_platform_module("number", "number", "NumberEntity"), "⚙ Settings — Pool Pump priority"),
            (_load_simple_platform_module("binary_sensor", "binary_sensor", "BinarySensorEntity"), "⚙ Settings — Pool Pump usable"),
            (_load_button_module(), "⚙ Settings — Pool Pump review"),
        ]

        for module, expected_name in platform_specs:
            with self.subTest(entity=expected_name):
                added = []

                async def run_setup() -> None:
                    await module.async_setup_entry(hass, entry, added.extend)

                asyncio.run(run_setup())
                managed_entities = [
                    entity
                    for entity in added
                    if (getattr(entity, "_attr_device_info", None) or {}).get("name") == "Managed Devices — ⚙ Settings — Pool Pump"
                ]
                self.assertTrue(managed_entities)
                self.assertIn(expected_name, [entity._attr_name for entity in managed_entities])

    def test_managed_device_buttons_tolerate_malformed_runtime_detail_container(self) -> None:
        coordinator = _coordinator()
        coordinator.data.device_details = "temporarily malformed runtime details"
        button_module = _load_button_module()

        review = button_module.ZeroNetExportShowManagedDeviceDetailButton(coordinator, "pool", "Pool")
        reset = button_module.ZeroNetExportResetDeviceOverridesButton(coordinator, "pool", "Pool")
        review.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(review.extra_state_attributes["managed_snapshot"], "no managed yet")
        self.assertEqual(reset.extra_state_attributes, {})

    def test_managed_device_control_rows_tolerate_null_runtime_detail(self) -> None:
        coordinator = _coordinator()
        coordinator.data.device_details = {"pool": None}

        switch_module = _load_simple_platform_module("switch", "switch", "SwitchEntity")
        number_module = _load_simple_platform_module("number", "number", "NumberEntity")
        binary_sensor_module = _load_simple_platform_module("binary_sensor", "binary_sensor", "BinarySensorEntity")
        button_module = _load_button_module()

        enabled = switch_module.ZeroNetExportDeviceEnabledSwitch(coordinator, "pool", "Pool")
        priority = number_module.ZeroNetExportDevicePriorityNumber(coordinator, "pool", "Pool")
        usable = binary_sensor_module.ZeroNetExportDeviceUsableBinarySensor(coordinator, "pool", "Pool")
        review = button_module.ZeroNetExportShowManagedDeviceDetailButton(coordinator, "pool", "Pool")
        reset = button_module.ZeroNetExportResetDeviceOverridesButton(coordinator, "pool", "Pool")
        review.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertIsNone(enabled.is_on)
        self.assertEqual(enabled.extra_state_attributes, {})
        self.assertIsNone(priority.native_value)
        self.assertEqual(priority.extra_state_attributes, {})
        self.assertIsNone(usable.is_on)
        self.assertEqual(usable.extra_state_attributes, {})
        self.assertIn("1 managed", review.extra_state_attributes["managed_snapshot"])
        self.assertEqual(reset.extra_state_attributes, {})


if __name__ == "__main__":
    unittest.main()
