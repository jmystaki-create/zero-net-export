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
BUTTON_PATH = PACKAGE_ROOT / "button.py"


def _load_button_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    homeassistant_pkg = sys.modules.setdefault("homeassistant", types.ModuleType("homeassistant"))
    homeassistant_pkg.__path__ = []

    components_pkg = sys.modules.setdefault("homeassistant.components", types.ModuleType("homeassistant.components"))
    components_pkg.__path__ = []
    homeassistant_pkg.components = components_pkg

    helpers_pkg = sys.modules.setdefault("homeassistant.helpers", types.ModuleType("homeassistant.helpers"))
    helpers_pkg.__path__ = []
    homeassistant_pkg.helpers = helpers_pkg

    persistent_notification_module = types.ModuleType("homeassistant.components.persistent_notification")
    persistent_notification_module.async_create = lambda *args, **kwargs: None
    sys.modules[persistent_notification_module.__name__] = persistent_notification_module
    components_pkg.persistent_notification = persistent_notification_module

    button_component_module = types.ModuleType("homeassistant.components.button")
    button_component_module.ButtonEntity = type("ButtonEntity", (), {})
    sys.modules[button_component_module.__name__] = button_component_module
    components_pkg.button = button_component_module

    entity_helper_module = types.ModuleType("homeassistant.helpers.entity")
    entity_helper_module.EntityCategory = types.SimpleNamespace(DIAGNOSTIC="diagnostic")
    sys.modules[entity_helper_module.__name__] = entity_helper_module
    helpers_pkg.entity = entity_helper_module

    update_coordinator_module = types.ModuleType("homeassistant.helpers.update_coordinator")

    class CoordinatorEntity:
        def __init__(self, coordinator) -> None:
            self.coordinator = coordinator

    update_coordinator_module.CoordinatorEntity = CoordinatorEntity
    sys.modules[update_coordinator_module.__name__] = update_coordinator_module
    helpers_pkg.update_coordinator = update_coordinator_module

    const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", CONST_PATH)
    assert const_spec and const_spec.loader
    integration_const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = integration_const_module
    const_spec.loader.exec_module(integration_const_module)

    entity_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.entity", ENTITY_PATH)
    assert entity_spec and entity_spec.loader
    integration_entity_module = importlib.util.module_from_spec(entity_spec)
    sys.modules[entity_spec.name] = integration_entity_module
    entity_spec.loader.exec_module(integration_entity_module)

    native_support_module = types.ModuleType("custom_components.zero_net_export.native_support")
    native_support_module.DEVICES_CONFIGURE_PATH = "devices path"
    native_support_module.DEVICES_SECTION_LABEL = "Managed Devices"
    native_support_module.POLICY_CONFIGURE_PATH = "policy path"
    native_support_module.POLICY_SECTION_LABEL = "Controls"
    native_support_module.PRIMARY_CONFIGURE_PATH = "primary path"
    native_support_module.SOURCES_CONFIGURE_PATH = "sources path"
    native_support_module.SOURCES_SECTION_LABEL = "Sensors"
    native_support_module.SUPPORT_CONFIGURE_PATH = "support path"
    native_support_module.SUPPORT_SECTION_LABEL = "Diagnostics"
    native_support_module.build_native_command_center_summary = lambda coordinator: {}
    native_support_module.build_native_operator_readiness = lambda coordinator: {}
    native_support_module.build_native_support_center = lambda coordinator: "support center"
    native_support_module.build_native_support_snapshot = lambda coordinator: "support snapshot"
    sys.modules[native_support_module.__name__] = native_support_module

    button_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.button", BUTTON_PATH)
    assert button_spec and button_spec.loader
    button_module = importlib.util.module_from_spec(button_spec)
    sys.modules[button_spec.name] = button_module
    button_spec.loader.exec_module(button_module)
    return button_module


class ButtonEntityCategoryTests(unittest.TestCase):
    def test_fleet_console_button_is_primary(self) -> None:
        button_module = _load_button_module()
        coordinator = SimpleNamespace(
            entry=SimpleNamespace(entry_id="entry-1", title="Test Entry"),
            data=None,
        )

        fleet_console = button_module.ZeroNetExportShowFleetConsoleButton(coordinator)
        diagnostics = button_module.ZeroNetExportShowNativeDiagnosticsButton(coordinator)

        self.assertIsNone(getattr(fleet_console, "_attr_entity_category", None))
        self.assertEqual(diagnostics._attr_entity_category, button_module.EntityCategory.DIAGNOSTIC)


if __name__ == "__main__":
    unittest.main()
