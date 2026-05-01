from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"
MODULE_PATH = PACKAGE_ROOT / "device_model.py"


def _load_device_model_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.device_model", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DeviceModelTests(unittest.TestCase):
    def test_fixed_toggle_adapter_supports_climate_entities(self) -> None:
        module = _load_device_model_module()
        device = module.DeviceConfig(
            key="living_room_ac",
            name="Living Room AC",
            kind=module.DEVICE_KIND_FIXED,
            entity_id="climate.living_room_ac",
            adapter=None,
            nominal_power_w=2500,
            min_power_w=2500,
            max_power_w=2500,
            step_w=2500,
            priority=100,
            enabled=True,
            min_on_seconds=900,
            min_off_seconds=900,
            cooldown_seconds=60,
            max_active_seconds=14400,
        )

        adapter, status, reason = module.resolve_device_adapter(device)

        self.assertIsNotNone(adapter)
        self.assertEqual(adapter.key, module.ADAPTER_FIXED_TOGGLE)
        self.assertEqual(status, "inferred")
        self.assertIn("climate.living_room_ac", reason)


if __name__ == "__main__":
    unittest.main()
