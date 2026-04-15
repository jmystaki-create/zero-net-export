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
MODULE_PATH = PACKAGE_ROOT / "candidate_utils.py"


def _load_candidate_utils_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", CONST_PATH)
    assert const_spec and const_spec.loader
    integration_const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = integration_const_module
    const_spec.loader.exec_module(integration_const_module)

    module_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.candidate_utils", MODULE_PATH)
    assert module_spec and module_spec.loader
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


class CandidateUtilsTests(unittest.TestCase):
    def test_discover_candidate_devices_prefers_stronger_domains_before_helpers(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="input_boolean.virtual_load", state="on", attributes={"friendly_name": "Virtual load"}),
            SimpleNamespace(entity_id="light.patio", state="on", attributes={"friendly_name": "Patio lights"}),
            SimpleNamespace(entity_id="number.ev_charger_limit", state="16", attributes={"friendly_name": "EV charger limit"}),
            SimpleNamespace(entity_id="switch.hot_water", state="off", attributes={"friendly_name": "Hot water relay"}),
            SimpleNamespace(entity_id="input_number.helper_limit", state="12", attributes={"friendly_name": "Helper limit"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids=set())

        self.assertEqual(
            [candidate["entity_id"] for candidate in candidates],
            [
                "switch.hot_water",
                "number.ev_charger_limit",
                "light.patio",
                "input_number.helper_limit",
                "input_boolean.virtual_load",
            ],
        )

    def test_discover_candidate_devices_filters_managed_unknown_and_unavailable_entities(self) -> None:
        module = _load_candidate_utils_module()
        states = [
            SimpleNamespace(entity_id="switch.managed_device", state="on", attributes={"friendly_name": "Managed"}),
            SimpleNamespace(entity_id="switch.unknown_device", state="unknown", attributes={"friendly_name": "Unknown"}),
            SimpleNamespace(entity_id="number.unavailable_device", state="unavailable", attributes={"friendly_name": "Unavailable"}),
            SimpleNamespace(entity_id="sensor.not_a_device", state="42", attributes={"friendly_name": "Not a device"}),
            SimpleNamespace(entity_id="switch.pool_pump", state="off", attributes={"friendly_name": "Pool pump"}),
        ]

        candidates = module.discover_candidate_devices(states, managed_entity_ids={"switch.managed_device"})

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["entity_id"], "switch.pool_pump")
        self.assertEqual(candidates[0]["kind"], "fixed")

    def test_assess_candidate_flags_helper_and_missing_unit_risk(self) -> None:
        module = _load_candidate_utils_module()

        helper_fit = module.assess_candidate(
            {
                "domain": "input_boolean",
                "kind": "fixed",
                "state": "on",
                "unit": "",
                "device_class": "",
            }
        )
        variable_fit = module.assess_candidate(
            {
                "domain": "input_number",
                "kind": "variable",
                "state": "12",
                "unit": "",
                "device_class": "",
            }
        )

        self.assertEqual(helper_fit["confidence"], "low")
        self.assertIn("automation intent", helper_fit["summary"])
        self.assertTrue(any("input_boolean helper" in warning for warning in helper_fit["warnings"]))
        self.assertEqual(variable_fit["confidence"], "medium")
        self.assertTrue(any("meaningful unit" in warning for warning in variable_fit["warnings"]))

    def test_build_candidate_preview_includes_usefulness_and_key_warning(self) -> None:
        module = _load_candidate_utils_module()

        preview = module.build_candidate_preview(
            {
                "entity_id": "input_boolean.virtual_load",
                "name": "Virtual load",
                "kind": "fixed",
                "domain": "input_boolean",
                "state": "on",
                "unit": "",
                "device_class": "",
            }
        )

        self.assertIn("Virtual load (input_boolean.virtual_load, fixed)", preview)
        self.assertIn("needs extra review", preview)
        self.assertIn("input_boolean helper", preview)

    def test_build_candidate_preview_uses_no_warning_fallback_for_strong_match(self) -> None:
        module = _load_candidate_utils_module()

        preview = module.build_candidate_preview(
            {
                "entity_id": "switch.hot_water",
                "name": "Hot water relay",
                "kind": "fixed",
                "domain": "switch",
                "state": "off",
                "unit": "",
                "device_class": "",
            },
            include_state=True,
        )

        self.assertIn("strong match", preview)
        self.assertIn("state off", preview)
        self.assertIn("No immediate warnings", preview)

    def test_build_candidate_name_summary_stays_compact_for_sensor_states(self) -> None:
        module = _load_candidate_utils_module()

        candidates = [
            {"name": "AC Outlet 2", "entity_id": "switch.ac_outlet_2"},
            {"name": "AdGuard Home Filtering", "entity_id": "switch.adguard_home_filtering"},
            {"name": "AdGuard Home Parental control", "entity_id": "switch.adguard_home_parental_control"},
            {"name": "3rd Bedroom Crossfade", "entity_id": "switch.bedroom_crossfade"},
            {"name": "3rd Bedroom Loudness", "entity_id": "switch.bedroom_loudness"},
        ]

        summary = module.build_candidate_name_summary(candidates)

        self.assertEqual(
            summary,
            "AC Outlet 2; AdGuard Home Filtering; AdGuard Home Parental control; +2 more",
        )
        self.assertLessEqual(len(summary), 240)


if __name__ == "__main__":
    unittest.main()
