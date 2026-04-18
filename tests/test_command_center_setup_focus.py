from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


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
    device_model_module.parse_device_configs = lambda raw: ([], [])
    device_model_module.build_device_summary = lambda *args, **kwargs: "summary"
    sys.modules[device_model_module.__name__] = device_model_module

    release_info_module = types.ModuleType("custom_components.zero_net_export.release_info")
    release_info_module.build_install_consistency_summary = lambda provenance: "Manifest matches code version"
    release_info_module.build_install_fingerprint_summary = lambda provenance: "- fingerprint ok"
    release_info_module.build_install_provenance = lambda: {"summary": "Installed 0.1.84"}
    release_info_module.build_release_info = lambda *args, **kwargs: {}
    release_info_module.build_install_repair_step = lambda *args, **kwargs: "repair step"
    release_info_module.build_install_validation_cli_steps = lambda *args, **kwargs: {}
    sys.modules[release_info_module.__name__] = release_info_module

    validation_module = types.ModuleType("custom_components.zero_net_export.validation")
    validation_module.ValidationIssue = object
    validation_module.SourceSpec = object
    validation_module.format_source_binding_label = lambda value: str(value)
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


class CommandCenterSetupFocusTests(unittest.TestCase):
    def test_command_center_guide_stays_setup_focused(self) -> None:
        native_support = _load_native_support_module()
        text = native_support.build_native_command_center_guide_text(
            {
                "headline_decision": "Setup incomplete, waiting for required sensors.",
                "alert_summary": "Missing required source roles: Solar power",
                "next_action_summary": "Open Configure > Sensors next.",
                "source_status": "Missing required source roles: Solar power",
                "policy_status": "Mode zero export; target 0 W",
                "support_status": "Runtime attention remains.",
                "energy_state_summary": "solar 4200 W | grid export 1800 W",
                "control_decision_summary": "mode zero export | target 0 W",
                "control_outcome_summary": "planned actions 1 | active load 1200 W",
                "fleet_activity_summary": "0 managed | 3 unmanaged | top AC Outlet 2",
                "recommended_section": native_support.SOURCES_SECTION_LABEL,
                "recommended_path": native_support.SOURCES_CONFIGURE_PATH,
                "source_mapping_summary": "Solar power -> sensor.pv_power",
                "source_attention_summary": "Solar power unavailable",
                "source_repair_step": "Open Sensors and remap Solar power.",
                "sources_path": native_support.SOURCES_CONFIGURE_PATH,
                "policy_path": native_support.POLICY_CONFIGURE_PATH,
                "mode_path": native_support.MODE_CONTROL_PATH,
                "support_path": native_support.SUPPORT_CONFIGURE_PATH,
                "devices_path": native_support.DEVICES_CONFIGURE_PATH,
            }
        )

        self.assertIn("This surface is for the basic setup only.", text)
        self.assertIn("Open Managed Devices only after the current setup blockers are clear.", text)
        self.assertIn("Now", text)
        self.assertIn("- Top alerts: Missing required source roles: Solar power", text)
        self.assertIn(
            f"- Recommended next step: Open {native_support.SOURCES_CONFIGURE_PATH} next.",
            text,
        )
        self.assertIn("Structured control board", text)
        self.assertIn("- Energy state: solar 4200 W | grid export 1800 W", text)
        self.assertIn("- Control outcome: planned actions 1 | active load 1200 W", text)
        self.assertIn("- Fleet activity: 0 managed | 3 unmanaged | top AC Outlet 2", text)
        self.assertIn("Setup check", text)
        self.assertIn("- Source map: Solar power -> sensor.pv_power", text)
        self.assertIn("- Diagnostics: Runtime attention remains.", text)
        self.assertNotIn("- Runtime health:", text)
        self.assertIn("Basic setup paths", text)
        self.assertIn(f"- Sensors: {native_support.SOURCES_CONFIGURE_PATH}", text)
        self.assertIn(f"- Controls: {native_support.POLICY_CONFIGURE_PATH}", text)
        self.assertIn(f"- Change live control mode: {native_support.MODE_CONTROL_PATH}", text)
        self.assertIn(f"- Managed Devices: {native_support.DEVICES_CONFIGURE_PATH}", text)
        self.assertIn(f"- Diagnostics: {native_support.SUPPORT_CONFIGURE_PATH}", text)
        self.assertIn("Bucket ownership", text)
        self.assertIn(
            f"- Managed Devices owns fleet onboarding, promotion, edits, enablement, and removal: {native_support.DEVICES_CONFIGURE_PATH}",
            text,
        )
        self.assertEqual(text.count(f"Open {native_support.SOURCES_CONFIGURE_PATH} next."), 1)
        self.assertNotIn("Installed package:", text)
        self.assertNotIn("Install consistency:", text)
        self.assertNotIn("Managed-device deep review", text)
        self.assertNotIn("Not here", text)


if __name__ == "__main__":
    unittest.main()
