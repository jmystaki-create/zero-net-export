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
        self.assertIn("reopen Sensors and source mapping to confirm these roles recover", guidance)

    def test_repair_step_names_missing_roles_in_recovery_check(self) -> None:
        native_support = _load_native_support_module()
        guidance = native_support.build_source_repair_step(
            missing_source_keys=["solar_power_entity", "grid_import_power_entity"],
        )
        self.assertIn("finish these required source roles: Solar power, Grid import power", guidance)
        self.assertIn(
            "reopen Sensors and source mapping to confirm these roles recover: Solar power, Grid import power.",
            guidance,
        )

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
        self.assertEqual(recommendation["recommended_section"], "Sensors and source mapping")
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
        self.assertEqual(recommendation["recommended_section"], "Managed devices")
        self.assertEqual(recommendation["recommended_path"], native_support.DEVICES_CONFIGURE_PATH)

    def test_command_center_guide_text_includes_source_blocker_details(self) -> None:
        native_support = _load_native_support_module()
        guide = native_support.build_native_command_center_guide_text(
            {
                "recommended_section": "Sensors",
                "recommended_path": native_support.SOURCES_CONFIGURE_PATH,
                "next_action_summary": "Repair the mapped-source blockers first.",
                "install_status": "install summary",
                "install_consistency": "install consistency",
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
            }
        )
        self.assertIn("Recommended section right now: Sensors and source mapping", guide)
        self.assertNotIn("Recommended section right now: Sensors\n", guide)
        self.assertIn("Use these native paths for the common operator jobs", guide)
        self.assertIn(f"- Fix source mapping or mapped-source blockers: {native_support.SOURCES_CONFIGURE_PATH}", guide)
        self.assertIn(f"- Add or edit managed devices: {native_support.DEVICES_CONFIGURE_PATH}", guide)
        self.assertIn("- Unavailable mapped roles: Solar power", guide)
        self.assertIn("- Stale mapped roles: Grid export power", guide)
        self.assertIn("- Current mapped-source blockers: Solar power (sensor.pv_power, unavailable)", guide)
        self.assertIn(f"- Sensors and source mapping: {native_support.SOURCES_CONFIGURE_PATH}", guide)

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
        self.assertIn("Missing required source roles", command_center["source_status"])
        self.assertIn("repair", command_center["device_next_step"])

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
        self.assertIn("Where each native path lives:", support_center)
        self.assertIn(f"- Sensors and source mapping: {native_support.SOURCES_CONFIGURE_PATH}", support_center)
        self.assertIn(f"- Managed devices: {native_support.DEVICES_CONFIGURE_PATH}", support_center)
        self.assertIn(f"- Controls: {native_support.POLICY_CONFIGURE_PATH}", support_center)
        self.assertIn(f"- Diagnostics: {native_support.SUPPORT_CONFIGURE_PATH}", support_center)


if __name__ == "__main__":
    unittest.main()
