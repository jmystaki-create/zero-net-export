from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from decimal import Decimal
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
    def test_operator_checklist_uses_normal_plural_copy_for_device_counts(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_source_attention_details = lambda state: {
            "validation_details": {"issues": []},
            "source_diagnostics": {},
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_selector_fallback_hint = lambda *args, **kwargs: ""

        entry = SimpleNamespace(data={key: f"sensor.{key}" for key in native_support.REQUIRED_SOURCE_KEYS}, options={})
        state = SimpleNamespace(usable_device_count=1, stale_data=False, safe_mode=False)

        checklist = native_support._build_operator_checklist(
            state,
            entry,
            [
                {"key": "pool", "name": "Pool pump"},
                {"key": "heater", "name": "Heater"},
            ],
            [],
        )["checklist"]
        details = {item["key"]: item["detail"] for item in checklist}

        self.assertEqual(details["sources_validated"], "Source roles currently validate cleanly enough for runtime control.")
        self.assertEqual(details["devices_configured"], "2 devices configured.")
        self.assertEqual(details["devices_usable"], "1 usable device available right now.")
        self.assertNotIn("Mapped sources currently validate", "\n".join(details.values()))
        self.assertNotIn("device(s)", "\n".join(details.values()))

    def test_compact_top_alert_summary_drops_literal_none_placeholders(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support._compact_top_alert_summary(
            ["None", "Managed Devices: blocked Pool pump (fixed | action turn_on)"],
            ["None", "Managed Devices: review first Virtual load (fixed) | review first"],
            fallback="No top-level alerts right now.",
        )

        self.assertEqual(
            summary,
            "Managed Devices: blocked Pool pump (fixed | action turn_on)",
        )
        self.assertNotIn("None", summary)

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
        self.assertEqual(
            summary["alert_summary"],
            "1 managed; active load 1200 W; 1 active managed device; no unmanaged candidates",
        )
        self.assertIn("solar 4200.0 W", summary["energy_state_summary"])
        self.assertIn("grid import 350.0 W", summary["energy_state_summary"])
        self.assertIn("battery charge 900.0 W", summary["energy_state_summary"])
        self.assertIn("battery discharge 0.0 W", summary["energy_state_summary"])
        self.assertIn("target", summary["control_decision_summary"])
        self.assertIn("Waiting for min-off timer to clear.", summary["control_decision_summary"])
        self.assertTrue(summary["control_outcome_summary"].startswith("planned actions 1 | ready actions 0 | active load 1200.0 W"))
        self.assertIn("active load 1200.0 W", summary["control_outcome_summary"])
        self.assertIn("1 managed", summary["fleet_activity_summary"])
        self.assertIn("active load 1200", summary["fleet_activity_summary"])
        self.assertIn("1 active managed device", summary["fleet_activity_summary"])
        self.assertIn("enabled 1", summary["fleet_activity_summary"])
        self.assertIn("usable 1", summary["fleet_activity_summary"])
        self.assertIn("1 fixed managed", summary["fleet_activity_summary"])
        self.assertIn("1200 W nominal", summary["fleet_activity_summary"])
        self.assertEqual(
            summary["device_status"],
            "1 managed; active load 1200 W; 1 active managed device; no unmanaged candidates",
        )
        self.assertNotIn("configured device available", summary["fleet_activity_summary"])
        self.assertNotIn("configured device available", summary["device_status"])
        self.assertIn("Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Sensors", summary["source_repair_step"])

    def test_fleet_activity_operator_format_keeps_trailing_managed_inventory_in_managed_bucket(self) -> None:
        native_support = _load_native_support_module()

        formatted = native_support.format_fleet_activity_for_operator(
            "1 managed | 2 unmanaged backlog | source blockers active | fixed backlog 1 review | "
            "variable backlog 1 ready | review Garage heater (fixed | review) | "
            "ready EV charger (variable | ready) | enabled 1 | disabled 1 | usable 1 | 1 fixed managed"
        )

        self.assertTrue(formatted.startswith("source blockers active; Managed devices: "))
        self.assertIn(
            "Managed devices: 1 managed | enabled 1 | disabled 1 | usable 1 | 1 fixed managed; Unmanaged backlog: 2 unmanaged backlog",
            formatted,
        )
        unmanaged_bucket = formatted.split("; Unmanaged backlog: ", 1)[1]
        self.assertNotIn("enabled 1", unmanaged_bucket)
        self.assertNotIn("disabled 1", unmanaged_bucket)
        self.assertNotIn("usable 1", unmanaged_bucket)
        self.assertNotIn("1 fixed managed", unmanaged_bucket)

    def test_fleet_activity_operator_format_labels_empty_unmanaged_section_as_candidates(self) -> None:
        native_support = _load_native_support_module()

        formatted = native_support.format_fleet_activity_for_operator(
            "1 managed | active load 1200 W | 1 active managed device | no unmanaged candidates"
        )

        self.assertEqual(
            formatted,
            "Managed devices: 1 managed | active load 1200 W | 1 active managed device; "
            "Unmanaged candidates: no unmanaged candidates",
        )
        self.assertNotIn("Unmanaged backlog: no unmanaged candidates", formatted)

    def test_fleet_activity_summary_names_disabled_managed_devices_when_inventory_is_visible(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support._build_command_center_fleet_activity_summary(
            SimpleNamespace(
                device_count=2,
                enabled_device_count=1,
                usable_device_count=1,
                fixed_device_count=2,
                variable_device_count=0,
                controllable_nominal_power_w=2400,
                active_controlled_power_w=0,
                device_details={},
            ),
            candidate_count=0,
            fixed_candidate_count=0,
            variable_candidate_count=0,
            review_needed_count=0,
            fixed_review_count=0,
            variable_review_count=0,
            review_candidate_name="",
            review_candidate_preview="",
            ready_candidate_name="",
            ready_candidate_preview="",
            top_candidate_name="",
            top_candidate_preview="",
            source_blocked=False,
        )

        self.assertIn("2 managed", summary)
        self.assertIn("enabled 1", summary)
        self.assertIn("disabled 1", summary)
        self.assertIn("usable 1", summary)
        self.assertIn("2 fixed managed", summary)

    def test_fleet_activity_summary_keeps_quiet_managed_inventory_before_unmanaged_backlog(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support._build_command_center_fleet_activity_summary(
            SimpleNamespace(
                device_count=2,
                enabled_device_count=1,
                usable_device_count=1,
                fixed_device_count=1,
                variable_device_count=1,
                controllable_nominal_power_w=3200,
                active_controlled_power_w=0,
                device_details={},
            ),
            candidate_count=2,
            fixed_candidate_count=1,
            variable_candidate_count=1,
            review_needed_count=1,
            fixed_review_count=1,
            variable_review_count=0,
            review_candidate_name="Relay",
            review_candidate_preview="Relay",
            ready_candidate_name="EV",
            ready_candidate_preview="EV",
            top_candidate_name="Relay",
            top_candidate_preview="Relay",
            source_blocked=False,
        )

        managed_index = summary.index("2 managed")
        enabled_index = summary.index("enabled 1")
        usable_index = summary.index("usable 1")
        fixed_index = summary.index("1 fixed managed")
        variable_index = summary.index("1 variable managed")
        unmanaged_index = summary.index("2 unmanaged backlog")
        self.assertLess(managed_index, enabled_index)
        self.assertLess(enabled_index, usable_index)
        self.assertLess(usable_index, fixed_index)
        self.assertLess(fixed_index, variable_index)
        self.assertLess(variable_index, unmanaged_index)
        self.assertIn("review Relay", summary)
        self.assertIn("ready EV", summary)

    def test_command_center_summary_uses_aggregate_active_load_when_runtime_rows_are_missing(self) -> None:
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
            reason="Holding near target.",
            control_reason="Active load already holding export near target.",
            control_summary="One managed load is already active.",
            export_error_w=25.0,
            active_controlled_power_w=1800.0,
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            controllable_nominal_power_w=1800.0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
        )
        coordinator = SimpleNamespace(data=state, entry=entry)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("active load 1800", summary["fleet_activity_summary"])
        self.assertIn("1 active managed device", summary["fleet_activity_summary"])
        self.assertEqual(
            summary["device_status"],
            "1 managed; active load 1800 W; 1 active managed device; no unmanaged candidates",
        )

    def test_command_center_summary_preserves_control_metrics_when_reason_text_is_long(self) -> None:
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
            reason="Monitoring export drift before acting.",
            control_reason=" ".join(["Waiting for the long-running device guard and export hysteresis review."] * 8),
            control_summary=" ".join(["Managed fleet outcome remains queued while runtime notes continue to stream."] * 8),
            export_error_w=350.0,
            planned_action_count=2,
            executable_action_count=1,
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

        self.assertIn("mode monitoring", summary["control_decision_summary"])
        self.assertIn("target", summary["control_decision_summary"])
        self.assertIn("error 350.0 W", summary["control_decision_summary"])
        self.assertIn("Waiting for the long-running device guard", summary["control_decision_summary"])
        self.assertIn("...", summary["control_decision_summary"])
        self.assertNotEqual(summary["control_decision_summary"], "mode monitoring")
        self.assertTrue(summary["control_outcome_summary"].startswith("planned actions 2 | ready actions 1 | active load 1200.0 W"))
        self.assertIn("active load 1200.0 W", summary["control_outcome_summary"])
        self.assertIn("Managed fleet outcome remains queued", summary["control_outcome_summary"])
        self.assertIn("...", summary["control_outcome_summary"])
        self.assertNotEqual(
            summary["control_outcome_summary"],
            "runtime pending | control outcome waiting",
        )
        self.assertLessEqual(len(summary["control_decision_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertLessEqual(len(summary["control_outcome_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)

    def test_command_center_summary_compacts_energy_board_instead_of_falling_back_when_values_are_long(self) -> None:
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

        huge = Decimal("1234567890.123456789012345678901234567890123456789")
        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            reason="Monitoring export drift before acting.",
            control_reason="Holding current load.",
            control_summary="No fleet change needed.",
            solar_power_w=huge,
            grid_import_power_w=huge,
            grid_export_power_w=huge,
            home_load_power_w=huge,
            battery_soc=Decimal("82.1234567890123456789"),
            battery_charge_power_w=huge,
            battery_discharge_power_w=huge,
            export_error_w=350.0,
            planned_action_count=0,
            executable_action_count=0,
            active_controlled_power_w=0.0,
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

        self.assertNotEqual(summary["energy_state_summary"], "runtime pending | energy state waiting")
        self.assertIn("solar ", summary["energy_state_summary"])
        self.assertIn("grid import ", summary["energy_state_summary"])
        self.assertIn("grid export ", summary["energy_state_summary"])
        self.assertIn("home load ", summary["energy_state_summary"])
        self.assertIn("battery ", summary["energy_state_summary"])
        self.assertLessEqual(len(summary["energy_state_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)

    def test_command_center_summary_uses_compact_runtime_pending_board_signals_before_first_runtime_load(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "setup_incomplete",
            "summary": "Runtime has not reported yet.",
            "next_step": "Open Configure and finish source mapping.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "None"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "None"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources pending"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.SOURCES_SECTION_LABEL,
        }
        native_support.REQUIRED_SOURCE_KEYS = []
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Managed Devices ready."
        native_support.build_source_mapping_summary = lambda merged: "No source mapping yet"
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        entry = SimpleNamespace(data={}, options={})
        coordinator = SimpleNamespace(data=None, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(summary["energy_state_summary"], "runtime pending | energy state waiting")
        self.assertEqual(summary["source_status"], "runtime pending | source health waiting")
        self.assertEqual(summary["control_outcome_summary"], "runtime pending | control outcome waiting")
        self.assertIn("managed", summary["fleet_activity_summary"])
        self.assertIn("no unmanaged candidates", summary["fleet_activity_summary"])
        self.assertNotIn("will appear here", summary["energy_state_summary"])
        self.assertNotIn("will appear here", summary["source_status"])
        self.assertNotIn("will appear here", summary["control_outcome_summary"])
        self.assertNotIn("will appear here", native_support.format_fleet_activity_for_operator(""))

    def test_native_path_normalization_expands_bare_configure_source_mapping_handoff(self) -> None:
        native_support = _load_native_support_module()

        normalized = native_support._normalize_native_path_text("Open Configure and finish source mapping.")

        self.assertIn(native_support.SOURCES_CONFIGURE_PATH, normalized)
        self.assertIn("finish required source roles", normalized)
        self.assertNotIn("Open Configure and finish source", normalized)

    def test_native_path_normalization_expands_bare_configure_to_finish_source_handoff(self) -> None:
        native_support = _load_native_support_module()

        normalized = native_support._normalize_native_path_text("Open Configure to finish source mapping.")

        self.assertIn(native_support.SOURCES_CONFIGURE_PATH, normalized)
        self.assertIn("to finish required source roles", normalized)
        self.assertNotIn("Open Configure to finish source", normalized)

    def test_native_path_normalization_expands_open_source_mapping_step_handoff(self) -> None:
        native_support = _load_native_support_module()

        normalized = native_support._normalize_native_path_text(
            "Open the source mapping step before enabling control."
        )

        self.assertEqual(
            normalized,
            f"Open {native_support.SOURCES_CONFIGURE_PATH} before enabling control.",
        )
        self.assertNotIn("source mapping step", normalized)
        self.assertNotIn("source roles step", normalized)

        plural_normalized = native_support._normalize_native_path_text(
            "Open source mappings step before enabling control."
        )

        self.assertEqual(
            plural_normalized,
            f"Open {native_support.SOURCES_CONFIGURE_PATH} before enabling control.",
        )
        self.assertNotIn("source mappings step", plural_normalized)
        self.assertNotIn("source roles step", plural_normalized)

    def test_native_path_normalization_expands_bare_section_handoffs(self) -> None:
        native_support = _load_native_support_module()

        normalized = native_support._normalize_native_path_text(
            "Open Sensors and finish the missing source roles. Open Sources to review source health. "
            "Open Managed Devices to review candidates."
        )

        self.assertIn(native_support.SOURCES_CONFIGURE_PATH, normalized)
        self.assertIn(native_support.DEVICES_CONFIGURE_PATH, normalized)
        self.assertNotIn("Open Sensors and", normalized)
        self.assertNotIn("Open Sources to", normalized)
        self.assertNotIn("Open Managed Devices to", normalized)

    def test_native_path_normalization_expands_bare_section_modifier_handoffs(self) -> None:
        native_support = _load_native_support_module()

        normalized = native_support._normalize_native_path_text(
            "Open Sensors first. Open Sources next. Open Controls after that. "
            "Open Managed Devices for review. Open Diagnostics with install evidence."
        )

        self.assertEqual(
            normalized,
            f"Open {native_support.SOURCES_CONFIGURE_PATH} first. "
            f"Open {native_support.SOURCES_CONFIGURE_PATH} next. "
            f"Open {native_support.POLICY_CONFIGURE_PATH} after that. "
            f"Open {native_support.DEVICES_CONFIGURE_PATH} for review. "
            f"Open {native_support.SUPPORT_CONFIGURE_PATH} with install evidence.",
        )
        self.assertNotIn("Open Sensors first", normalized)
        self.assertNotIn("Open Sources next", normalized)
        self.assertNotIn("Open Controls after", normalized)
        self.assertNotIn("Open Managed Devices for", normalized)
        self.assertNotIn("Open Diagnostics with", normalized)

    def test_native_path_normalization_expands_arrow_configure_handoffs(self) -> None:
        native_support = _load_native_support_module()

        normalized = native_support._normalize_native_path_text(
            "Open Configure -> Sensors. Open Configure -> Controls. "
            "Open Configure -> Managed Devices. Open Configure -> Diagnostics."
        )

        self.assertEqual(
            normalized,
            f"Open {native_support.SOURCES_CONFIGURE_PATH}. "
            f"Open {native_support.POLICY_CONFIGURE_PATH}. "
            f"Open {native_support.DEVICES_CONFIGURE_PATH}. "
            f"Open {native_support.SUPPORT_CONFIGURE_PATH}.",
        )
        self.assertNotIn("Open Configure ->", normalized)

    def test_native_path_normalization_expands_unicode_arrow_configure_handoffs(self) -> None:
        native_support = _load_native_support_module()

        normalized = native_support._normalize_native_path_text(
            "Open Configure → Sensors. Open Configure → Controls. "
            "Open Configure → Managed Devices. Open Configure → Diagnostics."
        )

        self.assertEqual(
            normalized,
            f"Open {native_support.SOURCES_CONFIGURE_PATH}. "
            f"Open {native_support.POLICY_CONFIGURE_PATH}. "
            f"Open {native_support.DEVICES_CONFIGURE_PATH}. "
            f"Open {native_support.SUPPORT_CONFIGURE_PATH}.",
        )
        self.assertNotIn("Open Configure →", normalized)

    def test_native_path_normalization_expands_bare_configure_bucket_handoffs(self) -> None:
        native_support = _load_native_support_module()

        normalized = native_support._normalize_native_path_text(
            "Path: Configure > Sensors. Next: Configure -> Managed Devices. "
            "Then Configure → Controls and Configure > Diagnostics."
        )

        self.assertEqual(
            normalized,
            f"Path: {native_support.SOURCES_CONFIGURE_PATH}. "
            f"Next: {native_support.DEVICES_CONFIGURE_PATH}. "
            f"Then {native_support.POLICY_CONFIGURE_PATH} and {native_support.SUPPORT_CONFIGURE_PATH}.",
        )
        self.assertNotIn("Path: Configure >", normalized)
        self.assertNotIn("Next: Configure ->", normalized)
        self.assertNotIn("Then Configure →", normalized)

    def test_native_path_normalization_preserves_expanded_unicode_arrow_paths(self) -> None:
        native_support = _load_native_support_module()

        already_expanded = (
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure → Sensors; "
            "then Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure → Managed Devices."
        )

        normalized = native_support._normalize_native_path_text(already_expanded)

        self.assertEqual(normalized, already_expanded)
        self.assertEqual(normalized.count("Settings -> Devices & Services -> Integrations -> Zero Net Export"), 2)

    def test_native_path_normalization_preserves_expanded_angle_configure_paths(self) -> None:
        native_support = _load_native_support_module()

        already_expanded = (
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure > Sensors; "
            "then Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure > Managed Devices."
        )

        normalized = native_support._normalize_native_path_text(already_expanded)

        self.assertEqual(normalized, already_expanded)
        self.assertEqual(normalized.count("Settings -> Devices & Services -> Integrations -> Zero Net Export"), 2)

    def test_command_center_fleet_activity_grouping_keeps_source_blocker_outside_managed_bucket(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support.format_fleet_activity_for_operator(
            "source blockers active | 1 managed | blocked Pool pump | 2 unmanaged backlog | 1 needs review | review Garage relay"
        )

        self.assertTrue(summary.startswith("source blockers active; Managed devices: 1 managed"))
        self.assertIn("Managed devices: 1 managed | blocked Pool pump", summary)
        self.assertIn("Unmanaged backlog: 2 unmanaged backlog | 1 needs review | review Garage relay", summary)
        self.assertNotIn("Managed devices: source blockers active", summary)

    def test_command_center_fleet_activity_grouping_keeps_source_blocker_outside_unmanaged_bucket(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support.format_fleet_activity_for_operator(
            "1 managed | blocked Pool pump | 2 unmanaged backlog | source blockers active | 1 needs review | review Garage relay"
        )

        self.assertTrue(summary.startswith("source blockers active; Managed devices: 1 managed"))
        self.assertIn("Managed devices: 1 managed | blocked Pool pump", summary)
        self.assertIn("Unmanaged backlog: 2 unmanaged backlog | 1 needs review | review Garage relay", summary)
        self.assertNotIn("Unmanaged backlog: 2 unmanaged backlog | source blockers active", summary)

    def test_command_center_fleet_activity_grouping_recovers_managed_on_top_from_reversed_parts(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support.format_fleet_activity_for_operator(
            "source blockers active | 2 unmanaged backlog | 1 needs review | review Garage relay | 1 managed | enabled 1 | usable 1 | 1 fixed managed"
        )

        self.assertTrue(summary.startswith("source blockers active; Managed devices: 1 managed"))
        self.assertLess(summary.index("Managed devices:"), summary.index("Unmanaged backlog:"))
        self.assertIn("Managed devices: 1 managed | enabled 1 | usable 1 | 1 fixed managed", summary)
        self.assertIn("Unmanaged backlog: 2 unmanaged backlog | 1 needs review | review Garage relay", summary)

    def test_command_center_fleet_activity_grouping_recovers_reversed_managed_actions(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support.format_fleet_activity_for_operator(
            "2 unmanaged backlog | 1 needs review | review Garage relay | "
            "1 managed | 1 managed device needs attention | blocked Pool pump | "
            "active load 900 W | 1 active managed device"
        )

        self.assertLess(summary.index("Managed devices:"), summary.index("Unmanaged backlog:"))
        self.assertIn(
            "Managed devices: 1 managed | 1 managed device needs attention | blocked Pool pump | active load 900 W | 1 active managed device",
            summary,
        )
        self.assertIn("Unmanaged backlog: 2 unmanaged backlog | 1 needs review | review Garage relay", summary)
        self.assertNotIn(
            "Unmanaged backlog: 2 unmanaged backlog | 1 needs review | review Garage relay | blocked Pool pump",
            summary,
        )

    def test_fleet_activity_fallback_normalizes_comma_separated_managed_unmanaged_counts(self) -> None:
        native_support = _load_native_support_module()

        fallback = native_support._fleet_activity_fallback_from_device_status(
            "Managed Devices: 2 managed, 2 unmanaged backlog; source blockers active"
        )
        summary = native_support.format_fleet_activity_for_operator(fallback)

        self.assertEqual(
            fallback,
            "2 managed | 2 unmanaged backlog | source blockers active",
        )
        self.assertTrue(summary.startswith("source blockers active; Managed devices: 2 managed"))
        self.assertIn("Unmanaged backlog: 2 unmanaged backlog", summary)
        self.assertNotIn("2 managed, 2 unmanaged backlog", summary)

    def test_fleet_activity_fallback_normalizes_device_candidate_count_labels(self) -> None:
        native_support = _load_native_support_module()

        fallback = native_support._fleet_activity_fallback_from_device_status(
            "Managed Devices: 2 managed devices, 1 unmanaged candidate, review Garage relay"
        )
        summary = native_support.format_fleet_activity_for_operator(fallback)

        self.assertEqual(
            fallback,
            "2 managed | 1 unmanaged backlog | review Garage relay",
        )
        self.assertEqual(
            summary,
            "Managed devices: 2 managed; Unmanaged backlog: 1 unmanaged backlog | review Garage relay",
        )
        self.assertNotIn("2 managed devices", summary)
        self.assertNotIn("1 unmanaged candidate", summary)

    def test_command_center_fleet_activity_infers_managed_count_from_kind_inventory(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support.format_fleet_activity_for_operator(
            "enabled 2 | usable 2 | 1 fixed managed | 1 variable managed | "
            "2 unmanaged backlog | 1 needs review | review Garage relay"
        )

        self.assertEqual(
            summary,
            "Managed devices: 2 managed | enabled 2 | usable 2 | 1 fixed managed | 1 variable managed; "
            "Unmanaged backlog: 2 unmanaged backlog | 1 needs review | review Garage relay",
        )
        self.assertNotIn("Managed devices: 1 fixed managed", summary)

    def test_command_center_fleet_activity_recovers_reversed_kind_inventory_without_count(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support.format_fleet_activity_for_operator(
            "2 unmanaged backlog | review Garage relay | 1 fixed managed | 1 variable managed"
        )

        self.assertEqual(
            summary,
            "Managed devices: 2 managed | 1 fixed managed | 1 variable managed; "
            "Unmanaged backlog: 2 unmanaged backlog | review Garage relay",
        )
        self.assertLess(summary.index("Managed devices:"), summary.index("Unmanaged backlog:"))

    def test_command_center_fleet_activity_groups_managed_actions_without_count(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support.format_fleet_activity_for_operator(
            "active load 900 W | 1 active managed device | 2 unmanaged backlog | review Garage relay"
        )

        self.assertEqual(
            summary,
            "Managed devices: active load 900 W | 1 active managed device; "
            "Unmanaged backlog: 2 unmanaged backlog | review Garage relay",
        )

    def test_command_center_fleet_activity_recovers_reversed_managed_actions_without_count(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support.format_fleet_activity_for_operator(
            "2 unmanaged backlog | review Garage relay | active load 900 W | 1 active managed device"
        )

        self.assertEqual(
            summary,
            "Managed devices: active load 900 W | 1 active managed device; "
            "Unmanaged backlog: 2 unmanaged backlog | review Garage relay",
        )
        self.assertLess(summary.index("Managed devices:"), summary.index("Unmanaged backlog:"))

    def test_raw_fleet_activity_keeps_source_blocker_global_for_empty_managed_fleet(self) -> None:
        native_support = _load_native_support_module()

        state = SimpleNamespace(
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            device_details={},
        )

        summary = native_support._build_command_center_fleet_activity_summary(
            state,
            candidate_count=2,
            fixed_candidate_count=1,
            variable_candidate_count=1,
            review_needed_count=1,
            fixed_review_count=1,
            variable_review_count=0,
            review_candidate_name="Garage relay",
            review_candidate_preview="Garage relay (fixed)",
            ready_candidate_name="EV charger",
            ready_candidate_preview="EV charger (variable)",
            top_candidate_name="Garage relay",
            top_candidate_preview="Garage relay (fixed)",
            source_blocked=True,
        )

        self.assertTrue(summary.startswith("source blockers active | no managed yet | 2 unmanaged backlog"))
        self.assertLess(
            summary.index("source blockers active"),
            summary.index("no managed yet"),
        )
        self.assertLess(
            summary.index("source blockers active"),
            summary.index("2 unmanaged backlog"),
        )

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
            summary["fleet_activity_summary"].index("1 needs review"),
        )
        self.assertLess(
            summary["fleet_activity_summary"].index("1 needs review"),
            summary["fleet_activity_summary"].index("review AC Outlet 2 (fixed) | review first | warn generic outlet label"),
        )
        self.assertIn("1 managed device needs attention", summary["fleet_activity_summary"])
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

    def test_command_center_summary_normalizes_empty_configured_status_with_unmanaged_backlog(self) -> None:
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
            device_status_summary="0 configured devices available",
            device_count=0,
            enabled_device_count=0,
            usable_device_count=0,
            fixed_device_count=0,
            controllable_nominal_power_w=0.0,
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

        self.assertIn("no managed yet", summary["fleet_activity_summary"])
        self.assertIn("1 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertIn("no managed yet", summary["device_status"])
        self.assertIn("1 unmanaged backlog", summary["device_status"])
        self.assertNotIn("0 configured devices available", summary["fleet_activity_summary"])
        self.assertNotIn("0 configured devices available", summary["device_status"])

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
        self.assertIn("review Garage", summary["fleet_activity_summary"])
        self.assertIn("(fixed)", summary["fleet_activity_summary"])
        self.assertIn("ready Pool", summary["fleet_activity_summary"])

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
        self.assertIn("review Garage", summary["fleet_activity_summary"])
        self.assertIn("(fixed)", summary["fleet_activity_summary"])
        self.assertIn("ready EV", summary["fleet_activity_summary"])
        self.assertIn("(variable)", summary["fleet_activity_summary"])

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
        self.assertIn("review Garage", summary["fleet_activity_summary"])
        self.assertIn("(fixed)", summary["fleet_activity_summary"])
        self.assertIn("ready EV", summary["fleet_activity_summary"])
        self.assertIn("(variable)", summary["fleet_activity_summary"])
        self.assertNotIn("6 fixed candidates", summary["fleet_activity_summary"])
        self.assertNotIn("6 variable candidates", summary["fleet_activity_summary"])
        self.assertNotIn("fixed backlog", summary["fleet_activity_summary"])
        self.assertNotIn("variable backlog", summary["fleet_activity_summary"])
        self.assertNotIn("planned action(s)", summary["fleet_activity_summary"])

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
        self.assertIn("review Virtual", summary["device_status"])
        self.assertIn("(fixed)", summary["device_status"])
        self.assertIn("ready EV charger", summary["device_status"])
        self.assertIn("(variable)", summary["device_status"])

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

    def test_device_status_helper_keeps_attention_first_focus_under_compaction(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support._command_center_device_status_with_unmanaged_context(
            "2 configured devices available",
            managed_count=2,
            candidate_count=2,
            fixed_candidate_count=1,
            variable_candidate_count=1,
            review_needed_count=1,
            fixed_review_count=1,
            variable_review_count=0,
            top_candidate_name="Review Candidate Alpha",
            top_candidate_preview="Review Candidate Alpha (fixed) | review first | warn helper-backed load needs review and validation",
            review_candidate_name="Review Candidate Alpha",
            review_candidate_preview="Review Candidate Alpha (fixed) | review first | warn helper-backed load needs review and validation",
            ready_candidate_name="Ready Candidate Beta",
            ready_candidate_preview="Ready Candidate Beta (variable) | likely useful | warm-floor preload absorber near main hallway",
            managed_attention_count=1,
            blocked_activity_count=1,
            active_managed_count=1,
            active_managed_power_w=920.0,
            attention_device_preview="Pool pump blocker (fixed | blocked)",
            blocked_device_preview="Pool pump blocker (fixed | blocked)",
            planned_device_preview="Heated floor (variable | target 920 W | action turn_on)",
            active_device_preview="Heated floor (variable | active 920 W)",
        )

        self.assertIn("attention first", summary)
        self.assertIn("blocked Po", summary)
        self.assertIn("plan H", summary)
        self.assertIn("active device Hea", summary)
        self.assertIn("2 unmanaged backlog", summary)
        self.assertIn("1 ready to promote", summary)
        self.assertLessEqual(len(summary), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)

    def test_device_status_helper_does_not_repeat_existing_unmanaged_or_source_blocker_story(self) -> None:
        native_support = _load_native_support_module()

        summary = native_support._command_center_device_status_with_unmanaged_context(
            "Managed Devices: 2 managed, 2 unmanaged backlog; source blockers active",
            managed_count=2,
            candidate_count=2,
            fixed_candidate_count=1,
            variable_candidate_count=1,
            review_needed_count=1,
            fixed_review_count=1,
            variable_review_count=0,
            top_candidate_name="Review Candidate Alpha",
            top_candidate_preview="Review Candidate Alpha (fixed) | review first | warn helper-backed load needs review and validation",
            review_candidate_name="Review Candidate Alpha",
            review_candidate_preview="Review Candidate Alpha (fixed) | review first | warn helper-backed load needs review and validation",
            ready_candidate_name="Ready Candidate Beta",
            ready_candidate_preview="Ready Candidate Beta (variable) | likely useful | warm-floor preload absorber near main hallway",
            source_blocked=True,
        )

        self.assertEqual(summary.count("unmanaged"), 1)
        self.assertEqual(summary.count("source blockers active"), 1)
        self.assertIn("review Review Candidate", summary)
        self.assertIn("ready Ready Candidate", summary)
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

        self.assertIn("1 configured, with 1 issue to repair", summary["device_status"])
        self.assertIn("2 unmanaged backlog", summary["device_status"])
        self.assertIn("source blockers active", summary["device_status"])
        self.assertNotIn("| 2 unmanaged |", f"| {summary['device_status']} |")
        self.assertIn("1 needs review", summary["device_status"])
        self.assertIn("1 ready to promote", summary["device_status"])
        self.assertIn("review Garage Power", summary["device_status"])
        self.assertIn("ready Dishwasher Power", summary["device_status"])
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

    def test_fleet_activity_uses_configured_managed_count_when_runtime_state_is_absent(self) -> None:
        native_support = _load_native_support_module()
        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime not loaded yet.",
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
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support.parse_device_configs = lambda raw: (
            [
                SimpleNamespace(
                    key="pool_pump",
                    name="Pool Pump",
                    kind="fixed",
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
                ),
                SimpleNamespace(
                    key="heated_floor",
                    name="Heated Floor",
                    kind="variable",
                    entity_id="number.heated_floor",
                    adapter="number",
                    nominal_power_w=2000,
                    min_power_w=400,
                    max_power_w=2000,
                    step_w=100,
                    priority=200,
                    enabled=True,
                    min_on_seconds=0,
                    min_off_seconds=0,
                    cooldown_seconds=0,
                    max_active_seconds=0,
                ),
            ],
            [],
        )
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {"name": "Garage outlet", "entity_id": "switch.garage_outlet", "kind": "fixed"},
                {"name": "EV charger", "entity_id": "number.ev_charger", "kind": "variable"},
            ],
            "Garage outlet",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "medium" if candidate.get("name") == "Garage outlet" else "high",
            "warnings": ["Generic outlet label"] if candidate.get("name") == "Garage outlet" else [],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage outlet (fixed) | review first | warn Generic outlet label"
            if candidate and candidate.get("name") == "Garage outlet"
            else "EV charger (variable) | likely useful"
        )

        entry = SimpleNamespace(data={native_support.CONF_DEVICE_INVENTORY_JSON: "[]"}, options={})
        coordinator = SimpleNamespace(data=None, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("2 managed", summary["fleet_activity_summary"])
        self.assertIn("2 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertNotIn("no managed yet", summary["fleet_activity_summary"])

    def test_fleet_activity_uses_configured_managed_count_when_runtime_count_is_missing(self) -> None:
        native_support = _load_native_support_module()
        state = SimpleNamespace(
            enabled_device_count=0,
            usable_device_count=0,
            device_details={},
        )

        summary = native_support._build_command_center_fleet_activity_summary(
            state,
            candidate_count=0,
            fixed_candidate_count=0,
            variable_candidate_count=0,
            review_needed_count=0,
            fixed_review_count=0,
            variable_review_count=0,
            review_candidate_name="",
            review_candidate_preview="",
            ready_candidate_name="",
            ready_candidate_preview="",
            top_candidate_name="",
            top_candidate_preview="",
            source_blocked=False,
            configured_managed_count=2,
        )

        self.assertIn("2 managed", summary)
        self.assertIn("no unmanaged candidates", summary)
        self.assertNotIn("no managed yet", summary)

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
            "next_step": "Repair the source blockers first.",
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
                "source blockers active | no managed yet | 1 unmanaged backlog | 1 fixed candidate | fixed backlog 1 review | 1 needs review | 1 fixed review | review AC Outlet 2"
            )
        )

    def test_command_center_summary_keeps_source_repair_note_outside_managed_unmanaged_split(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Repair the source blockers first.",
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
            summary["fleet_activity_summary"].index("source blockers active"),
            summary["fleet_activity_summary"].index("attention first Pool pump"),
        )
        self.assertLess(
            summary["fleet_activity_summary"].index("source blockers active"),
            summary["fleet_activity_summary"].index("1 unmanaged backlog"),
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
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices to continue in the Managed Devices workspace, review unmanaged candidate: AC Outlet 2 (fixed) | review first",
            summary["next_action_summary"],
        )
        self.assertIn(
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices to continue in the Managed Devices workspace, review unmanaged candidate: AC Outlet 2 (fixed) | review first",
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
            "to continue in the Managed Devices workspace, then add the first fixed or variable load manually because no surfaced unmanaged candidate is available."
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
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices to continue in the Managed Devices workspace, review unmanaged candidate: Virtual load, then promote ready unmanaged candidate: Dishwasher Power.",
            summary["next_action_summary"],
        )
        self.assertIn(
            "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices to continue in the Managed Devices workspace, review unmanaged candidate: Virtual load (fixed)",
            summary["device_next_step"],
        )
        self.assertIn(
            "then promote ready unmanaged candidate: Dishwasher Power (fixed) | likely useful",
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

    def test_command_center_summary_keeps_attention_focus_context_for_blocked_device(self) -> None:
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
            usable_device_count=1,
            blocked_planned_action_count=1,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "last_action_status": "failed to start",
                },
                "ev": {
                    "name": "EV charger",
                    "entity_id": "number.ev_charger_limit",
                    "kind": "variable",
                    "usable": True,
                    "planned_action": "hold",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn(
            "attention first Pool pump (fixed | not usable | action turn_on | last failed to start)",
            summary["fleet_activity_summary"],
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
            "attention first Pool pump (fixed | blocked | action turn_on)",
            summary["fleet_activity_summary"],
        )
        self.assertIn(
            "blocked Pool pump (fixed | blocked | action turn_on)",
            summary["fleet_activity_summary"],
        )

    def test_command_center_summary_prefers_distinct_blocked_device_focus_when_attention_already_names_first_device(self) -> None:
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
                    "name": "Water heater",
                    "entity_id": "switch.water_heater",
                    "kind": "fixed",
                    "usable": True,
                    "planned_action": "turn_off",
                    "action_executable": False,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn(
            "attention first Pool pump (fixed | blocked | action turn_on)",
            summary["fleet_activity_summary"],
        )
        self.assertIn("2 blocked managed actions", summary["fleet_activity_summary"])
        self.assertIn("blocked Water heater (fixed | blocked | action turn_off)", summary["fleet_activity_summary"])
        self.assertNotIn("blocked Pool pump (fixed | blocked | action turn_on)", summary["fleet_activity_summary"])
        self.assertIn("2 blocked managed actions", summary["device_status"])

    def test_command_center_summary_top_alert_names_blocked_count_and_first_device(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and confirm the blocked actions.",
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
            device_status_summary="Managed Devices: blocked Pool pump (fixed | blocked | action turn_on)",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=2,
            blocked_planned_action_count=2,
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
                    "name": "Water heater",
                    "entity_id": "switch.water_heater",
                    "kind": "fixed",
                    "usable": True,
                    "planned_action": "turn_off",
                    "action_executable": False,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn(
            "Managed Devices: 2 blocked managed actions, starting with Pool pump (fixed | action turn_on)",
            summary["alert_summary"],
        )

    def test_command_center_summary_top_alert_keeps_attention_count_with_first_device(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and confirm the attention items.",
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
            device_status_summary="Managed Devices: 2 managed devices need attention",
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
                    "planned_action": "hold",
                    "last_action_status": "failed",
                },
                "heater": {
                    "name": "Water heater",
                    "entity_id": "switch.water_heater",
                    "kind": "fixed",
                    "usable": True,
                    "planned_action": "hold",
                    "last_action_status": "timeout",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn(
            "Managed Devices: 2 managed devices need attention, attention first Pool pump (fixed | last failed)",
            summary["alert_summary"],
        )

    def test_command_center_summary_top_alert_names_single_attention_device_explicitly(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and confirm the attention item.",
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
            device_status_summary="Managed Devices: 1 managed device needs attention",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            blocked_planned_action_count=0,
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

        self.assertIn(
            "Managed Devices: attention first Pool pump (fixed | last failed)",
            summary["alert_summary"],
        )

    def test_command_center_summary_keeps_attention_count_when_only_generic_blocked_count_is_available(self) -> None:
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
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            blocked_planned_action_count=1,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "planned_action": "hold",
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("1 managed device needs attention", summary["fleet_activity_summary"])
        self.assertIn("1 blocked managed action", summary["fleet_activity_summary"])
        self.assertIn("1 managed device needs attention", summary["device_status"])
        self.assertIn("1 blocked managed action", summary["device_status"])

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

    def test_command_center_summary_keeps_active_cue_when_attention_first_device_overflows(self) -> None:
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
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Review Candidate Alpha with a deliberately long label near the garage side board and utility room",
                    "entity_id": "switch.review_candidate_alpha",
                    "kind": "fixed",
                },
                {
                    "name": "Ready Candidate Beta with a deliberately long label near the garage side board and utility room",
                    "entity_id": "switch.ready_candidate_beta",
                    "kind": "fixed",
                },
            ],
            "Review Candidate Alpha with a deliberately long label near the garage side board and utility room",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "medium" if "Review" in candidate.get("name", "") else "high",
            "warnings": ["helper-backed load needs review"] if "Review" in candidate.get("name", "") else [],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Review Candidate Alpha with a deliberately long label near the garage side board and utility room (fixed) | review first | warn helper-backed load needs review"
            if "Review" in candidate.get("name", "")
            else "Ready Candidate Beta with a deliberately long label near the garage side board and utility room (fixed) | likely useful | key warning: No immediate warnings"
        )

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
                    "name": "Pool pump with a spectacularly verbose blocked-and-active label near the patio side walkway and west fence line",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "action_executable": False,
                    "observed_active": True,
                },
                "heater": {
                    "name": "Heated floor controller with a shorter idle label",
                    "entity_id": "switch.heated_floor_controller",
                    "kind": "fixed",
                    "usable": True,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("attention first", summary["fleet_activity_summary"])
        self.assertIn("active", summary["fleet_activity_summary"])
        self.assertIn("review ", summary["fleet_activity_summary"])
        self.assertIn("ready ", summary["fleet_activity_summary"])

    def test_command_center_summary_keeps_distinct_active_device_when_blocked_attention_overflows(self) -> None:
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
        native_support.REQUIRED_SOURCE_KEYS = []
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage auxiliary outlet backlog candidate with a very long review-first descriptor for overflow coverage",
                    "entity_id": "switch.review_candidate_alpha",
                    "kind": "fixed",
                },
                {
                    "name": "EV charger export absorption candidate with a very long ready-next descriptor for overflow coverage",
                    "entity_id": "number.ready_candidate_beta",
                    "kind": "variable",
                },
            ],
            "Garage auxiliary outlet backlog candidate with a very long review-first descriptor for overflow coverage",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "medium" if candidate.get("entity_id") == "switch.review_candidate_alpha" else "high",
            "warnings": ["helper-backed load needs review"]
            if candidate.get("entity_id") == "switch.review_candidate_alpha"
            else [],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage auxiliary outlet backlog candidate with a very long review-first descriptor for overflow coverage (fixed) | review first | warn helper-backed load needs review"
            if candidate.get("entity_id") == "switch.review_candidate_alpha"
            else "EV charger export absorption candidate with a very long ready-next descriptor for overflow coverage (variable) | likely useful | key warning: No immediate warnings"
        )

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
            active_controlled_power_w=3000,
            device_details={
                "pool": {
                    "name": "Pool Pump Alpha with a blocked-and-active label that stays long enough to force overflow",
                    "entity_id": "switch.pool_pump_alpha",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "action_executable": False,
                    "last_action_status": "guard waiting",
                    "observed_active": True,
                    "current_power_w": 1200,
                },
                "heater": {
                    "name": "Heated floor west wing zone controller",
                    "entity_id": "number.heated_floor_limit",
                    "kind": "variable",
                    "usable": True,
                    "planned_action": "hold",
                    "observed_active": True,
                    "current_power_w": 1800,
                    "current_target_power_w": 1800,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("blocked Pool Pump", summary["fleet_activity_summary"])
        self.assertIn("review ", summary["fleet_activity_summary"])
        self.assertIn("ready ", summary["fleet_activity_summary"])
        self.assertIn("active device Heated floor", summary["fleet_activity_summary"])

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
        self.assertNotIn(
            "plan Pool pump (fixed | active 1185 W | action turn_on)",
            summary["fleet_activity_summary"],
        )
        self.assertIn(
            "active device Heated floor (variable | active 920 W)",
            summary["fleet_activity_summary"],
        )

    def test_command_center_summary_keeps_distinct_planned_device_when_attention_already_names_first_planned_device(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the managed fleet and confirm the next planned action.",
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
            device_status_summary="3 configured devices available",
            device_count=3,
            enabled_device_count=3,
            usable_device_count=3,
            active_controlled_power_w=920,
            device_details={
                "pool": {
                    "name": "Pool",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "priority": 10,
                    "observed_active": False,
                    "planned_action": "turn_on",
                },
                "heater": {
                    "name": "Heater",
                    "entity_id": "switch.water_heater",
                    "kind": "fixed",
                    "usable": True,
                    "priority": 20,
                    "observed_active": False,
                    "planned_action": "turn_off",
                },
                "floor": {
                    "name": "EV",
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

        self.assertIn("attention first Pool (fixed | action turn_on)", summary["fleet_activity_summary"])
        self.assertIn("plan Heater (fixed | action turn_off)", summary["fleet_activity_summary"])
        self.assertNotIn("plan Pool (fixed | action turn_on)", summary["fleet_activity_summary"])
        self.assertIn("active device EV (variable | active 920 W)", summary["fleet_activity_summary"])

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
        self.assertIn("1 active managed device", summary["control_outcome_summary"])
        self.assertNotIn("active load 0", summary["control_outcome_summary"])

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
        self.assertIn("review unmanaged candidate: Virtual load", summary["next_action_summary"])
        self.assertIn("promote ready unmanaged candidate: Dishwasher Power", summary["next_action_summary"])
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
            f"Open {native_support.DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, then edit device settings or stage enablement changes.",
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

        self.assertIn("Source blockers: Grid export power is unavailable", summary["alert_summary"])
        self.assertEqual(summary["source_status"], "Source blockers: Grid export power is unavailable")
        self.assertIn("Repair source blockers in Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Sensors", summary["policy_readiness"])
        self.assertNotIn("Mapped source blockers", summary["source_status"])
        self.assertNotIn("mapped-source blockers", summary["policy_readiness"])
        self.assertIn("Managed-device configuration needs repair for 1 item.", summary["alert_summary"])
        self.assertIn("Runtime health still needs operator attention.", summary["alert_summary"])
        self.assertEqual(
            summary["fleet_activity_summary"],
            "source blockers active | no managed yet | no unmanaged candidates",
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

        self.assertIn("Managed Devices: no managed yet; 2 unmanaged backlog.", summary["alert_summary"])
        self.assertIn("Managed Devices: review first Virtual load (fixed) | review first", summary["alert_summary"])
        self.assertIn("ready next Hot water relay (fixed) | likely useful", summary["alert_summary"])
        self.assertIn("review Virtual load (fixed) | review first", summary["fleet_activity_summary"])
        self.assertIn("ready Hot water relay (fixed) | likely useful", summary["fleet_activity_summary"])

    def test_command_center_summary_compacts_review_ready_alert_targets_before_dropping_backlog_story(self) -> None:
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
                {
                    "name": "Virtual load helper with a spectacularly verbose review-first label in the garage south-west board and utility cupboard for overflow coverage",
                    "entity_id": "input_boolean.virtual_load_helper",
                    "kind": "fixed",
                },
                {
                    "name": "Hot water relay with a remarkably long ready-next descriptor across the laundry branch and patio circuit for overflow coverage",
                    "entity_id": "switch.hot_water_relay",
                    "kind": "fixed",
                },
            ],
            "Virtual load helper with a spectacularly verbose review-first label in the garage south-west board and utility cupboard for overflow coverage",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "medium" if "Virtual load helper" in candidate.get("name", "") else "high",
            "warnings": ["helper-backed load needs review and validation"]
            if "Virtual load helper" in candidate.get("name", "")
            else [],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Virtual load helper with a spectacularly verbose review-first label in the garage south-west board and utility cupboard for overflow coverage (fixed) | review first | warn helper-backed load needs review and validation"
            if candidate and "Virtual load helper" in candidate.get("name", "")
            else "Hot water relay with a remarkably long ready-next descriptor across the laundry branch and patio circuit for overflow coverage (fixed) | likely useful"
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

        self.assertLessEqual(len(summary["alert_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("Managed Devices: no managed yet; 2 unmanaged backlog.", summary["alert_summary"])
        self.assertIn("Managed Devices: review first Virtual load helper", summary["alert_summary"])
        self.assertIn("ready next Hot water relay", summary["alert_summary"])
        self.assertNotIn("utility cupboard for overflow coverage", summary["alert_summary"])
        self.assertNotIn("laundry branch and patio circuit for overflow coverage", summary["alert_summary"])

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

        self.assertIn("Managed Devices: no managed yet; 2 unmanaged backlog.", summary["alert_summary"])
        self.assertIn("Managed Devices: ready next Hot water relay (fixed) | likely useful", summary["alert_summary"])
        self.assertIn("2 ready to promote", summary["fleet_activity_summary"])
        self.assertIn("ready Hot water relay (fixed) | likely useful", summary["fleet_activity_summary"])
        self.assertEqual(
            (
                "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices "
                "to continue in the Managed Devices workspace, then promote ready unmanaged candidate: Hot water relay (fixed) | likely useful"
            ),
            summary["device_next_step"],
        )
        self.assertEqual(
            (
                "Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Managed Devices "
                "to continue in the Managed Devices workspace, then promote ready unmanaged candidate: Hot water relay (fixed) | likely useful"
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
        self.assertIn("source blockers active", summary["alert_summary"])
        self.assertIn("Managed Devices: no managed yet; 2 unmanaged backlog.", summary["alert_summary"])
        self.assertIn("review first Virtual load helper", summary["alert_summary"])
        self.assertIn("ready next Hot water relay", summary["alert_summary"])
        self.assertNotIn("Installed package needs exact-build revalidation", summary["alert_summary"])
        self.assertLessEqual(len(summary["alert_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)

    def test_command_center_summary_uses_source_blocker_signal_for_missing_required_sources_under_alert_overflow(self) -> None:
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
                {
                    "name": "Virtual load helper with a very long review-first label for the garage overflow path",
                    "entity_id": "input_boolean.virtual_load_helper_with_a_very_long_review_first_label_for_the_garage_overflow_path",
                    "kind": "fixed",
                },
                {
                    "name": "Hot water relay with a very long ready-next label for the patio overflow path",
                    "entity_id": "switch.hot_water_relay_with_a_very_long_ready_next_label_for_the_patio_overflow_path",
                    "kind": "fixed",
                },
            ],
            "Virtual load helper with a very long review-first label for the garage overflow path",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "low" if "Virtual load" in candidate.get("name", "") else "high",
            "warnings": ["helper-backed load needs review"] if "Virtual load" in candidate.get("name", "") else [],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Virtual load helper with a very long review-first label for the garage overflow path (fixed) | review first | warn helper-backed load needs review"
            if candidate and "Virtual load" in candidate.get("name", "")
            else "Hot water relay with a very long ready-next label for the patio overflow path (fixed) | likely useful | warn generic outlet label"
        )

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="Managed Devices: 3 managed devices need attention",
            device_count=3,
            enabled_device_count=3,
            usable_device_count=2,
            blocked_planned_action_count=0,
            device_details={
                "pool_pump": {
                    "name": "Pool pump west pergola circulation relay with a deliberately long managed attention label near the patio side walkway",
                    "entity_id": "switch.pool_pump_west_pergola_circulation_relay_with_a_deliberately_long_managed_attention_label_near_the_patio_side_walkway",
                    "kind": "fixed",
                    "planned_action": "turn_on",
                    "last_action_status": "failed to start during export trim",
                },
                "heated_floor": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor",
                    "kind": "variable",
                    "usable": True,
                },
                "ev_charger": {
                    "name": "EV charger",
                    "entity_id": "number.ev_charger",
                    "kind": "variable",
                    "usable": True,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["alert_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("source blockers active", summary["alert_summary"])
        self.assertNotIn("Missing required source roles:", summary["alert_summary"])
        self.assertIn("attention first Pool pump", summary["alert_summary"])

    def test_command_center_summary_keeps_compact_managed_attention_alert_under_overflow(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "runtime_readiness",
            "summary": "Runtime health still needs operator attention because one very long explanatory sentence keeps expanding the alert strip beyond the Home Assistant state budget.",
            "next_step": "Review the next unmanaged candidate.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [],
            "stale_source_keys": ["grid_export_power", "home_load_power"],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: (
            "Grid export power is stale, home load telemetry still needs confirmation, and source freshness should be repaired before trusting the next controller decision."
        )
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "Grid export power, home load power"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Sources need attention"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.DEVICES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support.REQUIRED_SOURCE_KEYS = []
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage candidate 02",
                    "entity_id": "switch.garage_candidate_02",
                    "kind": "fixed",
                },
                {
                    "name": "Hot water relay",
                    "entity_id": "switch.hot_water_relay",
                    "kind": "fixed",
                },
            ],
            "Garage candidate 02",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "low" if "Garage candidate" in candidate.get("name", "") else "high",
            "warnings": ["helper-backed load needs review"] if "Garage candidate" in candidate.get("name", "") else [],
        }
        native_support.candidate_needs_review = lambda fit: fit.get("confidence") != "high"
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage candidate 02 (fixed) | review first | warn helper-backed load needs review"
            if candidate and "Garage candidate" in candidate.get("name", "")
            else "Hot water relay (fixed) | likely useful"
        )

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary="Managed Devices: 3 managed devices need attention",
            device_count=3,
            enabled_device_count=3,
            usable_device_count=2,
            blocked_planned_action_count=0,
            device_details={
                "pool_pump": {
                    "name": "Pool pump west pergola circulation relay with a deliberately long managed attention label near the patio side walkway",
                    "entity_id": "switch.pool_pump_west_pergola_circulation_relay_with_a_deliberately_long_managed_attention_label_near_the_patio_side_walkway",
                    "kind": "fixed",
                    "planned_action": "turn_on",
                    "current_power_w": 1185.0,
                    "last_action_status": "failed to start during export trim",
                },
                "heated_floor": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor",
                    "kind": "variable",
                    "usable": True,
                },
                "ev_charger": {
                    "name": "EV charger",
                    "entity_id": "number.ev_charger",
                    "kind": "variable",
                    "usable": True,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["alert_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("source blockers active", summary["alert_summary"])
        self.assertIn("attention first Pool pump", summary["alert_summary"])
        self.assertIn("action turn_on", summary["alert_summary"])
        self.assertNotIn("power 1185.0 W", summary["alert_summary"])
        self.assertIn("review first Garage candidate 02", summary["alert_summary"])
        self.assertIn("ready next Hot water relay", summary["alert_summary"])

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
            f"Open {native_support.DEVICES_CONFIGURE_PATH} to continue in the Managed Devices workspace, review unmanaged candidate: AC Outlet 2 (fixed) | review first",
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
            f"Open {native_support.SOURCES_CONFIGURE_PATH} to continue in Sensors and confirm the live source roles and health.",
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

    def test_command_center_summary_clips_long_headline_reason_instead_of_falling_back_generic(self) -> None:
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
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        long_reason = (
            "Controller is holding the current operating posture while the operator-facing headline remains intentionally long "
            "to prove the command-center summary keeps a real decision preview instead of collapsing into a generic unavailable fallback. "
            "This overflow case should still preserve the opening decision story in a clipped native form."
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
            battery_below_reserve=False,
            planned_action_count=0,
            executable_action_count=0,
            blocked_planned_action_count=0,
            active_controlled_power_w=0.0,
            usable_device_count=1,
            target_export_w=0.0,
            deadband_w=50.0,
            grid_export_power_w=None,
            grid_import_power_w=None,
            export_error_w=None,
            reason=long_reason,
            control_reason="",
            status="",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            health_summary="Healthy",
            diagnostic_summary="Healthy",
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["headline_decision"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertTrue(summary["headline_decision"].startswith("Controller is holding the current operating posture"))
        self.assertTrue(summary["headline_decision"].endswith("..."))
        self.assertNotEqual(summary["headline_decision"], "Runtime summary unavailable.")


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

    def test_command_center_summary_hides_inventory_mix_when_unmanaged_backlog_is_present(self) -> None:
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
            device_status_summary="Managed Devices: 2 managed devices need attention, attention first Pool pump (fixed | action turn_on), blocked Pool pump (fixed | blocked), 1 planned action, plan Pool pump (fixed | action turn_on)",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=1,
            fixed_device_count=1,
            variable_device_count=1,
            controllable_nominal_power_w=4200.0,
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
                    "nominal_power_w": 3000.0,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("2 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertIn("fixed backlog 1 review/1 ready", summary["fleet_activity_summary"])
        self.assertIn("review Garage", summary["fleet_activity_summary"])
        self.assertIn("(fixed)", summary["fleet_activity_summary"])
        self.assertIn("ready Pool", summary["fleet_activity_summary"])
        self.assertNotIn("enabled 2", summary["fleet_activity_summary"])
        self.assertNotIn("usable 1", summary["fleet_activity_summary"])
        self.assertNotIn("1 fixed managed", summary["fleet_activity_summary"])
        self.assertNotIn("1 variable managed", summary["fleet_activity_summary"])
        self.assertNotIn("4200 W nominal", summary["fleet_activity_summary"])

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
            device_status_summary="Managed Devices: 2 managed devices need attention, attention first Pool pump (fixed | action turn_on), blocked Pool pump (fixed | blocked), 1 planned action, plan Pool pump (fixed | action turn_on)",
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
        self.assertIn("review Garage", summary["fleet_activity_summary"])
        self.assertIn("(fixed)", summary["fleet_activity_summary"])
        self.assertIn("ready Pool", summary["fleet_activity_summary"])
        self.assertIn("fixed backlog 1 review/1 ready", summary["device_status"])
        self.assertIn("review Garage", summary["device_status"])
        self.assertIn("(fixed)", summary["device_status"])
        self.assertIn("ready Pool", summary["device_status"])

    def test_command_center_summary_fleet_activity_fallback_stays_signal_first(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Review the current fleet signals.",
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
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar"
        native_support._build_command_center_fleet_activity_summary = lambda *args, **kwargs: (
            "This intentionally oversized fleet-activity sentence should overflow the Home Assistant state limit and force "
            "the command center to fall back to its shorter device-status signal story while keeping the managed and "
            "unmanaged context visible instead of repeating helper-style section labels. "
        ) * 3
        native_support._prefer_review_ready_over_large_kind_mix = lambda summary: summary
        native_support._compact_fleet_activity_overflow_summary = lambda summary: summary
        native_support._restore_ready_promotion_count_under_overflow = lambda summary, **kwargs: summary
        native_support._restore_active_device_under_overflow = lambda summary, **kwargs: summary
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            reason="Holding while one managed device needs attention.",
            control_reason="Attention-first fleet check remains the next action.",
            status="Active",
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_status_summary=(
                "Managed Devices: 1 managed device needs attention; attention first Pool pump (fixed | blocked); "
                "1 unmanaged backlog; source blockers active"
            ),
            device_count=1,
            enabled_device_count=1,
            usable_device_count=0,
            blocked_planned_action_count=1,
            device_details={
                "pool_pump": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "action_executable": False,
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
        self.assertNotIn("Managed Devices:", summary["fleet_activity_summary"])
        self.assertIn("attention first Pool pump", summary["fleet_activity_summary"])
        self.assertIn("1 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertIn("source blockers active", summary["fleet_activity_summary"])

    def test_fleet_activity_fallback_dedupes_attention_overlap_from_device_status(self) -> None:
        native_support = _load_native_support_module()

        compacted = native_support._fleet_activity_fallback_from_device_status(
            "Managed Devices: 1 managed device needs attention; attention first Pool pump (fixed | blocked); "
            "1 blocked managed action; blocked Pool pump (fixed | blocked); 1 planned action; "
            "plan Pool pump (fixed | action turn_on); 2 managed; 2 unmanaged backlog; source blockers active; "
            "review Garage helper with a deliberately long review-first label near the utility room board (fixed) | review first | warn helper-backed load needs review and validation; "
            "ready EV charger with a deliberately long ready-next label near the driveway board (variable) | likely useful"
        )

        self.assertLessEqual(len(compacted), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("attention first", compacted)
        self.assertIn("2 unmanaged backlog", compacted)
        self.assertIn("source blockers active", compacted)
        self.assertIn("review Garage helper", compacted)
        self.assertIn("ready EV charger", compacted)
        self.assertNotIn("blocked Pool pump", compacted)
        self.assertNotIn("1 blocked managed action", compacted)
        self.assertNotIn("1 planned action", compacted)
        self.assertNotIn("plan Pool pump", compacted)

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
        native_support.REQUIRED_SOURCE_KEYS = [native_support.CONF_SOLAR_POWER_ENTITY]
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
        self.assertIn("attention first Hot water", summary["fleet_activity_summary"])
        self.assertIn("active load 5300 W", summary["fleet_activity_summary"])
        self.assertIn("active device EV char", summary["fleet_activity_summary"])
        self.assertIn("2 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertIn("source blockers active", summary["fleet_activity_summary"])
        self.assertIn("fixed backlog 1 review", summary["fleet_activity_summary"])
        self.assertIn("variable backlog 1 ready", summary["fleet_activity_summary"])
        self.assertIn("review Garage", summary["fleet_activity_summary"])
        self.assertIn("(fixed)", summary["fleet_activity_summary"])
        self.assertIn("ready EV", summary["fleet_activity_summary"])
        self.assertIn("(variable)", summary["fleet_activity_summary"])

    def test_command_center_summary_keeps_managed_inventory_context_when_sources_block_fleet(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime looks healthy.",
            "next_step": "Repair the source blockers first.",
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
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

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
            fixed_device_count=1,
            controllable_nominal_power_w=6500.0,
            device_details={
                "pool": {
                    "name": "Pool pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "action_executable": False,
                    "nominal_power_w": 1200,
                },
                "ev": {
                    "name": "EV charger",
                    "entity_id": "number.ev_charger_limit",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 5300.0,
                    "nominal_power_w": 5300,
                },
            },
        )
        coordinator = SimpleNamespace(
            data=state,
            entry=entry,
            hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])),
        )

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("source blockers active", summary["fleet_activity_summary"])
        self.assertIn("2 managed", summary["fleet_activity_summary"])
        self.assertIn("1 fixed managed", summary["fleet_activity_summary"])
        self.assertIn("1 variable managed", summary["fleet_activity_summary"])
        self.assertIn("6500 W nominal", summary["fleet_activity_summary"])
        self.assertLessEqual(len(summary["fleet_activity_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)

    def test_command_center_summary_keeps_active_device_signal_in_tighter_fleet_activity_overflow(self) -> None:
        native_support = _load_native_support_module()

        compacted = native_support._compact_fleet_activity_overflow_summary(
            " | ".join(
                [
                    "2 managed",
                    "2 managed devices need attention",
                    "attention first Hot water relay with an extraordinarily verbose managed-device attention label that should require tighter priority compaction",
                    "blocked Hot water relay with an extraordinarily verbose managed-device blocked label that should require tighter priority compaction",
                    "1 planned action",
                    "plan Hot water relay with an extraordinarily verbose managed-device plan label that should require tighter priority compaction",
                    "active load 5300 W",
                    "2 active managed devices",
                    "active device EV charger with an extraordinarily verbose active managed-device label that should remain visible after tighter priority compaction",
                    "2 unmanaged backlog",
                    "source blockers active",
                    "fixed backlog 1 review",
                    "variable backlog 1 ready",
                    "review Garage subboard auxiliary outlet bank candidate 02 with an extraordinarily verbose review-first descriptor that should require tighter priority compaction",
                    "ready EV charger export absorption control limit with an extraordinarily verbose ready-next descriptor that should require tighter priority compaction",
                ]
            )
        )

        self.assertLessEqual(len(compacted), 255)
        self.assertIn("attention first Hot water", compacted)
        self.assertIn("active load 5300 W", compacted)
        self.assertIn("2 active managed devices", compacted)
        self.assertIn("active device EV charger", compacted)
        self.assertIn("2 unmanaged backlog", compacted)
        self.assertIn("source blockers active", compacted)
        self.assertLess(compacted.index("source blockers active"), compacted.index("2 managed"))
        self.assertIn("review Garage", compacted)
        self.assertIn("ready EV", compacted)

    def test_command_center_summary_preserves_candidate_kind_in_review_ready_clipping(self) -> None:
        native_support = _load_native_support_module()

        self.assertEqual(
            "review Garage subboar... (fixed)",
            native_support._clip_review_ready_state_part(
                "review Garage subboard auxiliary outlet bank candidate 02 (fixed) | review first | warn generic outlet label",
                max_chars=32,
            ),
        )
        self.assertEqual(
            "ready EV charger e... (variable)",
            native_support._clip_review_ready_state_part(
                "ready EV charger export absorption control limit (variable) | likely useful",
                max_chars=32,
            ),
        )

    def test_clip_review_ready_state_part_prefers_review_warning_over_helperish_fit_copy_when_clipped(self) -> None:
        native_support = _load_native_support_module()

        review = native_support._clip_review_ready_state_part(
            "review Garage subboard auxiliary outlet bank candidate 02 west wing (fixed) | review carefully | warn generic circuit label",
            max_chars=80,
        )
        ready = native_support._clip_review_ready_state_part(
            "ready EV charger garage load-shedding candidate (variable) | likely useful | warn helper-backed",
            max_chars=80,
        )
        ready_without_warning = native_support._clip_review_ready_state_part(
            "ready EV charger export absorption control limit (variable) | likely useful | key warning: No immediate warnings",
            max_chars=80,
        )

        self.assertLessEqual(len(review), 80)
        self.assertIn("review Garage", review)
        self.assertIn("| warn ", review)
        self.assertNotIn("review carefully", review)
        self.assertLessEqual(len(ready), 80)
        self.assertIn("ready EV charger", ready)
        self.assertIn("| warn helper-backed", ready)
        self.assertNotIn("likely useful", ready)
        self.assertLessEqual(len(ready_without_warning), 80)
        self.assertIn("ready EV charger", ready_without_warning)
        self.assertIn("likely useful", ready_without_warning)

    def test_command_center_summary_preserves_candidate_kind_in_tighter_priority_overflow(self) -> None:
        native_support = _load_native_support_module()

        compacted = native_support._compact_fleet_activity_overflow_summary(
            " | ".join(
                [
                    "2 managed",
                    "attention first Hot water relay with an extraordinarily verbose managed-device attention label that should require tighter priority compaction",
                    "active load 5300 W",
                    "2 active managed devices",
                    "active device EV charger with an extraordinarily verbose active managed-device label that should remain visible after tighter priority compaction",
                    "2 unmanaged backlog",
                    "source blockers active",
                    "review Garage subboard auxiliary outlet bank candidate 02 (fixed) | review first | warn generic outlet label needs manual verification before promotion",
                    "ready EV charger export absorption control limit (variable) | likely useful | key warning: No immediate warnings",
                ]
            )
        )

        self.assertLessEqual(len(compacted), 255)
        self.assertIn("review ", compacted)
        self.assertIn("(fixed)", compacted)
        self.assertIn("ready ", compacted)
        self.assertIn("(variable)", compacted)

    def test_command_center_summary_overflow_compaction_drops_review_ready_helper_fragments(self) -> None:
        native_support = _load_native_support_module()

        compacted = native_support._compact_fleet_activity_overflow_summary(
            " | ".join(
                [
                    "1 managed",
                    "attention first Pool pump with a deliberately long operator label",
                    "enabled 1",
                    "usable 1",
                    "1 fixed managed",
                    "4200 W nominal",
                    "2 unmanaged backlog",
                    "1 needs review",
                    "review Review Candidate Alpha with a deliberately long label (fixed) | review first | warn generic outlet label",
                    "1 ready to promote",
                    "ready Ready Candidate Beta with a deliberately long label (variable) | likely useful | key warning: No immediate warnings",
                ]
            )
        )

        self.assertGreater(
            len(
                " | ".join(
                    [
                        "1 managed",
                        "attention first Pool pump with a deliberately long operator label",
                        "enabled 1",
                        "usable 1",
                        "1 fixed managed",
                        "4200 W nominal",
                        "2 unmanaged backlog",
                        "1 needs review",
                        "review Review Candidate Alpha with a deliberately long label (fixed) | review first | warn generic outlet label",
                        "1 ready to promote",
                        "ready Ready Candidate Beta with a deliberately long label (variable) | likely useful | key warning: No immediate warnings",
                    ]
                )
            ),
            native_support.MAX_NATIVE_SENSOR_STATE_CHARS,
        )
        self.assertLessEqual(len(compacted), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("review Review Candida", compacted)
        self.assertIn("(fixed)", compacted)
        self.assertIn("ready Ready Candid", compacted)
        self.assertIn("(variable)", compacted)
        self.assertNotIn("review first", compacted)
        self.assertNotIn("warn generic outlet label", compacted)
        self.assertNotIn("likely useful", compacted)
        self.assertNotIn("key warning:", compacted)

    def test_command_center_summary_compaction_keeps_active_device_alongside_review_ready_backlog_story(self) -> None:
        native_support = _load_native_support_module()

        state = SimpleNamespace(
            device_count=2,
            enabled_device_count=2,
            usable_device_count=2,
            device_details={
                "pool": {
                    "name": "Pool pump with a deliberately verbose patio-side equipment label",
                    "kind": "fixed",
                    "effective_enabled": True,
                    "usable": True,
                    "planned_action": "turn_on",
                    "observed_active": False,
                    "current_power_w": 0,
                },
                "ev": {
                    "name": "EV charger with a deliberately verbose garage-side runtime label",
                    "kind": "variable",
                    "effective_enabled": True,
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 920,
                    "current_target_power_w": 920,
                },
            },
        )

        summary = native_support._restore_active_device_under_overflow(
            native_support._build_command_center_fleet_activity_summary(
                state,
                candidate_count=2,
                fixed_candidate_count=1,
                variable_candidate_count=1,
                review_needed_count=1,
                fixed_review_count=1,
                variable_review_count=0,
                review_candidate_name="Garage auxiliary outlet bank candidate with a deliberately verbose review label",
                review_candidate_preview="Garage auxiliary outlet bank candidate with a deliberately verbose review label (fixed) | review carefully | warn generic outlet label requires review",
                ready_candidate_name="Air purifier circulation candidate with a deliberately verbose ready label",
                ready_candidate_preview="Air purifier circulation candidate with a deliberately verbose ready label (variable) | likely useful | warn helper-backed load should be verified",
                top_candidate_name="Garage auxiliary outlet bank candidate with a deliberately verbose review label",
                top_candidate_preview="Garage auxiliary outlet bank candidate with a deliberately verbose review label (fixed) | review carefully | warn generic outlet label requires review",
                source_blocked=False,
            ),
            active_managed_count=1,
            active_device_preview="EV charger with a deliberately verbose garage-side runtime label (variable | active 920 W)",
        )

        self.assertLessEqual(len(summary), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("attention first Pool pump", summary)
        self.assertIn("active device EV charger", summary)
        self.assertIn("2 unmanaged backlog", summary)
        self.assertIn("review Garage auxiliary", summary)
        self.assertIn("ready Air purifier", summary)

    def test_command_center_summary_overflow_prefers_backlog_story_over_candidate_inventory_counts(self) -> None:
        native_support = _load_native_support_module()

        compacted = native_support._compact_fleet_activity_overflow_summary(
            " | ".join(
                [
                    "2 managed",
                    "attention first Pool pump with an intentionally long attention label near the pergola west walkway",
                    "active load 920 W",
                    "1 active managed device",
                    "active device Heated floor west wing zone controller with a deliberately long runtime label",
                    "2 unmanaged backlog",
                    "1 fixed candidate",
                    "1 variable candidate",
                    "fixed backlog 1 review",
                    "variable backlog 1 ready",
                    "review Garage auxiliary outlet bank candidate 02 with a deliberately long review-first descriptor (fixed) | review first | warn generic outlet label needs review",
                    "ready EV charger export absorption control limit with a deliberately long ready-next descriptor (variable) | likely useful | key warning: No immediate warnings",
                ]
            )
        )

        self.assertLessEqual(len(compacted), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("2 managed", compacted)
        self.assertIn("2 unmanaged backlog", compacted)
        self.assertIn("review Garage", compacted)
        self.assertIn("ready EV", compacted)
        self.assertNotIn("1 fixed candidate", compacted)
        self.assertNotIn("1 variable candidate", compacted)

    def test_command_center_summary_overflow_compaction_keeps_focus_state_context(self) -> None:
        native_support = _load_native_support_module()

        compacted = native_support._compact_fleet_activity_overflow_summary(
            " | ".join(
                [
                    "2 managed",
                    "attention first Pool pump with a very long blocked label near the patio and side walkway (fixed | not usable | action turn_on)",
                    "active load 920 W",
                    "1 active managed device",
                    "active device Heated floor west wing zone controller with a very long active runtime label (variable | active 920 W)",
                    "2 unmanaged backlog",
                    "source blockers active",
                    "review Virtual load helper with a spectacularly verbose review-first label in the garage south-west board (fixed) | review first | warn helper-backed load needs review and validation",
                    "ready Dishwasher outlet with a remarkably long ready-next promotion candidate label near the utility room (fixed) | likely useful | warn high standby draw",
                ]
            )
        )

        self.assertLessEqual(len(compacted), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("attention first", compacted)
        self.assertTrue("(block)" in compacted or "(blocked)" in compacted)
        self.assertIn("active device", compacted)
        self.assertIn("(active)", compacted)
        self.assertIn("source blockers active", compacted)
        self.assertIn("review ", compacted)
        self.assertIn("ready ", compacted)

    def test_command_center_summary_compact_fleet_activity_keeps_focus_state_context(self) -> None:
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
        native_support.build_source_mapping_summary = lambda merged: ""
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

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
                "pool": {
                    "name": "Pool pump with a very long blocked label near the patio and side walkway",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "planned_action": "turn_on",
                    "action_executable": False,
                },
                "heated_floor": {
                    "name": "Heated floor west wing zone controller with a very long active runtime label",
                    "entity_id": "number.heated_floor",
                    "kind": "variable",
                    "observed_active": True,
                    "current_power_w": 920.0,
                },
            },
        )
        coordinator = SimpleNamespace(
            data=state,
            entry=entry,
            hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])),
        )

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("attention first", summary["fleet_activity_summary"])
        self.assertTrue(
            "(block)" in summary["fleet_activity_summary"]
            or "(blocked)" in summary["fleet_activity_summary"]
        )
        self.assertIn("active device", summary["fleet_activity_summary"])
        self.assertIn("(active", summary["fleet_activity_summary"])
        self.assertNotIn("configured devices available", summary["fleet_activity_summary"])

    def test_command_center_summary_tighter_priority_overflow_keeps_operational_focus_before_inventory_counts(self) -> None:
        native_support = _load_native_support_module()

        compacted = native_support._compact_fleet_activity_overflow_summary(
            " | ".join(
                [
                    "2 managed",
                    "2 managed devices need attention",
                    "attention first Pool pump with a very long blocked label near the patio and side walkway (fixed | not usable | action turn_on | extra extra extra extra extra extra extra extra)",
                    "2 blocked managed actions",
                    "blocked Pool pump with a very long blocked label near the patio and side walkway (fixed | blocked | action turn_on | extra extra extra extra extra extra extra extra)",
                    "2 planned actions",
                    "plan Pool pump with a very long blocked label near the patio and side walkway (fixed | action turn_on | extra extra extra extra extra extra extra extra)",
                    "active load 920 W",
                    "1 active managed device",
                    "active device Heated floor west wing zone controller with a very long active runtime label (variable | active 920 W | extra extra extra extra extra extra extra)",
                    "4 unmanaged backlog",
                    "source blockers active",
                    "fixed backlog 2 review/2 ready",
                    "2 need review",
                    "review Review Candidate Alpha with a deliberately long label (fixed) | review first | warn helper-backed load needs review and validation",
                    "2 ready to promote",
                    "ready Ready Candidate Beta with a deliberately long label (fixed) | likely useful | key warning: No immediate warnings",
                ]
            )
        )

        self.assertLessEqual(len(compacted), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertLess(compacted.index("attention first"), compacted.index("2 managed"))
        self.assertLess(compacted.index("active device"), compacted.index("2 managed"))
        self.assertIn("4 unmanaged backlog", compacted)
        self.assertIn("source blockers active", compacted)
        self.assertIn("review ", compacted)
        self.assertIn("ready ", compacted)

    def test_command_center_summary_overflow_compaction_keeps_active_cue_on_attention_first_device(self) -> None:
        native_support = _load_native_support_module()

        compacted = native_support._compact_fleet_activity_overflow_summary(
            " | ".join(
                [
                    "2 managed",
                    "attention first Pool pump with a spectacularly verbose blocked-and-active label near the patio side walkway (fixed | not usable | active 920 W)",
                    "2 unmanaged backlog",
                    "fixed backlog 2 review/2 ready",
                    "2 need review",
                    "review Review Candidate Alpha with a deliberately long label (fixed) | review first | warn helper-backed load needs review and validation",
                    "2 ready to promote",
                    "ready Ready Candidate Beta with a deliberately long label (fixed) | likely useful | key warning: No immediate warnings",
                ]
            )
        )

        self.assertLessEqual(len(compacted), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("attention first", compacted)
        self.assertIn("active", compacted)
        self.assertIn("review ", compacted)
        self.assertIn("ready ", compacted)

    def test_command_center_summary_restore_active_device_keeps_active_cue_with_blocked_story(self) -> None:
        native_support = _load_native_support_module()

        restored = native_support._restore_active_device_under_overflow(
            " | ".join(
                [
                    "2 managed",
                    "blocked Pool pump (fixed | blocked)",
                    "1 active managed device",
                    "2 unmanaged backlog",
                    "review Virtual load (fixed)",
                    "ready EV charger (variable)",
                ]
            ),
            active_managed_count=1,
            active_device_preview="Heated floor (active 920 W)",
        )

        self.assertLessEqual(len(restored), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("blocked Pool pump", restored)
        self.assertIn("active device", restored)
        self.assertIn("review ", restored)
        self.assertIn("ready ", restored)

    def test_command_center_summary_keeps_source_blockers_visible_when_fleet_activity_overflows(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime needs source repair before fleet changes.",
            "next_step": "Repair the mapped source blockers before relying on control.",
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
            "recommended_section": native_support.SOURCES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support.REQUIRED_SOURCE_KEYS = [native_support.CONF_SOLAR_POWER_ENTITY]
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage subboard auxiliary outlet bank candidate 02 with a very long ready-next descriptor for overflow",
                    "entity_id": "switch.garage_subboard_auxiliary_outlet_bank_candidate_02",
                    "kind": "fixed",
                },
                {
                    "name": "EV charger export absorption control limit with a very long review-first descriptor for overflow",
                    "entity_id": "number.ev_charger_export_absorption_control_limit",
                    "kind": "variable",
                },
            ],
            "Garage subboard auxiliary outlet bank candidate 02 with a very long ready-next descriptor for overflow",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "high" if candidate.get("kind") == "fixed" else "medium",
            "warnings": []
            if candidate.get("kind") == "fixed"
            else ["Generic outlet hardware label needs review."],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage subboard auxiliary outlet bank candidate 02 with a very long ready-next descriptor for overflow (fixed) | likely useful | key warning: No immediate warnings"
            if candidate and candidate.get("kind") == "fixed"
            else "EV charger export absorption control limit with a very long review-first descriptor for overflow (variable) | review first | warn generic outlet label needs manual verification before promotion"
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
        self.assertIn("source blockers active", summary["fleet_activity_summary"])
        self.assertIn("2 managed", summary["fleet_activity_summary"])
        self.assertIn("2 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertIn("review EV", summary["fleet_activity_summary"])
        self.assertIn("(variable)", summary["fleet_activity_summary"])
        self.assertIn("ready Garag", summary["fleet_activity_summary"])
        self.assertNotIn("configured devices available", summary["fleet_activity_summary"])

    def test_command_center_summary_keeps_source_blockers_visible_before_device_status_fallback(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime needs source repair before fleet changes.",
            "next_step": "Repair the mapped source blockers before relying on control.",
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
            "recommended_section": native_support.SOURCES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar\n- Grid: sensor.grid"
        native_support.REQUIRED_SOURCE_KEYS = [native_support.CONF_SOLAR_POWER_ENTITY]
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "ReviewCandidate0 ReviewCandidate0 ReviewCandidate0 ReviewCandidate0 ReviewCandidate0 ReviewCandidate0",
                    "entity_id": "switch.review_candidate_0",
                    "kind": "variable",
                },
                {
                    "name": "ReviewCandidate1 ReviewCandidate1 ReviewCandidate1 ReviewCandidate1 ReviewCandidate1",
                    "entity_id": "switch.review_candidate_1",
                    "kind": "fixed",
                },
                {
                    "name": "ReadyCandidate0 ReadyCandidate0 ReadyCandidate0 ReadyCandidate0 ReadyCandidate0 ReadyCandidate0",
                    "entity_id": "number.ready_candidate_0",
                    "kind": "variable",
                },
                {
                    "name": "ReadyCandidate1 ReadyCandidate1 ReadyCandidate1 ReadyCandidate1",
                    "entity_id": "switch.ready_candidate_1",
                    "kind": "fixed",
                },
            ],
            "ReviewCandidate0 ReviewCandidate0 ReviewCandidate0 ReviewCandidate0 ReviewCandidate0 ReviewCandidate0",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "medium" if "ReviewCandidate" in str(candidate.get("name") or "") else "high",
            "warnings": ["Generic outlet hardware label needs review."]
            if "ReviewCandidate" in str(candidate.get("name") or "")
            else [],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "ReviewCandidate0 ReviewCandidate0 ReviewCandidate0 ReviewCandidate0 ReviewCandidate0 ReviewCandidate0 (variable) | review first | warn generic outlet hardware label needs review"
            if candidate and candidate.get("entity_id") == "switch.review_candidate_0"
            else "ReviewCandidate1 ReviewCandidate1 ReviewCandidate1 ReviewCandidate1 ReviewCandidate1 (fixed) | review first | warn generic outlet hardware label needs review"
            if candidate and candidate.get("entity_id") == "switch.review_candidate_1"
            else "ReadyCandidate0 ReadyCandidate0 ReadyCandidate0 ReadyCandidate0 ReadyCandidate0 ReadyCandidate0 (variable) | likely useful | key warning: No immediate warnings"
            if candidate and candidate.get("entity_id") == "number.ready_candidate_0"
            else "ReadyCandidate1 ReadyCandidate1 ReadyCandidate1 ReadyCandidate1 (fixed) | likely useful | key warning: No immediate warnings"
        )

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            device_status_summary="2 configured devices available",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=2,
            fixed_device_count=2,
            variable_device_count=0,
            controllable_nominal_power_w=6500.0,
            blocked_planned_action_count=2,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            device_details={
                "managed_0": {
                    "name": "Managed0 Managed0",
                    "entity_id": "switch.managed_0",
                    "kind": "fixed",
                    "usable": True,
                    "planned_action": "turn_on",
                    "action_executable": False,
                    "last_action_status": "failed",
                },
                "managed_1": {
                    "name": "Managed1 Managed1",
                    "entity_id": "switch.managed_1",
                    "kind": "fixed",
                    "usable": True,
                    "planned_action": "turn_on",
                    "action_executable": False,
                    "last_action_status": "failed",
                },
            },
        )
        coordinator = SimpleNamespace(
            data=state,
            entry=entry,
            hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])),
        )

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("source blockers active", summary["fleet_activity_summary"])
        self.assertIn("2 managed", summary["fleet_activity_summary"])
        self.assertIn("4 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertIn("review ReviewCandidate0", summary["fleet_activity_summary"])
        self.assertIn("ready ReadyCandidate0", summary["fleet_activity_summary"])
        self.assertIn("source blockers active", summary["device_status"])
        self.assertIn("4 unmanaged backlog", summary["device_status"])
        self.assertNotEqual(summary["fleet_activity_summary"], summary["device_status"])
        self.assertNotIn("configured devices available", summary["fleet_activity_summary"])

    def test_command_center_summary_normalizes_source_blocker_next_action(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_install_provenance = lambda: {}
        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "operator_ready",
            "summary": "Runtime needs source repair before fleet changes.",
            "next_step": "Repair the mapped source blockers before relying on control.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": [native_support.CONF_SOLAR_POWER_ENTITY],
            "stale_source_keys": [],
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "Solar power unavailable"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "Solar power unavailable"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Source roles need attention: Solar power unavailable"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.SOURCES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: "- Solar: sensor.solar"
        native_support.REQUIRED_SOURCE_KEYS = []
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        state = SimpleNamespace(
            device_status_summary="1 managed device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            controllable_nominal_power_w=1200.0,
            blocked_planned_action_count=0,
            mode="monitoring",
            health_summary="Source repair needed",
            diagnostic_summary="Source repair needed",
            device_details={},
        )
        coordinator = SimpleNamespace(
            data=state,
            entry=SimpleNamespace(data={}, options={}),
            hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])),
        )

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertIn("Repair the source blockers", summary["next_action_summary"])
        self.assertNotIn("mapped source blockers", summary["next_action_summary"])

    def test_command_center_guide_normalizes_stale_mapped_role_next_action(self) -> None:
        native_support = _load_native_support_module()

        text = native_support.build_native_command_center_guide_text(
            {
                "headline_decision": "Source repair needed.",
                "alert_summary": "Source roles need attention.",
                "next_action_summary": "Repair mapped-role blockers, then repair the highlighted mapped-roles and review mapped sources before relying on control.",
                "energy_state_summary": "Solar unavailable.",
                "control_decision_summary": "Control paused.",
                "control_outcome_summary": "No action.",
                "fleet_activity_summary": "1 managed",
                "source_status": "Source roles need attention.",
                "policy_readiness": "Control paused until source roles recover.",
                "device_status": "1 managed",
                "support_status": "Diagnostics ready.",
                "recommended_section": native_support.SOURCES_SECTION_LABEL,
                "recommended_reason": "Source roles need attention.",
            }
        )

        self.assertIn("Repair source blockers", text)
        self.assertIn("repair the highlighted source roles", text)
        self.assertIn("review source roles", text)
        self.assertNotIn("mapped-role", text)
        self.assertNotIn("mapped roles", text)
        self.assertNotIn("mapped sources", text)

    def test_command_center_guide_normalizes_spaced_mapped_role_blockers(self) -> None:
        native_support = _load_native_support_module()

        text = native_support.build_native_command_center_guide_text(
            {
                "headline_decision": "Source repair needed.",
                "alert_summary": "Source roles need attention.",
                "next_action_summary": "Repair mapped role blockers, then review mapped role blocker detail before relying on control.",
                "energy_state_summary": "Solar unavailable.",
                "control_decision_summary": "Control paused.",
                "control_outcome_summary": "No action.",
                "fleet_activity_summary": "1 managed",
                "source_status": "Source roles need attention.",
                "policy_readiness": "Control paused until source roles recover.",
                "device_status": "1 managed",
                "support_status": "Diagnostics ready.",
                "recommended_section": native_support.SOURCES_SECTION_LABEL,
                "recommended_reason": "Source roles need attention.",
            }
        )

        self.assertIn("Repair source blockers", text)
        self.assertIn("review source blocker detail", text)
        self.assertNotIn("mapped role", text)
        self.assertNotIn("source role blockers", text)

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
        self.assertNotIn("1 fixed managed", summary["fleet_activity_summary"])
        self.assertNotIn("4200 W nominal", summary["fleet_activity_summary"])
        self.assertIn("1 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertIn("1 needs review", summary["fleet_activity_summary"])
        self.assertIn("review Garage candidate 02", summary["fleet_activity_summary"])
        self.assertNotIn("ready ", summary["fleet_activity_summary"])

    def test_command_center_summary_preserves_single_kind_ready_only_backlog_under_overflow(self) -> None:
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
            "confidence": "high",
            "warnings": [],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage subboard auxiliary outlet bank candidate 02 (fixed) | likely useful"
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
            device_status_summary="Managed Devices: 2 managed devices need attention, attention first Pool pump (fixed | action turn_on), blocked Pool pump (fixed | blocked), 1 planned action, plan Pool pump (fixed | action turn_on)",
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
        self.assertIn("fixed backlog 2 ready", summary["fleet_activity_summary"])
        self.assertIn("2 ready to promote", summary["fleet_activity_summary"])
        self.assertIn("ready Garage subboard au", summary["fleet_activity_summary"])
        self.assertIn("1 active managed device", summary["fleet_activity_summary"])
        self.assertIn("active device Heated flo", summary["fleet_activity_summary"])

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
            device_status_summary="Managed Devices: 2 managed devices need attention, attention first Pool pump (fixed | action turn_on), blocked Pool pump (fixed | blocked), 1 planned action, plan Pool pump (fixed | action turn_on)",
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
        self.assertIn("1 active managed device", summary["fleet_activity_summary"])
        self.assertIn("fixed backlog 2 review", summary["fleet_activity_summary"])
        self.assertIn("review Garage", summary["fleet_activity_summary"])
        self.assertNotIn("ready ", summary["fleet_activity_summary"])
        self.assertLessEqual(len(summary["device_status"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("fixed backlog 2 review", summary["device_status"])
        self.assertIn("review Garage", summary["device_status"])
        self.assertIn("(fixed)", summary["device_status"])
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
        self.assertIn("1 active managed device", summary["device_status"])
        self.assertIn("active device Pool Pump (fixed | active)", summary["device_status"])

    def test_command_center_device_status_keeps_active_device_signal_with_unmanaged_backlog(self) -> None:
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
        native_support.build_source_mapping_summary = lambda merged: ""
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage auxiliary outlet",
                    "entity_id": "switch.garage_aux_candidate_02",
                    "kind": "fixed",
                },
                {
                    "name": "EV charger export limit",
                    "entity_id": "number.ev_export_limit",
                    "kind": "variable",
                },
            ],
            "Garage auxiliary outlet",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "high" if candidate.get("kind") == "variable" else "medium",
            "warnings": [] if candidate.get("kind") == "variable" else ["Generic outlet label needs review"],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Garage auxiliary outlet (fixed) | review first | warn generic outlet label"
            if candidate and candidate.get("kind") == "fixed"
            else "EV charger export limit (variable) | likely useful | key warning: No immediate warnings"
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
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            variable_device_count=0,
            controllable_nominal_power_w=1185.0,
            blocked_planned_action_count=0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            validation_details={},
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
            },
        )
        coordinator = SimpleNamespace(
            data=state,
            entry=entry,
            hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])),
        )

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["device_status"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("1 active managed device", summary["device_status"])
        self.assertIn("active device Pool Pump", summary["device_status"])
        self.assertIn("(fixed", summary["device_status"])
        self.assertIn("2 unmanaged backlog", summary["device_status"])
        self.assertIn("review Garage auxiliary", summary["device_status"])
        self.assertIn("ready EV charger", summary["device_status"])

    def test_device_status_overflow_keeps_managed_focus_without_unmanaged_candidates(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "setup_needed",
            "summary": "Finish required source roles first.",
            "next_step": "Open Sensors and finish the missing source roles.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": ["solar_power"],
            "stale_source_keys": [],
            "validation_details": {"issues": []},
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "Missing solar power"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "Solar power"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Source blockers active"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.SOURCES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: ""
        native_support._command_center_candidate_snapshot = lambda coordinator, state: ([], "")

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            device_status_summary="4 configured devices available",
            device_count=4,
            enabled_device_count=4,
            usable_device_count=3,
            fixed_device_count=3,
            variable_device_count=1,
            controllable_nominal_power_w=6000.0,
            blocked_planned_action_count=2,
            active_controlled_power_w=4485.0,
            mode="monitoring",
            health_summary="Attention",
            diagnostic_summary="Attention",
            validation_details={},
            device_details={
                "pool_pump": {
                    "name": "Pool pump with very long label near pergola side walkway",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "effective_enabled": True,
                    "planned_action": "turn_on",
                    "last_result_label": "failed",
                    "observed_active": True,
                    "current_power_w": 1185.0,
                },
                "hot_water": {
                    "name": "Hot water relay with long label near garage door opener",
                    "entity_id": "switch.hot_water",
                    "kind": "fixed",
                    "usable": False,
                    "effective_enabled": True,
                    "planned_action": "turn_on",
                    "last_result_label": "timeout",
                    "observed_active": False,
                },
                "ev_charger": {
                    "name": "EV charger with very long label near front driveway panel",
                    "entity_id": "number.ev_export_limit",
                    "kind": "variable",
                    "usable": True,
                    "effective_enabled": True,
                    "observed_active": True,
                    "current_power_w": 3300.0,
                },
                "dishwasher": {
                    "name": "Dishwasher plug with label near kitchen bench",
                    "entity_id": "switch.dishwasher",
                    "kind": "fixed",
                    "usable": True,
                    "effective_enabled": True,
                    "observed_active": False,
                },
            },
        )
        coordinator = SimpleNamespace(
            data=state,
            entry=entry,
            hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])),
        )

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["device_status"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("4 managed", summary["device_status"])
        self.assertIn("2 active managed devices", summary["device_status"])
        self.assertIn("2 managed devices need attention", summary["device_status"])
        self.assertIn("2 blocked managed actions", summary["device_status"])
        self.assertIn("no unmanaged candidates", summary["device_status"])
        self.assertIn("source blockers active", summary["device_status"])

    def test_fleet_activity_overflow_keeps_active_device_focus_with_unmanaged_backlog(self) -> None:
        native_support = _load_native_support_module()

        native_support.build_native_operator_readiness = lambda coordinator: {
            "phase": "setup_needed",
            "summary": "Finish required source roles first.",
            "next_step": "Open Sensors and finish the missing source roles.",
        }
        native_support.build_source_attention_details = lambda state: {
            "unavailable_source_keys": ["solar_power"],
            "stale_source_keys": [],
            "validation_details": {"issues": []},
        }
        native_support.build_source_attention_summary = lambda *args, **kwargs: "Missing solar power"
        native_support.build_source_attention_role_summary = lambda *args, **kwargs: "Solar power"
        native_support.summarize_validation_issue_messages = lambda *args, **kwargs: "None"
        native_support.build_live_source_health_summary = lambda state: "Source blockers active"
        native_support.build_native_setup_recommendation = lambda **kwargs: {
            "recommended_section": native_support.SOURCES_SECTION_LABEL,
        }
        native_support.build_detailed_management_handoff = lambda *args, **kwargs: "Detailed managed fleet review ready."
        native_support.build_source_mapping_summary = lambda merged: ""

        candidates = [
            {
                "name": "Lounge Room Heated Floor Adaptive Controller",
                "entity_id": "number.lounge_room_heated_floor",
                "kind": "variable",
            },
            {
                "name": "Air Purifier North Bedroom High Output",
                "entity_id": "switch.air_purifier_north_bedroom",
                "kind": "fixed",
            },
        ]
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            candidates,
            candidates[0]["name"],
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "medium" if candidate.get("kind") == "variable" else "high",
            "warnings": ["Helper-backed entity needs review"] if candidate.get("kind") == "variable" else [],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Lounge Room Heated Floor Adaptive Controller (variable) | review first | warn helper-backed entity needs review"
            if candidate and candidate.get("kind") == "variable"
            else "Air Purifier North Bedroom High Output (fixed) | likely useful | key warning: No immediate warnings"
        )

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            reason="Monitoring while source setup is still incomplete.",
            control_reason="Waiting for missing source roles.",
            status="Paused",
            device_status_summary="1 configured device available",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            variable_device_count=0,
            controllable_nominal_power_w=1185.0,
            active_controlled_power_w=1185.0,
            blocked_planned_action_count=0,
            mode="monitoring",
            health_summary="Needs setup",
            diagnostic_summary="Needs setup",
            validation_details={},
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
            },
        )
        coordinator = SimpleNamespace(
            data=state,
            entry=entry,
            hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])),
        )

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("1 managed", summary["fleet_activity_summary"])
        self.assertIn("active device Pool Pu", summary["fleet_activity_summary"])
        self.assertIn("2 unmanaged backlog", summary["fleet_activity_summary"])
        self.assertIn("source blockers active", summary["fleet_activity_summary"])
        self.assertIn("review Lounge Room", summary["fleet_activity_summary"])
        self.assertIn("ready Air Purifier", summary["fleet_activity_summary"])

    def test_fleet_activity_overflow_restores_distinct_active_device_even_with_blocked_backlog(self) -> None:
        native_support = _load_native_support_module()
        native_support.build_source_mapping_summary = lambda merged: ""
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Review Candidate Alpha with a deliberately long label near the garage side board and utility room",
                    "entity_id": "switch.review_alpha",
                    "kind": "fixed",
                },
                {
                    "name": "Ready Candidate Beta with a deliberately long label near the patio board and laundry branch",
                    "entity_id": "switch.ready_beta",
                    "kind": "variable",
                },
            ],
            "Review Candidate Alpha with a deliberately long label near the garage side board and utility room",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "medium" if candidate.get("kind") == "fixed" else "high",
            "warnings": ["helper-backed load needs review and validation"] if candidate.get("kind") == "fixed" else [],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: (
            "Review Candidate Alpha with a deliberately long label near the garage side board and utility room (fixed) | review first | warn helper-backed load needs review and validation"
            if candidate and candidate.get("kind") == "fixed"
            else "Ready Candidate Beta with a deliberately long label near the patio board and laundry branch (variable) | likely useful | key warning: No immediate warnings"
        )

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            reason="Holding while one load is blocked, another is planned, and a third is actively running.",
            control_reason="Keeping the opening fleet story visible under overflow.",
            status="Active",
            device_status_summary="Managed Devices: 3 managed devices need attention",
            device_count=3,
            enabled_device_count=3,
            usable_device_count=1,
            fixed_device_count=2,
            variable_device_count=1,
            controllable_nominal_power_w=5000.0,
            active_controlled_power_w=1800.0,
            blocked_planned_action_count=2,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            validation_details={},
            device_details={
                "pool": {
                    "name": "Pool Pump West Patio Bank",
                    "entity_id": "switch.pool",
                    "kind": "fixed",
                    "usable": False,
                    "observed_active": False,
                    "planned_action": "turn_on",
                    "last_action_status": "blocked by safety",
                    "nominal_power_w": 1200.0,
                },
                "ev": {
                    "name": "EV charger north branch with long plan focus",
                    "entity_id": "number.ev",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": False,
                    "planned_action": "set_power",
                    "nominal_power_w": 2400.0,
                },
                "heater": {
                    "name": "Heated floor utility room south wing with long runtime focus",
                    "entity_id": "number.heater",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 1800.0,
                    "planned_action": "hold",
                    "nominal_power_w": 1400.0,
                },
            },
        )
        coordinator = SimpleNamespace(
            data=state,
            entry=entry,
            hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])),
        )

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertLessEqual(len(summary["fleet_activity_summary"]), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("attention first Pool Pump", summary["fleet_activity_summary"])
        self.assertIn("active device Heated", summary["fleet_activity_summary"])
        self.assertIn("review Review", summary["fleet_activity_summary"])
        self.assertIn("ready ", summary["fleet_activity_summary"])

    def test_fleet_activity_leads_with_operational_signals_before_inventory_counts(self) -> None:
        native_support = _load_native_support_module()
        native_support.build_source_mapping_summary = lambda merged: ""
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage auxiliary outlet bank",
                    "entity_id": "switch.garage_aux",
                    "kind": "fixed",
                },
                {
                    "name": "EV charger",
                    "entity_id": "switch.ev_charger",
                    "kind": "variable",
                },
            ],
            "Garage auxiliary outlet bank",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "high" if candidate.get("kind") == "variable" else "medium",
            "warnings": [] if candidate.get("kind") == "variable" else ["Generic outlet label"],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: candidate.get("name", "")

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            reason="Holding while one load is blocked and another is active.",
            control_reason="Waiting for the blocked load to clear.",
            status="Active",
            device_status_summary="Managed Devices: 2 managed, 2 unmanaged backlog",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=1,
            fixed_device_count=1,
            variable_device_count=1,
            controllable_nominal_power_w=3200.0,
            active_controlled_power_w=920.0,
            blocked_planned_action_count=1,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            validation_details={},
            device_details={
                "pool_pump": {
                    "name": "Pool Pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "observed_active": False,
                    "planned_action": "turn_on",
                    "last_action_status": "blocked by safety",
                    "nominal_power_w": 1200.0,
                },
                "heated_floor": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 920.0,
                    "planned_action": "hold",
                    "nominal_power_w": 2000.0,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)
        fleet_activity = summary["fleet_activity_summary"]

        self.assertLess(fleet_activity.index("attention first Pool Pump"), fleet_activity.index("2 managed"))
        self.assertLess(fleet_activity.index("active device Heated"), fleet_activity.index("2 managed"))
        self.assertIn("2 unmanaged backlog", fleet_activity)
        self.assertIn("review Garage auxiliary outle", fleet_activity)
        self.assertIn("ready EV charger", fleet_activity)

    def test_fleet_activity_prioritizes_review_ready_story_ahead_of_candidate_inventory_counts(self) -> None:
        native_support = _load_native_support_module()
        native_support.build_source_mapping_summary = lambda merged: ""
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage auxiliary outlet bank",
                    "entity_id": "switch.garage_aux",
                    "kind": "fixed",
                },
                {
                    "name": "EV charger",
                    "entity_id": "switch.ev_charger",
                    "kind": "variable",
                },
            ],
            "Garage auxiliary outlet bank",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "high" if candidate.get("kind") == "variable" else "medium",
            "warnings": [] if candidate.get("kind") == "variable" else ["Generic outlet label"],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: candidate.get("name", "")

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            reason="Holding while unmanaged review and ready-next backlog remain.",
            control_reason="Keeping fleet context visible.",
            status="Active",
            device_status_summary="Managed Devices: 1 managed, 2 unmanaged backlog",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            variable_device_count=0,
            controllable_nominal_power_w=1200.0,
            active_controlled_power_w=0.0,
            blocked_planned_action_count=0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            validation_details={},
            device_details={
                "pool_pump": {
                    "name": "Pool Pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "observed_active": False,
                    "planned_action": "hold",
                    "nominal_power_w": 1200.0,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)
        fleet_activity = summary["fleet_activity_summary"]

        self.assertIn("enabled 1", fleet_activity)
        self.assertIn("usable 1", fleet_activity)
        self.assertIn("1 fixed managed", fleet_activity)
        self.assertLess(fleet_activity.index("1 managed"), fleet_activity.index("enabled 1"))
        self.assertLess(fleet_activity.index("enabled 1"), fleet_activity.index("usable 1"))
        self.assertLess(fleet_activity.index("usable 1"), fleet_activity.index("1 fixed managed"))
        self.assertLess(fleet_activity.index("1 fixed managed"), fleet_activity.index("2 unmanaged backlog"))
        self.assertIn("fixed backlog 1 review", fleet_activity)
        self.assertIn("variable backlog 1 ready", fleet_activity)
        if "1 fixed candidate" in fleet_activity:
            self.assertLess(fleet_activity.index("fixed backlog 1 review"), fleet_activity.index("1 fixed candidate"))
        if "1 variable candidate" in fleet_activity:
            self.assertLess(fleet_activity.index("variable backlog 1 ready"), fleet_activity.index("1 variable candidate"))

    def test_fleet_activity_attention_label_absorbs_duplicate_blocked_focus(self) -> None:
        native_support = _load_native_support_module()
        native_support.build_source_mapping_summary = lambda merged: ""
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage helper",
                    "entity_id": "switch.garage_helper",
                    "kind": "fixed",
                },
                {
                    "name": "EV charger",
                    "entity_id": "switch.ev_charger",
                    "kind": "variable",
                },
            ],
            "Garage helper",
        )
        native_support.assess_candidate = lambda candidate: {
            "confidence": "high" if candidate.get("kind") == "variable" else "medium",
            "warnings": [] if candidate.get("kind") == "variable" else ["Generic outlet label"],
        }
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: candidate.get("name", "")

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            reason="Holding while one blocked load needs attention.",
            control_reason="Waiting for the blocked load to clear.",
            status="Active",
            device_status_summary="Managed Devices: 2 managed",
            device_count=2,
            enabled_device_count=2,
            usable_device_count=1,
            fixed_device_count=1,
            variable_device_count=1,
            controllable_nominal_power_w=3200.0,
            active_controlled_power_w=920.0,
            blocked_planned_action_count=1,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            validation_details={},
            device_details={
                "pool_pump": {
                    "name": "Pool Pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": False,
                    "observed_active": False,
                    "planned_action": "turn_on",
                    "last_action_status": "blocked by safety",
                    "nominal_power_w": 1200.0,
                },
                "heated_floor": {
                    "name": "Heated floor",
                    "entity_id": "number.heated_floor",
                    "kind": "variable",
                    "usable": True,
                    "observed_active": True,
                    "current_power_w": 920.0,
                    "planned_action": "hold",
                    "nominal_power_w": 2000.0,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)
        fleet_activity = summary["fleet_activity_summary"]

        self.assertIn("attention first Pool Pump", fleet_activity)
        self.assertIn("active device Heated", fleet_activity)
        self.assertIn("2 unmanaged backlog", fleet_activity)
        self.assertNotIn("blocked Pool Pump", fleet_activity)
        self.assertNotIn("1 blocked managed action", fleet_activity)

    def test_fleet_activity_attention_label_absorbs_duplicate_planned_focus(self) -> None:
        native_support = _load_native_support_module()
        native_support.build_source_mapping_summary = lambda merged: ""
        native_support._command_center_candidate_snapshot = lambda coordinator, state: (
            [
                {
                    "name": "Garage helper",
                    "entity_id": "switch.garage_helper",
                    "kind": "fixed",
                }
            ],
            "Garage helper",
        )
        native_support.assess_candidate = lambda candidate: {"confidence": "medium", "warnings": ["Generic outlet label"]}
        native_support.build_candidate_compact_preview = lambda candidate, include_warning=True: candidate.get("name", "")

        entry = SimpleNamespace(data={}, options={})
        state = SimpleNamespace(
            reason="Holding while one planned load needs attention.",
            control_reason="Preparing the next managed action.",
            status="Active",
            device_status_summary="Managed Devices: 1 managed",
            device_count=1,
            enabled_device_count=1,
            usable_device_count=1,
            fixed_device_count=1,
            variable_device_count=0,
            controllable_nominal_power_w=1200.0,
            active_controlled_power_w=0.0,
            blocked_planned_action_count=0,
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
            validation_details={},
            device_details={
                "pool_pump": {
                    "name": "Pool Pump",
                    "entity_id": "switch.pool_pump",
                    "kind": "fixed",
                    "usable": True,
                    "observed_active": False,
                    "planned_action": "turn_on",
                    "nominal_power_w": 1200.0,
                },
            },
        )
        coordinator = SimpleNamespace(data=state, entry=entry, hass=SimpleNamespace(states=SimpleNamespace(async_all=lambda: [])))

        summary = native_support.build_native_command_center_summary(coordinator)
        fleet_activity = summary["fleet_activity_summary"]

        self.assertIn("attention first Pool Pump", fleet_activity)
        self.assertIn("1 unmanaged backlog", fleet_activity)
        self.assertNotIn("plan Pool Pump", fleet_activity)
        self.assertNotIn("1 planned action", fleet_activity)

    def test_fleet_activity_overflow_drops_candidate_inventory_before_review_ready_previews(self) -> None:
        native_support = _load_native_support_module()

        compacted = native_support._compact_fleet_activity_overflow_summary(
            " | ".join(
                [
                    "1 managed",
                    "2 unmanaged backlog",
                    "1 fixed candidate",
                    "1 variable candidate",
                    "fixed backlog 1 review",
                    "variable backlog 1 ready",
                    "review Review Candidate Alpha with a deliberately long label near the garage side board and utility room (fixed) | review first | warn helper-backed load needs review and validation",
                    "ready Ready Candidate Beta with a deliberately long label near the patio board and laundry branch (variable) | likely useful | key warning: No immediate warnings",
                ]
            )
        )

        self.assertLessEqual(len(compacted), native_support.MAX_NATIVE_SENSOR_STATE_CHARS)
        self.assertIn("1 managed", compacted)
        self.assertIn("2 unmanaged backlog", compacted)
        self.assertIn("fixed backlog 1 review", compacted)
        self.assertIn("variable backlog 1 ready", compacted)
        self.assertIn("review Review Candida", compacted)
        self.assertIn("ready Ready Candid", compacted)
        self.assertNotIn("1 fixed candidate", compacted)
        self.assertNotIn("1 variable candidate", compacted)


if __name__ == "__main__":
    unittest.main()
