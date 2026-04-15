from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"
COORDINATOR_PATH = PACKAGE_ROOT / "coordinator.py"
CONST_PATH = PACKAGE_ROOT / "const.py"


class _DummyCoordinatorBase:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def __class_getitem__(cls, item):
        return cls


class _DummyStore:
    def __init__(self, *args, **kwargs) -> None:
        pass


def _load_coordinator_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    ha_pkg = sys.modules.setdefault("homeassistant", types.ModuleType("homeassistant"))

    util_pkg = sys.modules.setdefault("homeassistant.util", types.ModuleType("homeassistant.util"))
    dt_module = types.SimpleNamespace(
        parse_datetime=lambda value: datetime.fromisoformat(value.replace("Z", "+00:00")),
        now=lambda: datetime(2026, 4, 15, tzinfo=timezone.utc),
    )
    util_pkg.dt = dt_module
    ha_pkg.util = util_pkg

    config_entries_module = sys.modules.setdefault(
        "homeassistant.config_entries", types.ModuleType("homeassistant.config_entries")
    )
    config_entries_module.ConfigEntry = object

    helpers_pkg = sys.modules.setdefault("homeassistant.helpers", types.ModuleType("homeassistant.helpers"))
    storage_module = sys.modules.setdefault("homeassistant.helpers.storage", types.ModuleType("homeassistant.helpers.storage"))
    storage_module.Store = _DummyStore
    helpers_pkg.storage = storage_module

    update_coordinator_module = sys.modules.setdefault(
        "homeassistant.helpers.update_coordinator",
        types.ModuleType("homeassistant.helpers.update_coordinator"),
    )
    update_coordinator_module.DataUpdateCoordinator = _DummyCoordinatorBase
    update_coordinator_module.UpdateFailed = RuntimeError

    const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", CONST_PATH)
    assert const_spec and const_spec.loader
    const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = const_module
    const_spec.loader.exec_module(const_module)

    device_model_module = types.ModuleType("custom_components.zero_net_export.device_model")
    device_model_module.DeviceRuntime = object
    device_model_module.build_device_summary = lambda *args, **kwargs: "summary"
    device_model_module.parse_device_configs = lambda *args, **kwargs: ([], [])
    device_model_module.runtime_as_attributes = lambda *args, **kwargs: {}
    sys.modules[device_model_module.__name__] = device_model_module

    executor_module = types.ModuleType("custom_components.zero_net_export.executor")
    executor_module.ActionResult = object
    executor_module.execute_action = lambda *args, **kwargs: None
    sys.modules[executor_module.__name__] = executor_module

    planner_module = types.ModuleType("custom_components.zero_net_export.planner")
    planner_module.PlannerContext = object
    planner_module.PlannedDeviceAction = object
    planner_module.build_control_plan = lambda *args, **kwargs: None
    sys.modules[planner_module.__name__] = planner_module

    release_info_module = types.ModuleType("custom_components.zero_net_export.release_info")
    release_info_module.build_release_info = lambda *args, **kwargs: {}
    sys.modules[release_info_module.__name__] = release_info_module

    repairs_module = types.ModuleType("custom_components.zero_net_export.repairs")
    repairs_module.async_sync_repairs_issues = lambda *args, **kwargs: None
    sys.modules[repairs_module.__name__] = repairs_module

    validation_module = types.ModuleType("custom_components.zero_net_export.validation")
    validation_module.SourceSpec = lambda key, entity_id, quantity, required=True, allow_negative=False: SimpleNamespace(
        key=key,
        entity_id=entity_id,
        quantity=quantity,
        required=required,
        allow_negative=allow_negative,
    )
    validation_module.ValidationIssue = object
    validation_module.get_source_reading = lambda *args, **kwargs: None
    validation_module.issues_as_attributes = lambda *args, **kwargs: {}
    validation_module.parse_source_binding = lambda raw: SimpleNamespace(entity_id=raw, valid=bool(raw))
    validation_module.validate_sources = lambda *args, **kwargs: None
    sys.modules[validation_module.__name__] = validation_module

    coordinator_spec = importlib.util.spec_from_file_location(
        "custom_components.zero_net_export.coordinator",
        COORDINATOR_PATH,
    )
    assert coordinator_spec and coordinator_spec.loader
    coordinator_module = importlib.util.module_from_spec(coordinator_spec)
    sys.modules[coordinator_spec.name] = coordinator_module
    coordinator_spec.loader.exec_module(coordinator_module)
    return coordinator_module


