from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace

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
        self.assertEqual(sensor._attr_device_info["model"], "Fixed managed load")
        self.assertIn(("zero_net_export", "entry-1:managed-device:pool"), sensor._attr_device_info["identifiers"])
        self.assertEqual(sensor._attr_device_info["via_device"], ("zero_net_export", "entry-1"))

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
        self.assertEqual(sensor._attr_device_info["model"], "Fixed unmanaged candidate")
        self.assertIn(
            ("zero_net_export", "entry-1:unmanaged-candidate:switch_hot_water"),
            sensor._attr_device_info["identifiers"],
        )
        self.assertEqual(sensor._attr_device_info["via_device"], ("zero_net_export", "entry-1"))
        self.assertEqual(sensor.extra_state_attributes["integration_page_group"], "Un Managed")

    def test_fleet_workspace_summary_sensors_do_not_attach_to_primary_device_page(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()

        sensor = sensor_module.ZeroNetExportSensor(
            coordinator,
            "candidate_shortlist",
            "Managed Devices candidate shortlist",
        )

        self.assertIsNone(sensor._attr_device_info)

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


if __name__ == "__main__":
    unittest.main()
