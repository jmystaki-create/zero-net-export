import json
from pathlib import Path
import unittest


class TestBucketOwnershipCopy(unittest.TestCase):
    def test_bucket_ownership_and_workspace_split_stay_visible(self):
        integration_root = Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export"
        with (integration_root / "strings.json").open(encoding="utf-8") as handle:
            strings = json.load(handle)

        bootstrap = strings["config"]["step"]["user"]
        self.assertIn(
            "finish Sensors/source roles, Managed Devices onboarding, Controls policy/live mode, and Diagnostics",
            bootstrap["description"],
        )
        self.assertIn("until required source roles and managed devices are ready", bootstrap["description"])
        self.assertIn(
            "continue in Configure for Sensors/source roles, Managed Devices onboarding, Controls policy/live mode, and Diagnostics",
            bootstrap["data_description"]["name"],
        )
        self.assertNotIn("Controls tuning", bootstrap["description"])
        self.assertNotIn("Controls tuning", bootstrap["data_description"]["name"])
        self.assertNotIn("until you map sources and add devices", bootstrap["description"])
        self.assertNotIn("finish setup from Settings", bootstrap["description"])
        self.assertNotIn("finish source mapping, refresh tuning, and device onboarding", bootstrap["data_description"]["name"])

        steps = strings["options"]["step"]

        init_description = steps["init"]["description"]
        self.assertTrue(init_description.startswith("Now\n- Headline decision:"))
        self.assertIn("\n\nCommand-center use\n- Live setup and current operating picture.", init_description)
        self.assertIn("when fleet work is next, continue in the Managed Devices workspace.", init_description)
        self.assertNotIn("Use this command center for the basic setup and current operating picture only.", init_description)
        self.assertLess(init_description.index("Now\n- Headline decision:"), init_description.index("\n\nStructured control board"))
        self.assertLess(init_description.index("\n\nStructured control board"), init_description.index("\n\nCommand-center use"))
        self.assertIn("\n\nNative paths\n- Sensors: {sources_path}", init_description)
        self.assertIn("- Controls: {policy_path}\n- Live mode shortcut (Controls device action): {mode_path}", init_description)
        self.assertIn("- Managed Devices: {devices_path}", init_description)
        self.assertIn("- Diagnostics: {support_path}", init_description)
        self.assertIn("- Recommended section: {recommended_section}", init_description)
        self.assertNotIn("{recommended_menu_hint}", init_description)
        self.assertNotIn("The first menu item below", init_description)
        self.assertIn("\n\nBucket ownership\n- Sensors owns source roles and source health.", init_description)
        self.assertIn("Sensors owns source roles and source health.", init_description)
        self.assertNotIn("Finish source mapping and core control checks", init_description)
        self.assertNotIn("Sensors owns source mapping and source health.", init_description)
        self.assertIn("Managed Devices owns fleet onboarding, promotion, edits, enablement, and removal: {devices_path}", init_description)

        native_setup_description = steps["native_setup"]["description"]
        self.assertIn(
            "Sensors is the source-role and source-health home for the Zero Net Export command center.",
            native_setup_description,
        )
        self.assertNotIn("source-mapping and source-health home", native_setup_description)
        self.assertNotIn("Use this Sensors screen", native_setup_description)
        self.assertNotIn("Use this Sensors workspace", native_setup_description)
        self.assertIn("Managed-device promotion stays in the Managed Devices workspace; target export, reserve, deadband, and live mode stay in Controls.", native_setup_description)
        self.assertNotIn("Managed-device promotion stays in Managed Devices; target export, reserve, deadband, and live mode stay in Controls.", native_setup_description)
        self.assertNotIn("This is the source-mapping section of the Zero Net Export command center.", native_setup_description)
        self.assertNotIn("controller-policy tuning", native_setup_description)
        self.assertIn("Source status now", native_setup_description)
        self.assertIn("Source-role setup progress", native_setup_description)
        self.assertNotIn("Source mapping progress", native_setup_description)
        self.assertIn("- Required source roles mapped: {source_mapping_progress}", native_setup_description)
        self.assertNotIn("- Required roles mapped:", native_setup_description)
        self.assertIn("- Blocking source issues: {source_blocker_summary}", native_setup_description)
        self.assertNotIn("Sensors now", native_setup_description)
        self.assertIn("Bucket ownership and paths", native_setup_description)
        self.assertIn("- Sensors: {sources_path}", native_setup_description)
        self.assertIn("- Controls: {policy_path}\n- Live mode shortcut (Controls device action): {mode_path}", native_setup_description)
        self.assertIn("- Managed Devices: {devices_path}", native_setup_description)
        self.assertIn("- Diagnostics: {support_path}", native_setup_description)

        source_mapping_step = steps["native_setup_sources"]
        self.assertEqual(source_mapping_step["title"], "Sensors")
        source_mapping_description = source_mapping_step["description"]
        self.assertIn("Sensors owns required source roles for the current source layout.", source_mapping_description)
        self.assertNotIn("Sensors maps the required entities", source_mapping_description)
        self.assertNotIn("Use this Sensors screen", source_mapping_description)
        self.assertNotIn("Use this Sensors workspace", source_mapping_description)
        self.assertNotIn("set the refresh interval", source_mapping_description)
        self.assertIn("Sensors owns source repair and source-health work", source_mapping_description)
        self.assertIn("fleet onboarding stays in the Managed Devices workspace, and target export, reserve, deadband, and live mode stay in Controls", source_mapping_description)
        self.assertNotIn("fleet onboarding stays in Managed Devices, and target export, reserve, deadband, and live mode stay in Controls", source_mapping_description)
        self.assertNotIn("controller tuning in Controls", source_mapping_description)
        self.assertIn("Source-role setup progress", source_mapping_description)
        self.assertNotIn("Source mapping progress", source_mapping_description)
        self.assertIn("- Required source roles mapped: {source_mapping_progress}", source_mapping_description)
        self.assertNotIn("- Required roles mapped:", source_mapping_description)
        self.assertIn("- Blocking source issues: {source_blocker_summary}", source_mapping_description)
        self.assertIn("Use the native selectors first. Only drop to the fallback fields if Home Assistant rejects a valid choice.", source_mapping_description)
        self.assertNotIn("If Combined / net grid energy or Battery state of charge still triggers", source_mapping_description)
        self.assertNotIn("Source map now", source_mapping_description)
        self.assertNotIn("Sensors now", source_mapping_description)
        self.assertIn("Blocking source repair", source_mapping_description)
        self.assertIn("- Source repair path: {source_repair_step}", source_mapping_description)
        self.assertNotIn("Mapped-source repair path", source_mapping_description)
        self.assertIn("Live candidate cues for the current blocker:", source_mapping_description)
        self.assertIn("Current source map, for cross-check only:\n{source_mapping_summary}", source_mapping_description)
        self.assertNotIn("Other live candidates, only if the blocker persists:", source_mapping_description)
        self.assertIn("Fallback, only if Home Assistant rejects a valid choice:\n{fallback_guidance}", source_mapping_description)
        self.assertIn("Bucket ownership and paths", source_mapping_description)
        self.assertIn("- Sensors: {sources_path}", source_mapping_description)
        self.assertIn("- Controls: {policy_path}\n- Live mode shortcut (Controls device action): {mode_path}", source_mapping_description)
        self.assertIn("- Managed Devices: {devices_path}", source_mapping_description)
        self.assertIn("- Diagnostics: {support_path}", source_mapping_description)
        self.assertNotIn("refresh_seconds", source_mapping_step["data"])
        self.assertNotIn("refresh_seconds", source_mapping_step["data_description"])
        source_mapping_data_description = source_mapping_step["data_description"]
        self.assertNotIn("known entity/UUID validation bug", source_mapping_data_description["grid_energy_entity"])
        self.assertNotIn("entity/UUID validation bug", source_mapping_data_description["battery_soc_entity"])
        self.assertIn(
            "combined-grid energy source role",
            source_mapping_data_description["grid_energy_entity"],
        )
        self.assertIn(
            "battery reserve source health",
            source_mapping_data_description["battery_soc_entity"],
        )
        self.assertNotIn("native dropdown", source_mapping_data_description["grid_energy_entity"])
        self.assertNotIn("native dropdown", source_mapping_data_description["battery_soc_entity"])
        self.assertNotIn("selector validation", source_mapping_data_description["grid_energy_entity"])
        self.assertNotIn("selector validation", source_mapping_data_description["battery_soc_entity"])
        self.assertIn(
            "paste the same energy entity ID into this fallback field",
            source_mapping_data_description["grid_energy_entity_manual"],
        )
        self.assertIn(
            "paste the same battery SOC entity ID into this fallback field",
            source_mapping_data_description["battery_soc_entity_manual"],
        )
        self.assertNotIn("paste the same energy entity ID here", source_mapping_data_description["grid_energy_entity_manual"])
        self.assertNotIn("paste the same battery SOC entity ID here", source_mapping_data_description["battery_soc_entity_manual"])

        validation_checklist = (
            Path(__file__).resolve().parents[1] / "docs" / "VALIDATION_CHECKLIST.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Selector fallback validation", validation_checklist)
        self.assertIn("selector validation rejects a valid", validation_checklist)
        self.assertNotIn("combined-grid energy role selectable", source_mapping_data_description["grid_energy_entity"])
        self.assertNotIn("battery reserve setup usable", source_mapping_data_description["battery_soc_entity"])
        self.assertNotIn("combined-grid energy mapping still works", source_mapping_data_description["grid_energy_entity"])
        self.assertNotIn("Home Assistant's entity picker", source_mapping_data_description["grid_energy_entity"])
        self.assertNotIn("Home Assistant's entity picker", source_mapping_data_description["battery_soc_entity"])
        self.assertNotIn("Known deferred bug tracked", validation_checklist)
        self.assertNotIn("known HA field-level entity/UUID error", validation_checklist)
        self.assertNotIn("Entity is neither a valid entity ID nor a valid UUID", validation_checklist)

        coordinator_source = (integration_root / "coordinator.py").read_text(encoding="utf-8")
        config_flow_source = (integration_root / "config_flow.py").read_text(encoding="utf-8")
        native_support_source = (integration_root / "native_support.py").read_text(encoding="utf-8")
        self.assertNotIn("No required mapped sources currently look stale", coordinator_source)
        self.assertIn("No required source roles currently look stale", coordinator_source)
        self.assertNotIn("unavailable mapped role", config_flow_source)
        self.assertNotIn("stale mapped role", config_flow_source)
        self.assertNotIn("native dropdowns to reduce Home Assistant selector validation failures", config_flow_source)
        self.assertNotIn("Source mapping still has blocking validation errors", config_flow_source)
        self.assertIn("Source roles still have blocking validation errors", config_flow_source)
        self.assertIn("Fallback fields are only for valid Combined / net grid energy", config_flow_source)
        self.assertNotIn("Current mapping:", config_flow_source)
        self.assertNotIn("return here to review enablement", config_flow_source)
        self.assertNotIn("entity not surfaced here", config_flow_source)
        self.assertIn("return to the Managed Devices workspace to review enablement", config_flow_source)
        self.assertIn("entity not surfaced in the shortlist", config_flow_source)
        self.assertNotIn("required mapped roles are complete", native_support_source)
        self.assertNotIn("repair these highlighted mapped roles first", native_support_source)
        self.assertNotIn("review the mapped sources", native_support_source)
        self.assertNotIn("Finish source mapping first", native_support_source)
        self.assertNotIn("live source mapping and health", native_support_source)
        self.assertNotIn("Required source mapping complete", native_support_source)
        self.assertNotIn("Sources are mapped and managed devices exist", native_support_source)
        self.assertIn("required source roles are complete", native_support_source)
        self.assertIn("repair these highlighted source roles first", native_support_source)
        self.assertIn("review the source map", native_support_source)
        self.assertIn("Finish required source roles first", native_support_source)
        self.assertIn("live source roles and health", native_support_source)
        self.assertIn("Required source roles complete", native_support_source)
        self.assertIn("Source roles are complete and managed devices exist", native_support_source)
        self.assertNotIn("Save source mapping", config_flow_source)
        self.assertNotIn("Finish source mapping first", config_flow_source)
        self.assertNotIn("Sources are mapped and", config_flow_source)
        self.assertIn("Save the required source roles", config_flow_source)
        self.assertIn("Finish required source roles first", config_flow_source)
        self.assertIn("Source roles are complete and", config_flow_source)

        devices_description = steps["devices"]["description"]
        self.assertIn("Managed Devices is the native fleet workspace.", devices_description)
        self.assertIn("Managed devices stay on top, and the unmanaged promotion backlog stays below.", devices_description)
        self.assertNotIn("This is the Managed Devices workspace.", devices_description)
        self.assertNotIn("This is the main Managed Devices workspace for review, promotion, edits, enablement, disablement, and removal.", devices_description)
        self.assertNotIn("Use JSON only for recovery or bulk changes.", devices_description)
        self.assertNotIn("Use this native Configure screen as the main managed-device workspace.", devices_description)
        self.assertIn("Managed devices (top section)", devices_description)
        self.assertIn("Managed devices review:", devices_description)
        self.assertNotIn("Current managed fleet:", devices_description)
        self.assertIn("Unmanaged candidates (bottom section)", devices_description)
        self.assertIn("Currently surfaced unmanaged candidate: {top_candidate}", devices_description)
        self.assertNotIn("Top unmanaged candidate right now", devices_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", devices_description)
        self.assertIn("Secondary per-device review/audit path:", devices_description)
        self.assertIn("Managed Devices path: {configure_path}.", devices_description)
        self.assertNotIn("Primary path: {configure_path}.", devices_description)
        self.assertIn("Bucket ownership and paths", devices_description)
        self.assertIn("Managed Devices owns fleet onboarding, promotion, edits, enablement, and removal: {configure_path}", devices_description)
        self.assertIn("- Sensors owns source roles and source repair: {sources_path}", devices_description)
        self.assertNotIn("- Sensors owns source mapping and source repair", devices_description)
        self.assertIn("- Controls owns target export, reserve, deadband, and live mode: {policy_path}", devices_description)
        self.assertIn("- Diagnostics owns troubleshooting, repairs, and install validation: {support_path}", devices_description)

        bulk_enable_description = steps["device_bulk_enable"]["description"]
        self.assertEqual(
            steps["device_bulk_enable"]["title"],
            "Review managed devices workspace and enablement",
        )
        self.assertIn("Review managed-device enablement in the Managed Devices workspace, with managed devices on top and the unmanaged promotion backlog below.", bulk_enable_description)
        self.assertNotIn("Review managed-device enablement here", bulk_enable_description)
        self.assertIn("Keep enablement in the Managed Devices workspace.", bulk_enable_description)
        self.assertNotIn("Configure stays the primary fleet workspace", bulk_enable_description)
        self.assertIn("Keep source repair in Sensors, target export, reserve, deadband, and live mode in Controls, and troubleshooting in Diagnostics.", bulk_enable_description)
        self.assertNotIn("controller tuning in Controls", bulk_enable_description)
        self.assertIn("Managed Devices path: {configure_path}.", bulk_enable_description)
        self.assertNotIn("Primary path: {configure_path}.", bulk_enable_description)
        self.assertNotIn("Managed Devices owns fleet enablement", bulk_enable_description)
        self.assertNotIn("while you work through this workspace", bulk_enable_description)
        self.assertNotIn("while you use this screen", bulk_enable_description)
        self.assertNotIn("Use this native fleet review to temporarily stage larger installs without raw JSON.", bulk_enable_description)
        self.assertIn("Managed devices (top section)", bulk_enable_description)
        self.assertIn("Managed Devices: {device_count}", bulk_enable_description)
        self.assertIn("Managed devices review:", bulk_enable_description)
        self.assertNotIn("Current managed fleet:", bulk_enable_description)
        self.assertIn("Unmanaged candidates (bottom section)", bulk_enable_description)
        self.assertIn("Unmanaged candidate devices: {candidate_count}", bulk_enable_description)
        self.assertIn("Fixed-load candidates surfaced for review: {fixed_candidate_count}", bulk_enable_description)
        self.assertIn("{fixed_candidate_summary}", bulk_enable_description)
        self.assertIn("Variable-load candidates surfaced for review: {variable_candidate_count}", bulk_enable_description)
        self.assertIn("{variable_candidate_summary}", bulk_enable_description)
        self.assertIn("Currently surfaced unmanaged candidate: {top_candidate}", bulk_enable_description)
        self.assertNotIn("Top unmanaged candidate right now", bulk_enable_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", bulk_enable_description)
        self.assertIn("Candidate snapshot", bulk_enable_description)
        self.assertIn("Secondary per-device review/audit path:", bulk_enable_description)
        self.assertIn("Bucket ownership and paths", bulk_enable_description)
        self.assertIn("- Managed Devices: {configure_path}", bulk_enable_description)
        self.assertIn("- Sensors: {sources_path}", bulk_enable_description)
        self.assertIn("- Controls: {policy_path}", bulk_enable_description)
        self.assertIn("- Diagnostics: {support_path}", bulk_enable_description)
        self.assertIn(
            "promote a surfaced fixed-load or variable-load candidate when one fits",
            steps["devices"]["data_description"]["device_action"],
        )
        self.assertIn(
            "add a device manually when no surfaced candidate is right",
            steps["devices"]["data_description"]["device_action"],
        )
        self.assertIn(
            "open the Managed Devices workspace to review enablement, edit device settings, or remove a device from the fleet",
            steps["devices"]["data_description"]["device_action"],
        )
        self.assertIn(
            "use the advanced JSON editor only for recovery or bulk managed-device repair",
            steps["devices"]["data_description"]["device_action"],
        )
        self.assertIn(
            "Paste a JSON array of controllable devices into this recovery field",
            steps["devices_json"]["data_description"]["device_inventory_json"],
        )
        self.assertNotIn(
            "Paste a JSON array of controllable devices here",
            steps["devices_json"]["data_description"]["device_inventory_json"],
        )
        self.assertNotIn(
            "toggle which devices stay enabled, edit an existing device, remove a device",
            steps["devices"]["data_description"]["device_action"],
        )
        self.assertNotIn(
            "or open the advanced JSON editor.",
            steps["devices"]["data_description"]["device_action"],
        )

        edit_pick_description = steps["device_edit_pick"]["description"]
        self.assertIn("Edit managed-device settings in the Managed Devices workspace, with managed devices on top and the unmanaged promotion backlog below.", edit_pick_description)
        self.assertIn("Keep names, priorities, power limits, cooldowns, and enablement changes in this workspace.", edit_pick_description)
        self.assertNotIn("Choose which managed device to edit here", edit_pick_description)
        self.assertNotIn("Managed Devices owns this fleet-edit workflow.", edit_pick_description)
        self.assertIn("with managed devices on top and the unmanaged promotion backlog below.", edit_pick_description)
        self.assertNotIn("with the managed fleet on top and unmanaged promotion backlog below", edit_pick_description)
        self.assertNotIn("This is the in-place native edit path", edit_pick_description)
        self.assertIn("Managed devices (top section)", edit_pick_description)
        self.assertIn("Managed Devices: {device_count}", edit_pick_description)
        self.assertIn("Managed devices review:", edit_pick_description)
        self.assertNotIn("Current managed fleet:", edit_pick_description)
        self.assertIn("Unmanaged candidates (bottom section)", edit_pick_description)
        self.assertIn("Unmanaged candidate devices: {candidate_count}", edit_pick_description)
        self.assertIn("{fixed_candidate_summary}", edit_pick_description)
        self.assertIn("{variable_candidate_summary}", edit_pick_description)
        self.assertIn("Currently surfaced unmanaged candidate: {top_candidate}", edit_pick_description)
        self.assertNotIn("Top unmanaged candidate right now", edit_pick_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", edit_pick_description)
        self.assertIn("Candidate snapshot", edit_pick_description)
        self.assertIn("Bucket ownership and paths", edit_pick_description)

        remove_description = steps["device_remove"]["description"]
        self.assertIn("Remove a load from the Managed Devices workspace only when it should leave Zero Net Export entirely", remove_description)
        self.assertIn("managed devices stay on top and the unmanaged promotion backlog stays below", remove_description)
        self.assertIn("Disable a load instead when you only need a temporary stop.", remove_description)
        self.assertNotIn("Choose which managed device should leave the native fleet here", remove_description)
        self.assertNotIn("Use this only when a controllable load should leave Zero Net Export entirely", remove_description)
        self.assertNotIn("with the current managed fleet on top and the unmanaged promotion backlog still visible below", remove_description)
        self.assertIn("Managed devices (top section)", remove_description)
        self.assertIn("Managed devices review:", remove_description)
        self.assertNotIn("Current managed fleet:", remove_description)
        self.assertIn("Unmanaged candidates (bottom section)", remove_description)
        self.assertIn("Unmanaged candidate devices: {candidate_count}", remove_description)
        self.assertIn("{fixed_candidate_summary}", remove_description)
        self.assertIn("{variable_candidate_summary}", remove_description)
        self.assertIn("Currently surfaced unmanaged candidate: {top_candidate}", remove_description)
        self.assertNotIn("Top unmanaged candidate right now", remove_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", remove_description)
        self.assertIn("Candidate snapshot", remove_description)
        self.assertIn("Bucket ownership and paths", remove_description)

        self.assertEqual(steps["device_pick_candidate"]["title"], "Promotion shortlist")
        self.assertEqual(steps["device_pick_candidate_full"]["title"], "Promotion full list")
        self.assertEqual(steps["device_vetting"]["title"], "Promotion review")
        self.assertEqual(steps["device_template"]["title"], "Promotion preset")

        shortlist_description = steps["device_pick_candidate"]["description"]
        self.assertIn("Start promotion from the surfaced unmanaged {device_kind} candidates below, with managed devices on top and the unmanaged promotion backlog below.", shortlist_description)
        self.assertNotIn("Stay in the Managed Devices workspace while you choose the next candidate.", shortlist_description)
        self.assertNotIn("Managed Devices owns this promotion entry workflow.", shortlist_description)
        self.assertNotIn("Managed devices stay on top, and unmanaged promotion backlog stays below while you choose the next candidate.", shortlist_description)
        self.assertNotIn("keep the managed fleet visible on top and the unmanaged backlog visible below", shortlist_description)
        self.assertNotIn("Managed Devices owns this promotion entry step.", shortlist_description)

        full_list_description = steps["device_pick_candidate_full"]["description"]
        self.assertIn("Use the full unmanaged list when the shortlist still does not show the right surfaced entity, with managed devices on top and the unmanaged promotion backlog below.", full_list_description)
        self.assertNotIn("Stay in the Managed Devices workspace while you choose the next candidate.", full_list_description)
        self.assertNotIn("Managed Devices owns this full-list workflow.", full_list_description)
        self.assertNotIn("Managed devices stay on top, and unmanaged promotion backlog stays below while you choose the next candidate.", full_list_description)
        self.assertNotIn("keep the managed fleet visible on top and the unmanaged backlog visible below", full_list_description)
        self.assertNotIn("Managed Devices still owns this full-list step.", full_list_description)

        vetting_description = steps["device_vetting"]["description"]
        self.assertIn("Review this unmanaged candidate before it enters the managed fleet; managed devices stay on top and the unmanaged promotion backlog stays below.", vetting_description)
        self.assertNotIn("Review this unmanaged candidate here", vetting_description)
        self.assertNotIn("Stay in the Managed Devices workspace while you vet the candidate.", vetting_description)
        self.assertNotIn("Managed Devices owns this promotion workflow.", vetting_description)
        self.assertNotIn("Managed devices stay on top, and unmanaged promotion backlog stays below while you vet the candidate.", vetting_description)
        self.assertNotIn("keep the managed fleet visible on top and the unmanaged backlog visible below", vetting_description)
        self.assertIn("Managed devices (top section)", vetting_description)
        self.assertIn("Managed Devices: {device_count}", vetting_description)
        self.assertIn("Managed devices review:", vetting_description)
        self.assertNotIn("Current managed fleet:", vetting_description)
        self.assertIn("Unmanaged candidates (bottom section)", vetting_description)
        self.assertIn("Unmanaged candidate devices: {candidate_count}", vetting_description)
        self.assertIn("{fixed_candidate_summary}", vetting_description)
        self.assertIn("{variable_candidate_summary}", vetting_description)
        self.assertIn("Currently surfaced unmanaged candidate: {top_candidate}", vetting_description)
        self.assertNotIn("Top unmanaged candidate right now", vetting_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", vetting_description)
        self.assertIn("Candidate snapshot", vetting_description)
        self.assertIn("Secondary per-device review/audit path after promotion:", vetting_description)
        self.assertIn("Bucket ownership and paths", vetting_description)

        template_description = steps["device_template"]["description"]
        self.assertIn("Promotion path:", template_description)
        self.assertIn("{promotion_path_summary}", template_description)
        self.assertIn("Set safer starting defaults for this {device_kind} before save; managed devices stay on top and the unmanaged promotion backlog stays below.", template_description)
        self.assertNotIn("Choose safer starting defaults", template_description)
        self.assertNotIn("here before save", template_description)
        self.assertNotIn("Start this {device_kind} from a preset", template_description)
        self.assertNotIn("Stay in the Managed Devices workspace while you choose the preset.", template_description)
        self.assertNotIn("Managed Devices owns this promotion preset workflow.", template_description)
        self.assertNotIn("Managed devices stay on top, and unmanaged promotion backlog stays below while you choose the preset.", template_description)
        self.assertNotIn("Managed Devices still owns this promotion step", template_description)
        self.assertNotIn("with the current managed fleet on top and the unmanaged promotion backlog visible below while you choose the preset", template_description)
        self.assertIn("Managed devices (top section)", template_description)
        self.assertIn("Managed Devices: {device_count}", template_description)
        self.assertIn("Managed devices review:", template_description)
        self.assertNotIn("Current managed fleet:", template_description)
        self.assertIn("Unmanaged candidates (bottom section)", template_description)
        self.assertIn("Unmanaged candidate devices: {candidate_count}", template_description)
        self.assertIn("{fixed_candidate_summary}", template_description)
        self.assertIn("{variable_candidate_summary}", template_description)
        self.assertIn("Currently surfaced unmanaged candidate: {top_candidate}", template_description)
        self.assertNotIn("Top unmanaged candidate right now", template_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", template_description)
        self.assertIn("Candidate snapshot", template_description)
        self.assertIn("Bucket ownership and paths", template_description)

        add_description = steps["device_add"]["description"]
        self.assertIn("Promotion path:", add_description)
        self.assertIn("{promotion_path_summary}", add_description)
        self.assertIn("Confirm this {device_kind} in the Managed Devices workspace through native Home Assistant selectors.", add_description)
        self.assertIn("Finish the save with managed devices on top and the unmanaged promotion backlog below.", add_description)
        self.assertNotIn("Finish the save here", add_description)
        self.assertNotIn("Keep day-to-day promotion and save work here without dropping into raw JSON or any custom panel.", add_description)
        self.assertNotIn("Stay in the Managed Devices workspace while you confirm the final settings.", add_description)
        self.assertNotIn("Managed Devices owns this save workflow.", add_description)
        self.assertNotIn("Managed devices stay on top, and unmanaged promotion backlog stays below while you confirm the final settings.", add_description)
        self.assertNotIn("Managed Devices still owns this save step", add_description)
        self.assertNotIn("with the current managed fleet on top and the unmanaged promotion backlog visible below while you confirm the final settings", add_description)
        self.assertNotIn("This is the main native promotion flow", add_description)
        self.assertIn("Managed devices (top section)", add_description)
        self.assertIn("Managed Devices: {device_count}", add_description)
        self.assertIn("Managed devices review:", add_description)
        self.assertNotIn("Current managed fleet:", add_description)
        self.assertIn("Unmanaged candidates (bottom section)", add_description)
        self.assertIn("Unmanaged candidate devices: {candidate_count}", add_description)
        self.assertIn("{fixed_candidate_summary}", add_description)
        self.assertIn("{variable_candidate_summary}", add_description)
        self.assertIn("Currently surfaced unmanaged candidate: {top_candidate}", add_description)
        self.assertNotIn("Top unmanaged candidate right now", add_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", add_description)
        self.assertIn("Candidate snapshot", add_description)
        self.assertIn("Secondary per-device review/audit path after save:", add_description)
        self.assertIn("Bucket ownership and paths", add_description)

        shortlist_step = steps["device_pick_candidate"]
        self.assertEqual(shortlist_step["data"]["quick_pick"], "Promotion shortlist")
        shortlist_description = shortlist_step["description"]
        self.assertIn("Managed devices review:", shortlist_description)
        self.assertIn("Managed Devices: {device_count}", shortlist_description)
        self.assertIn("Start promotion from the surfaced unmanaged {device_kind} candidates below, with managed devices on top and the unmanaged promotion backlog below.", shortlist_description)
        self.assertNotIn("Use this Managed Devices shortlist to review the currently surfaced unmanaged {device_kind} candidates below.", shortlist_description)
        self.assertNotIn("Start promotion from the surfaced unmanaged {device_kind} shortlist below.", shortlist_description)
        self.assertIn("Review the current candidates first, then open the full unmanaged list or the manual add path in the Managed Devices workspace only if the right entity is still missing", shortlist_description)
        self.assertNotIn("Review the current candidates here first", shortlist_description)
        self.assertNotIn("best surfaced unmanaged", shortlist_description)
        self.assertNotIn("short, opinionated promotion shortlist", shortlist_description)
        self.assertIn("Unmanaged candidate devices: {candidate_count}", shortlist_description)
        self.assertIn("{fixed_candidate_summary}", shortlist_description)
        self.assertIn("{variable_candidate_summary}", shortlist_description)
        self.assertIn("Currently surfaced unmanaged candidate: {top_candidate}", shortlist_description)
        self.assertNotIn("Top unmanaged candidate right now", shortlist_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", shortlist_description)
        self.assertNotIn("Current managed fleet:", shortlist_description)
        self.assertIn("Bucket ownership and paths", shortlist_description)

        full_list_description = steps["device_pick_candidate_full"]["description"]
        self.assertIn("If the right entity is still missing from the full list, open the manual add path in the Managed Devices workspace from this dropdown, then finish the save in that workspace.", full_list_description)
        self.assertNotIn("If it is still missing here", full_list_description)
        self.assertNotIn("continue there", full_list_description)
        self.assertIn("Use the full unmanaged list when the shortlist still does not show the right surfaced entity, with managed devices on top and the unmanaged promotion backlog below.", full_list_description)
        self.assertIn("Managed Devices: {device_count}", full_list_description)
        self.assertIn("Unmanaged candidate devices: {candidate_count}", full_list_description)
        self.assertIn("{fixed_candidate_summary}", full_list_description)
        self.assertIn("{variable_candidate_summary}", full_list_description)
        self.assertNotIn("Choose from the full surfaced unmanaged {device_kind} list", full_list_description)
        self.assertNotIn("when the quick shortlist does not contain the right entity", full_list_description)
        self.assertNotIn("continue with the native Managed Devices form", full_list_description)
        self.assertNotIn("continue with the normal native form", full_list_description)
        self.assertNotIn("continue in that Managed Devices form", full_list_description)
        self.assertIn("Managed devices review:", full_list_description)
        self.assertIn("Bucket ownership and paths", full_list_description)

        self.assertEqual(
            steps["device_pick_candidate_full"]["data"]["candidate_entity_id"],
            "Surfaced unmanaged candidate",
        )
        self.assertEqual(
            steps["device_add"]["data"]["entity_id"],
            "Controllable Home Assistant entity",
        )
        self.assertIn(
            "directly controls the real load",
            steps["device_add"]["data_description"]["entity_id"],
        )
        self.assertIn(
            "review the fit and warnings carefully before saving",
            steps["device_add"]["data_description"]["entity_id"],
        )
        self.assertNotIn(
            "review helpers carefully before saving",
            steps["device_add"]["data_description"]["entity_id"],
        )
        self.assertIn("Currently surfaced unmanaged candidate: {top_candidate}", full_list_description)
        self.assertNotIn("Top unmanaged candidate right now", full_list_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", full_list_description)
        self.assertNotIn("Current managed fleet:", full_list_description)

        vetting_description = steps["device_vetting"]["description"]
        self.assertIn("Review this unmanaged candidate before it enters the managed fleet; managed devices stay on top and the unmanaged promotion backlog stays below.", vetting_description)
        self.assertNotIn("Review this unmanaged candidate here", vetting_description)

        template_description = steps["device_template"]["description"]
        self.assertIn("Set safer starting defaults for this {device_kind} before save; managed devices stay on top and the unmanaged promotion backlog stays below.", template_description)
        self.assertNotIn("Choose safer starting defaults", template_description)
        self.assertNotIn("here before save", template_description)

        source_description = steps["native_setup"]["description"]
        source_mapping_description = steps["native_setup_sources"]["description"]
        self.assertIn("Sensors path: {configure_path}.", source_description)
        self.assertIn("Sensors path: {configure_path}.", source_mapping_description)
        self.assertNotIn("Primary path:", source_description)
        self.assertNotIn("Primary path:", source_mapping_description)

        policy_description = steps["policy"]["description"]
        self.assertIn("Set Controls policy for target export, deadband, reserve threshold, refresh interval, and live mode.", policy_description)
        self.assertNotIn("Set Controls policy here", policy_description)
        self.assertIn("Controls owns controller behaviour and outcome.", policy_description)
        self.assertNotIn("Tune controller policy", policy_description)
        self.assertNotIn("Controls owns controller behaviour once source mapping is healthy and managed devices are ready", policy_description)
        self.assertIn("Keep source repair in Sensors, fleet work in the Managed Devices workspace, and troubleshooting in Diagnostics instead of shifting those jobs into Controls.", policy_description)
        self.assertNotIn("Keep source repair in Sensors, fleet work in Managed Devices, and troubleshooting in Diagnostics instead of shifting those jobs into Controls.", policy_description)
        self.assertIn("Controls now", policy_description)
        self.assertIn("Current controller decision: {control_decision_summary}", policy_description)
        self.assertIn("Current control outcome: {control_outcome_summary}", policy_description)
        self.assertIn("Recommended next step from Controls: {policy_next_step}", policy_description)
        self.assertNotIn("shifting those jobs into this screen", policy_description)
        self.assertNotIn("Recommended next step after this screen", policy_description)
        self.assertIn("Bucket ownership and paths", policy_description)
        self.assertIn("- Controls: {policy_path}\n- Live mode shortcut (Controls device action): {mode_path}", policy_description)
        self.assertIn("- Sensors: {sources_path}", policy_description)
        self.assertIn("- Managed Devices: {devices_path}", policy_description)
        self.assertIn("- Diagnostics: {support_path}", policy_description)
        self.assertIn("Controls path: {policy_path}.", policy_description)
        self.assertNotIn("Primary path: {policy_path}.", policy_description)

        support_description = steps["support"]["description"]
        self.assertIn("Diagnostics is for blockers, runtime health, and install evidence.", support_description)
        self.assertNotIn("Use this native section only when setup is blocked, runtime health needs explanation, or you need install-validation evidence.", support_description)
        self.assertIn("Troubleshooting, Repairs, and install validation belong in Diagnostics", support_description)
        self.assertNotIn("Troubleshooting, Repairs, and install validation stay here", support_description)
        self.assertIn("Sensors, Controls, and Managed Devices keep normal operator work.", support_description)
        self.assertIn("Diagnostics now", support_description)
        self.assertIn("- Top alerts: {support_attention_summary}", support_description)
        self.assertNotIn("- Recommended section: {recommended_section}", support_description)
        self.assertNotIn("- Recommended next step: {next_action_summary}", support_description)
        self.assertNotIn("Recommended command-center section", support_description)
        self.assertNotIn("Command-center next action", support_description)
        self.assertNotIn("Live control mode:", support_description)
        self.assertNotIn("Mode summary:", support_description)
        self.assertIn("Blocker triage", support_description)
        self.assertNotIn("Current blocker summary: {support_attention_summary}", support_description)
        self.assertNotIn("Recommended command-center path:", support_description)
        self.assertNotIn("Diagnostics follow-through:", support_description)
        self.assertIn("Blocking source roles: {support_source_attention_roles}", support_description)
        self.assertNotIn("Blocking mapped roles", support_description)
        self.assertIn("If Sensors owns the repair, use: {support_source_repair_step}", support_description)
        self.assertIn("Source-map evidence: {sources_path}", support_description)
        self.assertNotIn("For deeper source-map detail", support_description)
        self.assertIn("Blocked-role candidate cues", support_description)
        self.assertIn("Selector fallback, only if Home Assistant rejects a valid choice", support_description)
        self.assertNotIn("Selector workaround, only if Home Assistant rejects a valid choice", support_description)
        self.assertNotIn("picker bug", support_description)
        self.assertNotIn("Current mapped roles for reference", support_description)
        self.assertNotIn("Suggested source candidates for blocked roles", support_description)
        self.assertNotIn("Other matching source candidates", support_description)
        self.assertIn("Install validation", support_description)
        self.assertIn("Exact-build step", support_description)
        self.assertIn("Install evidence", support_description)
        self.assertNotIn("Installed package details", support_description)
        self.assertNotIn("Live hints", support_description)
        self.assertIn("Bucket ownership and paths", support_description)
        self.assertIn("- Sensors: {sources_path}", support_description)
        self.assertIn("- Controls: {policy_path}\n- Live mode shortcut (Controls device action): {mode_path}", support_description)
        self.assertIn("- Managed Devices: {devices_path}", support_description)
        self.assertIn("- Diagnostics: {support_path}", support_description)
        self.assertIn("Diagnostics path: {support_path}.", support_description)
        self.assertNotIn("Primary path:", support_description)

    def test_source_validation_recommendations_use_source_role_wording(self):
        integration_root = Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export"
        validation_source = (integration_root / "validation.py").read_text(encoding="utf-8")

        self.assertIn("each source role", validation_source)
        self.assertIn("Complete the required source roles", validation_source)
        self.assertIn("required source roles", validation_source)
        self.assertNotIn("Complete the required source mapping", validation_source)
        self.assertNotIn("each logical role", validation_source)
        self.assertNotIn("required roles or fix entity availability", validation_source)

    def test_validation_checklist_uses_source_role_wording_for_active_source_recovery(self):
        project_root = Path(__file__).resolve().parents[1]
        checklist = (project_root / "docs" / "VALIDATION_CHECKLIST.md").read_text(encoding="utf-8")

        self.assertIn("previously saved source roles", checklist)
        self.assertIn("Previously saved source roles are still present after restart", checklist)
        self.assertIn("required source roles recover as healthy runtime entities", checklist)
        self.assertIn("Real solar/grid source entities available for native source-role setup", checklist)
        self.assertIn("bootstrap-only step rather than a giant raw source-role form", checklist)
        self.assertIn("Entry can be created without choosing source roles", checklist)
        self.assertIn("Controls policy/live mode", checklist)
        self.assertIn("Managed Devices workspace", checklist)
        self.assertIn(
            "where Sensors/source roles live, where Controls policy/live mode lives, where Managed Devices fleet work lives, and where Diagnostics evidence lives",
            checklist,
        )
        self.assertIn("map required source roles in native Sensors setup", checklist)
        self.assertIn("Controls flow states whether target export, reserve, deadband, and live mode are actionable", checklist)
        self.assertNotIn("native source mapping", checklist)
        self.assertNotIn("raw source-mapping form", checklist)
        self.assertNotIn("mapping sources", checklist)
        self.assertNotIn("previously saved source mappings", checklist)
        self.assertNotIn("previously saved mapped sources", checklist)
        self.assertNotIn("required mapped sources recover", checklist)
        self.assertNotIn("Controls tuning", checklist)
        self.assertNotIn("controller-tuning paths", checklist)
        self.assertNotIn("Policy/settings flow states whether policy tuning", checklist)
        self.assertNotIn("where sources live, where policy/settings live, and where managed-device work lives", checklist)
        self.assertNotIn("map required sources in native setup", checklist)

    def test_readme_upgrade_steps_use_source_role_wording(self):
        project_root = Path(__file__).resolve().parents[1]
        readme = (project_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("previously saved source roles still appear", readme)
        self.assertNotIn("previously saved source mappings still appear", readme)
        self.assertNotIn("previously saved mapped sources still appear", readme)

    def test_readme_configuration_steps_use_current_bucket_labels(self):
        project_root = Path(__file__).resolve().parents[1]
        readme = (project_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("**Native Home Assistant setup path**: Sensors/source roles, Managed Devices, Controls, and Diagnostics live", readme)
        self.assertIn("operators to find Sensors, Controls, Managed Devices, and Diagnostics", readme)
        self.assertIn("Keep Sensors/source roles, Managed Devices, Controls, and Diagnostics available", readme)
        self.assertIn("Use **Sensors** to map your source entities", readme)
        self.assertIn("Use **Managed Devices** in Configure as the Managed Devices workspace", readme)
        self.assertIn("Treat **Managed Devices** as the home for per-device enablement", readme)
        self.assertIn("Use **Controls** in Configure for target/deadband/reserve defaults", readme)
        self.assertNotIn("**Native Home Assistant setup path**: source mapping, managed-device configuration, and controller tuning", readme)
        self.assertNotIn("Keep source mapping, managed devices, and controller tuning available", readme)
        self.assertNotIn("operators to find sources, policy, managed devices, and support", readme)
        self.assertNotIn("Use **Sources and source mapping**", readme)
        self.assertNotIn("**Managed devices**", readme)
        self.assertNotIn("Use **Policy and controller settings**", readme)

    def test_active_project_docs_use_current_bucket_labels(self):
        project_root = Path(__file__).resolve().parents[1]
        docs = {
            "PRODUCT_SPEC_V1.md": (project_root / "docs" / "PRODUCT_SPEC_V1.md").read_text(encoding="utf-8"),
            "DASHBOARD_SETUP.md": (project_root / "docs" / "DASHBOARD_SETUP.md").read_text(encoding="utf-8"),
            "REFERENCE_MATRIX.md": (project_root / "docs" / "REFERENCE_MATRIX.md").read_text(encoding="utf-8"),
            "VALIDATION_CHECKLIST.md": (project_root / "docs" / "VALIDATION_CHECKLIST.md").read_text(encoding="utf-8"),
        }
        ui_design = (project_root / "docs" / "UI_DESIGN.md").read_text(encoding="utf-8")
        ui_implementation_spec = (project_root / "docs" / "UI_IMPLEMENTATION_SPEC.md").read_text(encoding="utf-8")

        for name, text in docs.items():
            with self.subTest(doc=name):
                self.assertIn("Sensors/source roles", text)
                self.assertIn("Controls", text)
                self.assertIn("Managed Devices", text)
                self.assertIn("Diagnostics", text)
                self.assertNotIn("sources, policy, managed devices, and support", text)
                self.assertNotIn("source mapping, policy, managed devices", text)
                self.assertNotIn("where to set policy, and where to review health", text)

        self.assertIn(
            "never act without validated source roles and healthy source bindings",
            docs["PRODUCT_SPEC_V1.md"],
        )
        self.assertIn(
            "where Sensors/source roles, Controls policy/live mode, Managed Devices fleet work, and Diagnostics evidence live",
            docs["PRODUCT_SPEC_V1.md"],
        )
        self.assertIn("source roles or source bindings do not reconcile", docs["PRODUCT_SPEC_V1.md"])
        self.assertNotIn("never act without validated source mapping", docs["PRODUCT_SPEC_V1.md"])
        self.assertNotIn("mapped energy sources do not reconcile", docs["PRODUCT_SPEC_V1.md"])
        self.assertNotIn("where policy/settings live", docs["PRODUCT_SPEC_V1.md"])
        self.assertIn("source-role status and blocker visibility", ui_design)
        self.assertIn("source-map details only where an operator is cross-checking concrete entity bindings", ui_design)
        self.assertNotIn("source mapping status and blocker visibility", ui_design)
        self.assertIn("missing source roles", ui_implementation_spec)
        self.assertNotIn("missing source mapping", ui_implementation_spec)


if __name__ == "__main__":
    unittest.main()
