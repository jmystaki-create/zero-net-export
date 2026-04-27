from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace


class _FakeDeviceRegistry:
    def __init__(self, device):
        self.device = device
        self.updated = None

    def async_get_device(self, identifiers):
        return self.device if self.device.identifier in identifiers else None

    def async_update_device(self, device_id, **kwargs):
        self.updated = (device_id, kwargs)
        for key, value in kwargs.items():
            setattr(self.device, key, value)

from tests.test_sensor_entity_categories import _load_sensor_module


class IntegrationPageDeviceListTests(unittest.TestCase):
    def _coordinator(self):
        return SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Zero Net Export"),
            data=SimpleNamespace(
                validation_details={},
                device_details={
                    "pool": {
                        "name": "Pool Pump",
                        "kind": "fixed",
                        "entity_id": "switch.pool_pump",
                        "status": "ready",
                        "usable": True,
                    }
                },
            ),
        )

    def test_managed_device_sensors_register_managed_load_as_own_ha_device(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()

        sensor = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "pool", "Pool Pump")

        self.assertEqual(sensor._attr_device_info["name"], "Managed Devices — Pool Pump")
        self.assertEqual(sensor._attr_device_info["model"], "Managed Devices — Fixed managed load")
        self.assertIn(("zero_net_export", "entry-1:managed-device:pool"), sensor._attr_device_info["identifiers"])
        self.assertEqual(sensor._attr_device_info["via_device"], ("zero_net_export", "entry-1"))
        self.assertEqual(sensor._attr_device_info["suggested_area"], "Zero Net Export Managed Devices")
        self.assertEqual(sensor.extra_state_attributes["integration_page_group"], "Managed Devices")
        self.assertEqual(
            sensor._attr_device_info["configuration_url"],
            "homeassistant://navigate/config/integrations/integration/zero_net_export?managed_device=entry-1%3Apool",
        )

    def test_managed_device_async_added_updates_existing_registry_configuration_url(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        sensor = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "pool", "Pool Pump")
        identifier = ("zero_net_export", "entry-1:managed-device:pool")
        device = SimpleNamespace(id="device-1", identifier=identifier, configuration_url=None)
        registry = _FakeDeviceRegistry(device)
        sensor.hass = SimpleNamespace(device_registry=registry)

        asyncio.run(sensor.async_added_to_hass())

        self.assertEqual(
            registry.updated,
            (
                "device-1",
                {
                    "configuration_url": "homeassistant://navigate/config/integrations/integration/zero_net_export?managed_device=entry-1%3Apool"
                },
            ),
        )

    def test_managed_device_configuration_url_encodes_query_value(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()

        sensor = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "pool pump&main", "Pool Pump")

        self.assertEqual(
            sensor._attr_device_info["configuration_url"],
            "homeassistant://navigate/config/integrations/integration/zero_net_export?managed_device=entry-1%3Apool+pump%26main",
        )

    def test_unmanaged_candidate_configuration_url_encodes_query_value(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        candidate = {
            "entity_id": "switch.hot_water&boost",
            "name": "Hot Water Boost",
            "domain": "switch",
            "kind": "fixed",
            "state": "off",
        }

        sensor = sensor_module.ZeroNetExportUnmanagedCandidateSensor(coordinator, candidate)

        self.assertEqual(
            sensor._attr_device_info["configuration_url"],
            "homeassistant://navigate/config/entities?entity_id=switch.hot_water%26boost",
        )

    def test_unmanaged_candidate_sensor_registers_candidate_as_own_ha_device(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        candidate = {
            "entity_id": "switch.hot_water",
            "name": "Hot Water",
            "domain": "switch",
            "kind": "fixed",
            "state": "off",
        }

        sensor = sensor_module.ZeroNetExportUnmanagedCandidateSensor(coordinator, candidate)

        self.assertEqual(sensor._attr_device_info["name"], "Un Managed — Hot Water")
        self.assertEqual(sensor._attr_device_info["model"], "Un Managed — Fixed unmanaged candidate")
        self.assertIn(
            ("zero_net_export", "entry-1:unmanaged-candidate:switch_hot_water"),
            sensor._attr_device_info["identifiers"],
        )
        self.assertEqual(sensor._attr_device_info["via_device"], ("zero_net_export", "entry-1"))
        self.assertEqual(sensor._attr_device_info["suggested_area"], "Zero Net Export Un Managed")
        self.assertEqual(sensor.extra_state_attributes["integration_page_group"], "Un Managed")

    def test_unmanaged_candidate_async_added_updates_existing_registry_configuration_url(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        candidate = {
            "entity_id": "switch.hot_water",
            "name": "Hot Water",
            "domain": "switch",
            "kind": "fixed",
            "state": "off",
        }
        sensor = sensor_module.ZeroNetExportUnmanagedCandidateSensor(coordinator, candidate)
        identifier = ("zero_net_export", "entry-1:unmanaged-candidate:switch_hot_water")
        device = SimpleNamespace(id="device-2", identifier=identifier, configuration_url=None)
        registry = _FakeDeviceRegistry(device)
        sensor.hass = SimpleNamespace(device_registry=registry)

        asyncio.run(sensor.async_added_to_hass())

        self.assertEqual(
            registry.updated,
            ("device-2", {"configuration_url": "homeassistant://navigate/config/entities?entity_id=switch.hot_water"}),
        )

    def test_fleet_workspace_summary_sensors_do_not_attach_to_primary_device_page(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()

        sensor = sensor_module.ZeroNetExportSensor(
            coordinator,
            "candidate_shortlist",
            "Managed Devices candidate shortlist",
        )

        self.assertIsNone(sensor._attr_device_info)

    def test_base_entity_tolerates_missing_validation_details(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace()

        sensor = sensor_module.ZeroNetExportSensor(
            coordinator,
            "previous_installed_version",
            "Previous installed version",
        )

        self.assertIsNone(sensor.native_value)

    def test_setup_entry_adds_unmanaged_candidate_entities_for_integration_page_rows(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: [
            {
                "entity_id": "switch.hot_water",
                "name": "Hot Water",
                "domain": "switch",
                "kind": "fixed",
                "state": "off",
            }
        ]
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: []),
        )
        entry = SimpleNamespace(entry_id="entry-1")
        added = []

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())

        device_names = [
            entity._attr_device_info.get("name")
            for entity in added
            if getattr(entity, "_attr_device_info", None)
        ]
        self.assertIn("Managed Devices — Pool Pump", device_names)
        self.assertIn("Un Managed — Hot Water", device_names)

    def test_setup_entry_keeps_managed_device_row_when_detail_is_sparse(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data.device_details = {
            "pool": {
                "entity_id": "switch.pool_pump",
                "status": "ready",
                "usable": True,
            }
        }
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: []
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: []),
        )
        entry = SimpleNamespace(entry_id="entry-1")
        added = []

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())

        device_names = [
            entity._attr_device_info.get("name")
            for entity in added
            if getattr(entity, "_attr_device_info", None)
        ]
        self.assertIn("Managed Devices — pool", device_names)

    def test_setup_entry_tolerates_missing_runtime_device_details(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: []
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: []),
        )
        entry = SimpleNamespace(entry_id="entry-1")
        added = []

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())

        self.assertTrue(added)
        self.assertNotIn(
            "Managed Devices — pool",
            [
                entity._attr_device_info.get("name")
                for entity in added
                if getattr(entity, "_attr_device_info", None)
            ],
        )


if __name__ == "__main__":
    unittest.main()
