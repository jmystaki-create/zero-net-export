from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "frontend" / "managed-devices-panel.js"
INIT_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "__init__.py"
MANIFEST_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "manifest.json"


class ManagedDevicesPanelTests(unittest.TestCase):
    def test_panel_renders_right_side_gear_and_inline_editor(self) -> None:
        source = PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("grid-template-columns:1fr auto", source)
        self.assertIn("class=\"gear\"", source)
        self.assertIn("data-gear", source)
        self.assertIn("managedSurfaces", source)
        self.assertIn("const byKey = new Map()", source)
        self.assertIn("const stableKey = `${device.entry_id || entryId}:${deviceKey}`", source)
        self.assertIn("config_entry_id", source)
        self.assertIn("entry_id: root.dataset.entryId", source)
        self.assertIn("device_key: root.dataset.deviceKey", source)
        self.assertIn("data-device-key", source)
        self.assertIn("const editKey = `${entryId}:${key}`", source)
        self.assertIn("applyDeepLink(devices)", source)
        self.assertIn("new URLSearchParams(window.location.search).get('managed_device')", source)
        self.assertIn("`${entryId}:${key}` === requested", source)
        self.assertIn('data-save="${this.escapeAttr(editKey)}"', source)
        self.assertIn("Edit ${this.escapeAttr(device.name || key)} settings", source)
        self.assertIn("Save settings", source)
        self.assertIn("update_managed_device", source)

    def test_integration_registers_panel_static_assets_and_service(self) -> None:
        source = INIT_PATH.read_text(encoding="utf-8")

        self.assertIn("PANEL_URL_PATH = \"zero-net-export-managed-devices\"", source)
        self.assertIn("StaticPathConfig", source)
        self.assertIn("async_register_panel", source)
        self.assertIn("sidebar_title=\"ZNE Managed Devices\"", source)
        self.assertIn("update_managed_device", source)
        self.assertIn('vol.Optional("entry_id"): str', source)
        self.assertIn("candidate.entry_id == requested_entry_id", source)
        self.assertIn("async_update_entry(entry, options=merged_options)", source)
        self.assertIn("async_reload(entry.entry_id)", source)

    def test_manifest_loads_frontend_panel_dependencies(self) -> None:
        source = MANIFEST_PATH.read_text(encoding="utf-8")

        self.assertIn('"frontend"', source)
        self.assertIn('"http"', source)
        self.assertIn('"panel_custom"', source)


if __name__ == "__main__":
    unittest.main()
