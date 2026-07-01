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
    ha_pkg.__path__ = []

    helpers_pkg = types.ModuleType("homeassistant.helpers")
    helpers_pkg.__path__ = []
    sys.modules[helpers_pkg.__name__] = helpers_pkg

    device_registry_module = types.ModuleType("homeassistant.helpers.device_registry")
    device_registry_module.async_get = lambda hass: hass.device_registry
    sys.modules[device_registry_module.__name__] = device_registry_module

    entity_registry_module = types.ModuleType("homeassistant.helpers.entity_registry")
    entity_registry_module.async_get = lambda hass: hass.entity_registry
    sys.modules[entity_registry_module.__name__] = entity_registry_module

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

    native_support_module = types.ModuleType("custom_components.zero_net_export.native_support")
    native_support_module.DEVICES_CONFIGURE_PATH = "devices path"
    native_support_module.POLICY_CONFIGURE_PATH = "policy path"
    native_support_module.SOURCES_CONFIGURE_PATH = "sources path"
    native_support_module.build_native_command_center_summary = lambda coordinator: {}
    native_support_module.build_native_operator_readiness = lambda coordinator: {}
    native_support_module.format_fleet_activity_for_operator = lambda summary: str(summary or "").replace(
        "1 managed | 2 unmanaged backlog",
        "Managed devices: 1 managed; Unmanaged backlog: 2 unmanaged backlog",
    )
    native_support_module.build_source_attention_details = lambda state: {}
    native_support_module.build_source_attention_brief = lambda state, merged, limit=3, blocking_only=False: "None"
    native_support_module.build_source_attention_role_summary = lambda state, merged, limit=6, blocking_only=False: "None"
    native_support_module.build_source_attention_summary = lambda state, merged, limit=4, blocking_only=False: "None"
    native_support_module.summarize_validation_issue_messages = lambda state, severities=None, limit=3: "None"
    sys.modules[native_support_module.__name__] = native_support_module

    release_info_module = types.ModuleType("custom_components.zero_net_export.release_info")
    release_info_module.build_release_info = lambda *args, **kwargs: {}
    sys.modules[release_info_module.__name__] = release_info_module

    candidate_utils_module = types.ModuleType("custom_components.zero_net_export.candidate_utils")
    def _assess_candidate(candidate):
        name = str((candidate or {}).get("name") or (candidate or {}).get("entity_id") or "")
        lowered = name.lower()
        if "virtual load" in lowered:
            return {
                "confidence": "low",
                "summary": "Looks helper-backed and needs review before promotion.",
                "warnings": ["This is an input_boolean helper."],
            }
        if "ac outlet" in lowered:
            return {
                "confidence": "medium",
                "summary": "Looks like a plausible controllable candidate, but review before promotion.",
                "warnings": ["generic outlet label"],
            }
        return {
            "confidence": "high",
            "summary": "Looks like a plausible controllable candidate, but review before promotion.",
            "warnings": [],
        }

    candidate_utils_module.assess_candidate = _assess_candidate
    candidate_utils_module.build_candidate_fit_summary = lambda candidates, **kwargs: "candidate fit"
    candidate_utils_module.build_candidate_name_summary = lambda candidates, **kwargs: "candidate names"
    candidate_utils_module.build_candidate_overview_summary = lambda candidates, **kwargs: "candidate overview"
    candidate_utils_module.build_candidate_preview = lambda candidate, **kwargs: "candidate preview"
    candidate_utils_module.build_candidate_compact_preview = lambda candidate, **kwargs: (
        (
            f"{candidate.get('name') or candidate.get('entity_id') or 'candidate'} ({candidate.get('kind') or 'unknown'})"
            f" | {candidate_utils_module.build_candidate_review_hint(candidate, include_warning=False)}"
            + (
                f" | warn {((candidate_utils_module.assess_candidate(candidate).get('warnings') or [''])[0])}"
                if (candidate_utils_module.assess_candidate(candidate).get('warnings') or [])
                else ""
            )
        )
        if candidate
        else ""
    )
    candidate_utils_module.build_candidate_review_hint = lambda candidate, include_warning=True, **kwargs: (
        (
            "likely useful"
            if str(candidate_utils_module.assess_candidate(candidate).get("confidence") or "medium") == "high"
            else "review carefully"
        )
        + (
            f" | warn {((candidate_utils_module.assess_candidate(candidate).get('warnings') or [''])[0])}"
            if include_warning and (candidate_utils_module.assess_candidate(candidate).get("warnings") or [])
            else ""
        )
    )
    candidate_utils_module.candidate_needs_review = lambda fit: str((fit or {}).get("confidence") or "medium") != "high"
    candidate_utils_module.candidate_review_kind_counts = lambda candidates: (
        sum(
            1
            for candidate in candidates
            if candidate_utils_module.candidate_needs_review(candidate_utils_module.assess_candidate(candidate))
            and str((candidate or {}).get("kind") or "") != "variable"
        ),
        sum(
            1
            for candidate in candidates
            if candidate_utils_module.candidate_needs_review(candidate_utils_module.assess_candidate(candidate))
            and str((candidate or {}).get("kind") or "") == "variable"
        ),
    )
    candidate_utils_module.first_review_candidate = lambda candidates: next(
        (
            candidate
            for candidate in candidates
            if candidate_utils_module.candidate_needs_review(candidate_utils_module.assess_candidate(candidate))
        ),
        None,
    )
    candidate_utils_module.discover_candidate_devices = lambda states, managed_entity_ids: []
    sys.modules[candidate_utils_module.__name__] = candidate_utils_module

    sensor_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.sensor", SENSOR_PATH)
    assert sensor_spec and sensor_spec.loader
    sensor_module = importlib.util.module_from_spec(sensor_spec)
    sys.modules[sensor_spec.name] = sensor_module
    sensor_spec.loader.exec_module(sensor_module)
    return sensor_module