class SourceFreshnessProbeTests(unittest.TestCase):
    def test_companion_data_time_probe_keeps_static_sensor_fresh(self) -> None:
        coordinator_module = _load_coordinator_module()
        coordinator = coordinator_module.ZeroNetExportCoordinator.__new__(coordinator_module.ZeroNetExportCoordinator)
        coordinator.entry = SimpleNamespace(data={"refresh_seconds": 30}, options={})
        coordinator.hass = SimpleNamespace(
            states=SimpleNamespace(
                get=lambda entity_id: {
                    "sensor.x1_p6k_us_s_data_time": SimpleNamespace(
                        state="2026-04-15 10:57:42+00:00",
                        attributes={},
                        last_updated=datetime(2026, 4, 15, 0, 57, 42, tzinfo=timezone.utc),
                    )
                }.get(entity_id)
            )
        )
        spec = SimpleNamespace(
            key="grid_import_power_entity",
            entity_id="sensor.x1_p6k_us_s_grid_import",
            required=True,
            quantity="power",
        )
        now = datetime(2026, 4, 15, 0, 58, 0, tzinfo=timezone.utc)
        sensor_state = SimpleNamespace(last_updated=datetime(2026, 4, 15, 0, 17, 2, tzinfo=timezone.utc))

        stale_sources, freshness = coordinator._source_freshness(
            [spec],
            {"grid_import_power_entity": sensor_state},
            now,
        )

        self.assertEqual(stale_sources, [])
        detail = freshness["grid_import_power_entity"]
        self.assertFalse(detail["stale"])
        self.assertEqual(detail["freshness_probe_entity_id"], "sensor.x1_p6k_us_s_data_time")
        self.assertLess(detail["age_seconds"], 120)
        self.assertEqual(detail["entity_last_updated"], "2026-04-15T00:17:02+00:00")

    def test_energy_sensor_without_companion_probe_gets_longer_stale_threshold(self) -> None:
        coordinator_module = _load_coordinator_module()
        coordinator = coordinator_module.ZeroNetExportCoordinator.__new__(coordinator_module.ZeroNetExportCoordinator)
        coordinator.entry = SimpleNamespace(data={"refresh_seconds": 30}, options={})
        coordinator.hass = SimpleNamespace(states=SimpleNamespace(get=lambda entity_id: None))
        spec = SimpleNamespace(
            key="solar_energy_entity",
            entity_id="sensor.system_rome_yield_total",
            required=True,
            quantity="energy",
        )
        now = datetime(2026, 4, 15, 0, 58, 0, tzinfo=timezone.utc)
        sensor_state = SimpleNamespace(last_updated=now - timedelta(minutes=10))

        stale_sources, freshness = coordinator._source_freshness(
            [spec],
            {"solar_energy_entity": sensor_state},
            now,
        )

        self.assertEqual(stale_sources, [])
        detail = freshness["solar_energy_entity"]
        self.assertFalse(detail["stale"])
        self.assertIsNone(detail["freshness_probe_entity_id"])
        self.assertEqual(detail["stale_threshold_seconds"], 900)
        self.assertGreater(detail["age_seconds"], 120)

    def test_power_sensor_without_companion_probe_stays_stale(self) -> None:
        coordinator_module = _load_coordinator_module()
        coordinator = coordinator_module.ZeroNetExportCoordinator.__new__(coordinator_module.ZeroNetExportCoordinator)
        coordinator.entry = SimpleNamespace(data={"refresh_seconds": 30}, options={})
        coordinator.hass = SimpleNamespace(states=SimpleNamespace(get=lambda entity_id: None))
        spec = SimpleNamespace(
            key="solar_power_entity",
            entity_id="sensor.x1_p6k_us_s_solar_power",
            required=True,
            quantity="power",
        )
        now = datetime(2026, 4, 15, 0, 58, 0, tzinfo=timezone.utc)
        sensor_state = SimpleNamespace(last_updated=now - timedelta(minutes=10))

        stale_sources, freshness = coordinator._source_freshness(
            [spec],
            {"solar_power_entity": sensor_state},
            now,
        )

        self.assertEqual(len(stale_sources), 1)
        detail = freshness["solar_power_entity"]
        self.assertTrue(detail["stale"])
        self.assertIsNone(detail["freshness_probe_entity_id"])
        self.assertEqual(detail["stale_threshold_seconds"], 120)
        self.assertGreater(detail["age_seconds"], 120)


if __name__ == "__main__":
    unittest.main()
