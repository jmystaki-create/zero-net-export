from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"
NATIVE_SUPPORT_PATH = PACKAGE_ROOT / "native_support.py"
CONST_PATH = PACKAGE_ROOT / "const.py"
CANDIDATE_UTILS_PATH = PACKAGE_ROOT / "candidate_utils.py"


def _load_native_support_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    ha_pkg = sys.modules.setdefault("homeassistant", types.ModuleType("homeassistant"))
    util_pkg = sys.modules.setdefault("homeassistant.util", types.ModuleType("homeassistant.util"))
    util_pkg.dt = types.SimpleNamespace(now=lambda: None, parse_datetime=lambda value: None)
    ha_pkg.util = util_pkg

    const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", CONST_PATH)
    assert const_spec and const_spec.loader
    const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = const_module
    const_spec.loader.exec_module(const_module)

    coordinator_module = types.ModuleType("custom_components.zero_net_export.coordinator")
    coordinator_module.ZeroNetExportRuntimeState = object
    sys.modules[coordinator_module.__name__] = coordinator_module

    device_model_module = types.ModuleType("custom_components.zero_net_export.device_model")
    device_model_module.parse_device_configs = lambda entry: ([SimpleNamespace(key="pool_pump", name="Pool Pump", kind="load", entity_id="switch.pool_pump", adapter="switch", nominal_power_w=1200, min_power_w=0, max_power_w=1200, step_w=1200, priority=100, enabled=True, min_on_seconds=0, min_off_seconds=0, cooldown_seconds=0, max_active_seconds=0)], [])
    device_model_module.build_device_summary = lambda *args, **kwargs: "summary"
    sys.modules[device_model_module.__name__] = device_model_module

    release_info_module = types.ModuleType("custom_components.zero_net_export.release_info")
    release_info_module.build_install_consistency_summary = lambda provenance: "Manifest matches code version"
    release_info_module.build_install_fingerprint_summary = lambda provenance: "- fingerprint ok"
    release_info_module.build_install_provenance = lambda: {"summary": "Installed 0.1.83"}
    release_info_module.build_release_info = lambda *args, **kwargs: {}
    release_info_module.build_install_repair_step = lambda *args, **kwargs: "repair step"
    release_info_module.build_install_validation_cli_steps = lambda *args, **kwargs: {}
    sys.modules[release_info_module.__name__] = release_info_module

    validation_module = types.ModuleType("custom_components.zero_net_export.validation")
    validation_module.ValidationIssue = object
    validation_module.SourceSpec = object
    validation_module.format_source_binding_label = lambda *args, **kwargs: "label"
    sys.modules[validation_module.__name__] = validation_module

    candidate_utils_spec = importlib.util.spec_from_file_location(
        "custom_components.zero_net_export.candidate_utils",
        CANDIDATE_UTILS_PATH,
    )
    assert candidate_utils_spec and candidate_utils_spec.loader
    candidate_utils_module = importlib.util.module_from_spec(candidate_utils_spec)
    sys.modules[candidate_utils_spec.name] = candidate_utils_module
    candidate_utils_spec.loader.exec_module(candidate_utils_module)

    spec = importlib.util.spec_from_file_location(
        "custom_components.zero_net_export.native_support",
        NATIVE_SUPPORT_PATH,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CommandCenterSummaryTests(unittest.TestCase):
    def test_command_center_summary_exposes_structured_control_board_fields(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.REQUIRED_SOURCE_KEYS = []
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            reason="Monitoring export drift before acting.",
            control_reason="Waiting for min-off timer to clear.",
            status="Active",
            solar_power_w=4200.0,
            grid_import_power_w=350.0,
            grid_export_power_w=0.0,
            home_load_power_w=3850.0,
            battery_soc=78.0,
            battery_charge_power_w=900.0,
            battery_discharge_power_w=0.0,
            export_error_w=350.0,
            control_summary="One device staged, waiting on min-off guard.",
            planned_action_count=1,
            executable_action_count=0,
            active_controlled_power_w=1200.0,
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            controllable_nominal_power_w=1200.0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
        )
        coordinator = SimpleNamespace(data=state, entry=entry)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(summary["headline_decision"], "Action queued, waiting for device guard.")
        self.assertEqual(summary["alert_summary"], "1 managed; no unmanaged candidates")
        self.assertIn("solar 4200.0 W", summary["energy_state_summary"])
        self.assertIn("grid import 350.0 W", summary["energy_state_summary"])
        self.assertIn("battery charge 900.0 W", summary["energy_state_summary"])
        self.assertIn("battery discharge 0.0 W", summary["energy_state_summary"])
        self.assertIn("target", summary["control_decision_summary"])
        self.assertIn("Waiting for min-off timer to clear.", summary["control_decision_summary"])
        self.assertIn("planned actions 1", summary["control_outcome_summary"])
        self.assertIn("active load 1200.0 W", summary["control_outcome_summary"])
        self.assertIn("1 managed", summary["fleet_activity_summary"])
        self.assertIn("enabled 1", summary["fleet_activity_summary"])
        self.assertIn("usable 1", summary["fleet_activity_summary"])
        self.assertIn("1 fixed managed", summary["fleet_activity_summary"])
        self.assertIn("1200 W nominal", summary["fleet_activity_summary"])
        self.assertEqual(summary["device_status"], "1 managed; no unmanaged candidates")
        self.assertNotIn("configured device available", summary["fleet_activity_summary"])
        self.assertNotIn("configured device available", summary["device_status"])
        self.assertIn("Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Sensors", summary["source_repair_step"])

    def test_command_center_summary_includes_unmanaged_backlog_in_fleet_activity_when_hass_candidates_exist(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.REQUIRED_SOURCE_KEYS = []
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [{"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"}],
            "AC Outlet 2",
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            reason="Monitoring export drift before acting.",
            control_reason="Waiting for min-off timer to clear.",
            status="Active",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            controllable_nominal_power_w=1200.0,
            active_controlled_power_w=1200.0,
            blocked_planned_action_count=1,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "pool_pump": {"entity_id": "switch.pool_pump", "observed_active": True, "current_power_w": 1200.0},
            },
        )
        hass = SimpleNamespace(
            states=SimpleNamespace(
                async_all=lambda: [
                    SimpleNamespace(
                        entity_id="switch.pool_pump",
                        state="off",
                        attributes={"friendly_name": "Pool Pump"},
                    ),
                    SimpleNamespace(
                        entity_id="switch.ac_outlet_2",
                        state="off",
                        attributes={"friendly_name": "AC Outlet 2"},
                    ),
                ]
            )
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=hass)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("1 managed", summary["fleet_activity_summary"])
        self.assertIn("1 managed", summary["fleet_activity_summary"])
        self.assertLess(
            summary["fleet_activity_summary"].index("1 unmanaged backlog"),
            summary["fleet_activity_summary"].index("1 fixed managed"),
        )
        self.assertLess(
            summary["fleet_activity_summary"].index("review AC Outlet 2 (fixed) | review first | warn generic outlet label"),
            summary["fleet_activity_summary"].index("1200 W nominal"),
        )
        self.assertIn("1 fixed managed", summary["fleet_activity_summary"])
        self.assertIn("1200 W nominal", summary["fleet_activity_summary"])
        self.assertIn("1 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertNotIn("| 1 unmanaged |", f"| {summary['fleet_activity_summary']} |")
        self.assertIn("1 fixed candidate", summary["fleet_activity_summary"])
        self.assertIn("1 needs review", summary["fleet_activity_summary"])
        self.assertIn("review AC Outlet 2 (fixed) | review first | warn generic outlet label", summary["fleet_activity_summary"])
        self.assertNotIn("top AC Outlet 2", summary["fleet_activity_summary"])
        self.assertIn("review first", summary["fleet_activity_summary"])
        self.assertIn("warn generic outlet label", summary["fleet_activity_summary"])
        self.assertIn("1 blocked managed action", summary["fleet_activity_summary"])
        self.assertIn("active load 1200 W", summary["fleet_activity_summary"])
        self.assertIn("1 active managed device", summary["fleet_activity_summary"])
        self.assertNotIn("configured device available", summary["fleet_activity_summary"])
        self.assertIn("1 unmanaged backlog", summary["device_status"])
        self.assertNotIn("| 1 unmanaged |", f"| {summary['device_status']} |")
        self.assertIn("1 needs review", summary["device_status"])
        self.assertIn(
            "review AC Outlet 2 (fixed) | review first | warn generic outlet label",
            summary["device_status"],
        )
        self.assertNotIn(
            "top AC Outlet 2 (fixed) | review first | warn generic outlet label",
            summary["device_status"],
        )

    def test_command_center_summary_uses_runtime_device_details_when_fleet_counts_lag(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.REQUIRED_SOURCE_KEYS = []
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            device_status_summary="0 configured devices available",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "pool_pump": {
                    "name": "Pool Pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "enabled": True,
                    "effective_enabled": True,
                    "usable": True,
                    "nominal_power_w": 1200,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("1 managed", summary["fleet_activity_summary"])
        self.assertIn("enabled 1", summary["fleet_activity_summary"])
        self.assertIn("usable 1", summary["fleet_activity_summary"])
        self.assertIn("1 fixed managed", summary["fleet_activity_summary"])
        self.assertIn("1200 W nominal", summary["fleet_activity_summary"])
        self.assertNotIn("no managed yet", summary["fleet_activity_summary"])

    def test_command_center_summary_labels_candidate_count_as_unmanaged_backlog(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.REQUIRED_SOURCE_KEYS = []
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [{"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"}],
            "AC Outlet 2",
        )

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            controllable_nominal_power_w=1200.0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={},
        )
        hass = SimpleNamespace(
            states=SimpleNamespace(
                async_all=lambda: [
                    SimpleNamespace(
                        entity_id="switch.ac_outlet_2",
                        state="off",
                        attributes={"friendly_name": "AC Outlet 2"},
                    ),
                ]
            )
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=hass)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("1 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertIn("1 unmanaged backlog", summary["device_status"])

    def test_command_center_summary_keeps_fleet_activity_signal_when_long_details_would_overflow(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [{
                "name": "Garage subboard auxiliary outlet bank candidate 02",
                "entity_id": "switch.garage_subboard_auxiliary_outlet_bank_candidate_02",
                "kind": "fixed",
            }],
            "Garage subboard auxiliary outlet bank candidate 02",
        )
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage subboard auxiliary outlet bank candidate 02 (fixed) | review first | warn generic outlet label needs manual verification before promotion"
        )

        entry = SimpleNamespace(
            data={
                native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
                native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
                native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
                native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
                native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
                native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
            },
            options={},
        )
        state = SimpleNamespace(
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=0,
            fixed_device_count=1,
            controllable_nominal_power_w=4200.0,
            blocked_planned_action_count=1,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "hot_water": {
                    "name": "Hot water relay with extended descriptive label for operator review",
                    "entity_id": "switch.hot_water_relay_with_extended_descriptive_label_for_operator_review",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "action_executable": False,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertNotEqual(summary["fleet_activity_summary"], summary["device_status"])
        self.assertLessEqual(len(summary["fleet_activity_summary"]), 255)
        self.assertIn("1 managed", summary["fleet_activity_summary"])
        self.assertIn("1 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertNotIn("| 1 unmanaged |", f"| {summary['fleet_activity_summary']} |")
        self.assertIn("blocked Hot water relay", summary["fleet_activity_summary"])
        self.assertIn("review Garage subboard auxiliary outlet bank candidate 02", summary["fleet_activity_summary"])

    def test_command_center_summary_keeps_review_and_ready_counts_when_long_fleet_details_overflow(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage subboard auxiliary outlet bank candidate 02",
                    "entity_id": "switch.garage_subboard_auxiliary_outlet_bank_candidate_02",
                    "kind": "fixed",
                },
                {
                    "name": "Pool plant room contactor relay stage 03",
                    "entity_id": "switch.pool_plant_room_contactor_relay_stage_03",
                    "kind": "fixed",
                },
            ],
            "Garage subboard auxiliary outlet bank candidate 02",
        )
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage subboard auxiliary outlet bank candidate 02 (fixed) | review first | warn generic outlet label needs manual verification before promotion"
            if candidate and candidate.get("entity_id") == "switch.garage_subboard_auxiliary_outlet_bank_candidate_02"
            else "Pool plant room contactor relay stage 03 (fixed) | likely useful | key warning: No immediate warnings"
        )

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=0,
            fixed_device_count=1,
            controllable_nominal_power_w=4200.0,
            blocked_planned_action_count=1,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "hot_water": {
                    "name": "Hot water relay with extended descriptive label for operator review",
                    "entity_id": "switch.hot_water_relay_with_extended_descriptive_label_for_operator_review",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "action_executable": False,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), 255)
        self.assertIn("1 needs review", summary["fleet_activity_summary"])
        self.assertIn("1 ready to promote", summary["fleet_activity_summary"])
        self.assertIn("review Garage subboard auxili", summary["fleet_activity_summary"])
        self.assertIn("ready Pool plant room contact", summary["fleet_activity_summary"])

    def test_command_center_summary_keeps_candidate_kind_mix_when_overflow_compacts(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage subboard auxiliary outlet bank candidate 02",
                    "entity_id": "switch.garage_subboard_auxiliary_outlet_bank_candidate_02",
                    "kind": "fixed",
                },
                {
                    "name": "EV charger export absorption control limit",
                    "entity_id": "number.ev_charger_export_absorption_control_limit",
                    "kind": "variable",
                },
            ],
            "Garage subboard auxiliary outlet bank candidate 02",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "medium" if candidate.get("kind") == "fixed" else "high",
            "warnings": ["Generic outlet hardware label needs review."]
            if candidate.get("kind") == "fixed"
            else [],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage subboard auxiliary outlet bank candidate 02 (fixed) | review first | warn generic outlet label needs manual verification before promotion"
            if candidate and candidate.get("kind") == "fixed"
            else "EV charger export absorption control limit (variable) | likely useful | key warning: No immediate warnings"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), 255)
        self.assertIn("1 fixed candidate", summary["fleet_activity_summary"])
        self.assertIn("1 variable candidate", summary["fleet_activity_summary"])
        self.assertIn("1 needs review", summary["fleet_activity_summary"])
        self.assertIn("1 ready to promote", summary["fleet_activity_summary"])
        self.assertIn("review Garage subboard auxili", summary["fleet_activity_summary"])
        self.assertIn("ready EV charger export absor", summary["fleet_activity_summary"])

    def test_command_center_summary_drops_large_kind_mix_counts_before_review_ready_signals(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        candidates = [
            {
                "name": f"Garage auxiliary outlet candidate {index:02d}",
                "entity_id": f"switch.garage_aux_candidate_{index:02d}",
                "kind": "fixed",
            }
            for index in range(1, 7)
        ] + [
            {
                "name": f"EV charger export absorption limit candidate {index:02d}",
                "entity_id": f"number.ev_export_limit_candidate_{index:02d}",
                "kind": "variable",
            }
            for index in range(1, 7)
        ]
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (candidates, candidates[0]["name"])
        native_support.assess_candidate = lambda candidate: {
            "confidence": "medium" if candidate.get("kind") == "fixed" else "high",
            "warnings": ["Generic outlet hardware label needs manual verification."]
            if candidate.get("kind") == "fixed"
            else [],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage auxiliary outlet candidate 01 (fixed) | review first | warn generic outlet hardware label needs manual verification before promotion"
            if candidate and candidate.get("kind") == "fixed"
            else "EV charger export absorption limit candidate 01 (variable) | likely useful | key warning: No immediate warnings"
        )

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=0,
            fixed_device_count=1,
            controllable_nominal_power_w=4200.0,
            blocked_planned_action_count=1,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "hot_water": {
                    "name": "Hot water relay with extended descriptive label for operator review",
                    "entity_id": "switch.hot_water_relay_with_extended_descriptive_label_for_operator_review",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "action_executable": False,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), 255)
        self.assertIn("1 managed", summary["fleet_activity_summary"])
        self.assertIn("12 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertNotIn("12 unmanaged |", summary["fleet_activity_summary"])
        self.assertIn("blocked Hot water relay", summary["fleet_activity_summary"])
        self.assertIn("6 need review", summary["fleet_activity_summary"])
        self.assertIn("6 ready to promote", summary["fleet_activity_summary"])
        self.assertIn("review Garage auxiliary outle", summary["fleet_activity_summary"])
        self.assertIn("ready EV charger export absor", summary["fleet_activity_summary"])
        self.assertNotIn("6 fixed candidates", summary["fleet_activity_summary"])
        self.assertNotIn("6 variable candidates", summary["fleet_activity_summary"])
        self.assertNotIn("fixed backlog", summary["fleet_activity_summary"])
        self.assertNotIn("variable backlog", summary["fleet_activity_summary"])
        self.assertNotIn("1 planned action(s)", summary["fleet_activity_summary"])

    def test_command_center_summary_compacts_device_status_before_it_can_overflow_fallback_surfaces(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Virtual load helper with a spectacularly verbose review-first label in the garage south-west board",
                    "entity_id": "input_boolean.virtual_load_helper_with_a_spectacularly_verbose_review_first_label_in_the_garage_south_west_board",
                    "kind": "fixed",
                },
                {
                    "name": "EV charger export absorber with a spectacularly verbose ready-next label near the workshop entry",
                    "entity_id": "number.ev_charger_export_absorber_with_a_spectacularly_verbose_ready_next_label_near_the_workshop_entry",
                    "kind": "variable",
                },
            ],
            "Virtual load helper with a spectacularly verbose review-first label in the garage south-west board",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "low" if candidate.get("kind") == "fixed" else "high",
            "warnings": ["helper-backed load needs review and validation"] if candidate.get("kind") == "fixed" else ["generic outlet label with long wording for readiness"],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Virtual load helper with a spectacularly verbose review-first label in the garage south-west board (fixed) | review first | warn helper-backed load needs review and validation"
            if candidate and candidate.get("kind") == "fixed"
            else "EV charger export absorber with a spectacularly verbose ready-next label near the workshop entry (variable) | likely useful | warn generic outlet label with long wording for readiness"
        )

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            device_status_summary="Managed Devices: Pool pump blocked on a very long operator-facing explanation while heated floor continues running under a separate active-runtime explanation that should not erase the unmanaged backlog story",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=1,
            fixed_device_count=1,
            variable_device_count=1,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            blocked_planned_action_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["device_status"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("2 unmanaged backlog", summary["device_status"])
        self.assertNotIn("2 unmanaged;", summary["device_status"])
        self.assertIn("1 needs review", summary["device_status"])
        self.assertIn("1 ready to promote", summary["device_status"])
        self.assertIn("review Virtual load helper", summary["device_status"])
        self.assertIn("ready EV charger export absorber", summary["device_status"])

    def test_device_status_helper_keeps_ready_to_promote_grammar_under_plural_compaction(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support._command_center_device_status_with_unmanaged_context(
            "2 configured devices available",
            managed_count=2,
            candidate_count=4,
            fixed_candidate_count=2,
            variable_candidate_count=2,
            review_needed_count=2,
            fixed_review_count=1,
            variable_review_count=1,
            top_candidate_name="Review Candidate Alpha",
            top_candidate_preview="Review Candidate Alpha (fixed) | review first | warn helper-backed load needs review and validation",
            review_candidate_name="Review Candidate Alpha",
            review_candidate_preview="Review Candidate Alpha (fixed) | review first | warn helper-backed load needs review and validation",
            ready_candidate_name="Ready Candidate Beta",
            ready_candidate_preview="Ready Candidate Beta (variable) | likely useful | warm-floor preload absorber near main hallway",
        )

        self.assertIn("2 ready to promote", summary)
        self.assertNotIn("ready to promotes", summary)
        self.assertLessEqual(len(summary), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)

    def test_command_center_summary_keeps_managed_attention_visible_when_fleet_activity_overflows(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Virtual load helper with a spectacularly verbose review-first label in the garage south-west board",
                    "entity_id": "input_boolean.virtual_load_helper_with_a_spectacularly_verbose_review_first_label_in_the_garage_south_west_board",
                    "kind": "fixed",
                },
                {
                    "name": "EV charger export absorber with a spectacularly verbose ready-next label near the workshop entry",
                    "entity_id": "number.ev_charger_export_absorber_with_a_spectacularly_verbose_ready_next_label_near_the_workshop_entry",
                    "kind": "variable",
                },
            ],
            "Virtual load helper with a spectacularly verbose review-first label in the garage south-west board",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "low" if candidate.get("kind") == "fixed" else "high",
            "warnings": ["helper-backed load needs review and validation"] if candidate.get("kind") == "fixed" else ["generic outlet label with long wording for readiness"],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Virtual load helper with a spectacularly verbose review-first label in the garage south-west board (fixed) | review first | warn helper-backed load needs review and validation"
            if candidate and candidate.get("kind") == "fixed"
            else "EV charger export absorber with a spectacularly verbose ready-next label near the workshop entry (variable) | likely useful | warn generic outlet label with long wording for readiness"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            device_status_summary="Managed Devices: Pool pump blocked on a very long operator-facing explanation while heated floor continues running under a separate active-runtime explanation that should not erase the unmanaged backlog story",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=1,
            fixed_device_count=1,
            variable_device_count=1,
            controllable_nominal_power_w=3385.0,
            active_controlled_power_w=920.0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            blocked_planned_action_count=1,
            device_details={
                "pool_pump": {
                    "name": "Pool pump with a very long blocked label that should compact cleanly",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "observed_active": False,
                    "planned_action": "turn_on",
                    "nominal_power_w": 1185.0,
                },
                "heated_floor": {
                    "name": "Heated floor with a very long active runtime label that should survive",
                    "entity_id": "number.heated_floor",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 920.0,
                    "current_target_power_w": 920.0,
                    "planned_action": "hold",
                    "nominal_power_w": 2200.0,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("attention first Pool pump", summary["fleet_activity_summary"])
        self.assertIn("blocked Pool pump", summary["fleet_activity_summary"])
        self.assertIn("2 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertNotIn("| 2 unmanaged |", f"| {summary['fleet_activity_summary']} |")
        self.assertIn("fixed backlog 1 review", summary["fleet_activity_summary"])
        self.assertIn("variable backlog 1 ready", summary["fleet_activity_summary"])
        self.assertIn("review Virtual load", summary["fleet_activity_summary"])
        self.assertIn("ready EV charger", summary["fleet_activity_summary"])
        self.assertNotIn("1 fixed candidate", summary["fleet_activity_summary"])
        self.assertNotIn("1 variable candidate", summary["fleet_activity_summary"])

    def test_command_center_summary_surfaces_fixed_and_variable_review_mix(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"},
                {"name": "EV limit", "entity_id": "number.ev_limit", "kind": "variable"},
            ],
            "AC Outlet 2",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "medium",
            "warnings": ["Generic outlet hardware label needs review."]
            if candidate.get("kind") == "fixed"
            else ["Variable power controls need a meaningful unit, sane range, and clear relation to real device power."],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "AC Outlet 2 (fixed) | review first | warn generic outlet label"
            if candidate and candidate.get("kind") == "fixed"
            else "EV limit (variable) | review first | warn missing clear unit"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            reason="Monitoring export drift before acting.",
            control_reason="Waiting for min-off timer to clear.",
            status="Active",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            controllable_nominal_power_w=1200.0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={"pool_pump": {"entity_id": "switch.pool_pump"}},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("2 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertNotIn("| 2 unmanaged |", f"| {summary['fleet_activity_summary']} |")
        self.assertIn("fixed backlog 1 review", summary["fleet_activity_summary"])
        self.assertIn("variable backlog 1 review", summary["fleet_activity_summary"])
        self.assertIn("2 need review", summary["fleet_activity_summary"])
        self.assertIn("review AC Outlet 2", summary["fleet_activity_summary"])
        self.assertNotIn("top AC Outlet 2", summary["fleet_activity_summary"])
        self.assertIn("fixed backlog 1 review", summary["device_status"])
        self.assertIn("variable backlog 1 review", summary["device_status"])

    def test_command_center_summary_names_blocked_device_when_plan_is_non_executable_before_usable_flips_false(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            reason="Monitoring export drift before acting.",
            control_reason="Waiting for min-off timer to clear.",
            status="Active",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            controllable_nominal_power_w=1200.0,
            active_controlled_power_w=1185.0,
            blocked_planned_action_count=1,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "pool_pump": {
                    "name": "Pool Pump",
                    "entity_id": "switch.pool_pump",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 1185.0,
                    "planned_action": "on",
                    "action_executable": False,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("1 managed device needs attention", summary["fleet_activity_summary"])
        self.assertIn("blocked Pool Pump", summary["fleet_activity_summary"])
        self.assertIn("action on", summary["fleet_activity_summary"])
        self.assertIn("active load 1185 W", summary["fleet_activity_summary"])
        self.assertIn("1 active managed device", summary["fleet_activity_summary"])

    def test_command_center_summary_surfaces_recent_failure_attention_even_without_blocked_or_planned_action(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            reason="Monitoring export drift before acting.",
            control_reason="Holding current fleet posture.",
            status="Active",
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=2,
            fixed_device_count=2,
            controllable_nominal_power_w=2200.0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "pool_pump": {
                    "name": "Pool Pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "planned_action": "hold",
                    "last_action_status": "timeout",
                },
                "hot_water": {
                    "name": "Hot Water",
                    "entity_id": "switch.hot_water",
                    "kind": "fixed",
                    "usable": True,
                    "planned_action": "hold",
                    "last_action_status": "ok",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("1 managed device needs attention", summary["fleet_activity_summary"])
        self.assertIn("attention first Pool Pump (fixed | last timeout)", summary["fleet_activity_summary"])
        self.assertNotIn("blocked Pool Pump", summary["fleet_activity_summary"])
        self.assertNotIn("plan Pool Pump", summary["fleet_activity_summary"])

    def test_command_center_summary_prefers_attention_first_runtime_order_over_config_insertion_order(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support.build_install_provenance = lambda *args, **kwargs: {
            "pending_async_refresh": False,
            "manifest_matches_code_version": True,
        }
        native_support.build_install_consistency_summary = lambda provenance: "Installed build matches repo candidate"
        native_support.build_install_status_summary = lambda provenance: "Installed package matches current repo"
        native_support.build_install_next_step = lambda provenance: "No install action needed"
        native_support.build_install_snapshot_path = lambda provenance: "Open Diagnostics for install details"
        native_support.discover_candidate_devices = lambda *args, **kwargs: []

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            reason="Holding steady.",
            control_reason="Waiting for the next load action.",
            status="Active",
            device_status_summary="3 configured devices available",
            device_count=3,
            enabled_device_count=3,
            usable_device_count=2,
            fixed_device_count=2,
            variable_device_count=1,
            controllable_nominal_power_w=4700.0,
            active_controlled_power_w=2400.0,
            blocked_planned_action_count=1,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "steady_floor": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor",
                    "kind": "variable",
                    "usable": True,
                    "effective_enabled": True,
                    "priority": 50,
                    "planned_action": "hold",
                    "nominal_power_w": 2200.0,
                },
                "late_blocked": {
                    "name": "Water heater",
                    "entity_id": "switch.water_heater",
                    "kind": "fixed",
                    "usable": False,
                    "effective_enabled": True,
                    "priority": 120,
                    "planned_action": "turn_on",
                    "action_executable": False,
                    "nominal_power_w": 1800.0,
                },
                "earlier_plan": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "effective_enabled": True,
                    "priority": 80,
                    "planned_action": "turn_on",
                    "action_executable": True,
                    "nominal_power_w": 700.0,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("blocked Water heater (fixed | not usable", summary["fleet_activity_summary"])
        self.assertIn(
            f"Open {native_support.DEVICES_CONFIGURE_PATH} to review blocked devices in the Managed Devices workspace, starting with Water heater",
            summary["next_action_summary"],
        )

    def test_command_center_summary_keeps_managed_devices_workspace_explicit_for_active_plan(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Continue in Managed Devices.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            status="Running",
            current_mode="auto",
            solar_power=3200.0,
            grid_power=-600.0,
            home_power=2600.0,
            battery_soc=78.0,
            battery_power=-900.0,
            active_load_power=1400.0,
            target_export_w=0.0,
            export_error_w=-600.0,
            blocked_planned_action_count=0,
            candidate_summary="None",
            candidate_review_needed_count=0,
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "effective_enabled": True,
                    "priority": 80,
                    "planned_action": "turn_on",
                    "action_executable": True,
                    "nominal_power_w": 700.0,
                }
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("1 planned action", summary["fleet_activity_summary"])
        self.assertNotIn("planned action(s)", summary["fleet_activity_summary"])
        self.assertIn(
            f"Open {native_support.DEVICES_CONFIGURE_PATH} to confirm the active fleet plan in the Managed Devices workspace for Pool pump (fixed | action turn_on).",
            summary["next_action_summary"],
        )

    def test_command_center_summary_keeps_unmanaged_split_when_device_config_needs_repair(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Repair the managed-device configuration.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support.parse_device_configs = lambda entry: (
            [
                SimpleNamespace(
                    key="pool_pump",
                    name="Pool Pump",
                    kind="load",
                    entity_id="switch.pool_pump",
                    adapter="switch",
                    nominal_power_w=1200,
                    min_power_w=0,
                    max_power_w=1200,
                    step_w=1200,
                    priority=100,
                    enabled=True,
                    min_on_seconds=0,
                    min_off_seconds=0,
                    cooldown_seconds=0,
                    max_active_seconds=0,
                )
            ],
            ["missing adapter"],
        )

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            reason="Monitoring export drift before acting.",
            control_reason="Waiting for min-off timer to clear.",
            status="Active",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            controllable_nominal_power_w=1200.0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={"pool_pump": {"entity_id": "switch.pool_pump"}},
        )
        hass = SimpleNamespace(
            states=SimpleNamespace(
                async_all=lambda: [
                    SimpleNamespace(
                        entity_id="switch.garage_power",
                        state="off",
                        attributes={"friendly_name": "Garage Power"},
                    ),
                    SimpleNamespace(
                        entity_id="switch.dishwasher_power",
                        state="off",
                        attributes={"friendly_name": "Dishwasher Power"},
                    ),
                ]
            )
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=hass)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("1 configured, with 1 issue(s) to repair", summary["device_status"])
        self.assertIn("2 unmanaged backlog", summary["device_status"])
        self.assertNotIn("| 2 unmanaged |", f"| {summary['device_status']} |")
        self.assertIn("1 needs review", summary["device_status"])
        self.assertIn("1 ready to promote", summary["device_status"])
        self.assertIn("review Garage Power (fixed) | review first | warn generic circuit label", summary["device_status"])
        self.assertIn("ready Dishwasher Power (fixed) | likely useful", summary["device_status"])
        self.assertNotIn("2 unmanaged ready", summary["device_status"])

    def test_command_center_summary_keeps_review_first_hint_when_review_target_differs_from_top_candidate(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {"name": "Dishwasher Power", "entity_id": "switch.dishwasher_power", "kind": "fixed"},
                {"name": "Garage Power", "entity_id": "switch.garage_power", "kind": "fixed"},
            ],
            "Dishwasher Power",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "high" if candidate.get("name") == "Dishwasher Power" else "low",
            "warnings": [] if candidate.get("name") == "Dishwasher Power" else ["generic circuit label"],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_review_hint = lambda candidate, include_warning=True: (
            "likely useful"
            if candidate and candidate.get("name") == "Dishwasher Power"
            else ("review carefully | warn generic circuit label" if include_warning else "review carefully")
        )
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Dishwasher Power (fixed) | likely useful"
            if candidate and candidate.get("name") == "Dishwasher Power"
            else "Garage Power (fixed) | review carefully | warn generic circuit label"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            reason="Monitoring export drift before acting.",
            control_reason="Waiting for min-off timer to clear.",
            status="Active",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            controllable_nominal_power_w=1200.0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "pool_pump": {"entity_id": "switch.pool_pump"},
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("1 needs review", summary["fleet_activity_summary"])
        self.assertIn("review Garage Power", summary["fleet_activity_summary"])
        self.assertIn("review carefully", summary["fleet_activity_summary"])
        self.assertIn("warn generic circuit label", summary["fleet_activity_summary"])
        self.assertIn("ready Dishwasher Power", summary["fleet_activity_summary"])
        self.assertNotIn("top Dishwasher Power", summary["fleet_activity_summary"])
        self.assertIn("likely useful", summary["fleet_activity_summary"])
        self.assertIn("2 unmanaged backlog", summary["device_status"])
        self.assertNotIn("| 2 unmanaged |", f"| {summary['device_status']} |")
        self.assertIn("1 needs review", summary["device_status"])
        self.assertIn("1 ready to promote", summary["device_status"])
        self.assertIn("review Garage Power (fixed) | review carefully | warn generic circuit label", summary["device_status"])
        self.assertIn("ready Dishwasher Power (fixed) | likely useful", summary["device_status"])
        self.assertNotIn("top Dishwasher Power (fixed) | likely useful", summary["device_status"])

    def test_command_center_summary_names_ready_next_candidate_when_top_candidate_needs_review(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the next unmanaged candidate.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
                {"name": "Hot water relay", "entity_id": "switch.hot_water_relay", "kind": "fixed"},
            ],
            "Virtual load",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "low" if candidate.get("name") == "Virtual load" else "high",
            "warnings": ["helper-backed load needs review"] if candidate.get("name") == "Virtual load" else [],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_review_hint = lambda candidate, include_warning=True: (
            "review carefully | warn helper-backed load needs review"
            if candidate and candidate.get("name") == "Virtual load" and include_warning
            else (
                "review carefully"
                if candidate and candidate.get("name") == "Virtual load"
                else "likely useful"
            )
        )
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Virtual load (fixed) | review carefully | warn helper-backed load needs review"
            if candidate and candidate.get("name") == "Virtual load"
            else "Hot water relay (fixed) | likely useful"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("ready Hot water relay", summary["fleet_activity_summary"])
        self.assertIn("review Virtual load (fixed) | review carefully | warn helper-backed load needs review", summary["fleet_activity_summary"])
        self.assertNotIn("top Virtual load", summary["fleet_activity_summary"])
        self.assertIn("review Virtual load (fixed) | review carefully | warn helper-backed load needs review", summary["device_status"])
        self.assertIn("ready Hot water relay (fixed) | likely useful", summary["device_status"])
        self.assertNotIn("top Virtual load (fixed) | review carefully | warn helper-backed load needs review", summary["device_status"])

    def test_command_center_summary_names_ready_top_candidate_when_no_review_first_candidate_exists(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Promote the next unmanaged candidate.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [{"name": "Dishwasher Power", "entity_id": "switch.dishwasher_power", "kind": "fixed"}],
            "Dishwasher Power",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "high",
            "warnings": [],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_review_hint = lambda candidate, include_warning=True: "likely useful"
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Dishwasher Power (fixed) | likely useful"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("ready Dishwasher Power", summary["fleet_activity_summary"])
        self.assertNotIn("top Dishwasher Power", summary["fleet_activity_summary"])
        self.assertIn("ready Dishwasher Power (fixed) | likely useful", summary["device_status"])
        self.assertNotIn("top Dishwasher Power (fixed) | likely useful", summary["device_status"])

    def test_command_center_summary_lists_source_repair_before_candidate_mix_for_empty_fleet(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Repair the mapped-source blockers first.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [native_support.CONF_GRID_EXPORT_POWER_ENTITY],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "Grid export power is unavailable"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "Grid export power"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources need attention"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.SOURCES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Grid export: sensor.grid_export_power"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [{"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"}],
            "AC Outlet 2",
        )

        entry = SimpleNamespace(data={
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Needs attention",
            diagnostic_summary="Needs attention",
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertTrue(
            summary["fleet_activity_summary"].startswith(
                "no managed yet | 1 unmanaged backlog | source blockers active | 1 fixed candidate | fixed backlog 1 review | 1 needs review | 1 fixed review | review AC Outlet 2"
            )
        )

    def test_command_center_summary_keeps_managed_unmanaged_split_ahead_of_source_repair_note(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Repair the mapped-source blockers first.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [native_support.CONF_GRID_EXPORT_POWER_ENTITY],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "Grid export power is unavailable"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "Grid export power"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources need attention"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.SOURCES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Grid export: sensor.grid_export_power"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [{"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"}],
            "AC Outlet 2",
        )

        entry = SimpleNamespace(data={
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Needs attention",
            diagnostic_summary="Needs attention",
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=1,
            blocked_planned_action_count=1,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "action_executable": False,
                },
                "heater": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor_limit",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 920,
                    "planned_action": "hold",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLess(
            summary["fleet_activity_summary"].index("attention first Pool pump"),
            summary["fleet_activity_summary"].index("1 unmanaged backlog"),
        )
        self.assertLess(
            summary["fleet_activity_summary"].index("1 unmanaged backlog"),
            summary["fleet_activity_summary"].index("source blockers active"),
        )
        self.assertIn("blocked Pool pump", summary["fleet_activity_summary"])
        self.assertIn("review AC Outlet 2", summary["fleet_activity_summary"])

    def test_command_center_summary_prefers_top_candidate_preview_for_empty_fleet_next_step(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [{"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"}],
            "AC Outlet 2",
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn(
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices to continue in the Managed Devices workspace, start in the unmanaged section: AC Outlet 2 (fixed) | review first",
            summary["next_action_summary"],
        )
        self.assertIn(
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices to continue in the Managed Devices workspace, start in the unmanaged section: AC Outlet 2 (fixed) | review first",
            summary["device_next_step"],
        )
        self.assertNotIn("generic outlet hardware", summary["next_action_summary"])

    def test_command_center_summary_keeps_empty_fleet_handoff_workspace_first_when_no_candidates_exist(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Add the first managed device.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        expected = (
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices "
            "to continue in the Managed Devices workspace, then add the first fixed or variable load there because no surfaced unmanaged candidate is available."
        )
        self.assertEqual(expected, summary["device_next_step"])
        self.assertEqual(expected, summary["next_action_summary"])
        self.assertNotIn("promote next", summary["device_next_step"])
        self.assertNotIn("the surfaced candidate", summary["device_next_step"])

    def test_command_center_summary_prefers_review_first_candidate_when_it_differs_from_top_rank(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the next unmanaged candidate.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {"name": "Dishwasher Power", "entity_id": "switch.dishwasher_power", "kind": "fixed"},
                {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
            ],
            "Dishwasher Power",
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices to continue in the Managed Devices workspace, start in the unmanaged section: Virtual load, then promote next from the unmanaged section: Dishwasher Power.",
            summary["next_action_summary"],
        )
        self.assertIn(
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices to continue in the Managed Devices workspace, start in the unmanaged section: Virtual load (fixed)",
            summary["device_next_step"],
        )
        self.assertIn(
            "then promote next from the unmanaged section: Dishwasher Power (fixed) | likely useful",
            summary["device_next_step"],
        )
        self.assertNotIn("| likely useful", summary["next_action_summary"])
        self.assertIn("review Virtual load (fixed)", summary["device_status"])
        self.assertIn("ready Dishwasher Power (fixed) | likely useful", summary["device_status"])
        self.assertNotIn("top Dishwasher Power (fixed) | likely useful", summary["device_status"])

    def test_command_center_summary_names_blocked_and_planned_devices_in_fleet_activity(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=1,
            blocked_planned_action_count=1,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "usable": False,
                    "planned_action": "turn_on",
                },
                "ev": {
                    "name": "EV charger",
                    "entity_id": "number.ev_charger_limit",
                    "usable": True,
                    "planned_action": "hold",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("no unmanaged candidates", summary["fleet_activity_summary"])
        self.assertIn("1 managed device needs attention", summary["fleet_activity_summary"])
        self.assertIn("blocked Pool pump", summary["fleet_activity_summary"])
        self.assertIn("action turn_on", summary["fleet_activity_summary"])
        self.assertIn("plan Pool pump", summary["fleet_activity_summary"])
        self.assertLess(
            summary["fleet_activity_summary"].index("blocked Pool pump"),
            summary["fleet_activity_summary"].index("plan Pool pump"),
        )

    def test_command_center_summary_keeps_distinct_active_device_visible_with_attention(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.REQUIRED_SOURCE_KEYS = []
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=2,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "planned_action": "turn_on",
                },
                "heater": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor_limit",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 920,
                    "planned_action": "hold",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn(
            "attention first Pool pump (fixed | action turn_on)",
            summary["fleet_activity_summary"],
        )
        self.assertIn("active device Heated floor (variable | active 920 W)", summary["fleet_activity_summary"])
        self.assertNotIn("plan Pool pump", summary["fleet_activity_summary"])

    def test_command_center_summary_keeps_blocked_managed_signal_when_only_runtime_detail_marks_the_blocker(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and confirm the current live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="2 configured devices available",
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
                    "action_executable": False,
                },
                "heater": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor_limit",
                    "kind": "variable",
                    "usable": True,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn(
            "attention first Pool pump (fixed | blocked)",
            summary["fleet_activity_summary"],
        )
        self.assertIn(
            "blocked Pool pump (fixed | blocked | action turn_on)",
            summary["fleet_activity_summary"],
        )

    def test_command_center_summary_keeps_active_runtime_visible_when_attention_device_is_also_running(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and confirm the current live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            active_controlled_power_w=1185,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 1185,
                    "planned_action": "turn_on",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn(
            "attention first Pool pump (fixed | action turn_on | active 1185 W)",
            summary["fleet_activity_summary"],
        )
        self.assertIn(
            "plan Pool pump (fixed | active 1185 W | action turn_on)",
            summary["fleet_activity_summary"],
        )
        self.assertNotIn("active device Pool pump", summary["fleet_activity_summary"])

    def test_command_center_summary_keeps_distinct_active_device_when_first_active_load_is_planned(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and confirm the current live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")
        native_support.REQUIRED_SOURCE_KEYS = []

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=2,
            active_controlled_power_w=2105,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 1185,
                    "planned_action": "turn_on",
                },
                "heater": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor_limit",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 920,
                    "current_target_power_w": 920,
                    "planned_action": "hold",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("attention first Pool pump", summary["fleet_activity_summary"])
        self.assertIn(
            "active device Heated floor (variable | active 920 W)",
            summary["fleet_activity_summary"],
        )

    def test_command_center_summary_keeps_active_marker_when_attention_device_has_no_runtime_watts(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and confirm the current live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            active_controlled_power_w=0,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": None,
                    "planned_action": "turn_on",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn(
            "attention first Pool pump (fixed | action turn_on | active)",
            summary["fleet_activity_summary"],
        )
        self.assertIn(
            "plan Pool pump (fixed | action turn_on | active)",
            summary["fleet_activity_summary"],
        )
        self.assertNotIn("active load 0", summary["fleet_activity_summary"])
        self.assertNotIn("active device Pool pump", summary["fleet_activity_summary"])

    def test_command_center_summary_prefers_managed_devices_when_unmanaged_backlog_exists(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Validate the native Configure path in a real Home Assistant install.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
                {"name": "Dishwasher Power", "entity_id": "switch.dishwasher_power", "kind": "fixed"},
            ],
            "Virtual load",
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(summary["recommended_section"], native_support.DEVICES_SECTION_LABEL)
        self.assertEqual(summary["recommended_path"], native_support.DEVICES_CONFIGURE_PATH)
        self.assertIn(native_support.DEVICES_CONFIGURE_PATH, summary["next_action_summary"])
        self.assertIn("start in the unmanaged section: Virtual load", summary["next_action_summary"])
        self.assertIn("promote next from the unmanaged section: Dishwasher Power", summary["next_action_summary"])
        self.assertNotIn(native_support.SUPPORT_CONFIGURE_PATH, summary["next_action_summary"])
        self.assertIn("Virtual load", summary["device_next_step"])

    def test_command_center_summary_keeps_managed_devices_workspace_name_when_no_candidates_remain(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], None)

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(
            summary["device_next_step"],
            f"Open {native_support.DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then edit device settings or stage enablement changes there.",
        )
        self.assertNotIn("review the fleet", summary["device_next_step"])

    def test_command_center_summary_names_managed_devices_attention_explicitly(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }

        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "planned_action": "hold",
                    "last_action_status": "failed",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(
            summary["device_next_step"],
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices to continue in the Managed Devices workspace, starting with attention on Pool pump (fixed | last failed).",
        )

    def test_command_center_summary_keeps_separate_planned_device_when_it_differs_from_blocked_device(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=1,
            blocked_planned_action_count=1,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "hold",
                },
                "ev": {
                    "name": "EV charger",
                    "entity_id": "number.ev_charger_limit",
                    "kind": "variable",
                    "usable": True,
                    "planned_action": "set_power",
                    "current_target_power_w": 1800,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("2 managed devices need attention", summary["fleet_activity_summary"])
        self.assertIn("attention first Pool pump (fixed | not usable)", summary["fleet_activity_summary"])
        self.assertIn("blocked Pool pump (fixed | not usable)", summary["fleet_activity_summary"])
        self.assertIn("plan EV charger (variable | target 1800 W | action set_power)", summary["fleet_activity_summary"])

    def test_command_center_summary_keeps_blocked_device_visible_even_without_a_blocked_plan_count(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime still needs fleet attention.",
            "next_step": "Review the blocked managed device.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Attention needed",
            diagnostic_summary="Attention needed",
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=1,
            blocked_planned_action_count=0,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "usable": False,
                    "planned_action": "hold",
                },
                "ev": {
                    "name": "EV charger",
                    "entity_id": "number.ev_charger_limit",
                    "usable": True,
                    "planned_action": "hold",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("1 managed device needs attention", summary["fleet_activity_summary"])
        self.assertIn("attention first Pool pump", summary["fleet_activity_summary"])
        self.assertIn("blocked Pool pump", summary["fleet_activity_summary"])
        self.assertNotIn("plan Pool pump", summary["fleet_activity_summary"])

    def test_command_center_summary_surfaces_top_alerts_across_source_device_and_runtime_blocks(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "runtime_readiness",
            "summary": "Runtime health still needs operator attention.",
            "next_step": "Review the current runtime blocker.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [native_support.CONF_GRID_EXPORT_POWER_ENTITY],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "Grid export power is unavailable"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "Grid export power"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources need attention"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.SOURCES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Grid export: sensor.grid_export_power"

        native_support.parse_device_configs = lambda entry: ([], ["pool_pump missing entity_id"])

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Runtime health still needs operator attention.",
            diagnostic_summary="Runtime health still needs operator attention.",
        )
        coordinator = SimpleNamespace(data=state, entry=entry)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("Mapped-source blockers: Grid export power is unavailable", summary["alert_summary"])
        self.assertIn("Managed-device configuration needs repair for 1 item(s).", summary["alert_summary"])
        self.assertIn("Runtime health still needs operator attention.", summary["alert_summary"])
        self.assertEqual(
            summary["fleet_activity_summary"],
            "no managed yet | no unmanaged candidates | source blockers active",
        )

    def test_command_center_summary_surfaces_managed_device_attention_in_top_alerts(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=0,
            blocked_planned_action_count=1,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "hold",
                    "last_action_status": "failed",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn(
            "Managed Devices: blocked Pool pump (fixed | not usable | last failed)",
            summary["alert_summary"],
        )
        self.assertIn("blocked Pool pump (fixed | not usable | last failed)", summary["fleet_activity_summary"])

    def test_command_center_summary_surfaces_unmanaged_review_backlog_in_top_alerts(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the next unmanaged candidate.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
                {"name": "Hot water relay", "entity_id": "switch.hot_water_relay", "kind": "fixed"},
            ],
            "Virtual load",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "low" if candidate.get("name") == "Virtual load" else "high",
            "warnings": ["helper-backed load needs review"] if candidate.get("name") == "Virtual load" else [],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Virtual load (fixed) | review first"
            if candidate and candidate.get("name") == "Virtual load"
            else "Hot water relay (fixed) | likely useful"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            blocked_planned_action_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("Managed Devices: no managed yet.", summary["alert_summary"])
        self.assertIn("Managed Devices: review first Virtual load (fixed) | review first", summary["alert_summary"])
        self.assertIn("ready next Hot water relay (fixed) | likely useful", summary["alert_summary"])
        self.assertIn("review Virtual load (fixed) | review first", summary["fleet_activity_summary"])
        self.assertIn("ready Hot water relay (fixed) | likely useful", summary["fleet_activity_summary"])

    def test_command_center_summary_surfaces_ready_only_unmanaged_backlog_in_top_alerts(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review Managed Devices.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {"name": "Hot water relay", "entity_id": "switch.hot_water_relay", "kind": "fixed"},
                {"name": "Pool pump", "entity_id": "switch.pool_pump", "kind": "fixed"},
            ],
            "Hot water relay",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "high",
            "warnings": [],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            f"{candidate.get('name')} (fixed) | likely useful" if candidate else ""
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            blocked_planned_action_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("Managed Devices: no managed yet.", summary["alert_summary"])
        self.assertIn("Managed Devices: ready next Hot water relay (fixed) | likely useful", summary["alert_summary"])
        self.assertIn("2 ready to promote", summary["fleet_activity_summary"])
        self.assertIn("ready Hot water relay (fixed) | likely useful", summary["fleet_activity_summary"])
        self.assertEqual(
            (
                "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices "
                "to continue in the Managed Devices workspace, then promote next from the unmanaged section: Hot water relay (fixed) | likely useful"
            ),
            summary["device_next_step"],
        )
        self.assertEqual(
            (
                "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices "
                "to continue in the Managed Devices workspace, then promote next from the unmanaged section: Hot water relay (fixed) | likely useful"
            ),
            summary["next_action_summary"],
        )

    def test_command_center_summary_compacts_top_alerts_before_falling_back_to_none(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "runtime_readiness",
            "summary": "Runtime health still needs operator attention because one very long explanatory sentence keeps expanding the alert strip beyond the Home Assistant state budget.",
            "next_step": "Review the next unmanaged candidate.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": ["grid_export_power"],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: (
            "Grid export power is unavailable, home load telemetry is stale, and battery state of charge still needs confirmation before control can resume safely."
        )
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "Grid export power, home load power, battery state of charge"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources need attention"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.SOURCES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support.build_install_provenance = lambda: {
            "summary": "Installed 0.1.83",
            "pending_async_refresh": False,
            "manifest_matches_code_version": False,
        }
        native_support.build_install_consistency_summary = lambda provenance: (
            "Installed files still look older than the repo candidate and need exact-build revalidation before release bookkeeping can be trusted."
        )
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Virtual load helper with a very long review-first label",
                    "entity_id": "input_boolean.virtual_load_helper_with_a_very_long_review_first_label",
                    "kind": "fixed",
                },
                {
                    "name": "Hot water relay with a very long ready-next label",
                    "entity_id": "switch.hot_water_relay_with_a_very_long_ready_next_label",
                    "kind": "fixed",
                },
            ],
            "Virtual load helper with a very long review-first label",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "low" if "Virtual load" in candidate.get("name", "") else "high",
            "warnings": ["helper-backed load needs review"] if "Virtual load" in candidate.get("name", "") else [],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Virtual load helper with a very long review-first label (fixed) | review first | warn helper-backed load needs review"
            if candidate and "Virtual load" in candidate.get("name", "")
            else "Hot water relay with a very long ready-next label (fixed) | likely useful | warn generic outlet label"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            blocked_planned_action_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertNotEqual(summary["alert_summary"], "No top-level alerts right now.")
        self.assertIn("Mapped-source blockers:", summary["alert_summary"])
        self.assertIn("Managed Devices: no managed yet.", summary["alert_summary"])
        self.assertNotIn("Installed package needs exact-build revalidation", summary["alert_summary"])
        self.assertLessEqual(len(summary["alert_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)

    def test_command_center_summary_promotes_install_provenance_blockers_to_top_alert_and_diagnostics(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.POLICY_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support.build_install_provenance = lambda: {
            "summary": "Installed 0.1.83",
            "pending_async_refresh": True,
            "manifest_matches_code_version": None,
        }
        native_support.build_install_consistency_summary = lambda provenance: "Install provenance is still being refreshed asynchronously."
        native_support.build_install_repair_step = lambda provenance: "Wait for the install provenance refresh, then rerun exact-build validation."

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
        )
        coordinator = SimpleNamespace(data=state, entry=entry)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("Install provenance refresh still pending", summary["alert_summary"])
        self.assertEqual(summary["recommended_section"], native_support.SUPPORT_SECTION_LABEL)
        self.assertEqual(
            summary["next_action_summary"],
            "Wait for the install provenance refresh, then rerun exact-build validation.",
        )
        self.assertEqual(
            summary["device_next_step"],
            "Wait for the install provenance refresh, then rerun exact-build validation.",
        )

    def test_command_center_summary_gates_device_next_step_on_source_repair_before_fleet_work(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime health needs source repair.",
            "next_step": "Open Sensors first.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources need attention"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.SOURCES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: not configured\n- Grid: not configured"

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
        )
        coordinator = SimpleNamespace(data=state, entry=entry)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn(
            f"Open {native_support.SOURCES_CONFIGURE_PATH}, finish these required source roles:",
            summary["device_next_step"],
        )
        self.assertNotIn(native_support.DEVICES_CONFIGURE_PATH, summary["device_next_step"])
        self.assertEqual(
            summary["next_action_summary"],
            f"Open {native_support.SOURCES_CONFIGURE_PATH} and use the highlighted native guidance to continue.",
        )

    def test_command_center_summary_fallback_status_summary_uses_exact_native_path(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "",
            "next_step": "Validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: ""
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.SUPPORT_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={}, options={})
        long_summary = "Support summary " * 30
        state = SimpleNamespace(
            mode="monitoring",
            health_summary=long_summary,
            diagnostic_summary=long_summary,
            device_status_summary="",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
        )
        coordinator = SimpleNamespace(data=state, entry=entry)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(
            summary["status_summary"],
            f"Open {native_support.SUPPORT_CONFIGURE_PATH} to continue in Diagnostics with blocker triage, repairs, or install validation.",
        )
        self.assertNotIn("recommended command-center section", summary["status_summary"])

    def test_command_center_summary_fallback_status_summary_uses_managed_devices_next_step(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "",
            "next_step": "Review the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: ""
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [{"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2", "kind": "fixed"}],
            "AC Outlet 2",
        )

        original_truncate = native_support._truncate_state_summary

        def _devices_only_fallback(value, *args, **kwargs):
            fallback = kwargs.get("fallback")
            if isinstance(value, str) and value.startswith("Managed Devices:"):
                return fallback
            return original_truncate(value, *args, **kwargs)

        native_support._truncate_state_summary = _devices_only_fallback

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="Managed Devices: no managed yet, with an intentionally long fallback-triggering explanation that should not erase the first review step from the status summary",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(summary["device_next_step"], summary["status_summary"])
        self.assertIn(
            f"Open {native_support.DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, start in the unmanaged section: AC Outlet 2 (fixed) | review first",
            summary["status_summary"],
        )
        self.assertNotEqual(
            f"Open {native_support.DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace.",
            summary["status_summary"],
        )

    def test_command_center_summary_fallback_status_summary_uses_controls_bucket_path(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "",
            "next_step": "Tune the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: ""
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.POLICY_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        original_truncate = native_support._truncate_state_summary

        def _controls_only_fallback(value, *args, **kwargs):
            fallback = kwargs.get("fallback")
            if isinstance(value, str) and value.startswith("Mode monitoring;"):
                return fallback
            return original_truncate(value, *args, **kwargs)

        native_support._truncate_state_summary = _controls_only_fallback

        entry = SimpleNamespace(data={}, options={})
        long_summary = "Controls summary " * 30
        state = SimpleNamespace(
            mode="monitoring",
            health_summary=long_summary,
            diagnostic_summary=long_summary,
            device_status_summary="",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
        )
        coordinator = SimpleNamespace(data=state, entry=entry)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(
            summary["status_summary"],
            f"Open {native_support.POLICY_CONFIGURE_PATH} to continue in Controls and tune target export, deadband, reserve, or live mode.",
        )
        self.assertNotIn("recommended command-center section", summary["status_summary"])

    def test_command_center_summary_fallback_status_summary_uses_sensors_bucket_path(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "",
            "next_step": "Check the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: ""
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.SOURCES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        original_truncate = native_support._truncate_state_summary

        def _sensors_only_fallback(value, *args, **kwargs):
            fallback = kwargs.get("fallback")
            if isinstance(value, str) and value.startswith("Missing required source roles:"):
                return fallback
            return original_truncate(value, *args, **kwargs)

        native_support._truncate_state_summary = _sensors_only_fallback

        entry = SimpleNamespace(data={}, options={})
        long_summary = "Sensors summary " * 30
        state = SimpleNamespace(
            mode="monitoring",
            health_summary=long_summary,
            diagnostic_summary=long_summary,
            device_status_summary="",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
        )
        coordinator = SimpleNamespace(data=state, entry=entry)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(
            summary["status_summary"],
            f"Open {native_support.SOURCES_CONFIGURE_PATH} to continue in Sensors and confirm the live source mapping and health.",
        )
        self.assertNotIn("recommended command-center section", summary["status_summary"])

    def test_command_center_summary_uses_decision_first_headline_when_export_is_high(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            solar_power_w=6200.0,
            grid_export_power_w=2100.0,
            grid_import_power_w=0.0,
            home_load_power_w=1800.0,
            battery_soc=91.0,
            battery_below_reserve=False,
            target_export_w=0.0,
            deadband_w=50.0,
            planned_action_count=1,
            executable_action_count=1,
            blocked_planned_action_count=0,
            active_controlled_power_w=0.0,
            usable_device_count=1,
            export_error_w=2100.0,
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            control_reason="Engaging next device",
            control_summary="One device ready to switch on.",
            status="Active",
            reason="Normal control loop",
        )
        coordinator = SimpleNamespace(data=state, entry=entry)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(summary["headline_decision"], "Export too high, engaging load.")

    def test_command_center_summary_uses_decision_first_headline_when_near_target(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            solar_power_w=2500.0,
            grid_export_power_w=15.0,
            grid_import_power_w=0.0,
            home_load_power_w=2485.0,
            battery_soc=84.0,
            battery_below_reserve=False,
            target_export_w=0.0,
            deadband_w=50.0,
            planned_action_count=0,
            executable_action_count=0,
            blocked_planned_action_count=0,
            active_controlled_power_w=1200.0,
            usable_device_count=1,
            export_error_w=15.0,
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            control_reason="Holding current load",
            control_summary="Existing load is stable.",
            status="Active",
            reason="Normal control loop",
        )
        coordinator = SimpleNamespace(data=state, entry=entry)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(summary["headline_decision"], "Near target, holding current managed load.")


    def test_command_center_summary_keeps_live_managed_activity_ahead_of_unmanaged_backlog(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {"name": "Virtual load", "entity_id": "input_boolean.virtual_load", "kind": "fixed"},
                {"name": "EV charger limit", "entity_id": "number.ev_charger_limit", "kind": "variable"},
            ],
            "Virtual load",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "low" if candidate.get("entity_id") == "input_boolean.virtual_load" else "high",
            "summary": "Review before promotion.",
            "warnings": [],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_review_hint = lambda candidate, include_warning=True: (
            "review carefully | warn This is an input_boolean helper."
            if candidate.get("entity_id") == "input_boolean.virtual_load"
            else "likely useful"
        )
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Virtual load (fixed) | review carefully | warn This is an input_boolean helper."
            if candidate.get("entity_id") == "input_boolean.virtual_load"
            else "EV charger limit (variable) | likely useful"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            reason="Monitoring export drift before acting.",
            control_reason="Holding current load.",
            status="Active",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            controllable_nominal_power_w=1185.0,
            active_controlled_power_w=1185.0,
            blocked_planned_action_count=0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "pool_pump": {
                    "name": "Pool Pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "effective_enabled": True,
                    "observed_active": True,
                    "current_power_w": 1185.0,
                    "planned_action": "turn_on",
                    "nominal_power_w": 1185.0,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("active load 1185 W", summary["fleet_activity_summary"])
        self.assertIn("1 active managed device", summary["fleet_activity_summary"])
        self.assertIn("1 needs review", summary["fleet_activity_summary"])
        self.assertIn("1 ready to promote", summary["fleet_activity_summary"])
        self.assertIn("review Virtual load (fixed)", summary["fleet_activity_summary"])
        self.assertIn("ready EV charger limit (variable)", summary["fleet_activity_summary"])
        self.assertLess(
            summary["fleet_activity_summary"].index("active load 1185 W"),
            summary["fleet_activity_summary"].index("1 needs review"),
        )
        self.assertLess(
            summary["fleet_activity_summary"].index("1 active managed device"),
            summary["fleet_activity_summary"].index("review Virtual load (fixed)"),
        )
        self.assertLess(
            summary["fleet_activity_summary"].index("1 active managed device"),
            summary["fleet_activity_summary"].index("2 unmanaged backlog"),
        )

    def test_command_center_summary_surfaces_per_kind_backlog_mix_when_fixed_and_variable_candidates_split(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the next unmanaged candidate.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {"name": "Pool", "entity_id": "switch.pool", "kind": "fixed"},
                {"name": "EV", "entity_id": "number.ev", "kind": "variable"},
            ],
            "Pool",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "low" if candidate.get("kind") == "fixed" else "high",
            "warnings": ["needs review"] if candidate.get("kind") == "fixed" else [],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Pool (fixed) | review first"
            if candidate and candidate.get("kind") == "fixed"
            else "EV (variable) | likely useful"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("fixed backlog 1 review", summary["fleet_activity_summary"])
        self.assertIn("variable backlog 1 ready", summary["fleet_activity_summary"])
        self.assertIn("review Pool (fixed)", summary["fleet_activity_summary"])
        self.assertIn("ready EV (variable)", summary["fleet_activity_summary"])
        self.assertIn("fixed backlog 1 review", summary["device_status"])
        self.assertIn("variable backlog 1 ready", summary["device_status"])
        self.assertIn("review Pool (fixed)", summary["device_status"])
        self.assertIn("ready EV (variable)", summary["device_status"])

    def test_command_center_summary_keeps_single_kind_backlog_visible_without_overflow(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Pool",
                    "entity_id": "switch.pool",
                    "kind": "fixed",
                },
                {
                    "name": "Dishwasher",
                    "entity_id": "switch.dishwasher",
                    "kind": "fixed",
                },
            ],
            "Pool",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "low" if candidate and candidate.get("name") == "Pool" else "high",
            "warnings": ["confirm relay"] if candidate and candidate.get("name") == "Pool" else [],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Pool (fixed) | review first | warn confirm relay"
            if candidate and candidate.get("name") == "Pool"
            else "Dishwasher (fixed) | likely useful"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            device_status_summary="Managed Devices: no managed yet",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("fixed backlog 1 review/1 ready", summary["fleet_activity_summary"])
        self.assertIn("review Pool (fixed)", summary["fleet_activity_summary"])
        self.assertIn("ready Dishwasher (fixed)", summary["fleet_activity_summary"])
        self.assertIn("fixed backlog 1 review/1 ready", summary["device_status"])
        self.assertIn("review Pool (fixed)", summary["device_status"])
        self.assertIn("ready Dishwasher (fixed)", summary["device_status"])

    def test_command_center_summary_preserves_single_kind_review_ready_backlog_under_overflow(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage subboard auxiliary outlet bank candidate 02",
                    "entity_id": "switch.garage_subboard_auxiliary_outlet_bank_candidate_02",
                    "kind": "fixed",
                },
                {
                    "name": "Pool shed circulation relay candidate 03",
                    "entity_id": "switch.pool_shed_circulation_relay_candidate_03",
                    "kind": "fixed",
                },
            ],
            "Garage subboard auxiliary outlet bank candidate 02",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "low"
            if candidate and candidate.get("name") == "Garage subboard auxiliary outlet bank candidate 02"
            else "high",
            "warnings": ["generic outlet label needs manual verification before promotion"]
            if candidate and candidate.get("name") == "Garage subboard auxiliary outlet bank candidate 02"
            else [],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage subboard auxiliary outlet bank candidate 02 (fixed) | review first | warn generic outlet label needs manual verification before promotion"
            if candidate and candidate.get("name") == "Garage subboard auxiliary outlet bank candidate 02"
            else "Pool shed circulation relay candidate 03 (fixed) | likely useful"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            device_status_summary="Managed Devices: 2 managed devices need attention, attention first Pool pump (fixed | action turn_on), blocked Pool pump (fixed | blocked), 1 planned action(s), plan Pool pump (fixed | action turn_on)",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=1,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            blocked_planned_action_count=1,
            active_controlled_power_w=920.0,
            device_details={
                "pool_pump": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "last_action_status": "failed",
                },
                "heated_floor": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 920.0,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("fixed backlog 1 review/1 ready", summary["fleet_activity_summary"])
        self.assertIn("review Garage subboard", summary["fleet_activity_summary"])
        self.assertIn("ready Pool shed", summary["fleet_activity_summary"])
        self.assertIn("fixed backlog 1 review/1 ready", summary["device_status"])
        self.assertIn("review Garage subboard auxiliary outlet bank candidate 02", summary["device_status"])
        self.assertIn("ready Pool shed circulation relay candidate 03", summary["device_status"])

    def test_command_center_summary_keeps_managed_and_unmanaged_story_when_fleet_activity_overflows(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage subboard auxiliary outlet bank candidate 02 with a very long review-first descriptor for overflow",
                    "entity_id": "switch.garage_subboard_auxiliary_outlet_bank_candidate_02",
                    "kind": "fixed",
                },
                {
                    "name": "EV charger export absorption control limit with a very long ready-next descriptor for overflow",
                    "entity_id": "number.ev_charger_export_absorption_control_limit",
                    "kind": "variable",
                },
            ],
            "Garage subboard auxiliary outlet bank candidate 02 with a very long review-first descriptor for overflow",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "medium" if candidate.get("kind") == "fixed" else "high",
            "warnings": ["Generic outlet hardware label needs review."]
            if candidate.get("kind") == "fixed"
            else [],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage subboard auxiliary outlet bank candidate 02 with a very long review-first descriptor for overflow (fixed) | review first | warn generic outlet label needs manual verification before promotion"
            if candidate and candidate.get("kind") == "fixed"
            else "EV charger export absorption control limit with a very long ready-next descriptor for overflow (variable) | likely useful | key warning: No immediate warnings"
        )

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=1,
            controllable_nominal_power_w=6500.0,
            blocked_planned_action_count=1,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "hot_water": {
                    "name": "Hot water relay with verbose managed label",
                    "entity_id": "switch.hot_water_relay_with_verbose_managed_label",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "action_executable": False,
                },
                "ev_limit": {
                    "name": "EV charger with verbose managed label",
                    "entity_id": "number.ev_charger_with_verbose_managed_label",
                    "kind": "variable",
                    "observed_active": True,
                    "current_power_w": 5300.0,
                },
            },
        )
        coordinator = SimpleNamespace(
            data=state,
            entry=entry,
            hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])),
        )

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), 255)
        self.assertNotEqual(summary["fleet_activity_summary"], "2 configured devices available")
        self.assertNotIn("configured devices available", summary["fleet_activity_summary"])
        self.assertIn("2 managed", summary["fleet_activity_summary"])
        self.assertIn("blocked Hot water relay", summary["fleet_activity_summary"])
        self.assertIn("active load 5300 W", summary["fleet_activity_summary"])
        self.assertIn("2 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertIn("fixed backlog 1 review", summary["fleet_activity_summary"])
        self.assertIn("variable backlog 1 ready", summary["fleet_activity_summary"])
        self.assertIn("review Garage subboard", summary["fleet_activity_summary"])
        self.assertIn("ready EV charger", summary["fleet_activity_summary"])

    def test_command_center_summary_drops_nominal_before_single_kind_managed_mix_under_overflow(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support.REQUIRED_SOURCE_KEYS = []
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {"name": "Garage candidate 02", "entity_id": "switch.garage_candidate_02", "kind": "fixed"},
            ],
            "Garage candidate 02",
        )
        native_support.assess_candidate = lambda candidate: (
            {
                "confidence": "low",
                "warnings": ["generic outlet label needs manual verification before promotion"],
            }
            if candidate and candidate.get("entity_id") == "switch.garage_candidate_02"
            else {"confidence": "high", "warnings": []}
        )
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage candidate 02 (fixed) | review first | warn generic outlet label needs manual verification before promotion"
            if candidate and candidate.get("entity_id") == "switch.garage_candidate_02"
            else ""
        )

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            device_status_summary="Managed Devices: 1 managed device needs attention, attention first Pool pump blocker (fixed | blocked)",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=0,
            fixed_device_count=1,
            variable_device_count=0,
            controllable_nominal_power_w=4200.0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            blocked_planned_action_count=0,
            device_details={
                "pool_pump": {
                    "name": "Pool pump blocker",
                    "entity_id": "switch.pool_pump_blocker",
                    "kind": "fixed",
                    "usable": False,
                    "action_executable": False,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("1 fixed managed", summary["fleet_activity_summary"])
        self.assertNotIn("4200 W nominal", summary["fleet_activity_summary"])
        self.assertIn("1 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertIn("1 needs review", summary["fleet_activity_summary"])
        self.assertIn("review Garage candidate 02", summary["fleet_activity_summary"])
        self.assertNotIn("ready ", summary["fleet_activity_summary"])

    def test_command_center_summary_preserves_single_kind_review_only_backlog_under_overflow(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage subboard auxiliary outlet bank candidate 02",
                    "entity_id": "switch.garage_subboard_auxiliary_outlet_bank_candidate_02",
                    "kind": "fixed",
                },
                {
                    "name": "Workshop north wall outlet verification candidate 04",
                    "entity_id": "switch.workshop_north_wall_outlet_verification_candidate_04",
                    "kind": "fixed",
                },
            ],
            "Garage subboard auxiliary outlet bank candidate 02",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "low",
            "warnings": ["generic outlet label needs manual verification before promotion"],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage subboard auxiliary outlet bank candidate 02 (fixed) | review first | warn generic outlet label needs manual verification before promotion"
            if candidate and candidate.get("name") == "Garage subboard auxiliary outlet bank candidate 02"
            else "Workshop north wall outlet verification candidate 04 (fixed) | review first | warn confirm downstream circuit before promotion"
        )

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            device_status_summary="Managed Devices: 2 managed devices need attention, attention first Pool pump (fixed | action turn_on), blocked Pool pump (fixed | blocked), 1 planned action(s), plan Pool pump (fixed | action turn_on)",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=1,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            blocked_planned_action_count=1,
            active_controlled_power_w=920.0,
            device_details={
                "pool_pump": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "last_action_status": "failed",
                },
                "heated_floor": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 920.0,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("fixed backlog 2 review", summary["fleet_activity_summary"])
        self.assertIn("review Garage subboard", summary["fleet_activity_summary"])
        self.assertNotIn("ready ", summary["fleet_activity_summary"])
        self.assertLessEqual(len(summary["device_status"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("fixed backlog 2 review", summary["device_status"])
        self.assertIn("review Garage subboard auxiliary outlet bank candidate 02", summary["device_status"])
        self.assertNotIn("ready ", summary["device_status"])

    def test_command_center_summary_prefers_controls_over_diagnostics_when_policy_is_the_recommended_home(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "steady_state",
            "summary": "Runtime looks healthy.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.POLICY_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=2,
            fixed_device_count=1,
            variable_device_count=1,
            controllable_nominal_power_w=3385.0,
            active_controlled_power_w=0.0,
            blocked_planned_action_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(
            (
                "Sources and devices are in place, so open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Controls "
                "next to tune target export, deadband, reserve, or live mode."
            ),
            summary["next_action_summary"],
        )
        self.assertEqual(native_support.POLICY_SECTION_LABEL, summary["recommended_section"])
        self.assertNotIn("diagnostics review", summary["next_action_summary"])
        self.assertNotIn(native_support.SUPPORT_CONFIGURE_PATH, summary["next_action_summary"])

    def test_command_center_summary_operator_ready_keeps_controls_handoff_when_policy_is_recommended(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Validate the native Configure path plus device-page diagnostics in a real Home Assistant install.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.POLICY_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=2,
            fixed_device_count=1,
            variable_device_count=1,
            controllable_nominal_power_w=3385.0,
            active_controlled_power_w=0.0,
            blocked_planned_action_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(
            (
                "Sources and devices are in place, so open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Controls "
                "next to tune target export, deadband, reserve, or live mode."
            ),
            summary["next_action_summary"],
        )
        self.assertEqual(native_support.POLICY_SECTION_LABEL, summary["recommended_section"])
        self.assertNotIn("real Home Assistant install", summary["next_action_summary"])
        self.assertNotIn(native_support.SUPPORT_CONFIGURE_PATH, summary["next_action_summary"])

    def test_command_center_summary_truncation_fallback_keeps_controls_handoff_when_policy_is_recommended(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Tune target export, deadband, reserve, and live mode after reviewing the operator console. " * 8,
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.POLICY_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=2,
            fixed_device_count=1,
            variable_device_count=1,
            controllable_nominal_power_w=3385.0,
            active_controlled_power_w=0.0,
            blocked_planned_action_count=0,
            device_details={},
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(
            (
                "Sources and devices are in place, so open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Controls "
                "next to tune target export, deadband, reserve, or live mode."
            ),
            summary["next_action_summary"],
        )
        self.assertEqual(native_support.POLICY_SECTION_LABEL, summary["recommended_section"])
        self.assertNotIn(native_support.SUPPORT_CONFIGURE_PATH, summary["next_action_summary"])

    def test_command_center_summary_surfaces_active_managed_load_and_count_in_fleet_activity(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            reason="Monitoring export drift before acting.",
            control_reason="Holding current load.",
            status="Active",
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=2,
            fixed_device_count=1,
            variable_device_count=1,
            controllable_nominal_power_w=3385.0,
            active_controlled_power_w=2105.0,
            blocked_planned_action_count=0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "pool_pump": {
                    "name": "Pool Pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 1185.0,
                    "planned_action": "hold",
                    "nominal_power_w": 1185.0,
                },
                "heated_floor": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 920.0,
                    "current_target_power_w": 920.0,
                    "planned_action": "hold",
                    "nominal_power_w": 2200.0,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("active load 2105 W", summary["fleet_activity_summary"])
        self.assertIn("2 active managed devices", summary["fleet_activity_summary"])
        self.assertIn("active device Heated floor (variable | active 920 W)", summary["fleet_activity_summary"])
        self.assertIn("1 fixed managed", summary["fleet_activity_summary"])
        self.assertIn("1 variable managed", summary["fleet_activity_summary"])
        self.assertIn("3385 W nominal", summary["fleet_activity_summary"])

    def test_command_center_summary_keeps_active_device_signal_when_runtime_power_is_missing(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and validate the next live action.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources healthy"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        entry = SimpleNamespace(data={
            native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            native_support.CONF_SOLAR_ENERGY_ENTITY: "sensor.solar_energy",
            native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
            native_support.CONF_GRID_EXPORT_POWER_ENTITY: "sensor.grid_export_power",
            native_support.CONF_GRID_IMPORT_ENERGY_ENTITY: "sensor.grid_import_energy",
            native_support.CONF_GRID_EXPORT_ENERGY_ENTITY: "sensor.grid_export_energy",
        }, options={})
        state = SimpleNamespace(
            reason="Monitoring export drift before acting.",
            control_reason="Holding current load.",
            status="Active",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            variable_device_count=0,
            controllable_nominal_power_w=1185.0,
            active_controlled_power_w=0.0,
            blocked_planned_action_count=0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "pool_pump": {
                    "name": "Pool Pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": None,
                    "planned_action": "hold",
                    "nominal_power_w": 1185.0,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("1 active managed device", summary["fleet_activity_summary"])
        self.assertIn("active device Pool Pump (fixed | active)", summary["fleet_activity_summary"])
        self.assertNotIn("active load 0", summary["fleet_activity_summary"])


if __name__ == "__main__":
    unittest.main()
