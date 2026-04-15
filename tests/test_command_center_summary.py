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
            mode="monitoring",
            health_summary="Healthy",
            diagnostic_summary="Healthy",
        )
        coordinator = SimpleNamespace(data=state, entry=entry)

        summary = native_support.build_native_command_center_summary(coordinator)

        self.assertEqual(summary["headline_decision"], "Action queued, waiting for device guard.")
        self.assertEqual(summary["alert_summary"], "1 configured device available")
        self.assertIn("solar 4200.0 W", summary["energy_state_summary"])
        self.assertIn("grid import 350.0 W", summary["energy_state_summary"])
        self.assertIn("battery charge 900.0 W", summary["energy_state_summary"])
        self.assertIn("battery discharge 0.0 W", summary["energy_state_summary"])
        self.assertIn("target", summary["control_decision_summary"])
        self.assertIn("Waiting for min-off timer to clear.", summary["control_decision_summary"])
        self.assertIn("planned actions 1", summary["control_outcome_summary"])
        self.assertIn("active load 1200.0 W", summary["control_outcome_summary"])
        self.assertIn("managed 1", summary["fleet_activity_summary"])
        self.assertIn("usable 1", summary["fleet_activity_summary"])
        self.assertIn("Open Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure -> Sensors", summary["source_repair_step"])

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
            f"Open {native_support.SUPPORT_CONFIGURE_PATH} to continue in the recommended command-center section.",
        )
        self.assertNotIn("Open Configure", summary["status_summary"])

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


if __name__ == "__main__":
    unittest.main()