class SensorEntityCategoryTests(unittest.TestCase):
    def test_command_center_sensor_attributes_expose_grouped_fleet_activity(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module.build_native_command_center_summary = lambda coordinator: {
            "status_summary": "Command center ready.",
            "recommended_path": "devices path",
            "next_action_summary": "Review Managed Devices.",
            "source_status": "Sources ready.",
            "source_attention_roles": "None",
            "fleet_activity_summary": "1 managed | 2 unmanaged backlog",
            "device_status": "Managed Devices: 1 managed, 2 unmanaged backlog.",
            "device_next_step": "Review unmanaged candidates.",
            "policy_status": "Controls ready.",
            "policy_readiness": "Ready.",
            "support_status": "Diagnostics ready.",
            "recommended_section": "Managed Devices",
            "sources_path": "sources path",
            "devices_path": "devices path",
            "policy_path": "policy path",
            "support_path": "support path",
        }
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(validation_details={}),
        )
        sensor = sensor_module.ZeroNetExportSensor(coordinator, "command_center_status", "Command center status")
        attrs = sensor.extra_state_attributes

        self.assertEqual(
            attrs["fleet_activity_summary"],
            "Managed devices: 1 managed; Unmanaged backlog: 2 unmanaged backlog",
        )
        self.assertEqual(attrs["current_focus_section"], "Managed Devices")
        self.assertEqual(attrs["current_focus_path"], "devices path")
        self.assertNotIn("recommended_section", attrs)
        self.assertNotIn("recommended_path", attrs)

    def test_command_center_focus_path_state_is_capped_but_attribute_keeps_full_path(self) -> None:
        sensor_module = _load_sensor_module()
        long_path = "Settings -> " + " -> ".join(f"Very long path segment {index}" for index in range(30))
        sensor_module.build_native_command_center_summary = lambda coordinator: {
            "status_summary": "Command center ready.",
            "recommended_path": long_path,
            "next_action_summary": "Review Diagnostics.",
        }
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(validation_details={}),
        )
        sensor = sensor_module.ZeroNetExportSensor(
            coordinator,
            "command_center_recommended_path",
            "Command center focus path",
        )

        self.assertLessEqual(len(sensor.native_value), 255)
        self.assertTrue(sensor.native_value.endswith("..."))
        self.assertEqual(sensor.extra_state_attributes["current_focus_path"], long_path)

    def test_fleet_next_step_sensor_uses_managed_devices_label(self) -> None:
        sensor_module = _load_sensor_module()

        self.assertEqual(
            sensor_module.SENSOR_DEFS["fleet_console_next_step"],
            "Managed Devices next step",
        )

    def test_recommendation_sensor_display_name_reports_native_next_action(self) -> None:
        sensor_module = _load_sensor_module()

        self.assertEqual(
            sensor_module.SENSOR_DEFS["recommendation"],
            "Current native next action",
        )
        self.assertNotEqual(sensor_module.SENSOR_DEFS["recommendation"], "Recommendation")

    def test_source_attention_sensor_attributes_use_current_next_step_wording(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module.build_native_operator_readiness = lambda coordinator: {"next_step": "Open Sensors."}
        sensor_module.build_source_attention_summary = lambda *args, **kwargs: "Missing solar source"
        sensor_module.summarize_validation_issue_messages = lambda *args, **kwargs: "Missing solar source"
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                validation_details={},
                source_diagnostics={},
            ),
        )
        sensor = sensor_module.ZeroNetExportSensor(
            coordinator,
            "mapped_source_blocker_next_step",
            "Mapped source blocker next step",
        )
        attrs = sensor.extra_state_attributes

        self.assertEqual(attrs["current_native_next_step"], "Open Sensors.")
        self.assertNotIn("recommended_next_step", attrs)

    def test_managed_fleet_attention_names_managed_devices_when_sources_block_review(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module.build_source_attention_summary = lambda *args, **kwargs: "Missing solar source"
        sensor_module.summarize_validation_issue_messages = lambda *args, **kwargs: "Missing solar source"
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        sensor = sensor_module.ZeroNetExportSensor(
            coordinator,
            "managed_fleet_attention",
            "Managed devices attention",
        )
        sensor.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            sensor.native_value,
            "No managed devices yet | source blockers active",
        )

    def test_managed_fleet_attention_uses_bucket_first_clear_state_when_no_attention_remains(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                    },
                }
            ),
        )
        sensor = sensor_module.ZeroNetExportSensor(
            coordinator,
            "managed_fleet_attention",
            "Managed devices attention",
        )
        sensor.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(sensor.native_value, "Managed Devices: clear right now")

    def test_managed_fleet_attention_keeps_empty_fleet_review_in_managed_devices(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
        ]
        sensor_module.assess_candidate = lambda candidate: {
            "confidence": "low",
            "warnings": ["This is an input_boolean helper."],
        }
        sensor_module.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        sensor = sensor_module.ZeroNetExportSensor(
            coordinator,
            "managed_fleet_attention",
            "Managed devices attention",
        )
        sensor.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            sensor.native_value,
            "No managed devices yet | Managed Devices workspace: review unmanaged candidate: Virtual load (fixed) | review carefully | warn This is an input_boolean helper.",
        )

    def test_managed_overview_sensor_uses_managed_devices_label(self) -> None:
        sensor_module = _load_sensor_module()

        self.assertEqual(
            sensor_module.SENSOR_DEFS["device_count"],
            "Managed Devices count",
        )
        self.assertEqual(
            sensor_module.SENSOR_DEFS["enabled_device_count"],
            "Managed Devices enabled count",
        )
        self.assertEqual(
            sensor_module.SENSOR_DEFS["usable_device_count"],
            "Managed Devices usable count",
        )
        self.assertEqual(
            sensor_module.SENSOR_DEFS["controllable_nominal_power_w"],
            "Managed Devices controllable power",
        )
        self.assertEqual(
            sensor_module.SENSOR_DEFS["device_status_summary"],
            "Managed Devices status summary",
        )
        self.assertEqual(
            sensor_module.SENSOR_DEFS["managed_devices_surface"],
            "Managed Devices surface",
        )
        self.assertEqual(
            sensor_module.SENSOR_DEFS["managed_fleet_overview"],
            "Managed Devices overview",
        )
        self.assertEqual(
            sensor_module.SENSOR_DEFS["unmanaged_candidate_overview"],
            "Managed Devices unmanaged backlog",
        )
        self.assertEqual(
            sensor_module.SENSOR_DEFS["top_unmanaged_candidate"],
            "Managed Devices surfaced unmanaged candidate",
        )

    def test_managed_devices_surface_sensor_shows_current_device_page_fleet_state(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC outlet", "entity_id": "switch.ac_outlet", "kind": "fixed"},
            {"name": "Dishwasher", "entity_id": "switch.dishwasher", "kind": "fixed"},
        ]
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": False,
                        "effective_enabled": True,
                        "planned_action": "blocked",
                        "guard_status": "source_blocked",
                    },
                }
            ),
        )
        sensor = sensor_module.ZeroNetExportSensor(
            coordinator,
            "managed_devices_surface",
            "Managed Devices surface",
        )
        sensor.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            sensor.native_value,
            "Managed Devices surface | 1 managed | 1 needs attention | blocked Pool pump | 2 unmanaged backlog | review AC outlet (fixed) | review carefully | warn generic outlet label | open ⚙ Settings — Managed Devices workspace",
        )
        self.assertNotIn("open Managed Devices workspace", sensor.native_value)
        self.assertIsNone(sensor.entity_category)
        self.assertEqual(sensor.extra_state_attributes["configure_path"], "devices path")
        self.assertEqual(sensor.extra_state_attributes["candidate_count"], 2)

    def test_fleet_workspace_sensors_are_primary_entities(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=None,
        )

        managed_overview = sensor_module.ZeroNetExportSensor(
            coordinator,
            "managed_fleet_overview",
            "Managed devices overview",
        )
        shortlist = sensor_module.ZeroNetExportSensor(
            coordinator,
            "candidate_shortlist",
            "Candidate shortlist",
        )

        self.assertIsNone(managed_overview.entity_category)
        self.assertIsNone(shortlist.entity_category)

    def test_tier_one_sensor_card_keeps_only_curated_primary_sensors(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=None,
        )

        primary = sensor_module.ZeroNetExportSensor(coordinator, "active_controlled_power_w", "Active controlled power")
        health = sensor_module.ZeroNetExportSensor(coordinator, "health_status", "Health status")
        telemetry = sensor_module.ZeroNetExportSensor(coordinator, "solar_power_w", "Solar power")
        device_count = sensor_module.ZeroNetExportSensor(coordinator, "device_count", "Managed Devices count")

        self.assertIsNone(primary.entity_category)
        self.assertIsNone(health.entity_category)
        self.assertEqual(telemetry.entity_category, "diagnostic")
        self.assertEqual(device_count.entity_category, "diagnostic")
        self.assertTrue(primary.entity_registry_visible_default)
        self.assertFalse(telemetry.entity_registry_visible_default)
        self.assertFalse(device_count.entity_registry_visible_default)

    def test_tier_one_diagnostics_card_keeps_only_curated_diagnostics_visible_by_default(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=None,
        )

        summary = sensor_module.ZeroNetExportSensor(
            coordinator,
            "diagnostic_summary",
            "Diagnostic summary",
        )
        next_step = sensor_module.ZeroNetExportSensor(
            coordinator,
            "command_center_next_step",
            "Command center next step",
        )
        release_summary = sensor_module.ZeroNetExportSensor(
            coordinator,
            "release_summary",
            "Release summary",
        )
        device_count = sensor_module.ZeroNetExportSensor(
            coordinator,
            "device_count",
            "Managed Devices count",
        )

        self.assertEqual(summary.entity_category, "diagnostic")
        self.assertEqual(next_step.entity_category, "diagnostic")
        self.assertEqual(release_summary.entity_category, "diagnostic")
        self.assertTrue(summary.entity_registry_visible_default)
        self.assertTrue(next_step.entity_registry_visible_default)
        self.assertFalse(release_summary.entity_registry_visible_default)
        self.assertFalse(device_count.entity_registry_visible_default)

    def test_managed_device_summary_stays_primary_while_secondary_runtime_details_become_diagnostic(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "status": "Ready for control",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "priority": 90,
                        "current_power_w": 1185,
                        "nominal_power_w": 1200,
                        "planned_action": "turn_on",
                        "current_active_seconds": 930,
                        "active_runtime_today_seconds": 4530,
                    }
                }
            ),
        )

        managed_overview = sensor_module.ZeroNetExportSensor(
            coordinator,
            "managed_fleet_overview",
            "Managed devices overview",
        )
        managed_overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))
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

        self.assertEqual(summary._attr_name, "Zero Net Export configuration")
        self.assertEqual(
            managed_overview.native_value,
            "1 managed | no unmanaged candidates | 1 managed device needs attention | plan Pool pump | 1 enabled | 1 usable | 1 fixed managed | 1200 W nominal",
        )
        self.assertEqual(managed_overview.extra_state_attributes["planned_count"], 1)
        self.assertEqual(managed_overview.extra_state_attributes["usable_count"], 1)
        self.assertEqual(
            summary.native_value,
            "Enabled, fixed load, priority 90, nominal 1200 W",
        )
        self.assertEqual(status.native_value, "Planned")
        self.assertIsNone(getattr(summary, "_attr_entity_category", None))
        self.assertEqual(current_power._attr_entity_category, sensor_module.EntityCategory.DIAGNOSTIC)
        self.assertIsNone(getattr(status, "_attr_entity_category", None))
        self.assertEqual(plan._attr_entity_category, sensor_module.EntityCategory.DIAGNOSTIC)
        self.assertEqual(guard._attr_entity_category, sensor_module.EntityCategory.DIAGNOSTIC)
        self.assertEqual(planned_delta._attr_entity_category, sensor_module.EntityCategory.DIAGNOSTIC)
        self.assertEqual(runtime._attr_entity_category, sensor_module.EntityCategory.DIAGNOSTIC)
        self.assertEqual(last_requested._attr_entity_category, sensor_module.EntityCategory.DIAGNOSTIC)

    def test_managed_summary_keeps_active_cue_when_same_device_is_planned(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="test-entry", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "status": "Running",
                        "priority": 90,
                        "observed_active": True,
                        "current_power_w": 1185,
                        "nominal_power_w": 1200,
                        "current_active_seconds": 930,
                        "active_runtime_today_seconds": 4530,
                        "planned_action": "turn_on",
                    }
                }
            ),
        )

        summary = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "pool", "Pool pump")

        self.assertEqual(
            summary.native_value,
            "Enabled, fixed load, priority 90, nominal 1200 W",
        )

    def test_variable_managed_summary_surfaces_target_and_relevant_guard(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="test-entry", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "ev": {
                        "name": "EV charger",
                        "kind": "variable",
                        "usable": False,
                        "effective_enabled": True,
                        "priority": 60,
                        "operator_priority_override": 45,
                        "operator_enabled_override": False,
                        "status": "Guarded",
                        "current_power_w": 620,
                        "nominal_power_w": 7400,
                        "current_target_power_w": 1400,
                        "guard_status": "blocked",
                        "planned_action": "hold",
                        "last_action_status": "guard_blocked",
                    }
                }
            ),
        )

        summary = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "ev", "EV charger")

        self.assertEqual(
            summary.native_value,
            "Enabled, variable load, priority 60, nominal 7400 W",
        )

    def test_managed_summary_surfaces_active_runtime_when_no_attention_or_plan_exists(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="test-entry", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "heater": {
                        "name": "Water heater",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "status": "Running",
                        "priority": 40,
                        "observed_active": True,
                        "current_power_w": 730,
                        "nominal_power_w": 1200,
                        "current_active_seconds": 125,
                        "active_runtime_today_seconds": 3720,
                        "planned_action": "hold",
                    }
                }
            ),
        )

        summary = sensor_module.ZeroNetExportDeviceManagedSummarySensor(coordinator, "heater", "Water heater")

        self.assertEqual(
            summary.native_value,
            "Enabled, fixed load, priority 40, nominal 1200 W",
        )

    def test_managed_fleet_overview_surfaces_unmanaged_backlog_when_fleet_is_empty(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
            {"name": "EV charger limit", "entity_id": "number.ev_charger_limit", "kind": "variable"},
        ]

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertIn("no managed yet | 2 unmanaged backlog | 1 fixed candidate | 1 variable candidate", overview.native_value)
        self.assertIn("fixed backlog 1 review", overview.native_value)
        self.assertIn("variable backlog 1 ready", overview.native_value)
        self.assertIn("1 needs review", overview.native_value)
        self.assertIn("1 ready to promote", overview.native_value)
        self.assertIn("review AC Outlet 2 (fixed)", overview.native_value)
        self.assertIn("ready EV charger limit", overview.native_value)
        self.assertNotIn("top AC Outlet 2", overview.native_value)
        self.assertEqual(overview.extra_state_attributes["candidate_count"], 2)
        self.assertEqual(overview.extra_state_attributes["review_needed_count"], 1)
        self.assertEqual(overview.extra_state_attributes["ready_candidate_count"], 1)
        self.assertEqual(overview.extra_state_attributes["top_candidate"]["name"], "AC Outlet 2")
        self.assertEqual(overview.extra_state_attributes["top_candidate_name"], "AC Outlet 2")
        self.assertEqual(overview.extra_state_attributes["review_candidate"]["name"], "AC Outlet 2")
        self.assertEqual(overview.extra_state_attributes["ready_candidate"]["name"], "EV charger limit")
        self.assertFalse(overview.extra_state_attributes["source_blocked"])

    def test_unmanaged_candidate_overview_sensor_is_distinct_from_shortlist(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
            {"name": "EV charger limit", "entity_id": "number.ev_charger_limit", "kind": "variable"},
        ]
        sensor_module.build_candidate_name_summary = lambda candidates, **kwargs: "AC Outlet 2 (fixed | likely useful); EV charger limit (variable | likely useful)"

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(device_details={}),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "unmanaged_candidate_overview", "Unmanaged candidate overview")
        shortlist = sensor_module.ZeroNetExportSensor(coordinator, "candidate_shortlist", "Candidate shortlist")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))
        shortlist.hass = overview.hass

        self.assertIn("2 candidates | 1 fixed candidate | 1 variable candidate", overview.native_value)
        self.assertIn("fixed backlog 1 review", overview.native_value)
        self.assertIn("variable backlog 1 ready", overview.native_value)
        self.assertIn("review AC Outlet 2 (fixed) | review carefully", overview.native_value)
        self.assertIn("ready EV charger limit (variable) | likely useful", overview.native_value)
        self.assertEqual(shortlist.native_value, "AC Outlet 2 (fixed | likely useful); EV charger limit (variable | likely useful)")
        self.assertEqual(overview.extra_state_attributes["fixed_candidate_count"], 1)
        self.assertEqual(overview.extra_state_attributes["variable_candidate_count"], 1)

    def test_top_unmanaged_candidate_hides_raw_entity_id(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
        ]
        sensor_module.build_candidate_preview = lambda candidate, **kwargs: (
            f"{candidate['name']} | include_entity_id={kwargs.get('include_entity_id', True)}"
        )

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(device_details={}),
        )
        top = sensor_module.ZeroNetExportSensor(coordinator, "top_unmanaged_candidate", "Currently surfaced unmanaged candidate")
        top.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(top.native_value, "AC Outlet 2 | include_entity_id=False")

    def test_fleet_workspace_candidate_discovery_is_cached_per_coordinator_state(self) -> None:
        sensor_module = _load_sensor_module()
        calls: list[tuple[str, ...]] = []

        def _discover(hass, managed_ids):
            calls.append(tuple(sorted(managed_ids)))
            return [
                {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
                {"name": "EV charger limit", "entity_id": "number.ev_charger_limit", "kind": "variable"},
            ]

        sensor_module._candidate_devices_for_hass = _discover
        sensor_module.build_candidate_name_summary = lambda candidates, **kwargs: "AC Outlet 2 (fixed | likely useful); EV charger limit (variable | likely useful)"

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(device_details={}),
        )
        hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))
        overview = sensor_module.ZeroNetExportSensor(coordinator, "unmanaged_candidate_overview", "Unmanaged candidate overview")
        shortlist = sensor_module.ZeroNetExportSensor(coordinator, "candidate_shortlist", "Candidate shortlist")
        top = sensor_module.ZeroNetExportSensor(coordinator, "top_unmanaged_candidate", "Currently surfaced unmanaged candidate")
        overview.hass = hass
        shortlist.hass = hass
        top.hass = hass

        self.assertIn("fixed backlog 1 review", overview.native_value)
        self.assertIn("variable backlog 1 ready", overview.native_value)
        self.assertIn("review AC Outlet 2 (fixed) | review carefully", overview.native_value)
        self.assertIn("ready EV charger limit (variable) | likely useful", overview.native_value)
        self.assertEqual(shortlist.native_value, "AC Outlet 2 (fixed | likely useful); EV charger limit (variable | likely useful)")
        self.assertEqual(top.native_value, "candidate preview")
        self.assertEqual(len(calls), 1)

    def test_managed_fleet_overview_names_review_candidate_when_top_target_looks_usable(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "Hot water relay", "entity_id": "switch.hot_water", "kind": "fixed"},
            {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
        ]
        sensor_module.assess_candidate = lambda candidate: {
            "confidence": "high" if candidate.get("entity_id") == "switch.hot_water" else "low",
            "summary": "Review before promotion.",
            "warnings": [],
        }
        sensor_module.build_candidate_review_hint = lambda candidate, include_warning=True, **kwargs: (
            "likely useful"
            if candidate.get("entity_id") == "switch.hot_water"
            else (
                "review carefully | warn This is an input_boolean helper."
                if include_warning
                else "review carefully"
            )
        )

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                        "nominal_power_w": 1185,
                    }
                }
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertIn("1 managed | 2 unmanaged backlog | 2 fixed candidates", overview.native_value)
        self.assertIn("fixed backlog 1 review/1 ready", overview.native_value)
        self.assertIn("1 ready to promote", overview.native_value)
        self.assertIn("review Virtual load (fixed) | review carefully | warn", overview.native_value)
        self.assertIn("ready Hot water relay (fixed) | likely useful", overview.native_value)
        self.assertNotIn("top Hot water relay", overview.native_value)
        self.assertIn("1 fixed managed", overview.native_value)

    def test_unmanaged_candidate_overview_prefers_ready_label_when_top_candidate_is_ready_next(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "Hot water relay", "entity_id": "switch.hot_water", "kind": "fixed"},
            {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
        ]
        sensor_module.assess_candidate = lambda candidate: {
            "confidence": "high" if candidate.get("entity_id") == "switch.hot_water" else "low",
            "summary": "Review before promotion.",
            "warnings": [],
        }
        sensor_module.build_candidate_review_hint = lambda candidate, include_warning=True, **kwargs: (
            "likely useful"
            if candidate.get("entity_id") == "switch.hot_water"
            else (
                "review carefully | warn This is an input_boolean helper."
                if include_warning
                else "review carefully"
            )
        )

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(device_details={}),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "unmanaged_candidate_overview", "Unmanaged candidate overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertIn("2 candidates | 2 fixed candidates | fixed backlog 1 review/1 ready", overview.native_value)
        self.assertIn("1 needs review", overview.native_value)
        self.assertIn("review Virtual load (fixed) | review carefully", overview.native_value)
        self.assertIn("1 ready to promote", overview.native_value)
        self.assertIn("ready Hot water relay (fixed) | likely useful", overview.native_value)

    def test_workspace_overview_surfaces_per_kind_backlog_mix_for_mixed_review_and_ready_candidates(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
            {"name": "EV charger limit", "entity_id": "number.ev_charger_limit", "kind": "variable"},
        ]
        sensor_module.assess_candidate = lambda candidate: {
            "confidence": "low" if candidate.get("kind") == "fixed" else "high",
            "summary": "Review before promotion.",
            "warnings": ["helper-backed load needs review"] if candidate.get("kind") == "fixed" else [],
        }
        sensor_module.build_candidate_review_hint = lambda candidate, include_warning=True, **kwargs: (
            "review carefully | warn helper-backed load needs review"
            if candidate.get("kind") == "fixed"
            else "likely useful"
        )

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                        "nominal_power_w": 1185,
                    }
                }
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        unmanaged = sensor_module.ZeroNetExportSensor(coordinator, "unmanaged_candidate_overview", "Unmanaged candidate overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))
        unmanaged.hass = overview.hass

        self.assertIn("fixed backlog 1 review", overview.native_value)
        self.assertIn("variable backlog 1 ready", overview.native_value)
        self.assertIn("fixed backlog 1 review", unmanaged.native_value)
        self.assertIn("variable backlog 1 ready", unmanaged.native_value)
        self.assertEqual(overview.extra_state_attributes["fixed_review_count"], 1)
        self.assertEqual(overview.extra_state_attributes["variable_review_count"], 0)
        self.assertEqual(overview.extra_state_attributes["fixed_ready_count"], 0)
        self.assertEqual(overview.extra_state_attributes["variable_ready_count"], 1)

    def test_managed_fleet_overview_keeps_top_unmanaged_target_visible_with_existing_fleet(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
            {"name": "EV charger limit", "entity_id": "number.ev_charger_limit", "kind": "variable"},
        ]

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                        "nominal_power_w": 1185,
                    }
                }
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertIn("1 managed | 2 unmanaged backlog | 1 fixed candidate | 1 variable candidate", overview.native_value)
        self.assertIn("fixed backlog 1 review", overview.native_value)
        self.assertIn("variable backlog 1 ready", overview.native_value)
        self.assertIn("1 needs review", overview.native_value)
        self.assertIn("1 ready to promote", overview.native_value)
        self.assertIn("review AC Outlet 2 (fixed)", overview.native_value)
        self.assertIn("ready EV charger limit", overview.native_value)
        self.assertNotIn("top AC Outlet 2", overview.native_value)
        self.assertLessEqual(len(overview.native_value), 255)

    def test_unmanaged_candidate_overview_keeps_single_kind_review_backlog_visible(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
            {"name": "Pool pump helper", "entity_id": "input_boolean.pool_pump_helper", "kind": "fixed"},
        ]
        sensor_module.assess_candidate = lambda candidate: {
            "confidence": "low",
            "summary": "Review before promotion.",
            "warnings": ["helper-backed load needs review"],
        }
        sensor_module.candidate_review_kind_counts = lambda candidates: (2, 0)
        sensor_module.build_candidate_review_hint = lambda candidate, include_warning=True, **kwargs: (
            "review carefully | warn helper-backed load needs review"
            if include_warning
            else "review carefully"
        )

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "unmanaged_candidate_overview", "Unmanaged candidate overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertIn("2 fixed candidates", overview.native_value)
        self.assertIn("fixed backlog 2 review", overview.native_value)
        self.assertIn("2 need review", overview.native_value)
        self.assertNotIn("ready to promote", overview.native_value)

    def test_managed_fleet_overview_names_first_blocked_and_planned_devices(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
        ]

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": False,
                        "effective_enabled": True,
                        "observed_active": True,
                        "current_power_w": 1185,
                        "planned_action": "turn_on",
                        "nominal_power_w": 1185,
                    },
                    "ev": {
                        "name": "EV charger",
                        "kind": "variable",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                    },
                }
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertIn("1 managed device needs attention", overview.native_value)
        self.assertIn("blocked Pool pump", overview.native_value)
        self.assertIn("plan Pool pump", overview.native_value)
        self.assertIn("active load 1185 W", overview.native_value)
        self.assertIn("1 active managed device", overview.native_value)
        self.assertLess(
            overview.native_value.index("blocked Pool pump"),
            overview.native_value.index("active load 1185 W"),
        )
        self.assertEqual(overview.extra_state_attributes["first_blocked_device"], "Pool pump")
        self.assertEqual(overview.extra_state_attributes["first_active_plan_device"], "Pool pump")

    def test_managed_fleet_overview_keeps_live_managed_activity_ahead_of_unmanaged_backlog(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
            {"name": "EV charger limit", "entity_id": "number.ev_charger_limit", "kind": "variable"},
        ]
        sensor_module.assess_candidate = lambda candidate: {
            "confidence": "low" if candidate.get("entity_id") == "input_boolean.virtual_load" else "high",
            "summary": "Review before promotion.",
            "warnings": [],
        }
        sensor_module.build_candidate_review_hint = lambda candidate, include_warning=True, **kwargs: (
            "review carefully | warn This is an input_boolean helper."
            if candidate.get("entity_id") == "input_boolean.virtual_load"
            else "likely useful"
        )

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "observed_active": True,
                        "current_power_w": 1185,
                        "planned_action": "turn_on",
                        "nominal_power_w": 1185,
                    },
                }
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertIn("active load 1185 W", overview.native_value)
        self.assertIn("1 active managed device", overview.native_value)
        self.assertIn("1 needs review", overview.native_value)
        self.assertIn("1 ready to promote", overview.native_value)
        self.assertIn("review Virtual load (fixed)", overview.native_value)
        self.assertIn("review carefully", overview.native_value)
        self.assertIn("ready", overview.native_value)
        self.assertLess(
            overview.native_value.index("active load 1185 W"),
            overview.native_value.index("1 needs review"),
        )
        self.assertLess(
            overview.native_value.index("1 active managed device"),
            overview.native_value.index("review Virtual load (fixed)"),
        )

    def test_managed_fleet_overview_prefers_attention_first_order_over_config_insertion_order(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: []

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "ev": {
                        "name": "EV charger",
                        "kind": "variable",
                        "usable": True,
                        "effective_enabled": True,
                        "priority": 50,
                        "planned_action": "set_power",
                    },
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": False,
                        "effective_enabled": True,
                        "priority": 10,
                        "planned_action": "turn_on",
                    },
                }
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertIn("blocked Pool pump", overview.native_value)
        self.assertIn("plan Pool pump", overview.native_value)
        self.assertEqual(overview.extra_state_attributes["first_attention_device"], "Pool pump")
        self.assertEqual(overview.extra_state_attributes["first_blocked_device"], "Pool pump")
        self.assertEqual(overview.extra_state_attributes["first_active_plan_device"], "Pool pump")

    def test_managed_fleet_overview_keeps_blocked_activity_visible_without_unusable_runtime_row(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
        ]

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                blocked_planned_action_count=1,
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "observed_active": True,
                        "current_power_w": 730,
                        "planned_action": "hold",
                        "nominal_power_w": 1185,
                    },
                },
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertIn("1 managed | 1 unmanaged backlog", overview.native_value)
        self.assertIn("1 fixed candidate", overview.native_value)
        self.assertIn("1 needs review", overview.native_value)
        self.assertIn("review AC Outlet 2 (fixed) | review carefully | warn", overview.native_value)
        self.assertIn("blocked 1 | active load 730 W | 1 active managed device", overview.native_value)
        self.assertNotIn("top AC Outlet 2", overview.native_value)
        self.assertIn("1 fixed managed | 1185 W nominal", overview.native_value)
        self.assertEqual(overview.extra_state_attributes["blocked_activity_count"], 1)
        self.assertEqual(overview.extra_state_attributes["blocked_planned_action_count"], 1)

    def test_managed_fleet_overview_surfaces_source_repair_before_promotion_backlog(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
        ]
        sensor_module.build_source_attention_summary = lambda state, merged, limit=2, blocking_only=False: (
            "Missing required source roles: Solar power" if blocking_only else "None"
        )

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        ready = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_ready", "Managed devices ready next")
        hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))
        overview.hass = hass
        ready.hass = hass

        self.assertEqual(
            overview.native_value,
            "source blockers active | no managed yet | 1 unmanaged backlog | 1 fixed candidate | fixed backlog 1 review | 1 needs review | 1 fixed review | review AC Outlet 2 (fixed) | review carefully | warn generic outlet label",
        )
        self.assertTrue(ready.native_value.startswith("source blockers active | 1 fixed candidate"))
        self.assertTrue(overview.extra_state_attributes["source_blocked"])
        self.assertEqual(
            overview.extra_state_attributes["source_blocker_summary"],
            "Missing required source roles: Solar power",
        )
        self.assertEqual(
            overview.extra_state_attributes["source_repair_path"],
            "sources path",
        )

    def test_managed_fleet_overview_keeps_source_repair_and_unmanaged_backlog_visible_with_existing_fleet(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
            {"name": "EV charger limit", "entity_id": "number.ev_charger_limit", "kind": "variable"},
        ]
        sensor_module.build_source_attention_summary = lambda state, merged, limit=2, blocking_only=False: (
            "Missing required source roles: Solar power" if blocking_only else "None"
        )

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                        "nominal_power_w": 1185,
                    }
                }
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertTrue(overview.native_value.startswith("source blockers active | 1 managed | 2 unmanaged backlog"))
        self.assertNotIn("top AC Outlet 2", overview.native_value)
        self.assertIn("1 needs review", overview.native_value)
        self.assertIn("review AC Outlet 2 (fixed)", overview.native_value)
        self.assertIn("1 ready to promote", overview.native_value)
        self.assertLessEqual(len(overview.native_value), 255)

    def test_fleet_console_next_step_prioritizes_named_blocked_devices_before_more_promotions(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
        ]

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "heater": {
                        "name": "Heated floor",
                        "kind": "fixed",
                        "usable": False,
                        "effective_enabled": True,
                        "planned_action": "hold",
                    }
                }
            ),
        )
        next_step = sensor_module.ZeroNetExportSensor(coordinator, "fleet_console_next_step", "Managed devices next step")
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to review blocked devices in the Managed Devices workspace starting with Heated floor, then fix the next guard or readiness issue",
        )

    def test_fleet_console_next_step_keeps_blocked_activity_priority_without_unusable_runtime_row(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
        ]

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                blocked_planned_action_count=1,
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                    }
                },
            ),
        )
        next_step = sensor_module.ZeroNetExportSensor(coordinator, "fleet_console_next_step", "Managed devices next step")
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to review blocked devices in the Managed Devices workspace, then fix the next guard or readiness issue",
        )
        self.assertEqual(next_step.extra_state_attributes["blocked_count"], 0)
        self.assertEqual(next_step.extra_state_attributes["blocked_activity_count"], 1)

    def test_fleet_console_next_step_names_non_executable_blocked_device_before_usable_flips_false(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: []

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                blocked_planned_action_count=1,
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "on",
                        "action_executable": False,
                    }
                },
            ),
        )
        next_step = sensor_module.ZeroNetExportSensor(coordinator, "fleet_console_next_step", "Managed devices next step")
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed fleet overview")
        overview.hass = next_step.hass

        self.assertEqual(
            next_step.native_value,
            "Open devices path to review blocked devices in the Managed Devices workspace starting with Pool pump, then fix the next guard or readiness issue",
        )
        self.assertIn("blocked Pool pump", overview.native_value)
        self.assertEqual(overview.extra_state_attributes["first_blocked_device"], "Pool pump")

    def test_fleet_console_next_step_keeps_managed_devices_workspace_explicit_for_active_plan(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: []

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "turn_on",
                        "action_executable": True,
                    }
                },
            ),
        )
        next_step = sensor_module.ZeroNetExportSensor(coordinator, "fleet_console_next_step", "Managed devices next step")
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to confirm the active fleet plan in the Managed Devices workspace for Pool pump",
        )

    def test_fleet_console_next_step_names_top_candidate_when_fleet_is_empty(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
        ]

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(device_details={}),
        )
        next_step = sensor_module.ZeroNetExportSensor(coordinator, "fleet_console_next_step", "Managed devices next step")
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to continue in the Managed Devices workspace, review unmanaged candidate: AC Outlet 2",
        )

    def test_fleet_console_next_step_uses_review_first_candidate_before_promotion(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "Dishwasher Power", "entity_id": "switch.dishwasher_power", "kind": "fixed"},
            {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
        ]
        sensor_module.first_review_candidate = lambda candidates: candidates[1]

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(device_details={}),
        )
        next_step = sensor_module.ZeroNetExportSensor(coordinator, "fleet_console_next_step", "Managed devices next step")
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to continue in the Managed Devices workspace, review unmanaged candidate: Virtual load, then promote ready unmanaged candidate: Dishwasher Power",
        )

    def test_fleet_console_next_step_uses_ready_next_wording_when_no_review_first_candidate_exists(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "Dishwasher Power", "entity_id": "switch.dishwasher_power", "kind": "fixed"},
        ]
        sensor_module.first_review_candidate = lambda candidates: None

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(device_details={}),
        )
        next_step = sensor_module.ZeroNetExportSensor(coordinator, "fleet_console_next_step", "Managed devices next step")
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to continue in the Managed Devices workspace, then promote ready unmanaged candidate: Dishwasher Power",
        )

    def test_fleet_console_next_step_keeps_empty_fleet_manual_add_in_managed_devices(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: []
        sensor_module.first_review_candidate = lambda candidates: None

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        next_step = sensor_module.ZeroNetExportSensor(coordinator, "fleet_console_next_step", "Managed devices next step")
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to continue in the Managed Devices workspace, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available",
        )

    def test_fleet_console_next_step_names_ready_next_candidate_after_review_when_backlog_is_mixed(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "Dishwasher Power", "entity_id": "switch.dishwasher_power", "kind": "fixed"},
            {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
        ]
        sensor_module.first_review_candidate = lambda candidates: candidates[1]

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "switch.pool_pump": {
                        "entity_id": "switch.pool_pump",
                        "name": "Pool pump",
                        "status": "ready",
                        "planned_action": "hold",
                        "blocked_by": None,
                    }
                }
            ),
        )
        next_step = sensor_module.ZeroNetExportSensor(coordinator, "fleet_console_next_step", "Managed devices next step")
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to continue in the Managed Devices workspace, review unmanaged candidate: Virtual load, then promote ready unmanaged candidate: Dishwasher Power",
        )

    def test_fleet_console_next_step_prioritizes_source_repair_before_fleet_work(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
        ]
        sensor_module.build_source_attention_summary = lambda state, merged, limit=3, blocking_only=False: (
            "Missing required source roles: Solar power" if blocking_only else "None"
        )

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        next_step = sensor_module.ZeroNetExportSensor(coordinator, "fleet_console_next_step", "Managed devices next step")
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open sources path, repair blocking source roles first, then return to devices path",
        )

    def test_fleet_console_next_step_keeps_healthy_fallback_on_controls_only(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: []
        sensor_module.first_review_candidate = lambda candidates: None

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "switch.pool_pump": {
                        "entity_id": "switch.pool_pump",
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                        "blocked_by": None,
                    }
                }
            ),
        )
        next_step = sensor_module.ZeroNetExportSensor(coordinator, "fleet_console_next_step", "Managed devices next step")
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to continue in the Managed Devices workspace, then edit device settings or stage enablement changes",
        )
        self.assertNotIn("policy path", next_step.native_value)
        self.assertNotIn("sources path", next_step.native_value)

    def test_mapped_source_blocker_next_step_uses_operator_source_blocker_wording(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module.build_source_attention_summary = lambda *args, **kwargs: "Solar power unavailable"

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        next_step = sensor_module.ZeroNetExportSensor(
            coordinator,
            "mapped_source_blocker_next_step",
            "Source blocker next step",
        )
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))
        summary = sensor_module.ZeroNetExportSensor(
            coordinator,
            "mapped_source_blocker_summary",
            "Source blocker summary",
        )

        self.assertEqual(next_step._attr_name, "Source blocker next step")
        self.assertEqual(summary._attr_name, "Source blocker summary")
        self.assertNotIn("Mapped-source", next_step._attr_name)
        self.assertNotIn("Mapped-source", summary._attr_name)
        self.assertEqual(
            next_step.native_value,
            "Open sources path, repair source blockers, then save and reload the integration",
        )
        self.assertNotIn("repair mapped-source blockers", next_step.native_value)

    def test_mapped_source_blocker_next_step_reuses_operator_readiness_when_sources_are_healthy(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module.build_native_operator_readiness = lambda coordinator: {
            "next_step": "Open devices path to continue in the Managed Devices workspace, review unmanaged candidate: AC Outlet 2"
        }

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        next_step = sensor_module.ZeroNetExportSensor(
            coordinator,
            "mapped_source_blocker_next_step",
            "Source blocker next step",
        )
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to continue in the Managed Devices workspace, review unmanaged candidate: AC Outlet 2",
        )
        self.assertNotIn("continue in devices path or policy path", next_step.native_value)

    def test_mapped_source_blocker_next_step_truncates_long_operator_state(self) -> None:
        sensor_module = _load_sensor_module()
        long_next_step = (
            "Open devices path to continue in the Managed Devices workspace, "
            "review unmanaged candidate: Master Bathroom Heated Floor (variable) "
            "| review first | warn helper-backed, then promote ready unmanaged "
            "candidate: Lounge Room Heated Floor (fixed) | likely useful. "
        ) * 2
        sensor_module.build_native_operator_readiness = lambda coordinator: {"next_step": long_next_step}

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        next_step = sensor_module.ZeroNetExportSensor(
            coordinator,
            "mapped_source_blocker_next_step",
            "Source blocker next step",
        )
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertLessEqual(len(next_step.native_value), 255)
        self.assertTrue(next_step.native_value.endswith("..."))
        self.assertEqual(next_step.extra_state_attributes["current_native_next_step"], long_next_step)

    def test_mapped_source_blocker_next_step_uses_managed_devices_manual_add_when_no_readiness_step_exists(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module.build_native_operator_readiness = lambda coordinator: {}

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        next_step = sensor_module.ZeroNetExportSensor(
            coordinator,
            "mapped_source_blocker_next_step",
            "Source blocker next step",
        )
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to continue in the Managed Devices workspace, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available",
        )
        self.assertNotIn("continue in devices path or policy path", next_step.native_value)

    def test_mapped_source_blocker_next_step_keeps_managed_devices_workspace_when_fleet_is_ready_and_no_readiness_step_exists(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module.build_native_operator_readiness = lambda coordinator: {}

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                    },
                }
            ),
        )
        next_step = sensor_module.ZeroNetExportSensor(
            coordinator,
            "mapped_source_blocker_next_step",
            "Source blocker next step",
        )
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to continue in the Managed Devices workspace, then edit device settings or stage enablement changes",
        )
        self.assertNotIn("policy path", next_step.native_value)
        self.assertNotIn("continue in devices path or policy path", next_step.native_value)

    def test_command_center_next_step_truncates_long_state_and_keeps_attribute_detail(self) -> None:
        sensor_module = _load_sensor_module()
        long_next_step = (
            "Open devices path to continue in the Managed Devices workspace, "
            "review unmanaged candidate: Master Bathroom Heated Floor (variable) "
            "| review first | warn helper-backed, then promote ready unmanaged "
            "candidate: Lounge Room Heated Floor (fixed) | likely useful. "
        ) * 2
        sensor_module.build_native_command_center_summary = lambda coordinator: {
            "next_action_summary": long_next_step,
            "recommended_path": "devices path",
            "recommended_section": "Managed Devices",
        }

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        next_step = sensor_module.ZeroNetExportSensor(
            coordinator,
            "command_center_next_step",
            "Command center next step",
        )

        self.assertLessEqual(len(next_step.native_value), 255)
        self.assertTrue(next_step.native_value.endswith("..."))
        self.assertEqual(next_step.extra_state_attributes["current_next_step"], long_next_step)

    def test_fleet_workspace_attributes_reuse_cached_candidate_discovery(self) -> None:
        sensor_module = _load_sensor_module()
        calls: list[tuple[list[object], set[str]]] = []

        def discover(states, managed_entity_ids):
            calls.append((list(states), set(managed_entity_ids)))
            return [{"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"}]

        sensor_module.discover_candidate_devices = discover
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "entity_id": "switch.pool_pump",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "kind": "fixed",
                    }
                },
                validation_details={},
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(
            states=SimpleNamespace(async_all=lambda: [SimpleNamespace(entity_id="switch.ac_outlet_2")])
        )

        self.assertEqual(
            overview.native_value,
            "1 managed | 1 unmanaged backlog | 1 fixed candidate | fixed backlog 1 review | 1 needs review | 1 fixed review | review AC Outlet 2 (fixed) | review carefully | warn generic outlet label | 1 enabled | 1 usable | 1 fixed managed",
        )
        self.assertEqual(overview.extra_state_attributes["candidate_count"], 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], {"switch.pool_pump"})

    def test_managed_fleet_overview_names_disabled_devices(self) -> None:
        sensor_module = _load_sensor_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "entity_id": "switch.pool_pump",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "kind": "fixed",
                        "nominal_power_w": 1200,
                    },
                    "heater": {
                        "name": "Water heater",
                        "entity_id": "switch.water_heater",
                        "usable": False,
                        "enabled": False,
                        "effective_enabled": False,
                        "kind": "fixed",
                        "nominal_power_w": 900,
                    },
                },
                validation_details={},
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertIn("2 managed | no unmanaged candidates", overview.native_value)
        self.assertIn("1 enabled | 1 disabled | 1 usable", overview.native_value)
        self.assertEqual(overview.extra_state_attributes["disabled_count"], 1)

    def test_managed_fleet_overview_truncates_long_state_to_255_chars(self) -> None:
        sensor_module = _load_sensor_module()
        long_top_name = "Extremely Verbose Candidate Label " * 5
        long_review_name = "Needs Careful Review Before Promotion " * 4

        sensor_module.discover_candidate_devices = lambda states, managed_entity_ids: [
            {"name": long_top_name.strip(), "entity_id": "switch.verbose_top", "kind": "fixed"},
            {"name": long_review_name.strip(), "entity_id": "switch.verbose_review", "kind": "variable"},
        ]
        sensor_module.assess_candidate = lambda candidate: {
            "confidence": "high" if candidate.get("entity_id") == "switch.verbose_top" else "medium",
            "summary": "Verbose but plausible.",
            "warnings": [] if candidate.get("entity_id") == "switch.verbose_top" else ["Manual review recommended"],
        }
        sensor_module.build_candidate_review_hint = lambda candidate, **kwargs: (
            "likely useful after a fairly long operator-facing explanation that keeps going"
        )
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump with an overly descriptive managed label",
                        "entity_id": "switch.pool_pump",
                        "usable": False,
                        "enabled": True,
                        "effective_enabled": True,
                        "kind": "fixed",
                        "planned_action": "turn_on",
                        "nominal_power_w": 1800,
                    },
                    "heater": {
                        "name": "Heated floor with another long descriptive name",
                        "entity_id": "switch.heated_floor",
                        "usable": True,
                        "enabled": True,
                        "effective_enabled": True,
                        "kind": "variable",
                        "planned_action": "",
                        "nominal_power_w": 2200,
                    },
                },
                validation_details={},
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(
            states=SimpleNamespace(async_all=lambda: [SimpleNamespace(entity_id="switch.verbose_top")])
        )

        value = overview.native_value

        self.assertLessEqual(len(value), 255)
        self.assertIn("2 managed | 2 unmanaged backlog", value)
        self.assertIn("1 needs review", value)
        self.assertIn("1 ready to promote", value)
        self.assertIn("review ", value)
        self.assertIn("ready ", value)

    def test_unmanaged_candidate_overview_keeps_review_and_ready_split_when_long_state_overflows(self) -> None:
        sensor_module = _load_sensor_module()
        long_ready_name = "Likely Useful Candidate " * 5
        long_review_name = "Needs Additional Review Candidate " * 5

        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": long_ready_name.strip(), "entity_id": "switch.ready_candidate", "kind": "fixed"},
            {"name": long_review_name.strip(), "entity_id": "switch.review_candidate", "kind": "variable"},
        ]
        sensor_module.assess_candidate = lambda candidate: {
            "confidence": "high" if candidate.get("entity_id") == "switch.ready_candidate" else "medium",
            "summary": "Verbose but plausible.",
            "warnings": [] if candidate.get("entity_id") == "switch.ready_candidate" else ["Manual review recommended"],
        }
        sensor_module.build_candidate_review_hint = lambda candidate, **kwargs: (
            "likely useful after a fairly long operator-facing explanation that keeps going"
            if candidate.get("entity_id") == "switch.ready_candidate"
            else "review carefully after a fairly long operator-facing explanation that keeps going | warn Manual review recommended"
        )

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(device_details={}),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "unmanaged_candidate_overview", "Unmanaged candidate overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        value = overview.native_value

        self.assertLessEqual(len(value), 255)
        self.assertIn("2 candidates", value)
        self.assertIn("1 needs review", value)
        self.assertIn("1 ready to promote", value)
        self.assertIn("review ", value)
        self.assertIn("ready ", value)

    def test_managed_fleet_overview_keeps_distinct_active_device_visible_with_attention(self) -> None:
        sensor_module = _load_sensor_module()
        state = SimpleNamespace(
            device_count=2,
            enabled_device_count=2,
            usable_device_count=2,
            blocked_planned_action_count=0,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "planned_action": "turn_on",
                    "nominal_power_w": 1185,
                },
                "heater": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor_limit",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 920,
                    "planned_action": "hold",
                    "nominal_power_w": 2200,
                },
            },
            validation_details={},
        )
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: []
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=state,
        )

        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            overview.native_value,
            "2 managed | no unmanaged candidates | 1 managed device needs attention | 1 active plan | active load 920 W | 1 active managed device | active device Heated floor (variable | active 920 W) | 2 usable | 1 fixed managed | 1 variable managed | 3385 W nominal",
        )

    def test_managed_fleet_overview_surfaces_active_managed_load_and_count(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: []

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "observed_active": True,
                        "current_power_w": 1185,
                        "planned_action": "hold",
                        "nominal_power_w": 1185,
                    },
                    "heater": {
                        "name": "Heated floor",
                        "kind": "variable",
                        "usable": True,
                        "effective_enabled": True,
                        "observed_active": True,
                        "current_power_w": 920,
                        "planned_action": "hold",
                        "nominal_power_w": 2200,
                    },
                }
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            overview.native_value,
            "2 managed | no unmanaged candidates | active load 2105 W | 2 active managed devices | active device Heated floor (variable | active 920 W) | 2 enabled | 2 usable | 1 fixed managed | 1 variable managed | 3385 W nominal",
        )

    def test_managed_fleet_overview_keeps_active_device_visible_without_runtime_watts(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: []

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "turn_on",
                        "nominal_power_w": 1185,
                    },
                    "heater": {
                        "name": "Heated floor",
                        "kind": "variable",
                        "usable": True,
                        "effective_enabled": True,
                        "observed_active": True,
                        "current_power_w": None,
                        "planned_action": "hold",
                        "nominal_power_w": 2200,
                    },
                }
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        overview.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            overview.native_value,
            "2 managed | no unmanaged candidates | 1 managed device needs attention | 1 active plan | 1 active managed device | active device Heated floor (variable | active) | 2 enabled | 2 usable | 1 fixed managed | 1 variable managed | 3385 W nominal",
        )

    def test_managed_fleet_attention_keeps_active_count_when_runtime_watts_are_missing(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: []

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pool": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "turn_on",
                        "nominal_power_w": 1185,
                    },
                    "heater": {
                        "name": "Heated floor",
                        "kind": "variable",
                        "usable": True,
                        "effective_enabled": True,
                        "observed_active": True,
                        "current_power_w": None,
                        "planned_action": "hold",
                        "nominal_power_w": 2200,
                    },
                }
            ),
        )
        attention = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_attention", "Managed devices attention")
        attention.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            attention.native_value,
            "1 managed device needs attention | attention Pool pump | plan Pool pump | 1 active managed device",
        )
        self.assertNotIn("active load 0", attention.native_value)

    def test_managed_fleet_overview_surfaces_failed_only_attention_before_steady_rows(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: []

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pump": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                        "last_action_status": "failed",
                        "nominal_power_w": 1185,
                    },
                    "heater": {
                        "name": "Heated floor",
                        "kind": "variable",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                        "nominal_power_w": 2200,
                    },
                }
            ),
        )
        overview = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_overview", "Managed devices overview")
        attention = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_attention", "Managed devices attention")
        ready = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_ready", "Managed devices ready next")
        hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))
        overview.hass = hass
        attention.hass = hass
        ready.hass = hass

        self.assertEqual(
            overview.native_value,
            "2 managed | no unmanaged candidates | 1 managed device needs attention | attention Pool pump | 2 enabled | 2 usable | 1 fixed managed | 1 variable managed | 3385 W nominal",
        )
        self.assertEqual(
            attention.native_value,
            "1 managed device needs attention | attention Pool pump",
        )
        self.assertEqual(ready.native_value, "No unmanaged candidates right now")
        self.assertEqual(overview.extra_state_attributes["attention_count"], 1)
        self.assertEqual(overview.extra_state_attributes["recent_attention_count"], 1)
        self.assertEqual(overview.extra_state_attributes["first_attention_device"], "Pool pump")

    def test_device_page_attention_and_ready_sensors_surface_mixed_fleet_state(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
            {"name": "Hot water relay", "entity_id": "switch.hot_water", "kind": "fixed"},
        ]

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(
                device_details={
                    "pump": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": False,
                        "effective_enabled": True,
                        "planned_action": "turn_on",
                        "nominal_power_w": 1185,
                    },
                    "heater": {
                        "name": "Heated floor",
                        "kind": "variable",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                        "nominal_power_w": 2200,
                    },
                }
            ),
        )
        attention = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_attention", "Managed devices attention")
        ready = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_ready", "Managed devices ready next")
        hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))
        attention.hass = hass
        ready.hass = hass

        self.assertEqual(
            attention.native_value,
            "1 managed device needs attention | attention Pool pump | blocked Pool pump | plan Pool pump",
        )
        self.assertEqual(
            ready.native_value,
            "2 fixed candidates | fixed backlog 1 review/1 ready | 1 ready to promote | ready Hot water relay (fixed) | likely useful | 1 still needs review | review Virtual load (fixed) | review carefully | warn This is an input_boolean helper.",
        )
        self.assertEqual(attention.extra_state_attributes["first_attention_device"], "Pool pump")
        self.assertEqual(ready.extra_state_attributes["ready_candidate"]["name"], "Hot water relay")

    def test_managed_fleet_ready_sensor_keeps_fixed_variable_backlog_mix_visible(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
            {"name": "Hot water relay", "entity_id": "switch.hot_water", "kind": "fixed"},
            {"name": "EV limit", "entity_id": "number.ev_limit", "kind": "variable"},
        ]
        sensor_module.assess_candidate = lambda candidate: {
            "confidence": "low" if candidate.get("name") == "Virtual load" else "high",
            "warnings": ["This is an input_boolean helper."] if candidate.get("name") == "Virtual load" else [],
        }
        sensor_module.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        sensor_module.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Virtual load (fixed) | review carefully | warn This is an input_boolean helper."
            if candidate and candidate.get("name") == "Virtual load"
            else (
                "Hot water relay (fixed) | likely useful"
                if candidate and candidate.get("name") == "Hot water relay"
                else "EV limit (variable) | likely useful"
            )
        )

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry", data={}, options={}),
            data=SimpleNamespace(device_details={}),
        )
        ready = sensor_module.ZeroNetExportSensor(coordinator, "managed_fleet_ready", "Managed devices ready next")
        ready.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            ready.native_value,
            "2 fixed candidates | 1 variable candidate | fixed backlog 1 review/1 ready | variable backlog 1 ready | 2 ready to promote | ready Hot water relay (fixed) | likely useful | 1 still needs review | review Virtual load (fixed) | review carefully | warn",
        )

    def test_fleet_console_next_step_prioritizes_failed_only_attention_before_new_promotions(self) -> None:
        sensor_module = _load_sensor_module()
        sensor_module._candidate_devices_for_hass = lambda hass, managed_ids: [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
        ]

        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(
                device_details={
                    "pump": {
                        "name": "Pool pump",
                        "kind": "fixed",
                        "usable": True,
                        "effective_enabled": True,
                        "planned_action": "hold",
                        "last_action_status": "failed",
                    }
                }
            ),
        )
        next_step = sensor_module.ZeroNetExportSensor(coordinator, "fleet_console_next_step", "Managed devices next step")
        next_step.hass = SimpleNamespace(states=SimpleNamespace(async_all=lambda: []))

        self.assertEqual(
            next_step.native_value,
            "Open devices path to continue in the Managed Devices workspace, starting with attention on Pool pump",
        )
        self.assertEqual(next_step.extra_state_attributes["first_attention_device"], "Pool pump")


if __name__ == "__main__":
    unittest.main()
