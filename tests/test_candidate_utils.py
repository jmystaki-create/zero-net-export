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


if __name__ == "__main__":
    unittest.main()
