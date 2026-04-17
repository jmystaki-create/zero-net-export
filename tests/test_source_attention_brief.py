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
    device_model_module.parse_device_configs = lambda raw: ([], [])
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


class SourceAttentionBriefTests(unittest.TestCase):
    def test_build_source_attention_brief_returns_compact_summary(self) -> None:
        native_support = _load_native_support_module()
        native_support.build_source_attention_details = lambda state: {
            "source_diagnostics": {
                native_support.CONF_GRID_IMPORT_POWER_ENTITY: {
                    "entity_id": "sensor.grid_import_power",
                    "status": "unavailable",
                    "stale": False,
                    "issues": [],
                },
                native_support.CONF_SOLAR_POWER_ENTITY: {
                    "entity_id": "sensor.solar_power",
                    "status": "ok",
                    "stale": True,
                    "issues": [],
                },
            },
            "validation_issues": [],
            "unavailable_source_keys": [native_support.CONF_GRID_IMPORT_POWER_ENTITY],
            "stale_source_keys": [native_support.CONF_SOLAR_POWER_ENTITY],
        }

        summary = native_support.build_source_attention_brief(
            SimpleNamespace(),
            {
                native_support.CONF_GRID_IMPORT_POWER_ENTITY: "sensor.grid_import_power",
                native_support.CONF_SOLAR_POWER_ENTITY: "sensor.solar_power",
            },
            limit=3,
        )

        self.assertIn("Grid import power (unavailable)", summary)
        self.assertIn("Solar power (stale)", summary)


if __name__ == "__main__":
    unittest.main()
