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
        self.assertIn("Zero Net Export app-visible entities", source)
        self.assertIn("data-section=\"${this._escape(id)}\"", source)
        self.assertIn("Overview", source)
        self.assertIn("Sources", source)
        self.assertIn("Managed Devices", source)
        self.assertIn("Controls", source)
        self.assertIn("Runtime", source)
        self.assertIn("Diagnostics", source)

    def test_app_reads_real_backend_entities_for_workflow_sections(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("sensor.zero_net_export_status", source)
        self.assertIn("binary_sensor.zero_net_export_safe_mode", source)
        self.assertIn("sensor.zero_net_export_source_blocker_summary", source)
        self.assertIn("sensor.managed_devices_overview", source)
        self.assertIn("switch.zero_net_export_enabled", source)
        self.assertIn("select.zero_net_export_mode", source)
        self.assertIn("number.zero_net_export_target_export", source)
        self.assertIn("sensor.zero_net_export_installed_version", source)

    def test_app_exposes_safe_edit_actions_through_home_assistant_services(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn('callService("switch"', source)
        self.assertIn('callService("select"', source)
        self.assertIn('callService("number"', source)
        self.assertIn('callService("zero_net_export", "update_managed_device"', source)
        self.assertIn('callService("zero_net_export", "remove_managed_device"', source)
        self.assertIn('callService("zero_net_export", "update_source_roles"', source)
        self.assertIn("REMOVE FROM ZNE", source)
        self.assertIn("The original Home Assistant entity is left untouched", source)

    def test_sources_app_workflow_lists_roles_and_preserves_values_before_save(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn('key: "solar_power_entity", label: "Solar power", required: true', source)
        self.assertIn('key: "grid_export_energy_entity", label: "Grid export energy", required: true', source)
        self.assertIn('key: "battery_discharge_power_entity", label: "Battery discharge power", required: false', source)
        self.assertIn("data-zne-source-role", source)
        self.assertIn("data-zne-source-original", source)
        self.assertIn('data-zne-action="update-source-roles"', source)
        self.assertIn("Source saves are scoped to the selected Zero Net Export plan.", source)
        self.assertIn("Source-role save requested", source)
        self.assertIn("if (value || original || value !== original)", source)

        values_capture = source.index("const sourceRoleValues =")
        busy_render = source.index("this._busy = true;")
        self.assertLess(values_capture, busy_render)

    def test_sources_app_workflow_shows_binding_health_and_wrapping_layout(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("_sourceState(role, suffix, suffixName)", source)
        self.assertIn('"binding_label"', source)
        self.assertIn("Reading:", source)
        self.assertIn("Issues:", source)
        self.assertIn(".zne-source-editor", source)
        self.assertIn("grid-template-columns: minmax(150px, 0.35fr) minmax(0, 1fr);", source)
        self.assertIn(".zne-source-detail input", source)

    def test_app_captures_managed_device_form_values_before_busy_render(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        key_capture = source.index("const managedDeviceKey =")
        confirm_capture = source.index("const managedConfirm =")
        busy_render = source.index("this._busy = true;")

        self.assertLess(key_capture, busy_render)
        self.assertLess(confirm_capture, busy_render)
        self.assertIn("device_key: managedDeviceKey", source)
        self.assertIn('if (managedConfirm !== "REMOVE FROM ZNE")', source)

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

        self.assertIn('"version": "0.2.6"', source)
        self.assertIn('"frontend"', source)
        self.assertIn('"http"', source)
        self.assertIn('"panel_custom"', source)
        self.assertIn('"homeassistant": "2026.6.4"', hacs_source)

    def test_managed_devices_summary_rows_allow_long_live_values(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("grid-template-columns: minmax(88px, 0.35fr) minmax(0, 1fr);", source)
        self.assertIn("overflow-wrap: anywhere;", source)
        self.assertIn("white-space: normal;", source)
        self.assertIn(".zne-row > strong", source)
        self.assertIn(".zne-row, .zne-source {\n            grid-template-columns: minmax(0, 1fr);", source)

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

    def test_backend_source_role_update_service_is_supported_and_scoped(self) -> None:
        init_source = INIT_PATH.read_text(encoding="utf-8")
        services_source = SERVICES_PATH.read_text(encoding="utf-8")

        self.assertIn("UPDATE_SOURCE_ROLES_SCHEMA", init_source)
        self.assertIn("_async_update_source_roles_from_app", init_source)
        self.assertIn("update_source_roles", init_source)
        self.assertIn("validate_configured_entities", init_source)
        self.assertIn("async_update_entry(entry, data=merged_data, options=merged_options)", init_source)
        self.assertIn("await hass.config_entries.async_reload(entry.entry_id)", init_source)
        self.assertIn("update_source_roles:", services_source)
        self.assertIn("solar_power_entity:", services_source)
        self.assertIn("battery_discharge_power_entity:", services_source)

    def test_native_remove_device_hook_is_backend_only(self) -> None:
        init_source = INIT_PATH.read_text(encoding="utf-8")

        self.assertIn("async_remove_config_entry_device", init_source)
        self.assertIn("supports_remove_device", init_source)
        self.assertIn("original/source", init_source)
        self.assertIn("Home Assistant device and entity untouched", init_source)
        self.assertNotIn("custom overflow", init_source.lower())


if __name__ == "__main__":
    unittest.main()
