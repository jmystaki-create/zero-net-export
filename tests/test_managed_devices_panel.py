from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_PANEL_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "frontend" / "zero-net-export-app.js"
INIT_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "__init__.py"
CONST_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "const.py"
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

    def test_managed_devices_panel_surfaces_unmanaged_candidate_queue(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("candidate_devices", source)
        self.assertIn("Unmanaged Candidate Queue", source)
        self.assertIn("candidate_count", source)
        self.assertIn("review_needed_count", source)
        self.assertIn("ready_candidate_count", source)
        self.assertIn("fixed_candidate_count", source)
        self.assertIn("variable_candidate_count", source)
        self.assertIn("zne-candidate-table", source)
        self.assertIn("zne-candidate-header", source)
        self.assertIn("zne-candidate-row", source)
        self.assertIn("candidate.needs_review", source)
        self.assertIn("candidate.warning_summary", source)
        self.assertIn("candidate.fit_confidence", source)

    def test_managed_devices_panel_promotes_unmanaged_candidates_from_app(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("_promoteCandidateId", source)
        self.assertIn("_promotionDraft = {}", source)
        self.assertIn("_promoteConfirmed = false", source)
        self.assertIn("_candidatePromotionPanel(candidate)", source)
        self.assertIn("_capturePromotionDraft()", source)
        self.assertIn("_resetPromotionDraft()", source)
        self.assertIn('data-zne-action="candidate-review"', source)
        self.assertIn("Review &amp; promote", source)
        self.assertIn("Promote to fleet", source)
        self.assertIn('data-zne-action="promote-candidate"', source)
        self.assertIn("data-zne-promotion-panel", source)
        self.assertIn('tabindex="-1"', source)
        self.assertIn('panel.scrollIntoView({ block: "start", behavior: "smooth" });', source)
        self.assertIn('candidate.entity_id === this._promoteCandidateId ? "Reviewing" : "Review &amp; promote"', source)
        self.assertIn(".zne-candidate-row.selected", source)
        self.assertIn("[data-zne-promote-field]", source)
        self.assertIn("[data-zne-promote-confirm]", source)
        self.assertIn('event.target.closest("[data-zne-promote-field]")', source)
        self.assertIn('event.target.closest("[data-zne-promote-confirm]")', source)
        self.assertIn('const defaults = { ...this._candidatePromotionDefaults(candidate), ...this._promotionDraft };', source)
        self.assertIn('${this._promoteConfirmed ? "checked" : ""}', source)
        self.assertIn("const promoteValues = this._capturePromotionDraft();", source)
        self.assertIn("const promoteConfirmed = this._promoteConfirmed;", source)
        self.assertIn('callService("zero_net_export", "promote_managed_device"', source)
        self.assertIn("candidate_entity_id: promoteCandidateId", source)
        self.assertIn("confirm: true", source)
        self.assertIn("The original Home Assistant device/entity will not be modified", source)

        self.assertLess(
            source.index("${this._candidatePromotionPanel(promotionCandidate)}"),
            source.index('<div class="zne-candidate-table">'),
        )

    def test_managed_devices_panel_orders_managed_fleet_before_unmanaged_queue(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertLess(source.index("<!-- Fleet Table -->"), source.index("<!-- Unmanaged Candidate Queue -->"))
        self.assertLess(source.index("Fleet List (${filtered.length} devices)"), source.index("Unmanaged Candidate Queue"))

    def test_managed_devices_fleet_summary_uses_compact_spaced_stats(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("zne-fleet-stats zne-fleet-summary-stats", source)
        self.assertIn(".zne-fleet-summary-stats", source)
        self.assertIn("grid-template-columns: repeat(auto-fit, minmax(92px, 1fr));", source)
        self.assertIn(".zne-stat strong", source)
        self.assertIn("margin-right: 4px;", source)

    def test_managed_devices_panel_sorts_numeric_priorities_after_promotion(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("const prioritySortValue = (priority) => {", source)
        self.assertIn("Number.isFinite(Number(priority))", source)
        self.assertIn("return Number(priority);", source)
        self.assertIn("valA = prioritySortValue(a.priority);", source)
        self.assertIn("valB = prioritySortValue(b.priority);", source)
        self.assertNotIn("(a.priority || \"\").toLowerCase()", source)
        self.assertNotIn("(b.priority || \"\").toLowerCase()", source)

    def test_managed_devices_panel_shows_on_off_traffic_light_per_fleet_row(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("_deviceActivityIndicator(device)", source)
        self.assertIn('device.observed_active === true || device.observed_active === "true"', source)
        self.assertIn('const label = active ? "On" : "Off";', source)
        self.assertIn('const tone = active ? "on" : "off";', source)
        self.assertIn("<span>Power</span>", source)
        self.assertIn("${this._deviceActivityIndicator(d)}", source)
        self.assertIn(".zne-traffic-light.on", source)
        self.assertIn(".zne-traffic-light.off", source)
        self.assertIn("Device is currently", source)

    def test_app_exposes_safe_edit_actions_through_home_assistant_services(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn('callService("switch"', source)
        self.assertIn('callService("select"', source)
        self.assertIn('callService("number"', source)
        self.assertIn('callService("zero_net_export", "update_managed_device"', source)
        self.assertIn('callService("zero_net_export", "remove_managed_device"', source)
        self.assertIn('callService("zero_net_export", "update_source_roles"', source)
        self.assertIn('callService("zero_net_export", "pause_executor"', source)
        self.assertIn('callService("zero_net_export", "resume_executor"', source)
        self.assertIn('callService("zero_net_export", "export_diagnostics"', source)
        self.assertIn('callService("zero_net_export", "repair_issue"', source)
        self.assertIn("REMOVE FROM ZNE", source)
        self.assertIn("The original Home Assistant entity is left untouched", source)

    def test_app_exposes_and_uses_selected_plan_context(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("this._selectedEntryIdValue", source)
        self.assertIn("Selected plan context", source)
        self.assertIn("_entryServiceData()", source)
        self.assertIn('throw new Error("Select a Zero Net Export plan first.")', source)
        self.assertIn("select.dataset.zneEntryId", source)
        self.assertIn("...this._entryServiceData()", source)
        self.assertIn("Plan context selected.", source)

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
        self.assertIn("_sourceEntitySlug(role)", source)
        self.assertIn('battery_soc_entity: "battery_state_of_charge"', source)
        self.assertIn('"binding_label"', source)
        self.assertIn("Reading:", source)
        self.assertIn("Issues:", source)
        self.assertIn(".zne-source-editor", source)
        self.assertIn("grid-template-columns: minmax(150px, 0.35fr) minmax(0, 1fr);", source)
        self.assertIn(".zne-source-detail input", source)

    def test_overview_reconciliation_console_uses_live_runtime_metrics(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("this._realtimeTimer = window.setInterval(() => this._render(), 10000)", source)
        self.assertIn("window.clearInterval(this._realtimeTimer)", source)
        self.assertIn("_reconciliationMetrics()", source)
        self.assertIn('"sensor.zero_net_export_home_load_power_w"', source)
        self.assertIn('"sensor.zero_net_export_solar_power_w"', source)
        self.assertIn('"sensor.zero_net_export_battery_charge_power_w"', source)
        self.assertIn('"sensor.zero_net_export_battery_discharge_power_w"', source)
        self.assertIn('"sensor.zero_net_export_surplus_w"', source)
        self.assertIn('"sensor.zero_net_export_last_reconciliation_error_w"', source)
        self.assertIn('"sensor.zero_net_export_confidence"', source)
        self.assertIn("const batteryPower = hasBatteryPower ? dischargeValue - chargeValue : undefined", source)
        self.assertIn("Source Power", source)
        self.assertIn("Battery Power", source)
        self.assertIn("Confidence", source)
        self.assertIn("Last update", source)
        self.assertIn("zne-metric-value", source)
        self.assertIn("zne-metric-updated", source)
        self.assertIn("zne-metric-detail", source)
        self.assertIn("text-align: left;", source)
        self.assertIn("Source blocker:", source)
        self.assertIn("Stale source:", source)

    def test_overview_readiness_console_explains_errors_and_resolution_steps(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("_readinessModel(status, safeMode, sourceMismatch)", source)
        self.assertIn("_readinessItemTemplate(item)", source)
        self.assertIn("zne-readiness-card", source)
        self.assertIn("zne-readiness-summary", source)
        self.assertIn("zne-readiness-item", source)
        self.assertIn("_managedDeviceQueueFacts", source)
        self.assertIn("What is wrong", source)
        self.assertIn("How to resolve", source)
        self.assertIn("Do this first", source)
        self.assertIn("Fix source health first", source)
        self.assertIn("unmanaged candidates are waiting", source)
        self.assertIn("sensor.zero_net_export_command_center_status", source)
        self.assertIn("sensor.zero_net_export_command_center_next_step", source)
        self.assertIn("sensor.zero_net_export_source_blocker_summary", source)
        self.assertIn("sensor.zero_net_export_stale_source_summary", source)
        self.assertIn("sensor.zero_net_export_control_guard_summary", source)
        self.assertIn("Source blockers", source)
        self.assertIn("Reconcile power balance", source)
        self.assertIn("Review managed-device queue", source)
        self.assertIn("_isBlockingPolicyReadiness(value)", source)
        self.assertIn("actionable now", source)

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

        self.assertIn('"version": "0.4.16"', source)
        self.assertIn('"frontend"', source)
        self.assertIn('"http"', source)
        self.assertIn('"panel_custom"', source)
        self.assertIn('"homeassistant": "2026.6.4"', hacs_source)

    def test_app_module_url_is_version_cache_busted(self) -> None:
        source = CONST_PATH.read_text(encoding="utf-8")

        self.assertIn("APP_MODULE_URL", source)
        self.assertIn("?v={INTEGRATION_VERSION}", source)

    def test_app_custom_element_registration_is_idempotent(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn('customElements.get("zero-net-export-app")', source)
        self.assertIn('customElements.define("zero-net-export-app"', source)

    def test_managed_devices_summary_rows_allow_long_live_values(self) -> None:
        source = APP_PANEL_PATH.read_text(encoding="utf-8")

        self.assertIn("grid-template-columns: minmax(88px, 0.35fr) minmax(0, 1fr);", source)
        self.assertIn("overflow-wrap: anywhere;", source)
        self.assertIn("line-height: 1.35;", source)
        self.assertIn(".zne-row > strong", source)
        self.assertIn("display: block;", source)
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
        self.assertIn("promote_managed_device", init_source)
        self.assertIn("PROMOTE_MANAGED_DEVICE_SCHEMA", init_source)
        self.assertIn("SERVICE_FLOAT = vol.Coerce(float)", init_source)
        self.assertIn("SERVICE_INT = vol.Coerce(int)", init_source)
        self.assertIn("_async_promote_managed_device_from_candidate", init_source)
        self.assertIn("discover_candidate_devices(hass.states.async_all(), managed_entity_ids)", init_source)
        self.assertIn("Candidate '{candidate_entity_id}' is already managed", init_source)
        self.assertIn("Candidate '{candidate_entity_id}' is not currently available for promotion", init_source)
        self.assertIn("This created a ZNE managed-load record and child device", init_source)
        self.assertIn("update_managed_device:", services_source)
        self.assertIn("remove_managed_device:", services_source)
        self.assertIn("promote_managed_device:", services_source)
        self.assertIn("candidate_entity_id:", services_source)
        self.assertIn("Confirm promotion", services_source)
        self.assertIn("The original Home Assistant device and entity are left untouched", services_source)

    def test_managed_device_service_schemas_accept_ui_number_payloads(self) -> None:
        init_source = INIT_PATH.read_text(encoding="utf-8")

        self.assertIn('vol.Optional("priority"): SERVICE_INT', init_source)
        self.assertIn('vol.Optional("nominal_power_w"): SERVICE_FLOAT', init_source)
        self.assertIn('vol.Optional("min_power_w"): SERVICE_FLOAT', init_source)
        self.assertIn('vol.Optional("max_power_w"): SERVICE_FLOAT', init_source)
        self.assertIn('vol.Optional("step_w"): SERVICE_FLOAT', init_source)
        self.assertIn('vol.Optional("min_on_seconds"): SERVICE_INT', init_source)
        self.assertIn('vol.Optional("min_off_seconds"): SERVICE_INT', init_source)
        self.assertIn('vol.Optional("cooldown_seconds"): SERVICE_INT', init_source)
        self.assertIn('vol.Optional("max_active_seconds"): SERVICE_INT', init_source)
        self.assertNotIn('vol.Optional("nominal_power_w"): float', init_source)
        self.assertNotIn('vol.Optional("priority"): int', init_source)

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

    def test_backend_entry_scoped_services_fail_ambiguous_multi_entry_calls(self) -> None:
        init_source = INIT_PATH.read_text(encoding="utf-8")
        services_source = SERVICES_PATH.read_text(encoding="utf-8")

        self.assertIn("def _entry_from_service_call", init_source)
        self.assertIn('len(entries) > 1', init_source)
        self.assertIn('raise ValueError("Set entry_id when more than one Zero Net Export plan is configured")', init_source)
        self.assertIn("def _coordinator_from_service_call", init_source)
        self.assertIn('("pause_executor", _handle_pause_executor, ENTRY_SCOPED_SERVICE_SCHEMA)', init_source)
        self.assertIn("hass.services.async_register(DOMAIN, service_name, handler, schema=schema)", init_source)
        self.assertIn('"pause_executor"', init_source)
        self.assertIn('"resume_executor"', init_source)
        self.assertIn('"export_diagnostics"', init_source)
        self.assertIn('"repair_issue"', init_source)
        self.assertIn("pause_executor:", services_source)
        self.assertIn("resume_executor:", services_source)
        self.assertIn("repair_issue:", services_source)

    def test_native_remove_device_hook_is_backend_only(self) -> None:
        init_source = INIT_PATH.read_text(encoding="utf-8")

        self.assertIn("async_remove_config_entry_device", init_source)
        self.assertIn("supports_remove_device", init_source)
        self.assertIn("original/source", init_source)
        self.assertIn("Home Assistant device and entity untouched", init_source)
        self.assertNotIn("custom overflow", init_source.lower())


if __name__ == "__main__":
    unittest.main()
