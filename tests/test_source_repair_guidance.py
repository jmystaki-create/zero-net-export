from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"
CONST_PATH = PACKAGE_ROOT / "const.py"
NATIVE_SUPPORT_PATH = PACKAGE_ROOT / "native_support.py"


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
    util_pkg.dt = types.SimpleNamespace(parse_datetime=lambda value: value, now=lambda: None)
    ha_pkg.util = util_pkg

    const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", CONST_PATH)
    assert const_spec and const_spec.loader
    const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = const_module
    const_spec.loader.exec_module(const_module)

    device_model_module = types.ModuleType("custom_components.zero_net_export.device_model")
    device_model_module.parse_device_configs = lambda raw: ([], [])
    sys.modules[device_model_module.__name__] = device_model_module

    release_info_module = types.ModuleType("custom_components.zero_net_export.release_info")
    release_info_module.build_install_consistency_summary = lambda data: "install consistency"
    release_info_module.build_install_fingerprint_summary = lambda data: "install fingerprint summary"
    release_info_module.build_install_provenance = lambda: {"summary": "install summary"}
    release_info_module.build_release_info = lambda: {}
    sys.modules[release_info_module.__name__] = release_info_module

    validation_module = types.ModuleType("custom_components.zero_net_export.validation")
    validation_module.SourceSpec = object
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


if __name__ == "__main__":
    unittest.main()
