from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace


class _FakeDeviceRegistry:
    def __init__(self, device):
        self.device = device
        self.updated = None
        self.removed = []

    def async_get_device(self, identifiers):
        return self.device if self.device is not None and self.device.identifier in identifiers else None

    def async_update_device(self, device_id, **kwargs):
        self.updated = (device_id, kwargs)
        for key, value in kwargs.items():
            setattr(self.device, key, value)

    def async_remove_device(self, device_id):
        self.removed.append(device_id)
        if self.device is not None and self.device.id == device_id:
            self.device = None

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
        self.assertNotIn("suggested_area", sensor._attr_device_info)
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

        self.assertEqual(registry.updated[0], "device-1")
        self.assertEqual(
            registry.updated[1]["configuration_url"],
            "homeassistant://navigate/config/integrations/integration/zero_net_export?managed_device=entry-1%3Apool",
        )
        self.assertEqual(registry.updated[1]["name"], "Managed Devices — Pool Pump")
        self.assertEqual(registry.updated[1]["model"], "Managed Devices — Fixed managed load")

    def test_managed_device_configuration_url_encodes_query_value(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()

        sensor = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "pool pump&main", "Pool Pump")

        self.assertEqual(
            sensor._attr_device_info["configuration_url"],
            "homeassistant://navigate/config/integrations/integration/zero_net_export?managed_device=entry-1%3Apool+pump%26main",
        )

    def test_managed_device_configuration_url_preserves_raw_device_key_separators(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()

        sensor = sensor_module.ZeroNetExportDeviceManagedSummarySensor(
            coordinator,
            "pool.pump/main:one",
            "Pool Pump",
        )

        self.assertEqual(
            sensor._attr_device_info["configuration_url"],
            "homeassistant://navigate/config/integrations/integration/zero_net_export?managed_device=entry-1%3Apool.pump%2Fmain%3Aone",
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
        self.assertNotIn("suggested_area", sensor._attr_device_info)
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

        self.assertEqual(registry.updated[0], "device-2")
        self.assertEqual(
            registry.updated[1]["configuration_url"],
            "homeassistant://navigate/config/entities?entity_id=switch.hot_water",
        )
        self.assertEqual(registry.updated[1]["name"], "Un Managed — Hot Water")
        self.assertEqual(registry.updated[1]["model"], "Un Managed — Fixed unmanaged candidate")

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

    def test_base_sensor_tolerates_missing_runtime_value_attributes(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})

        sensor = sensor_module.ZeroNetExportSensor(
            coordinator,
            "grid_power_w",
            "Grid power",
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

    def test_setup_entry_keeps_managed_row_and_candidates_when_detail_is_none(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data.device_details = {"pool": None}
        captured_managed_ids = []

        def discover_candidates(states, managed_entity_ids):
            captured_managed_ids.append(managed_entity_ids)
            return [
                {
                    "entity_id": "switch.hot_water",
                    "name": "Hot Water",
                    "domain": "switch",
                    "kind": "fixed",
                    "state": "off",
                }
            ]

        sensor_module.discover_candidate_devices = discover_candidates
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
        self.assertIn("Un Managed — Hot Water", device_names)
        self.assertEqual(captured_managed_ids, [set()])

    def test_setup_entry_tolerates_malformed_managed_detail(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data.device_details = {"pool": "temporarily malformed runtime detail"}
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

    def test_fleet_workspace_summaries_tolerate_null_managed_detail(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data.device_details = {"pool": None}
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: []
        sensor = sensor_module.ZeroNetExportSensor(
            coordinator,
            "managed_fleet_overview",
            "Managed Devices overview",
        )
        sensor.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertIn("1 managed", sensor.native_value)
        self.assertEqual(sensor.extra_state_attributes["managed_devices"], [{}])

    def test_per_device_sensors_tolerate_null_managed_detail(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data.device_details = {"pool": None}

        status = sensor_module.ZeroNetExportDeviceStatusSensor(coordinator, "pool", "Pool")
        summary = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "pool", "Pool")

        self.assertIsNone(status.native_value)
        self.assertEqual(status.extra_state_attributes, {})
        self.assertIn("status unknown", summary.native_value)

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

    def test_setup_entry_merges_config_inventory_when_runtime_has_only_some_managed_rows(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data.device_details = {
            "pool": {
                "name": "Runtime Pool Pump",
                "kind": "fixed",
                "entity_id": "switch.pool_pump",
                "status": "ready",
            }
        }
        captured_managed_ids = []

        def discover_candidates(states, managed_entity_ids):
            captured_managed_ids.append(managed_entity_ids)
            return []

        sensor_module.discover_candidate_devices = discover_candidates
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: []),
        )
        entry = SimpleNamespace(
            entry_id="entry-1",
            data={
                "device_inventory_json": '[{"key":"pool","name":"Pool Pump","kind":"fixed","entity_id":"switch.pool_pump","nominal_power_w":1200,"min_power_w":1200,"max_power_w":1200,"step_w":1200},{"key":"ev","name":"EV Charger","kind":"variable","entity_id":"number.ev_charger","nominal_power_w":3200,"min_power_w":600,"max_power_w":3200,"step_w":100}]'
            },
            options={},
        )
        added = []

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())

        device_names = [
            entity._attr_device_info.get("name")
            for entity in added
            if getattr(entity, "_attr_device_info", None)
        ]
        self.assertIn("Managed Devices — Runtime Pool Pump", device_names)
        self.assertIn("Managed Devices — EV Charger", device_names)
        self.assertEqual(captured_managed_ids, [{"switch.pool_pump", "number.ev_charger"}])

    def test_setup_entry_uses_config_inventory_for_managed_rows_before_runtime_details(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})
        captured_managed_ids = []

        def discover_candidates(states, managed_entity_ids):
            captured_managed_ids.append(managed_entity_ids)
            return [
                {
                    "entity_id": "switch.hot_water",
                    "name": "Hot Water",
                    "domain": "switch",
                    "kind": "fixed",
                    "state": "off",
                }
            ]

        sensor_module.discover_candidate_devices = discover_candidates
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: []),
        )
        entry = SimpleNamespace(
            entry_id="entry-1",
            data={
                "device_inventory_json": '[{"key":"pool","name":"Pool Pump","kind":"fixed","entity_id":"switch.pool_pump","nominal_power_w":1200,"min_power_w":1200,"max_power_w":1200,"step_w":1200}]'
            },
            options={},
        )
        added = []

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())

        device_names = [
            entity._attr_device_info.get("name")
            for entity in added
            if getattr(entity, "_attr_device_info", None)
        ]
        managed_infos = [
            entity._attr_device_info
            for entity in added
            if getattr(entity, "_attr_device_info", None)
            and entity._attr_device_info.get("name") == "Managed Devices — Pool Pump"
        ]
        self.assertTrue(managed_infos)
        self.assertTrue(
            all(info.get("model") == "Managed Devices — Fixed managed load" for info in managed_infos)
        )
        self.assertIn("Un Managed — Hot Water", device_names)
        self.assertEqual(captured_managed_ids, [{"switch.pool_pump"}])

    def test_config_fallback_managed_rows_keep_status_and_summary_detail(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: []
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: []),
        )
        entry = SimpleNamespace(
            entry_id="entry-1",
            data={
                "device_inventory_json": '[{"key":"pool","name":"Pool Pump","kind":"fixed","entity_id":"switch.pool_pump","nominal_power_w":1200,"min_power_w":1200,"max_power_w":1200,"step_w":1200}]'
            },
            options={},
        )
        added = []

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())

        summary = next(
            entity
            for entity in added
            if isinstance(entity, sensor_module.ZeroNetExportDeviceManagedSummarySensor)
            and entity._device_key == "pool"
        )
        status = next(
            entity
            for entity in added
            if isinstance(entity, sensor_module.ZeroNetExportDeviceStatusSensor)
            and entity._device_key == "pool"
        )

        self.assertIn("fixed load", summary.native_value)
        self.assertIn("configured", summary.native_value)
        self.assertEqual(status.native_value, "configured")
        self.assertEqual(status.extra_state_attributes["entity_id"], "switch.pool_pump")

    def test_config_fallback_managed_rows_are_excluded_from_later_unmanaged_discovery(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})
        captured_managed_ids = []

        def discover_candidates(states, managed_entity_ids):
            captured_managed_ids.append(managed_entity_ids)
            return []

        sensor_module.discover_candidate_devices = discover_candidates
        hass = SimpleNamespace(
            states=SimpleNamespace(async_all=lambda: []),
        )
        coordinator._zne_integration_page_managed_details = {
            "pool": {"name": "Pool Pump", "kind": "fixed", "entity_id": "switch.pool_pump"}
        }

        sensor_module._candidate_devices_for_state(coordinator, hass, coordinator.data)

        self.assertEqual(captured_managed_ids, [{"switch.pool_pump"}])

    def test_setup_entry_syncs_new_managed_device_rows_after_setup(self) -> None:
        sensor_module = _load_sensor_module()
        listeners = []

        def add_listener(listener):
            listeners.append(listener)
            return lambda: listeners.remove(listener)

        coordinator = self._coordinator()
        coordinator.async_add_listener = add_listener
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: []),
        )
        entry = SimpleNamespace(entry_id="entry-1", async_on_unload=lambda unsubscribe: None)
        added = []
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: []

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())
        self.assertTrue(listeners)
        self.assertNotIn(
            "Managed Devices — EV Charger",
            [
                entity._attr_device_info.get("name")
                for entity in added
                if getattr(entity, "_attr_device_info", None)
            ],
        )

        coordinator.data.device_details["ev"] = {
            "name": "EV Charger",
            "kind": "variable",
            "entity_id": "number.ev_charger",
            "status": "ready",
        }
        listeners[0]()

        self.assertIn(
            "Managed Devices — EV Charger",
            [
                entity._attr_device_info.get("name")
                for entity in added
                if getattr(entity, "_attr_device_info", None)
            ],
        )

    def test_setup_entry_removes_stale_managed_device_rows_after_setup(self) -> None:
        sensor_module = _load_sensor_module()
        listeners = []

        def add_listener(listener):
            listeners.append(listener)
            return lambda: listeners.remove(listener)

        coordinator = self._coordinator()
        coordinator.async_add_listener = add_listener
        registry_device = SimpleNamespace(
            id="managed-device-1",
            identifier=("zero_net_export", "entry-1:managed-device:pool"),
        )
        registry = _FakeDeviceRegistry(registry_device)
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: []),
            device_registry=registry,
        )
        entry = SimpleNamespace(entry_id="entry-1", data={}, options={}, async_on_unload=lambda unsubscribe: None)
        added = []
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: []

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())
        stale_entities = [
            entity
            for entity in added
            if (getattr(entity, "_attr_device_info", None) or {}).get("name") == "Managed Devices — Pool Pump"
        ]
        self.assertTrue(stale_entities)
        removed = []
        for stale_entity in stale_entities:
            stale_entity.async_remove = lambda **kwargs: removed.append(kwargs)

        coordinator.data.device_details.clear()
        listeners[0]()

        self.assertEqual(removed, [{"force_remove": True}] * len(stale_entities))
        self.assertEqual(registry.removed, ["managed-device-1"])

    def test_setup_entry_refreshes_existing_managed_device_row_metadata(self) -> None:
        sensor_module = _load_sensor_module()
        listeners = []

        def add_listener(listener):
            listeners.append(listener)
            return lambda: listeners.remove(listener)

        coordinator = self._coordinator()
        coordinator.async_add_listener = add_listener
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: []),
        )
        entry = SimpleNamespace(entry_id="entry-1", async_on_unload=lambda unsubscribe: None)
        added = []
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: []

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())
        managed_summary = next(
            entity
            for entity in added
            if isinstance(entity, sensor_module.ZeroNetExportDeviceManagedSummarySensor)
            and entity._device_key == "pool"
        )
        writes = []
        managed_summary.async_write_ha_state = lambda: writes.append(managed_summary._attr_device_info["name"])

        self.assertNotIn("device_pool_current_target_power_w", [getattr(entity, "_key", None) for entity in added])

        coordinator.data.device_details["pool"]["name"] = "Main Pool Pump"
        coordinator.data.device_details["pool"]["kind"] = "variable"
        listeners[0]()

        status = next(
            entity
            for entity in added
            if isinstance(entity, sensor_module.ZeroNetExportDeviceStatusSensor)
            and entity._device_key == "pool"
        )

        self.assertEqual(managed_summary._attr_name, "Main Pool Pump managed summary")
        self.assertEqual(status._attr_name, "Main Pool Pump status")
        self.assertEqual(managed_summary._attr_device_info["name"], "Managed Devices — Main Pool Pump")
        self.assertEqual(managed_summary._attr_device_info["model"], "Managed Devices — Variable managed load")
        self.assertIn("device_pool_current_target_power_w", [getattr(entity, "_key", None) for entity in added])
        self.assertTrue(writes)

    def test_candidate_cache_invalidates_when_ha_candidate_states_change(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})
        current_states = [
            SimpleNamespace(
                entity_id="switch.hot_water",
                state="off",
                attributes={"friendly_name": "Hot Water"},
            )
        ]
        hass = SimpleNamespace(
            states=SimpleNamespace(async_all=lambda: list(current_states)),
        )
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: [
            {
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name", state.entity_id),
                "domain": state.entity_id.split(".", 1)[0],
                "kind": "fixed",
                "state": state.state,
                "unit": "",
                "device_class": "",
            }
            for state in states
            if state.entity_id not in managed_entity_ids
        ]

        first = sensor_module._candidate_devices_for_state(coordinator, hass, coordinator.data)
        current_states[:] = [
            SimpleNamespace(
                entity_id="switch.ev_charger",
                state="off",
                attributes={"friendly_name": "EV Charger"},
            )
        ]
        second = sensor_module._candidate_devices_for_state(coordinator, hass, coordinator.data)

        self.assertEqual([candidate["entity_id"] for candidate in first], ["switch.hot_water"])
        self.assertEqual([candidate["entity_id"] for candidate in second], ["switch.ev_charger"])

    def test_setup_entry_syncs_new_unmanaged_candidate_rows_after_setup(self) -> None:
        sensor_module = _load_sensor_module()
        listeners = []

        def add_listener(listener):
            listeners.append(listener)
            return lambda: listeners.remove(listener)

        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})
        coordinator.async_add_listener = add_listener
        current_states = []
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: list(current_states)),
        )
        entry = SimpleNamespace(entry_id="entry-1", async_on_unload=lambda unsubscribe: None)
        added = []
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: [
            {
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name", state.entity_id),
                "domain": state.entity_id.split(".", 1)[0],
                "kind": "fixed",
                "state": state.state,
            }
            for state in states
            if state.entity_id not in managed_entity_ids
        ]

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())
        self.assertTrue(listeners)
        self.assertNotIn(
            "Un Managed — Hot Water",
            [
                entity._attr_device_info.get("name")
                for entity in added
                if getattr(entity, "_attr_device_info", None)
            ],
        )

        current_states.append(
            SimpleNamespace(
                entity_id="switch.hot_water",
                state="off",
                attributes={"friendly_name": "Hot Water"},
            )
        )
        listeners[-1]()

        self.assertIn(
            "Un Managed — Hot Water",
            [
                entity._attr_device_info.get("name")
                for entity in added
                if getattr(entity, "_attr_device_info", None)
            ],
        )

    def test_setup_entry_removes_stale_unmanaged_candidate_rows_after_setup(self) -> None:
        sensor_module = _load_sensor_module()
        listeners = []

        def add_listener(listener):
            listeners.append(listener)
            return lambda: listeners.remove(listener)

        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})
        coordinator.async_add_listener = add_listener
        registry_device = SimpleNamespace(
            id="unmanaged-device-1",
            identifier=("zero_net_export", "entry-1:unmanaged-candidate:switch_hot_water"),
        )
        registry = _FakeDeviceRegistry(registry_device)
        current_states = [
            SimpleNamespace(
                entity_id="switch.hot_water",
                state="off",
                attributes={"friendly_name": "Hot Water"},
            )
        ]
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: list(current_states)),
            device_registry=registry,
        )
        entry = SimpleNamespace(entry_id="entry-1", async_on_unload=lambda unsubscribe: None)
        added = []
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: [
            {
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name", state.entity_id),
                "domain": state.entity_id.split(".", 1)[0],
                "kind": "fixed",
                "state": state.state,
            }
            for state in states
            if state.entity_id not in managed_entity_ids
        ]

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())
        stale_entity = next(
            entity
            for entity in added
            if (getattr(entity, "_attr_device_info", None) or {}).get("name") == "Un Managed — Hot Water"
        )
        removed = []
        stale_entity.async_remove = lambda **kwargs: removed.append(kwargs)

        current_states.clear()
        listeners[-1]()

        self.assertEqual(removed, [{"force_remove": True}])
        self.assertEqual(registry.removed, ["unmanaged-device-1"])

    def test_setup_entry_refreshes_existing_unmanaged_candidate_row_details(self) -> None:
        sensor_module = _load_sensor_module()
        listeners = []

        def add_listener(listener):
            listeners.append(listener)
            return lambda: listeners.remove(listener)

        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})
        coordinator.async_add_listener = add_listener
        current_states = [
            SimpleNamespace(
                entity_id="switch.hot_water",
                state="off",
                attributes={"friendly_name": "Hot Water"},
            )
        ]
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: list(current_states)),
        )
        entry = SimpleNamespace(entry_id="entry-1", async_on_unload=lambda unsubscribe: None)
        added = []
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: [
            {
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name", state.entity_id),
                "domain": state.entity_id.split(".", 1)[0],
                "kind": "fixed",
                "state": state.state,
            }
            for state in states
            if state.entity_id not in managed_entity_ids
        ]

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())
        candidate = next(
            entity
            for entity in added
            if isinstance(entity, sensor_module.ZeroNetExportUnmanagedCandidateSensor)
        )
        writes = []
        candidate.async_write_ha_state = lambda: writes.append(candidate.native_value)

        current_states[:] = [
            SimpleNamespace(
                entity_id="switch.hot_water",
                state="on",
                attributes={"friendly_name": "Hot Water Boost"},
            )
        ]
        listeners[-1]()

        self.assertEqual(candidate._attr_name, "Hot Water Boost unmanaged candidate")
        self.assertEqual(candidate._attr_device_info["name"], "Un Managed — Hot Water Boost")
        self.assertEqual(candidate.extra_state_attributes["state"], "on")
        self.assertTrue(writes)

    def test_unmanaged_candidate_update_refreshes_existing_registry_metadata(self) -> None:
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
        device = SimpleNamespace(
            id="device-2",
            identifier=identifier,
            configuration_url="homeassistant://navigate/config/entities?entity_id=switch.hot_water",
            name="Un Managed — Hot Water",
            model="Un Managed — Fixed unmanaged candidate",
        )
        registry = _FakeDeviceRegistry(device)
        sensor.hass = SimpleNamespace(device_registry=registry)

        sensor.update_candidate({
            "entity_id": "switch.hot_water",
            "name": "Hot Water Boost",
            "domain": "switch",
            "kind": "variable",
            "state": "on",
        })

        self.assertEqual(registry.updated[0], "device-2")
        self.assertEqual(registry.updated[1]["name"], "Un Managed — Hot Water Boost")
        self.assertEqual(registry.updated[1]["model"], "Un Managed — Variable unmanaged candidate")

    def test_setup_entry_syncs_unmanaged_candidate_rows_on_ha_state_change(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator_listeners = []
        bus_listeners = []

        def add_listener(listener):
            coordinator_listeners.append(listener)
            return lambda: coordinator_listeners.remove(listener)

        def listen(event_type, listener):
            bus_listeners.append((event_type, listener))
            return lambda: bus_listeners.remove((event_type, listener))

        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})
        coordinator.async_add_listener = add_listener
        current_states = []
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: list(current_states)),
            bus=SimpleNamespace(async_listen=listen),
        )
        entry = SimpleNamespace(entry_id="entry-1", async_on_unload=lambda unsubscribe: None)
        added = []
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: [
            {
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name", state.entity_id),
                "domain": state.entity_id.split(".", 1)[0],
                "kind": "fixed",
                "state": state.state,
            }
            for state in states
            if state.entity_id not in managed_entity_ids
        ]

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())
        self.assertEqual([event_type for event_type, _listener in bus_listeners], ["state_changed"])

        current_states.append(
            SimpleNamespace(
                entity_id="switch.hot_water",
                state="off",
                attributes={"friendly_name": "Hot Water"},
            )
        )
        bus_listeners[0][1](SimpleNamespace(data={"entity_id": "switch.hot_water"}))

        self.assertIn(
            "Un Managed — Hot Water",
            [
                entity._attr_device_info.get("name")
                for entity in added
                if getattr(entity, "_attr_device_info", None)
            ],
        )


if __name__ == "__main__":
    unittest.main()
