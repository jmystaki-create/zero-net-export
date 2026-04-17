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
NATIVE_SUPPORT_PATH = PACKAGE_ROOT / "native_support.py"


def _load_native_support_module(*, parse_device_result=([], [])):
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    ha_pkg = sys.modules.setdefault("homeassistant", types.ModuleType("homeassistant"))
    util_pkg = sys.modules.setdefault("homeassistant.util", types.ModuleType("homeassistant.util"))
    util_pkg.dt = types.SimpleNamespace(
        parse_datetime=lambda value: value,
        now=lambda: types.SimpleNamespace(isoformat=lambda: "2026-04-14T00:00:00+00:00"),
    )
    ha_pkg.util = util_pkg

    const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", CONST_PATH)
    assert const_spec and const_spec.loader
    const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = const_module
    const_spec.loader.exec_module(const_module)

    device_model_module = types.ModuleType("custom_components.zero_net_export.device_model")
    device_model_module.parse_device_configs = lambda raw: parse_device_result
    sys.modules[device_model_module.__name__] = device_model_module

    release_info_module = types.ModuleType("custom_components.zero_net_export.release_info")
    release_info_module.build_install_consistency_summary = lambda data: "install consistency"
    release_info_module.build_install_fingerprint_summary = lambda data: "install fingerprint summary"
    release_info_module.build_install_provenance = lambda: {"summary": "install summary"}
    release_info_module.build_install_repair_step = lambda data=None: "install repair step"
    release_info_module.build_release_info = lambda *args, **kwargs: {}
    sys.modules[release_info_module.__name__] = release_info_module

    validation_module = types.ModuleType("custom_components.zero_net_export.validation")
    validation_module.SourceSpec = lambda key, raw, source_kind, required=True: types.SimpleNamespace(
        key=key,
        raw=raw,
        source_kind=source_kind,
        required=required,
    )
    validation_module.format_source_binding_label = lambda value: str(value)
    sys.modules[validation_module.__name__] = validation_module

    native_support_spec = importlib.util.spec_from_file_location(
        "custom_components.zero_net_export.native_support",
        NATIVE_SUPPORT_PATH,
    )
    assert native_support_spec and native_support_spec.loader
    native_support_module = importlib.util.module_from_spec(native_support_spec)
    sys.modules[native_support_spec.name] = native_support_module
    native_support_spec.loader.exec_module(native_support_module)
    return native_support_module


