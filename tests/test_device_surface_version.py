from __future__ import annotations

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ENTITY_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "entity.py"


class DeviceSurfaceVersionTests(unittest.TestCase):
    def test_device_surface_uses_integration_version_without_manifest_io(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            package_dir = base / "custom_components" / "zero_net_export"
            package_dir.mkdir(parents=True)
            (base / "custom_components").mkdir(exist_ok=True)
            (base / "custom_components" / "__init__.py").write_text("")
            (package_dir / "__init__.py").write_text("")
            (package_dir / "entity.py").write_text(ENTITY_PATH.read_text())
            (package_dir / "const.py").write_text(
                'CONF_DEVICE_INVENTORY_JSON = "device_inventory_json"\n'
                'DEFAULT_DEVICE_INVENTORY_JSON = "[]"\n'
                'DOMAIN = "zero_net_export"\n'
                'INTEGRATION_VERSION = "7.7.7"\n'
            )
            (package_dir / "device_model.py").write_text(
                'def parse_device_configs(raw_inventory):\n'
                '    return [], []\n'
            )

            custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
            custom_components_pkg.__path__ = [str(base / "custom_components")]
            integration_pkg = sys.modules.setdefault(
                "custom_components.zero_net_export",
                types.ModuleType("custom_components.zero_net_export"),
            )
            integration_pkg.__path__ = [str(package_dir)]

            helpers_pkg = sys.modules.setdefault("homeassistant.helpers", types.ModuleType("homeassistant.helpers"))
            update_module = sys.modules.setdefault(
                "homeassistant.helpers.update_coordinator",
                types.ModuleType("homeassistant.helpers.update_coordinator"),
            )

            class DummyCoordinatorEntity:
                def __init__(self, coordinator) -> None:
                    self.coordinator = coordinator

                @property
                def device_info(self):
                    return self._attr_device_info

            update_module.CoordinatorEntity = DummyCoordinatorEntity
            helpers_pkg.update_coordinator = update_module

            const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", package_dir / "const.py")
            assert const_spec and const_spec.loader
            const_module = importlib.util.module_from_spec(const_spec)
            sys.modules[const_spec.name] = const_module
            const_spec.loader.exec_module(const_module)

            previous_modules = {
                name: sys.modules.get(name)
                for name in (
                    "custom_components.zero_net_export.const",
                    "custom_components.zero_net_export.device_model",
                    "custom_components.zero_net_export.entity",
                )
            }
            try:
                entity_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.entity", package_dir / "entity.py")
                assert entity_spec and entity_spec.loader
                entity_module = importlib.util.module_from_spec(entity_spec)
                sys.modules[entity_spec.name] = entity_module
                entity_spec.loader.exec_module(entity_module)

                class FakeCoordinator:
                    def __init__(self) -> None:
                        self.entry = types.SimpleNamespace(entry_id="entry-1", title="Zero Net Export")

                entity = entity_module.ZeroNetExportEntity(FakeCoordinator(), "status", "Status")
                self.assertEqual(entity.device_info["sw_version"], "7.7.7")
            finally:
                for name, module in previous_modules.items():
                    if module is None:
                        sys.modules.pop(name, None)
                    else:
                        sys.modules[name] = module


if __name__ == "__main__":
    unittest.main()
