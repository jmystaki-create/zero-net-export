from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ENTITY_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "entity.py"
CONST_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "const.py"


class DeviceSurfaceVersionTests(unittest.TestCase):
    def test_device_surface_version_reads_packaged_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            package_dir = base / "custom_components" / "zero_net_export"
            package_dir.mkdir(parents=True)
            (base / "custom_components").mkdir(exist_ok=True)
            (base / "custom_components" / "__init__.py").write_text("")
            (package_dir / "__init__.py").write_text("")
            (package_dir / "manifest.json").write_text(json.dumps({"version": "9.9.9"}))
            (package_dir / "entity.py").write_text(ENTITY_PATH.read_text())
            (package_dir / "const.py").write_text(CONST_PATH.read_text())

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
            update_module.CoordinatorEntity = object
            helpers_pkg.update_coordinator = update_module

            const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", package_dir / "const.py")
            assert const_spec and const_spec.loader
            const_module = importlib.util.module_from_spec(const_spec)
            sys.modules[const_spec.name] = const_module
            const_spec.loader.exec_module(const_module)

            entity_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.entity", package_dir / "entity.py")
            assert entity_spec and entity_spec.loader
            entity_module = importlib.util.module_from_spec(entity_spec)
            sys.modules[entity_spec.name] = entity_module
            entity_spec.loader.exec_module(entity_module)

            self.assertEqual(entity_module._device_surface_version(), "9.9.9")


if __name__ == "__main__":
    unittest.main()