class SourceRepairGuidanceTests(unittest.TestCase):
    def test_repair_step_prefers_exact_affected_role_summary_when_available(self) -> None:
        native_support = _load_native_support_module()
        guidance = native_support.build_source_repair_step(
            unavailable_source_keys=["solar_power_entity"],
            stale_source_keys=["grid_export_power_entity"],
            affected_roles=(
                "Solar power -> sensor.pv_power (unavailable); "
                "Grid export power -> sensor.grid_export (stale 245 s)"
            ),
        )
        self.assertIn("repair these mapped-source blockers first", guidance)
        self.assertIn("Solar power -> sensor.pv_power (unavailable)", guidance)
        self.assertIn("Grid export power -> sensor.grid_export (stale 245 s)", guidance)
        self.assertIn("make sure the mapped entities still exist and are reporting fresh numeric values", guidance)
        self.assertIn("restore live availability for Solar power", guidance)
        self.assertIn("refresh or replace stale readings for Grid export power", guidance)
        self.assertIn("reopen Sensors to confirm these roles recover", guidance)

    def test_repair_step_names_missing_roles_in_recovery_check(self) -> None:
        native_support = _load_native_support_module()
        guidance = native_support.build_source_repair_step(
            missing_source_keys=["solar_power_entity", "grid_import_power_entity"],
        )
        self.assertIn("finish these required source roles: Solar power, Grid import power", guidance)
        self.assertIn(
            "reopen Sensors to confirm these roles recover: Solar power, Grid import power.",
            guidance,
        )

    def test_repair_step_with_unavailable_roles_only_tells_operator_to_restore_availability(self) -> None:
        native_support = _load_native_support_module()
        guidance = native_support.build_source_repair_step(
            unavailable_source_keys=["solar_power_entity"],
        )
        self.assertIn("restore live availability for Solar power", guidance)
        self.assertNotIn("refresh or replace stale readings", guidance)

    def test_unavailable_sources_do_not_also_appear_as_stale_roles(self) -> None:
        native_support = _load_native_support_module()
        state = types.SimpleNamespace(
            validation_details={
                "source_diagnostics": {
                    "solar_power_entity": {
                        "status": "unavailable",
                        "entity_id": "sensor.pv_power",
                        "issues": ["Solar power entity sensor.pv_power is unavailable"],
                    }
                },
                "source_freshness": {
                    "solar_power_entity": {
                        "stale": True,
                        "age_seconds": 245,
                    }
                },
            },
            source_diagnostics={},
        )
        details = native_support.build_source_attention_details(state)
        self.assertEqual(details["unavailable_source_keys"], ["solar_power_entity"])
        self.assertEqual(details["stale_source_keys"], [])
        summary = native_support.build_source_attention_summary(
            state,
            {"solar_power_entity": "sensor.pv_power"},
        )
        self.assertIn("Solar power (sensor.pv_power, unavailable)", summary)
        self.assertNotIn("stale 245 s", summary)

    def test_repair_step_without_affected_role_summary_still_names_roles_in_recovery_check(self) -> None:
        native_support = _load_native_support_module()
        guidance = native_support.build_source_repair_step(
            unavailable_source_keys=["solar_power_entity"],
            stale_source_keys=["grid_export_power_entity"],
        )
        self.assertIn(
            "reopen Sensors to confirm these roles recover: Solar power, Grid export power.",
            guidance,
        )

    def test_stale_only_freshness_entries_appear_in_attention_details_and_summaries(self) -> None:
        native_support = _load_native_support_module()
        state = types.SimpleNamespace(
            source_diagnostics={},
            validation_details={
                "source_diagnostics": {},
                "source_freshness": {
                    "grid_import_power_entity": {
                        "entity_id": "sensor.grid_import",
                        "stale": True,
                        "age_seconds": 245,
                        "last_updated": "2026-04-14T00:00:00+00:00",
                        "stale_threshold_seconds": 120,
                    }
                },
                "issues": [],
            },
        )
        details = native_support.build_source_attention_details(state)
        self.assertEqual(details["unavailable_source_keys"], [])
        self.assertEqual(details["stale_source_keys"], ["grid_import_power_entity"])
        self.assertEqual(
            details["source_diagnostics"]["grid_import_power_entity"]["entity_id"],
            "sensor.grid_import",
        )

        summary = native_support.build_source_attention_summary(
            state,
            {"grid_import_power_entity": "sensor.grid_import"},
        )
        self.assertIn("Grid import power (sensor.grid_import, stale 245 s)", summary)

        role_summary = native_support.build_source_attention_role_summary(
            state,
            {"grid_import_power_entity": "sensor.grid_import"},
        )
        self.assertIn("Grid import power -> sensor.grid_import (stale 245 s)", role_summary)

    def test_energy_sources_respect_extended_stale_threshold_in_attention_details(self) -> None:
        native_support = _load_native_support_module()
        state = types.SimpleNamespace(
            source_diagnostics={},
            validation_details={
                "source_diagnostics": {},
                "source_freshness": {
                    "solar_energy": {
                        "entity_id": "sensor.system_rome_yield_total",
                        "stale": False,
                        "age_seconds": 824,
                        "last_updated": "2026-04-14T00:00:00+00:00",
                        "stale_threshold_seconds": 900,
                        "required": True,
                    }
                },
                "issues": [],
            },
        )
        details = native_support.build_source_attention_details(state)
        self.assertEqual(details["unavailable_source_keys"], [])
        self.assertEqual(details["stale_source_keys"], [])
        self.assertEqual(
            native_support.build_source_attention_summary(
                state,
                {"solar_energy": "sensor.system_rome_yield_total"},
                blocking_only=True,
            ),
            "None",
        )

    def test_repair_step_with_validation_only_guides_operator_to_confirm_entity_selection(self) -> None:
        native_support = _load_native_support_module()
        guidance = native_support.build_source_repair_step(
            blocking_validation_details="Battery state of charge entity sensor.battery_soc is not numeric",
            affected_roles="Battery state of charge -> sensor.battery_soc (Battery state of charge entity sensor.battery_soc is not numeric)",
        )
        self.assertIn("Confirm each mapped entity selection still points at the intended Home Assistant entity", guidance)
        self.assertIn("Battery state of charge entity sensor.battery_soc is not numeric", guidance)

    def test_attention_role_summary_includes_validation_only_role_errors(self) -> None:
        native_support = _load_native_support_module()
        state = types.SimpleNamespace(
            source_diagnostics={},
            validation_details={
                "issues": [
                    {
                        "code": "battery_soc_entity_non_numeric",
                        "severity": "error",
                        "message": "Battery state of charge entity sensor.battery_soc is not numeric",
                    }
                ]
            },
        )
        summary = native_support.build_source_attention_role_summary(
            state,
            {"battery_soc_entity": "sensor.battery_soc"},
        )
        concise = native_support.build_source_attention_summary(
            state,
            {"battery_soc_entity": "sensor.battery_soc"},
        )
        self.assertIn("Battery state of charge -> sensor.battery_soc", summary)
        self.assertIn("is not numeric", summary)
        self.assertIn(
            "Battery state of charge (sensor.battery_soc, Battery state of charge entity sensor.battery_soc is not numeric)",
            concise,
        )

    def test_fallback_hint_picks_up_multiword_validation_suffixes(self) -> None:
        native_support = _load_native_support_module()
        guidance = native_support.build_source_selector_fallback_hint(
            validation_issues=[
                {
                    "code": "grid_import_energy_entity_missing_entity",
                    "severity": "error",
                    "message": "Grid import energy entity is missing",
                },
                {
                    "code": "battery_soc_entity_non_numeric",
                    "severity": "error",
                    "message": "Battery state of charge entity sensor.battery_soc is not numeric",
                },
            ]
        )
        self.assertIn("Combined / net grid energy", guidance)
        self.assertIn("Battery state of charge", guidance)

    def test_setup_recommendation_prefers_sensors_when_source_blockers_exist(self) -> None:
        native_support = _load_native_support_module()
        recommendation = native_support.build_native_setup_recommendation(
            missing_source_keys=["solar_power_entity"],
            source_attention_roles="Solar power -> sensor.pv_power (unavailable)",
            device_issues=[],
            has_devices=False,
            readiness_phase="operator_setup",
        )
        self.assertEqual(recommendation["recommended_section"], "Sensors")
        self.assertEqual(recommendation["recommended_path"], native_support.SOURCES_CONFIGURE_PATH)

    def test_setup_recommendation_prefers_managed_devices_when_sources_are_ready(self) -> None:
        native_support = _load_native_support_module()
        recommendation = native_support.build_native_setup_recommendation(
            missing_source_keys=[],
            source_attention_roles="None",
            device_issues=[],
            has_devices=False,
            readiness_phase="operator_setup",
        )
        self.assertEqual(recommendation["recommended_section"], "Managed Devices")
        self.assertEqual(recommendation["recommended_path"], native_support.DEVICES_CONFIGURE_PATH)

    def test_command_center_guide_text_includes_source_blocker_details(self) -> None:
        native_support = _load_native_support_module()
        guide = native_support.build_native_command_center_guide_text(
            {
                "recommended_section": "Sensors",
                "recommended_path": native_support.SOURCES_CONFIGURE_PATH,
                "recommended_reason": "Mapped source blockers: Solar power unavailable.",
                "next_action_summary": "Repair the mapped-source blockers first.",
                "install_status": "install summary",
                "install_consistency": "install consistency",
                "headline_decision": "Source data needs attention, control is constrained.",
                "alert_summary": "Missing required source roles: Solar power",
                "energy_state_summary": "solar 0 W | grid import 900 W",
                "control_decision_summary": "mode automatic | target 0 W",
                "control_outcome_summary": "planned actions 0 | active load 0 W",
                "fleet_activity_summary": "0 managed | 4 unmanaged | top AC Outlet 2",
                "source_status": "Mapped source blockers: Solar power unavailable.",
                "source_mapping_summary": "Solar power -> sensor.pv_power",
                "unavailable_sources": "Solar power",
                "stale_sources": "Grid export power",
                "source_attention_summary": "Solar power (sensor.pv_power, unavailable)",
                "source_attention_roles": "Solar power -> sensor.pv_power (unavailable)",
                "device_status": "No managed devices configured yet",
                "device_next_step": "Add a controllable load.",
                "policy_status": "Mode Automatic",
                "policy_readiness": "Repair mapped-source blockers first.",
                "support_status": "Runtime attention remains.",
                "detailed_management_summary": "Use the device page for deeper per-device review.",
                "sources_path": native_support.SOURCES_CONFIGURE_PATH,
                "devices_path": native_support.DEVICES_CONFIGURE_PATH,
                "policy_path": native_support.POLICY_CONFIGURE_PATH,
                "support_path": native_support.SUPPORT_CONFIGURE_PATH,
                "mode_path": native_support.MODE_CONTROL_PATH,
            }
        )
        self.assertIn("This surface is for the basic setup only.", guide)
        self.assertIn("Open Managed Devices only after the current setup blockers are clear.", guide)
        self.assertIn("Now", guide)
        self.assertIn("- Recommended section: Sensors", guide)
        self.assertNotIn("- Recommended section: Sensors and source mapping", guide)
        self.assertIn(f"- Recommended path: {native_support.SOURCES_CONFIGURE_PATH}", guide)
        self.assertIn("Structured control board", guide)
        self.assertIn("- Energy state: solar 0 W | grid import 900 W", guide)
        self.assertIn("- Fleet activity: 0 managed | 4 unmanaged | top AC Outlet 2", guide)
        self.assertIn("Setup check", guide)
        self.assertIn("- Source map: Solar power -> sensor.pv_power", guide)
        self.assertIn("- Runtime health: Runtime attention remains.", guide)
        self.assertIn("- Source blockers: Solar power (sensor.pv_power, unavailable)", guide)
        self.assertIn("Basic setup paths", guide)
        self.assertIn(f"- Sensors: {native_support.SOURCES_CONFIGURE_PATH}", guide)
        self.assertIn(f"- Controls: {native_support.POLICY_CONFIGURE_PATH}", guide)
        self.assertIn(f"- Change live control mode: {native_support.MODE_CONTROL_PATH}", guide)
        self.assertIn("Bucket ownership", guide)
        self.assertIn(f"- Managed Devices owns fleet onboarding, edits, enablement, and removal: {native_support.DEVICES_CONFIGURE_PATH}", guide)
        self.assertIn(f"- Diagnostics owns troubleshooting, repairs, and install validation: {native_support.SUPPORT_CONFIGURE_PATH}.", guide)
        self.assertNotIn("Not here", guide)

    def test_normalize_command_center_section_upgrades_legacy_sensors_label(self) -> None:
        native_support = _load_native_support_module()
        self.assertEqual(
            native_support.normalize_command_center_section("Sensors"),
            native_support.SOURCES_SECTION_LABEL,
        )
        self.assertEqual(
            native_support.normalize_command_center_section(native_support.SOURCES_SECTION_LABEL),
            native_support.SOURCES_SECTION_LABEL,
        )

    def test_command_center_keeps_sources_as_the_recommended_section_when_source_blockers_and_device_issues_coexist(self) -> None:
        native_support = _load_native_support_module(parse_device_result=([], ["device config invalid"]))

        class _FakeCoordinator:
            entry = SimpleNamespace(
                title="Test Entry",
                entry_id="entry-1",
                version=1,
                data={"solar_power_entity": None},
                options={},
            )
            data = types.SimpleNamespace(
                validation_details={},
                source_diagnostics={},
                stale_data=False,
                usable_device_count=0,
                safe_mode=False,
            )

        command_center = native_support.build_native_command_center_summary(_FakeCoordinator())
        self.assertEqual(command_center["recommended_section"], native_support.SOURCES_SECTION_LABEL)
        self.assertEqual(command_center["recommended_path"], native_support.SOURCES_CONFIGURE_PATH)
        self.assertEqual(command_center["recommended_reason"], command_center["source_status"])
        self.assertIn("Missing required source roles", command_center["source_status"])
        self.assertIn(native_support.SOURCES_CONFIGURE_PATH, command_center["device_next_step"])
        self.assertNotIn(native_support.DEVICES_CONFIGURE_PATH, command_center["device_next_step"])

    def test_support_center_lists_each_native_path(self) -> None:
        native_support = _load_native_support_module()

        class _FakeCoordinator:
            entry = SimpleNamespace(
                title="Test Entry",
                entry_id="entry-1",
                version=1,
                data={},
                options={},
            )
            data = None

        support_center = native_support.build_native_support_center(_FakeCoordinator())
        self.assertIn("Zero Net Export diagnostics guide", support_center)
        self.assertNotIn("native support center", support_center)
        self.assertIn("Where each native path lives:", support_center)
        self.assertIn("Why this section is recommended:", support_center)
        self.assertIn(f"- Sensors: {native_support.SOURCES_CONFIGURE_PATH}", support_center)
        self.assertIn(f"- Managed Devices: {native_support.DEVICES_CONFIGURE_PATH}", support_center)
        self.assertIn(f"- Controls: {native_support.POLICY_CONFIGURE_PATH}", support_center)
        self.assertIn(f"- Diagnostics: {native_support.SUPPORT_CONFIGURE_PATH}", support_center)
        self.assertIn("What each command-center section is for:", support_center)
        self.assertIn(
            f"- {native_support.SOURCES_SECTION_LABEL}: source mapping, mapped-source health, and source-remediation guidance.",
            support_center,
        )
        self.assertIn("- Managed Devices: fleet onboarding, edits, enablement, and removal.", support_center)
        self.assertIn("- Controls: controller policy defaults, thresholds, and readiness.", support_center)
        self.assertIn("- Diagnostics: runtime health, install consistency, and troubleshooting guidance.", support_center)
        self.assertIn("Diagnostics snapshot", support_center)

    def test_detailed_management_path_uses_diagnostics_wording(self) -> None:
        native_support = _load_native_support_module()
        self.assertIn("native diagnostics actions", native_support.DETAILED_MANAGEMENT_PATH)
        self.assertNotIn("native support actions", native_support.DETAILED_MANAGEMENT_PATH)

    def test_support_snapshot_uses_diagnostics_snapshot_wording(self) -> None:
        native_support = _load_native_support_module()

        class _FakeCoordinator:
            entry = SimpleNamespace(
                title="Test Entry",
                entry_id="entry-1",
                version=1,
                data={},
                options={},
            )
            data = None

        snapshot = native_support.build_native_support_snapshot(_FakeCoordinator())
        self.assertIn("Zero Net Export diagnostics snapshot", snapshot)
        self.assertNotIn("Zero Net Export support snapshot", snapshot)

    def test_command_center_summary_uses_positive_source_blocker_copy_when_none_exist(self) -> None:
        native_support = _load_native_support_module()

        class _FakeCoordinator:
            entry = SimpleNamespace(
                title="Test Entry",
                entry_id="entry-1",
                version=1,
                data={
                    "solar_power_entity": "sensor.pv_power",
                    "solar_energy_entity": "sensor.pv_energy",
                    "grid_import_power_entity": "sensor.grid_import_power",
                    "grid_export_power_entity": "sensor.grid_export_power",
                    "grid_import_energy_entity": "sensor.grid_import_energy",
                    "grid_export_energy_entity": "sensor.grid_export_energy",
                },
                options={},
            )
            data = types.SimpleNamespace(
                validation_details={},
                source_diagnostics={},
                stale_data=False,
                usable_device_count=0,
                safe_mode=False,
                diagnostic_summary="Mapped sources currently look healthy across 6 mapped role(s).",
                health_summary="Healthy.",
                mode="automatic",
            )

        command_center = native_support.build_native_command_center_summary(_FakeCoordinator())
        self.assertEqual(command_center["source_attention_summary"], "No mapped-source blockers currently highlighted")

    def test_command_center_blocker_copy_ignores_optional_stale_sources(self) -> None:
        native_support = _load_native_support_module()

        class _FakeCoordinator:
            entry = SimpleNamespace(
                title="Test Entry",
                entry_id="entry-1",
                version=1,
                data={
                    "solar_power_entity": "sensor.pv_power",
                    "solar_energy_entity": "sensor.pv_energy_total",
                    "grid_import_power_entity": "sensor.grid_import_power",
                    "grid_export_power_entity": "sensor.grid_export_power",
                    "grid_import_energy_entity": "sensor.grid_import_energy",
                    "grid_export_energy_entity": "sensor.grid_export_energy",
                    "battery_discharge_power_entity": "sensor.battery_discharge_power",
                },
                options={},
            )
            data = types.SimpleNamespace(
                validation_details={
                    "source_diagnostics": {
                        "solar_energy": {
                            "entity_id": "sensor.pv_energy_total",
                            "required": True,
                        },
                        "grid_import_power": {
                            "entity_id": "sensor.grid_import_power",
                            "required": True,
                        },
                        "grid_export_power": {
                            "entity_id": "sensor.grid_export_power",
                            "required": True,
                        },
                        "battery_discharge_power": {
                            "entity_id": "sensor.battery_discharge_power",
                            "required": False,
                        },
                    },
                    "source_freshness": {
                        "solar_energy": {"stale": True, "age_seconds": 824, "required": True},
                        "grid_import_power": {"stale": True, "age_seconds": 824, "required": True},
                        "grid_export_power": {"stale": True, "age_seconds": 824, "required": True},
                        "battery_discharge_power": {"stale": True, "age_seconds": 824, "required": False},
                    },
                },
                source_diagnostics={},
                stale_data=True,
                usable_device_count=0,
                safe_mode=True,
                health_summary="Runtime attention remains.",
                diagnostic_summary="Runtime attention remains.",
                mode="automatic",
            )

        command_center = native_support.build_native_command_center_summary(_FakeCoordinator())
        self.assertIn("solar_energy", command_center["source_attention_summary"])
        self.assertIn("grid_import_power", command_center["source_attention_summary"])
        self.assertIn("grid_export_power", command_center["source_attention_summary"])
        self.assertNotIn("battery_discharge_power", command_center["source_attention_summary"])
        self.assertNotIn("battery_discharge_power", command_center["source_attention_roles"])
        self.assertNotIn("battery_discharge_power", command_center["recommended_reason"])

    def test_command_center_blocker_copy_ignores_slow_required_energy_staleness(self) -> None:
        native_support = _load_native_support_module()

        class _FakeCoordinator:
            entry = SimpleNamespace(
                title="Test Entry",
                entry_id="entry-1",
                version=1,
                data={
                    "solar_power_entity": "sensor.pv_power",
                    "solar_energy_entity": "sensor.pv_energy_total",
                    "grid_import_power_entity": "sensor.grid_import_power",
                    "grid_export_power_entity": "sensor.grid_export_power",
                    "grid_import_energy_entity": "sensor.grid_import_energy",
                    "grid_export_energy_entity": "sensor.grid_export_energy",
                },
                options={},
            )
            data = types.SimpleNamespace(
                validation_details={
                    "source_diagnostics": {
                        "solar_energy": {
                            "entity_id": "sensor.pv_energy_total",
                            "required": True,
                        },
                        "grid_import_power": {
                            "entity_id": "sensor.grid_import_power",
                            "required": True,
                        },
                    },
                    "source_freshness": {
                        "solar_energy": {
                            "stale": True,
                            "age_seconds": 1532,
                            "required": True,
                            "stale_blocks_runtime": False,
                        },
                        "grid_import_power": {
                            "stale": False,
                            "age_seconds": 12,
                            "required": True,
                            "stale_blocks_runtime": True,
                        },
                    },
                },
                source_diagnostics={},
                stale_data=False,
                usable_device_count=1,
                safe_mode=False,
                health_summary="Healthy.",
                diagnostic_summary="Mapped sources currently look healthy across 6 mapped role(s).",
                mode="automatic",
            )

        command_center = native_support.build_native_command_center_summary(_FakeCoordinator())
        self.assertEqual(command_center["source_attention_summary"], "No mapped-source blockers currently highlighted")
        self.assertNotIn("solar_energy", command_center["recommended_reason"])

    def test_support_center_surfaces_current_source_blockers_near_the_top(self) -> None:
        native_support = _load_native_support_module()

        class _FakeCoordinator:
            entry = SimpleNamespace(
                title="Test Entry",
                entry_id="entry-1",
                version=1,
                data={"solar_power_entity": "sensor.pv_power"},
                options={},
            )
            data = types.SimpleNamespace(
                validation_details={
                    "source_diagnostics": {
                        "solar_power_entity": {
                            "status": "unavailable",
                            "entity_id": "sensor.pv_power",
                            "issues": ["Solar power entity sensor.pv_power is unavailable"],
                        }
                    }
                },
                source_diagnostics={},
                stale_data=False,
                usable_device_count=0,
                safe_mode=True,
                reason="Solar power is unavailable.",
                diagnostic_summary="Runtime attention remains.",
                health_summary="Runtime attention remains.",
            )

        support_center = native_support.build_native_support_center(_FakeCoordinator())
        self.assertIn(
            "Current mapped-source blockers: Solar power (sensor.pv_power, unavailable)",
            support_center,
        )
        self.assertIn(
            "Affected mapped roles: Solar power -> sensor.pv_power (unavailable; Solar power entity sensor.pv_power is unavailable)",
            support_center,
        )
        self.assertIn("Unavailable mapped roles: Solar power", support_center)
        self.assertIn("Stale mapped roles: None", support_center)


if __name__ == "__main__":
    unittest.main()
