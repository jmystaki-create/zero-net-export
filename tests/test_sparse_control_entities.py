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
ENTITY_PATH = PACKAGE_ROOT / "entity.py"
NUMBER_PATH = PACKAGE_ROOT / "number.py"
SELECT_PATH = PACKAGE_ROOT / "select.py"
SWITCH_PATH = PACKAGE_ROOT / "switch.py"


def _load_module(module_name: str, path: Path):
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    ha_pkg = sys.modules.setdefault("homeassistant", types.ModuleType("homeassistant"))
    ha_pkg.__path__ = []

    const_module = types.ModuleType("homeassistant.const")
    const_module.UnitOfPower = types.SimpleNamespace(WATT="W")
    sys.modules[const_module.__name__] = const_module

    number_component_module = types.ModuleType("homeassistant.components.number")
    number_component_module.NumberEntity = type("NumberEntity", (), {})
    sys.modules[number_component_module.__name__] = number_component_module

    select_component_module = types.ModuleType("homeassistant.components.select")
    select_component_module.SelectEntity = type("SelectEntity", (), {})
    sys.modules[select_component_module.__name__] = select_component_module

    switch_component_module = types.ModuleType("homeassistant.components.switch")
    switch_component_module.SwitchEntity = type("SwitchEntity", (), {})
    sys.modules[switch_component_module.__name__] = switch_component_module

    entity_helper_module = types.ModuleType("homeassistant.helpers.entity")
    entity_helper_module.EntityCategory = types.SimpleNamespace(CONFIG="config", DIAGNOSTIC="diagnostic")
    sys.modules[entity_helper_module.__name__] = entity_helper_module

    update_coordinator_module = types.ModuleType("homeassistant.helpers.update_coordinator")

    class CoordinatorEntity:
        def __init__(self, coordinator) -> None:
            self.coordinator = coordinator

    update_coordinator_module.CoordinatorEntity = CoordinatorEntity
    sys.modules[update_coordinator_module.__name__] = update_coordinator_module

    for spec_name, spec_path in (
        ("custom_components.zero_net_export.const", CONST_PATH),
        ("custom_components.zero_net_export.entity", ENTITY_PATH),
        (module_name, path),
    ):
        spec = importlib.util.spec_from_file_location(spec_name, spec_path)
        assert spec and spec.loader
        loaded = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = loaded
        spec.loader.exec_module(loaded)

    return sys.modules[module_name]


class SparseControlEntityTests(unittest.TestCase):
    def _coordinator(self):
        return SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=SimpleNamespace(validation_details={}),
        )

    def test_number_tolerates_missing_runtime_value_attributes(self) -> None:
        number_module = _load_module("custom_components.zero_net_export.number", NUMBER_PATH)

        number = number_module.ZeroNetExportNumber(self._coordinator(), "target_export_w", "Target export", 0, 10000, 10)

        self.assertIsNone(number.native_value)

    def test_select_tolerates_missing_mode_attribute(self) -> None:
        select_module = _load_module("custom_components.zero_net_export.select", SELECT_PATH)

        mode = select_module.ZeroNetExportModeSelect(self._coordinator(), "mode", "Mode")

        self.assertIsNone(mode.current_option)

    def test_switch_tolerates_missing_enabled_attribute(self) -> None:
        switch_module = _load_module("custom_components.zero_net_export.switch", SWITCH_PATH)

        enabled = switch_module.ZeroNetExportEnabledSwitch(self._coordinator(), "enabled", "Enabled")

        self.assertIsNone(enabled.is_on)


if __name__ == "__main__":
    unittest.main()
