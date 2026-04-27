from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"
CONST_PATH = PACKAGE_ROOT / "const.py"
DEVICE_MODEL_PATH = PACKAGE_ROOT / "device_model.py"
PLANNER_PATH = PACKAGE_ROOT / "planner.py"


def _load_planner_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    for name, path in (
        ("custom_components.zero_net_export.const", CONST_PATH),
        ("custom_components.zero_net_export.device_model", DEVICE_MODEL_PATH),
        ("custom_components.zero_net_export.planner", PLANNER_PATH),
    ):
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)

    return sys.modules["custom_components.zero_net_export.planner"]


class PlannerCopyTests(unittest.TestCase):
    def test_safe_mode_reason_uses_action_planning_not_recommendation_wording(self) -> None:
        module = _load_planner_module()

        plan = module.build_control_plan(
            module.PlannerContext(
                enabled=True,
                mode=module.MODE_SOFT_ZERO_EXPORT,
                safe_mode=True,
                target_export_w=0.0,
                deadband_w=50.0,
                grid_import_power_w=0.0,
                grid_export_power_w=1200.0,
                battery_soc=None,
                battery_reserve_soc=20.0,
            ),
            [],
        )

        self.assertEqual(plan.status, "blocked")
        self.assertEqual(
            plan.reason,
            "Source validation is degraded or blocked, so the planner will not surface device actions.",
        )
        self.assertNotIn("recommend", plan.reason.lower())


if __name__ == "__main__":
    unittest.main()
