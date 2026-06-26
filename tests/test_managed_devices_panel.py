from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_PANEL_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "frontend" / "zero-net-export-app.js"
INIT_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "__init__.py"
MANIFEST_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "manifest.json"
SERVICES_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "services.yaml"
APP_API_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "app_api.py"
HACS_PATH = REPO_ROOT / "hacs.json"


class ManagedDevicesPanelTests(unittest.TestCase):
    def test_zero_net_export_app_panel_asset_is_shipped(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("customElements.define(\"zero-net-export-app\"", source)
        self.assertIn("Version ${version}", source)
        self.assertIn("Zero Net Export entities visible", source)

    def test_integration_registers_supported_sidebar_app_panel(self) -> None:
        source = INIT_PATH.read_text(encoding="utf-8")

        self.assertIn("panel_custom.async_register_panel", source)
        self.assertIn("StaticPathConfig", source)
        self.assertIn("APP_PANEL_URL_PATH", source)
        self.assertIn("APP_MODULE_URL", source)
        self.assertIn("sidebar_title=APP_PANEL_TITLE", source)
        self.assertIn("config_panel_domain=DOMAIN", source)
        self.assertNotIn("zero-net-export-managed-devices", source)
        self.assertNotIn("sidebar_title=\"ZNE Managed Devices\"", source)

    def test_manifest_declares_app_panel_dependencies_and_release_version(self) -> None:
        source = MANIFEST_PATH.read_text(encoding="utf-8")
        hacs_source = HACS_PATH.read_text(encoding="utf-8")

        self.assertIn('"version": "0.2.0"', source)
        self.assertIn('"frontend"', source)
        self.assertIn('"http"', source)
        self.assertIn('"panel_custom"', source)
        self.assertIn('"homeassistant": "2026.6.4"', hacs_source)

    def test_app_panel_config_includes_backend_readiness_values(self) -> None:
        source = APP_API_PATH.read_text(encoding="utf-8")

        self.assertIn('"version": INTEGRATION_VERSION', source)
        self.assertIn('"entries": [', source)
        self.assertIn('"entry_id": entry.entry_id', source)
        self.assertIn('"state": str(getattr(entry, "state", "unknown"))', source)

    def test_backend_managed_device_update_service_remains_available(self) -> None:
        init_source = INIT_PATH.read_text(encoding="utf-8")
        services_source = SERVICES_PATH.read_text(encoding="utf-8")

        self.assertIn("update_managed_device", init_source)
        self.assertIn("remove_managed_device", init_source)
        self.assertIn("update_managed_device:", services_source)
        self.assertIn("remove_managed_device:", services_source)
        self.assertIn("The original Home Assistant device and entity are left untouched", services_source)

    def test_native_remove_device_hook_is_backend_only(self) -> None:
        init_source = INIT_PATH.read_text(encoding="utf-8")

        self.assertIn("async_remove_config_entry_device", init_source)
        self.assertIn("supports_remove_device", init_source)
        self.assertIn("original/source", init_source)
        self.assertIn("Home Assistant device and entity untouched", init_source)
        self.assertNotIn("custom overflow", init_source.lower())


if __name__ == "__main__":
    unittest.main()
