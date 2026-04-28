from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace


class _FakeDeviceRegistry:
    def __init__(self, device):
        devices = [] if device is None else (list(device) if isinstance(device, list) else [device])
        self.devices = {item.id: item for item in devices}
        self.device = devices[0] if len(devices) == 1 else None
        self.updated = None
        self.removed = []

    def async_get_device(self, identifiers):
        for device in self.devices.values():
            if device.identifier in identifiers:
                return device
        return None

    def async_update_device(self, device_id, **kwargs):
        device = self.devices[device_id]
        self.updated = (device_id, kwargs)
        for key, value in kwargs.items():
            setattr(device, key, value)
            if self.device is not None and self.device.id == device_id:
                setattr(self.device, key, value)

    def async_remove_device(self, device_id):
        self.removed.append(device_id)
        self.devices.pop(device_id, None)
        if self.device is not None and self.device.id == device_id:
            self.device = None


class _FakeEntityRegistry:
    def __init__(self, entities):
        self.entities = {item.entity_id: item for item in entities}
        self.removed = []

    def async_remove(self, entity_id):
        self.removed.append(entity_id)
        self.entities.pop(entity_id, None)

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

        self.assertEqual(sensor._attr_device_info["name"], "Managed Devices — ⚙ Settings — Pool Pump")
        self.assertEqual(sensor._attr_device_info["model"], "Managed Devices — ⚙ Settings — Fixed managed load")
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
        self.assertEqual(registry.updated[1]["name"], "Managed Devices — ⚙ Settings — Pool Pump")
        self.assertEqual(registry.updated[1]["model"], "Managed Devices — ⚙ Settings — Fixed managed load")

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

    def test_managed_device_identifier_sanitizes_query_sensitive_device_key(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()

        sensor = sensor_module.ZeroNetExportDeviceManagedSummarySensor(
            coordinator,
            "Pool Pump/Main:One & Boost",
            "Pool Pump",
        )

        self.assertIn(
            ("zero_net_export", "entry-1:managed-device:pool_pump_main_one_boost_18a397c3"),
            sensor._attr_device_info["identifiers"],
        )
        self.assertEqual(
            sensor._attr_device_info["configuration_url"],
            "homeassistant://navigate/config/integrations/integration/zero_net_export?managed_device=entry-1%3APool+Pump%2FMain%3AOne+%26+Boost",
        )

    def test_child_device_identifiers_remain_unique_after_sanitizing_separators(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()

        managed_slash = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "pool/main", "Pool Main")
        managed_colon = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "pool:main", "Pool Main")
        unmanaged_slash = sensor_module.unmanaged_candidate_cleanup_device_info(
            coordinator,
            {"entity_id": "switch.load/a", "name": "Load A", "domain": "switch", "kind": "fixed", "state": "off"},
        )
        unmanaged_colon = sensor_module.unmanaged_candidate_cleanup_device_info(
            coordinator,
            {"entity_id": "switch.load:a", "name": "Load A", "domain": "switch", "kind": "fixed", "state": "off"},
        )

        managed_identifiers = [next(iter(entity._attr_device_info["identifiers"])) for entity in (managed_slash, managed_colon)]
        unmanaged_identifiers = [next(iter(device_info["identifiers"])) for device_info in (unmanaged_slash, unmanaged_colon)]

        self.assertNotEqual(managed_identifiers[0], managed_identifiers[1])
        self.assertNotEqual(unmanaged_identifiers[0], unmanaged_identifiers[1])
        for _, identifier in managed_identifiers + unmanaged_identifiers:
            suffix = identifier.rsplit(":", 1)[-1]
            self.assertRegex(suffix, r"^[a-z0-9_]+_[a-f0-9]{8}$")

    def test_child_device_identifiers_remain_unique_after_case_normalizing(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()

        managed_upper = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "Pool", "Pool")
        managed_lower = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "pool", "pool")
        unmanaged_upper = sensor_module.unmanaged_candidate_cleanup_device_info(
            coordinator,
            {"entity_id": "switch.Load", "name": "Load", "domain": "switch", "kind": "fixed", "state": "off"},
        )
        unmanaged_lower = sensor_module.unmanaged_candidate_cleanup_device_info(
            coordinator,
            {"entity_id": "switch.load", "name": "load", "domain": "switch", "kind": "fixed", "state": "off"},
        )

        managed_identifiers = [next(iter(entity._attr_device_info["identifiers"])) for entity in (managed_upper, managed_lower)]
        unmanaged_identifiers = [next(iter(device_info["identifiers"])) for device_info in (unmanaged_upper, unmanaged_lower)]

        self.assertNotEqual(managed_identifiers[0], managed_identifiers[1])
        self.assertNotEqual(unmanaged_identifiers[0], unmanaged_identifiers[1])
        self.assertRegex(managed_identifiers[0][1].rsplit(":", 1)[-1], r"^pool_[a-f0-9]{8}$")
        self.assertEqual(managed_identifiers[1][1].rsplit(":", 1)[-1], "pool")
        self.assertRegex(unmanaged_identifiers[0][1].rsplit(":", 1)[-1], r"^switch_load_[a-f0-9]{8}$")
        self.assertRegex(unmanaged_identifiers[1][1].rsplit(":", 1)[-1], r"^switch_load_[a-f0-9]{8}$")

    def test_unmanaged_candidate_cleanup_device_info_is_identifier_only(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        candidate = {
            "entity_id": "switch.hot_water",
            "name": "Hot Water",
            "domain": "switch",
            "kind": "fixed",
            "state": "off",
        }

        device_info = sensor_module.unmanaged_candidate_cleanup_device_info(coordinator, candidate)

        self.assertEqual(
            device_info,
            {
                "identifiers": {
                    ("zero_net_export", "entry-1:unmanaged-candidate:switch_hot_water_b4dd5c9c")
                }
            },
        )
        self.assertNotIn("name", device_info)
        self.assertNotIn("model", device_info)
        self.assertNotIn("configuration_url", device_info)
        self.assertNotIn("via_device", device_info)

    def test_managed_device_async_added_removes_legacy_raw_registry_row(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        sensor = sensor_module.ZeroNetExportDeviceManagedSummarySensor(
            coordinator,
            "pool.pump/main:one",
            "Pool Pump",
        )
        current_identifier = (
            "zero_net_export",
            "entry-1:managed-device:pool_pump_main_one_82055144",
        )
        raw_legacy_identifier = (
            "zero_net_export",
            "entry-1:managed-device:pool.pump/main:one",
        )
        normalized_legacy_identifier = (
            "zero_net_export",
            "entry-1:managed-device:pool_pump_main_one",
        )
        registry = _FakeDeviceRegistry(
            [
                SimpleNamespace(id="raw-legacy-device", identifier=raw_legacy_identifier, configuration_url=None),
                SimpleNamespace(id="normalized-legacy-device", identifier=normalized_legacy_identifier, configuration_url=None),
                SimpleNamespace(id="current-device", identifier=current_identifier, configuration_url=None),
            ]
        )
        sensor.hass = SimpleNamespace(device_registry=registry)

        asyncio.run(sensor.async_added_to_hass())

        self.assertIn("raw-legacy-device", registry.removed)
        self.assertIn("normalized-legacy-device", registry.removed)
        self.assertNotIn("raw-legacy-device", registry.devices)
        self.assertNotIn("normalized-legacy-device", registry.devices)
        self.assertIn("current-device", registry.devices)
        self.assertEqual(registry.updated[0], "current-device")

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

    def test_unmanaged_candidate_cleanup_uses_legacy_device_list_naming(self) -> None:
        sensor_module = _load_sensor_module()

        self.assertTrue(hasattr(sensor_module, "_cleanup_legacy_unmanaged_candidate_device_rows"))
        self.assertFalse(hasattr(sensor_module, "_remove_unmanaged_candidate_peer_rows"))

    def test_setup_entry_suppresses_unmanaged_candidate_peer_rows(self) -> None:
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
        self.assertIn("Managed Devices — ⚙ Settings — Pool Pump", device_names)
        self.assertNotIn("Un Managed — Hot Water", device_names)

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
        self.assertIn("Managed Devices — ⚙ Settings — pool", device_names)

    def test_setup_entry_keeps_managed_row_and_suppresses_candidate_peer_rows_when_detail_is_none(self) -> None:
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
        self.assertIn("Managed Devices — ⚙ Settings — pool", device_names)
        self.assertNotIn("Un Managed — Hot Water", device_names)
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
        self.assertIn("Managed Devices — ⚙ Settings — pool", device_names)

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
            "Managed Devices — ⚙ Settings — pool",
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
        self.assertIn("Managed Devices — ⚙ Settings — Runtime Pool Pump", device_names)
        self.assertIn("Managed Devices — ⚙ Settings — EV Charger", device_names)
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
            and entity._attr_device_info.get("name") == "Managed Devices — ⚙ Settings — Pool Pump"
        ]
        self.assertTrue(managed_infos)
        self.assertTrue(
            all(info.get("model") == "Managed Devices — ⚙ Settings — Fixed managed load" for info in managed_infos)
        )
        self.assertNotIn("Un Managed — Hot Water", device_names)
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
            "Managed Devices — ⚙ Settings — EV Charger",
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
            "Managed Devices — ⚙ Settings — EV Charger",
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
            if (getattr(entity, "_attr_device_info", None) or {}).get("name") == "Managed Devices — ⚙ Settings — Pool Pump"
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

        self.assertEqual(managed_summary._attr_name, "⚙ Settings — Main Pool Pump managed summary")
        self.assertEqual(status._attr_name, "⚙ Settings — Main Pool Pump status")
        self.assertEqual(managed_summary._attr_device_info["name"], "Managed Devices — ⚙ Settings — Main Pool Pump")
        self.assertEqual(managed_summary._attr_device_info["model"], "Managed Devices — ⚙ Settings — Variable managed load")
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

    def test_setup_entry_suppresses_new_unmanaged_candidate_peer_rows_after_setup(self) -> None:
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

        self.assertNotIn(
            "Un Managed — Hot Water",
            [
                entity._attr_device_info.get("name")
                for entity in added
                if getattr(entity, "_attr_device_info", None)
            ],
        )

    def test_setup_entry_removes_stale_unmanaged_candidate_registry_rows_after_setup(self) -> None:
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
            identifier=("zero_net_export", "entry-1:unmanaged-candidate:switch_hot_water_b4dd5c9c"),
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
        self.assertEqual(registry.removed, ["unmanaged-device-1"])

        current_states.clear()
        listeners[-1]()

        self.assertEqual(registry.removed, ["unmanaged-device-1"])

    def test_setup_entry_removes_preexisting_unmanaged_registry_rows_without_current_candidates(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})
        registry = _FakeDeviceRegistry(
            [
                SimpleNamespace(
                    id="stale-unmanaged-device",
                    identifier=("zero_net_export", "entry-1:unmanaged-candidate:switch_old_load"),
                ),
                SimpleNamespace(
                    id="managed-device",
                    identifier=("zero_net_export", "entry-1:managed-device:pool"),
                ),
            ]
        )
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: []),
            device_registry=registry,
        )
        entry = SimpleNamespace(entry_id="entry-1", async_on_unload=lambda unsubscribe: None)
        added = []
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: []

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())

        self.assertEqual(registry.removed, ["stale-unmanaged-device"])
        self.assertIn("managed-device", registry.devices)

    def test_setup_entry_removes_entity_registry_entries_for_stale_unmanaged_peer_rows(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})
        registry = _FakeDeviceRegistry(
            [
                SimpleNamespace(
                    id="stale-unmanaged-device",
                    identifier=("zero_net_export", "entry-1:unmanaged-candidate:switch_old_load"),
                ),
                SimpleNamespace(
                    id="controller-device",
                    identifier=("zero_net_export", "entry-1"),
                ),
            ]
        )
        entity_registry = _FakeEntityRegistry(
            [
                SimpleNamespace(
                    entity_id="sensor.old_load_unmanaged_candidate",
                    config_entry_id="entry-1",
                    device_id="stale-unmanaged-device",
                    unique_id="entry-1_unmanaged_candidate_switch_old_load",
                ),
                SimpleNamespace(
                    entity_id="sensor.orphaned_load_unmanaged_candidate",
                    config_entry_id="entry-1",
                    device_id=None,
                    unique_id="entry-1_orphaned_load_unmanaged_candidate",
                ),
                SimpleNamespace(
                    entity_id="sensor.old_load_unmanaged_candidate_switch_old_load",
                    config_entry_id="entry-1",
                    device_id=None,
                    unique_id="entry-1_unmanaged_candidate_switch_old_load",
                ),
                SimpleNamespace(
                    entity_id="sensor.new_registry_shape_old_load_unmanaged_candidate",
                    config_entry_id=None,
                    config_entry_ids={"entry-1"},
                    device_id=None,
                    unique_id="entry-1_unmanaged_candidate_switch_new_shape",
                ),
                SimpleNamespace(
                    entity_id="sensor.missing_config_id_old_load_unmanaged_candidate",
                    config_entry_id=None,
                    device_id="stale-unmanaged-device",
                    unique_id="entry-1_unmanaged_candidate_switch_missing_config_id",
                ),
                SimpleNamespace(
                    entity_id="sensor.missing_config_orphaned_old_load_unmanaged_candidate",
                    config_entry_id=None,
                    device_id=None,
                    unique_id="entry-1_unmanaged_candidate_switch_missing_config_orphaned",
                ),
                SimpleNamespace(
                    entity_id="sensor.other_missing_config_orphaned_old_load_unmanaged_candidate",
                    config_entry_id=None,
                    device_id=None,
                    unique_id="other-entry_unmanaged_candidate_switch_missing_config_orphaned",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_orphaned_unmanaged_candidate_count",
                    config_entry_id="entry-1",
                    device_id=None,
                    unique_id="entry-1_unmanaged_candidate_count",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_unmanaged_candidate_count",
                    config_entry_id="entry-1",
                    device_id="controller-device",
                    unique_id="entry-1_unmanaged_candidate_count",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_attached_unmanaged_candidate_count",
                    config_entry_id="entry-1",
                    device_id="stale-unmanaged-device",
                    unique_id="entry-1_unmanaged_candidate_count",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_top_unmanaged_candidate",
                    config_entry_id="entry-1",
                    device_id=None,
                    unique_id="entry-1_top_unmanaged_candidate",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_attached_top_unmanaged_candidate",
                    config_entry_id="entry-1",
                    device_id="stale-unmanaged-device",
                    unique_id="entry-1_top_unmanaged_candidate",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_orphaned_top_unmanaged_candidate",
                    config_entry_id="entry-1",
                    device_id=None,
                    unique_id=None,
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_attached_current_top_unmanaged_candidate",
                    config_entry_id="entry-1",
                    device_id="stale-unmanaged-device",
                    unique_id=None,
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_attached_candidate_shortlist",
                    config_entry_id="entry-1",
                    device_id="stale-unmanaged-device",
                    unique_id="entry-1_candidate_shortlist",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_attached_top_candidate_fit",
                    config_entry_id="entry-1",
                    device_id="stale-unmanaged-device",
                    unique_id="entry-1_top_candidate_fit",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_attached_top_candidate_warnings",
                    config_entry_id="entry-1",
                    device_id="stale-unmanaged-device",
                    unique_id="entry-1_top_candidate_warnings",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_attached_candidate_shortlist_fit",
                    config_entry_id="entry-1",
                    device_id="stale-unmanaged-device",
                    unique_id="entry-1_candidate_shortlist_fit",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_attached_fleet_console_next_step",
                    config_entry_id="entry-1",
                    device_id="stale-unmanaged-device",
                    unique_id="entry-1_fleet_console_next_step",
                ),
                SimpleNamespace(
                    entity_id="sensor.other_entry_old_load_unmanaged_candidate",
                    config_entry_id="other-entry",
                    device_id="stale-unmanaged-device",
                    unique_id="other-entry_unmanaged_candidate_switch_old_load",
                ),
            ]
        )
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: []),
            device_registry=registry,
            entity_registry=entity_registry,
        )
        entry = SimpleNamespace(entry_id="entry-1", async_on_unload=lambda unsubscribe: None)
        added = []
        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: []

        async def run_setup() -> None:
            await sensor_module.async_setup_entry(hass, entry, added.extend)

        asyncio.run(run_setup())

        self.assertEqual(registry.removed, ["stale-unmanaged-device"])
        self.assertEqual(
            entity_registry.removed,
            [
                "sensor.old_load_unmanaged_candidate",
                "sensor.orphaned_load_unmanaged_candidate",
                "sensor.old_load_unmanaged_candidate_switch_old_load",
                "sensor.new_registry_shape_old_load_unmanaged_candidate",
                "sensor.missing_config_id_old_load_unmanaged_candidate",
                "sensor.missing_config_orphaned_old_load_unmanaged_candidate",
            ],
        )
        self.assertIn("sensor.other_missing_config_orphaned_old_load_unmanaged_candidate", entity_registry.entities)
        self.assertIn("sensor.zero_net_export_orphaned_unmanaged_candidate_count", entity_registry.entities)
        self.assertIn("sensor.zero_net_export_unmanaged_candidate_count", entity_registry.entities)
        self.assertIn("sensor.zero_net_export_attached_unmanaged_candidate_count", entity_registry.entities)
        self.assertIn("sensor.zero_net_export_top_unmanaged_candidate", entity_registry.entities)
        self.assertIn("sensor.zero_net_export_attached_top_unmanaged_candidate", entity_registry.entities)
        self.assertIn("sensor.zero_net_export_orphaned_top_unmanaged_candidate", entity_registry.entities)
        self.assertIn("sensor.zero_net_export_attached_current_top_unmanaged_candidate", entity_registry.entities)
        self.assertIn("sensor.zero_net_export_attached_candidate_shortlist", entity_registry.entities)
        self.assertIn("sensor.zero_net_export_attached_top_candidate_fit", entity_registry.entities)
        self.assertIn("sensor.zero_net_export_attached_top_candidate_warnings", entity_registry.entities)
        self.assertIn("sensor.zero_net_export_attached_candidate_shortlist_fit", entity_registry.entities)
        self.assertIn("sensor.zero_net_export_attached_fleet_console_next_step", entity_registry.entities)
        self.assertIn("sensor.other_entry_old_load_unmanaged_candidate", entity_registry.entities)

    def test_unmanaged_cleanup_without_device_enumeration_removes_orphan_entity_registry_entries(self) -> None:
        sensor_module = _load_sensor_module()
        entity_registry = _FakeEntityRegistry(
            [
                SimpleNamespace(
                    entity_id="sensor.orphaned_old_load_unmanaged_candidate",
                    config_entry_id=None,
                    device_id=None,
                    unique_id="entry-1_unmanaged_candidate_switch_old_load",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_unmanaged_candidate_count",
                    config_entry_id="entry-1",
                    device_id=None,
                    unique_id="entry-1_unmanaged_candidate_count",
                ),
                SimpleNamespace(
                    entity_id="sensor.other_entry_old_load_unmanaged_candidate",
                    config_entry_id="other-entry",
                    device_id=None,
                    unique_id="other-entry_unmanaged_candidate_switch_old_load",
                ),
            ]
        )
        hass = SimpleNamespace(
            device_registry=SimpleNamespace(async_remove_device=lambda device_id: None),
            entity_registry=entity_registry,
        )

        removed_device_ids = sensor_module.remove_unmanaged_candidate_child_devices_for_entry(hass, "entry-1")

        self.assertEqual(removed_device_ids, set())
        self.assertEqual(entity_registry.removed, ["sensor.orphaned_old_load_unmanaged_candidate"])
        self.assertIn("sensor.zero_net_export_unmanaged_candidate_count", entity_registry.entities)
        self.assertIn("sensor.other_entry_old_load_unmanaged_candidate", entity_registry.entities)

    def test_unmanaged_cleanup_with_unreadable_device_enumeration_removes_orphan_entity_registry_entries(self) -> None:
        sensor_module = _load_sensor_module()

        class _UnreadableDevices:
            def values(self):
                raise RuntimeError("registry storage is unavailable")

        entity_registry = _FakeEntityRegistry(
            [
                SimpleNamespace(
                    entity_id="sensor.orphaned_old_load_unmanaged_candidate",
                    config_entry_id=None,
                    device_id=None,
                    unique_id="entry-1_unmanaged_candidate_switch_old_load",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_unmanaged_candidate_count",
                    config_entry_id="entry-1",
                    device_id=None,
                    unique_id="entry-1_unmanaged_candidate_count",
                ),
                SimpleNamespace(
                    entity_id="sensor.other_entry_old_load_unmanaged_candidate",
                    config_entry_id="other-entry",
                    device_id=None,
                    unique_id="other-entry_unmanaged_candidate_switch_old_load",
                ),
            ]
        )
        hass = SimpleNamespace(
            device_registry=SimpleNamespace(
                async_remove_device=lambda device_id: None,
                devices=_UnreadableDevices(),
            ),
            entity_registry=entity_registry,
        )

        removed_device_ids = sensor_module.remove_unmanaged_candidate_child_devices_for_entry(hass, "entry-1")

        self.assertEqual(removed_device_ids, set())
        self.assertEqual(entity_registry.removed, ["sensor.orphaned_old_load_unmanaged_candidate"])
        self.assertIn("sensor.zero_net_export_unmanaged_candidate_count", entity_registry.entities)
        self.assertIn("sensor.other_entry_old_load_unmanaged_candidate", entity_registry.entities)

    def test_current_unmanaged_candidate_direct_cleanup_removes_attached_entity_registry_entries(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = self._coordinator()
        coordinator.data = SimpleNamespace(validation_details={})

        class _LookupOnlyDeviceRegistry:
            def __init__(self, device):
                self.device = device
                self.removed = []

            def async_get_device(self, identifiers):
                if self.device and self.device.identifier in identifiers:
                    return self.device
                return None

            def async_remove_device(self, device_id):
                self.removed.append(device_id)
                if self.device and self.device.id == device_id:
                    self.device = None

        registry = _LookupOnlyDeviceRegistry(
            SimpleNamespace(
                id="current-unmanaged-device",
                identifier=("zero_net_export", "entry-1:unmanaged-candidate:switch_hot_water_b4dd5c9c"),
            )
        )
        entity_registry = _FakeEntityRegistry(
            [
                SimpleNamespace(
                    entity_id="sensor.hot_water_unmanaged_candidate",
                    config_entry_id="entry-1",
                    device_id="current-unmanaged-device",
                    unique_id="entry-1_unmanaged_candidate_switch_hot_water",
                ),
                SimpleNamespace(
                    entity_id="sensor.zero_net_export_unmanaged_candidate_count",
                    config_entry_id="entry-1",
                    device_id=None,
                    unique_id="entry-1_unmanaged_candidate_count",
                ),
            ]
        )
        hass = SimpleNamespace(
            data={"zero_net_export": {"entry-1": coordinator}},
            states=SimpleNamespace(async_all=lambda: []),
            device_registry=registry,
            entity_registry=entity_registry,
        )
        candidate = {
            "entity_id": "switch.hot_water",
            "name": "Hot Water",
            "domain": "switch",
            "kind": "fixed",
            "state": "off",
        }

        sensor_module.remove_integration_page_child_device_registry(
            hass,
            sensor_module.unmanaged_candidate_cleanup_device_info(coordinator, candidate),
        )

        self.assertEqual(registry.removed, ["current-unmanaged-device"])
        self.assertEqual(entity_registry.removed, ["sensor.hot_water_unmanaged_candidate"])
        self.assertIn("sensor.zero_net_export_unmanaged_candidate_count", entity_registry.entities)

    def test_setup_entry_keeps_unmanaged_candidates_out_of_peer_rows_when_details_change(self) -> None:
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

        current_states[:] = [
            SimpleNamespace(
                entity_id="switch.hot_water",
                state="on",
                attributes={"friendly_name": "Hot Water Boost"},
            )
        ]
        listeners[-1]()

        device_names = [
            entity._attr_device_info.get("name")
            for entity in added
            if getattr(entity, "_attr_device_info", None)
        ]
        self.assertNotIn("Un Managed — Hot Water", device_names)
        self.assertNotIn("Un Managed — Hot Water Boost", device_names)

    def test_setup_entry_removes_unmanaged_candidate_peer_rows_on_ha_state_change(self) -> None:
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

        self.assertNotIn(
            "Un Managed — Hot Water",
            [
                entity._attr_device_info.get("name")
                for entity in added
                if getattr(entity, "_attr_device_info", None)
            ],
        )


if __name__ == "__main__":
    unittest.main()
