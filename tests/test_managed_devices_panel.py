from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "frontend" / "managed-devices-panel.js"
INIT_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "__init__.py"
MANIFEST_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "manifest.json"
SERVICES_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "services.yaml"


class ManagedDevicesPanelTests(unittest.TestCase):
    def test_custom_managed_devices_panel_asset_is_not_shipped(self) -> None:
        self.assertFalse(PANEL_PATH.exists())

    def test_integration_does_not_register_sidebar_panel(self) -> None:
        source = INIT_PATH.read_text(encoding="utf-8")

        self.assertNotIn("async_register_panel", source)
        self.assertNotIn("StaticPathConfig", source)
        self.assertNotIn("PANEL_URL_PATH", source)
        self.assertNotIn("zero-net-export-managed-devices", source)
        self.assertNotIn("sidebar_title=\"ZNE Managed Devices\"", source)

    def test_manifest_has_no_frontend_panel_dependencies(self) -> None:
        source = MANIFEST_PATH.read_text(encoding="utf-8")

        self.assertNotIn('"frontend"', source)
        self.assertNotIn('"http"', source)
        self.assertNotIn('"panel_custom"', source)

    def test_backend_managed_device_update_service_remains_available(self) -> None:
        init_source = INIT_PATH.read_text(encoding="utf-8")
        services_source = SERVICES_PATH.read_text(encoding="utf-8")

        self.assertIn("update_managed_device", init_source)
        self.assertIn("update_managed_device:", services_source)


if __name__ == "__main__":
    unittest.main()
