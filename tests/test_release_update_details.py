from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from datetime import datetime, timezone
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


class ReleaseUpdateDetailsTests(unittest.TestCase):
    def test_release_update_details_passes_current_version_to_release_info(self) -> None:
        coordinator_module = _load_coordinator_module()
        captured: dict[str, object] = {}

        def _build_release_info(current_version: str, *, include_changelog: bool = True) -> dict[str, object]:
            captured["current_version"] = current_version
            captured["include_changelog"] = include_changelog
            return {
                "current_version": current_version,
                "changes_preview": "Release notes deferred until Diagnostics surfaces request them.",
                "summary": f"Installed version {current_version}",
            }

        coordinator_module.build_release_info = _build_release_info
        coordinator = coordinator_module.ZeroNetExportCoordinator.__new__(coordinator_module.ZeroNetExportCoordinator)
        coordinator._previous_installed_version = None
        coordinator._last_seen_integration_version = coordinator_module.INTEGRATION_VERSION
        coordinator._version_update_detected_at = None

        details = coordinator._release_update_details()

        self.assertEqual(captured["current_version"], coordinator_module.INTEGRATION_VERSION)
        self.assertFalse(captured["include_changelog"])
        self.assertEqual(details["installed_version"], coordinator_module.INTEGRATION_VERSION)
        self.assertFalse(details["update_detected"])

    def test_release_update_details_flags_rollbacks_without_claiming_upgrade(self) -> None:
        coordinator_module = _load_coordinator_module()

        coordinator_module.build_release_info = lambda *args, **kwargs: {
            "current_version": "0.1.83",
            "changes_preview": "Release notes deferred until Diagnostics surfaces request them.",
            "summary": "Installed version 0.1.83",
        }
        coordinator = coordinator_module.ZeroNetExportCoordinator.__new__(coordinator_module.ZeroNetExportCoordinator)
        coordinator._previous_installed_version = "0.1.84"
        coordinator._last_seen_integration_version = "0.1.83"
        coordinator._version_update_detected_at = datetime(2026, 4, 16, tzinfo=timezone.utc)

        details = coordinator._release_update_details()

        self.assertTrue(details["update_detected"])
        self.assertEqual(details["version_change_direction"], -1)
        self.assertIn("Version changed from 0.1.84 to 0.1.83.", details["summary"])
        self.assertIn("rollback or mixed version history", details["summary"])
        self.assertNotIn("Updated from 0.1.84 to 0.1.83.", details["summary"])

    def test_release_update_details_keeps_upgrade_wording_for_newer_builds(self) -> None:
        coordinator_module = _load_coordinator_module()

        coordinator_module.build_release_info = lambda *args, **kwargs: {
            "current_version": "0.1.84",
            "changes_preview": "Release notes deferred until Diagnostics surfaces request them.",
            "summary": "Installed version 0.1.84",
        }
        coordinator = coordinator_module.ZeroNetExportCoordinator.__new__(coordinator_module.ZeroNetExportCoordinator)
        coordinator._previous_installed_version = "0.1.83"
        coordinator._last_seen_integration_version = "0.1.84"
        coordinator._version_update_detected_at = datetime(2026, 4, 16, tzinfo=timezone.utc)

        details = coordinator._release_update_details()

        self.assertTrue(details["update_detected"])
        self.assertEqual(details["version_change_direction"], 1)
        self.assertIn("Updated from 0.1.83 to 0.1.84.", details["summary"])


if __name__ == "__main__":
    unittest.main()
