import json
from pathlib import Path
import unittest


class TestBucketOwnershipCopy(unittest.TestCase):
    def test_bucket_ownership_and_workspace_split_stay_visible(self):
        integration_root = Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export"
        with (integration_root / "strings.json").open(encoding="utf-8") as handle:
            strings = json.load(handle)

        steps = strings["options"]["step"]

        init_description = steps["init"]["description"]
        self.assertIn("Use this command center for setup and the current operating picture.", init_description)
        self.assertIn("When the next step moves into fleet work, continue in the Managed Devices workspace.", init_description)
        self.assertNotIn("Use this command center for the basic setup and current operating picture only.", init_description)
        self.assertIn("\n\nBasic setup paths\n- Sensors: {sources_path}", init_description)
        self.assertIn("- Controls: {policy_path}\n- Live mode shortcut (Controls device action): {mode_path}", init_description)
        self.assertIn("- Managed Devices: {devices_path}", init_description)
        self.assertIn("- Diagnostics: {support_path}", init_description)
        self.assertIn("\n\nBucket ownership\n- Sensors owns source mapping and source health.", init_description)
        self.assertIn("Sensors owns source mapping and source health.", init_description)
        self.assertIn("Managed Devices owns fleet onboarding, promotion, edits, enablement, and removal: {devices_path}", init_description)

        native_setup_description = steps["native_setup"]["description"]
        self.assertIn(
            "Use this Sensors workspace as the source-mapping and source-health home for the Zero Net Export command center.",
            native_setup_description,
        )
        self.assertNotIn("Use this Sensors screen", native_setup_description)
        self.assertIn("Keep managed-device promotion in Managed Devices and controller-policy tuning in Controls.", native_setup_description)
        self.assertNotIn("This is the source-mapping section of the Zero Net Export command center.", native_setup_description)
        self.assertIn("Source status now", native_setup_description)
        self.assertIn("Source mapping progress", native_setup_description)
        self.assertIn("- Required roles mapped: {source_mapping_progress}", native_setup_description)
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
        self.assertIn("Use this Sensors workspace to map the required entities for the current source layout.", source_mapping_description)
        self.assertNotIn("Use this Sensors screen", source_mapping_description)
        self.assertNotIn("set the refresh interval", source_mapping_description)
        self.assertIn("Sensors owns source repair and source-health work", source_mapping_description)
        self.assertIn("keep fleet onboarding in Managed Devices and controller tuning in Controls", source_mapping_description)
        self.assertIn("Source mapping progress", source_mapping_description)
        self.assertIn("- Required roles mapped: {source_mapping_progress}", source_mapping_description)
        self.assertIn("- Blocking source issues: {source_blocker_summary}", source_mapping_description)
        self.assertIn("Use the native selectors first. Only drop to the fallback fields if Home Assistant rejects a valid choice.", source_mapping_description)
        self.assertNotIn("If Combined / net grid energy or Battery state of charge still triggers", source_mapping_description)
        self.assertNotIn("Source map now", source_mapping_description)
        self.assertNotIn("Sensors now", source_mapping_description)
        self.assertIn("Blocking source repair", source_mapping_description)
        self.assertIn("Best live candidates for the current blocker:", source_mapping_description)
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

        devices_description = steps["devices"]["description"]
        self.assertIn("This is the main Managed Devices workspace for review, promotion, edits, enablement, disablement, and removal.", devices_description)
        self.assertIn("Managed devices stay on top, and unmanaged promotion backlog stays below.", devices_description)
        self.assertNotIn("Use this native Configure screen as the main managed-device workspace.", devices_description)
        self.assertIn("Managed devices (top section)", devices_description)
        self.assertIn("Managed devices review:", devices_description)
        self.assertNotIn("Current managed fleet:", devices_description)
        self.assertIn("Unmanaged candidates (bottom section)", devices_description)
        self.assertIn("Currently surfaced unmanaged candidate: {top_candidate}", devices_description)
        self.assertNotIn("Top unmanaged candidate right now", devices_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", devices_description)
        self.assertIn("Detailed native review path, only after the main fleet step is clear", devices_description)
        self.assertIn("Bucket ownership and paths", devices_description)
        self.assertIn("Managed Devices owns fleet onboarding, promotion, edits, enablement, and removal: {configure_path}", devices_description)
        self.assertIn("- Sensors owns source mapping and source repair: {sources_path}", devices_description)
        self.assertIn("- Controls owns target export, reserve, deadband, and live mode: {policy_path}", devices_description)
        self.assertIn("- Diagnostics owns troubleshooting, repairs, and install validation: {support_path}", devices_description)

        bulk_enable_description = steps["device_bulk_enable"]["description"]
        self.assertEqual(
            steps["device_bulk_enable"]["title"],
            "Review managed devices workspace and enablement",
        )
        self.assertIn("Use this Managed Devices workspace to stage enablement changes without raw JSON.", bulk_enable_description)
        self.assertIn("Configure stays the primary fleet workspace for enablement", bulk_enable_description)
        self.assertIn("Managed devices stay on top, and unmanaged promotion backlog stays below", bulk_enable_description)
        self.assertIn("Primary path: {configure_path}.", bulk_enable_description)
        self.assertIn("Managed Devices owns fleet enablement", bulk_enable_description)
        self.assertIn("while you work through this workspace", bulk_enable_description)
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
        self.assertIn("Detailed native review path, only after the main fleet step is clear", bulk_enable_description)
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
            "open the Managed Devices workspace to toggle which devices stay enabled",
            steps["devices"]["data_description"]["device_action"],
        )

        edit_pick_description = steps["device_edit_pick"]["description"]
        self.assertIn("Use this Managed Devices workspace to choose which managed device to edit from the native fleet list.", edit_pick_description)
        self.assertIn("Managed Devices owns this fleet-edit workflow.", edit_pick_description)
        self.assertIn("Managed devices stay on top, and unmanaged promotion backlog stays below.", edit_pick_description)
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
        self.assertIn("Use this Managed Devices workspace to choose which managed device should leave the native fleet.", remove_description)
        self.assertNotIn("Choose which managed device should be removed from the native fleet", remove_description)
        self.assertIn("Managed Devices owns this fleet-removal workflow", remove_description)
        self.assertIn("Managed devices stay on top, and unmanaged promotion backlog stays below.", remove_description)
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
        self.assertIn("Use this Managed Devices workspace shortlist to start promotion from the surfaced unmanaged {device_kind} candidates below.", shortlist_description)
        self.assertIn("Stay in the Managed Devices workspace while you choose the next candidate.", shortlist_description)
        self.assertNotIn("Managed Devices owns this promotion entry workflow.", shortlist_description)
        self.assertIn("Managed devices stay on top, and unmanaged promotion backlog stays below while you choose the next candidate.", shortlist_description)
        self.assertNotIn("keep the managed fleet visible on top and the unmanaged backlog visible below", shortlist_description)
        self.assertNotIn("Managed Devices owns this promotion entry step.", shortlist_description)

        full_list_description = steps["device_pick_candidate_full"]["description"]
        self.assertIn("Use this Managed Devices workspace full list when the shortlist still does not show the right surfaced entity.", full_list_description)
        self.assertIn("Stay in the Managed Devices workspace while you choose the next candidate.", full_list_description)
        self.assertNotIn("Managed Devices owns this full-list workflow.", full_list_description)
        self.assertIn("Managed devices stay on top, and unmanaged promotion backlog stays below while you choose the next candidate.", full_list_description)
        self.assertNotIn("keep the managed fleet visible on top and the unmanaged backlog visible below", full_list_description)
        self.assertNotIn("Managed Devices still owns this full-list step.", full_list_description)

        vetting_description = steps["device_vetting"]["description"]
        self.assertIn("Use this Managed Devices workspace review to vet this unmanaged candidate before it enters the managed fleet.", vetting_description)
        self.assertIn("Stay in the Managed Devices workspace while you vet the candidate.", vetting_description)
        self.assertNotIn("Managed Devices owns this promotion workflow.", vetting_description)
        self.assertIn("Managed devices stay on top, and unmanaged promotion backlog stays below while you vet the candidate.", vetting_description)
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
        self.assertIn("Detailed native review path after promotion, only if you need deeper per-device review", vetting_description)
        self.assertIn("Bucket ownership and paths", vetting_description)

        template_description = steps["device_template"]["description"]
        self.assertIn("Promotion path:", template_description)
        self.assertIn("{promotion_path_summary}", template_description)
        self.assertIn("Use this Managed Devices workspace to choose safer starting defaults for this {device_kind} before save.", template_description)
        self.assertNotIn("Start this {device_kind} from a preset", template_description)
        self.assertIn("Stay in the Managed Devices workspace while you choose the preset.", template_description)
        self.assertNotIn("Managed Devices owns this promotion preset workflow.", template_description)
        self.assertIn("Managed devices stay on top, and unmanaged promotion backlog stays below while you choose the preset.", template_description)
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
        self.assertIn("Stay in the Managed Devices workspace while you confirm the final settings.", add_description)
        self.assertNotIn("Managed Devices owns this save workflow.", add_description)
        self.assertIn("Managed devices stay on top, and unmanaged promotion backlog stays below while you confirm the final settings.", add_description)
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
        self.assertIn("Detailed native review path after save, only if you need deeper per-device review", add_description)
        self.assertIn("Bucket ownership and paths", add_description)

        shortlist_step = steps["device_pick_candidate"]
        self.assertEqual(shortlist_step["data"]["quick_pick"], "Promotion shortlist")
        shortlist_description = shortlist_step["description"]
        self.assertIn("Managed devices review:", shortlist_description)
        self.assertIn("Managed Devices: {device_count}", shortlist_description)
        self.assertIn("Use this Managed Devices workspace shortlist to start promotion from the surfaced unmanaged {device_kind} candidates below.", shortlist_description)
        self.assertNotIn("Use this Managed Devices shortlist to review the currently surfaced unmanaged {device_kind} candidates below.", shortlist_description)
        self.assertNotIn("Start promotion from the surfaced unmanaged {device_kind} shortlist below.", shortlist_description)
        self.assertIn("open the full unmanaged list or the manual Managed Devices form only if the right entity is still missing", shortlist_description)
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
        self.assertIn("open the manual Managed Devices form from this dropdown and continue there", full_list_description)
        self.assertIn("Use this Managed Devices workspace full list when the shortlist still does not show the right surfaced entity.", full_list_description)
        self.assertIn("Managed Devices: {device_count}", full_list_description)
        self.assertIn("Unmanaged candidate devices: {candidate_count}", full_list_description)
        self.assertIn("{fixed_candidate_summary}", full_list_description)
        self.assertIn("{variable_candidate_summary}", full_list_description)
        self.assertNotIn("Choose from the full surfaced unmanaged {device_kind} list", full_list_description)
        self.assertNotIn("when the quick shortlist does not contain the right entity", full_list_description)
        self.assertNotIn("continue with the native Managed Devices form", full_list_description)
        self.assertNotIn("continue with the normal native form", full_list_description)
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

        policy_description = steps["policy"]["description"]
        self.assertIn("Controls owns controller behaviour and outcome.", policy_description)
        self.assertNotIn("Controls owns controller behaviour once source mapping is healthy and managed devices are ready", policy_description)
        self.assertIn("Keep source repair in Sensors, fleet work in Managed Devices, and troubleshooting in Diagnostics instead of shifting those jobs into Controls.", policy_description)
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
        self.assertIn("Primary path: {policy_path}.", policy_description)

        support_description = steps["support"]["description"]
        self.assertIn("Use Diagnostics when setup is blocked, runtime health needs explanation, or you need install-validation evidence.", support_description)
        self.assertNotIn("Use this native section only when setup is blocked, runtime health needs explanation, or you need install-validation evidence.", support_description)
        self.assertIn("Diagnostics owns troubleshooting, repairs, and install validation", support_description)
        self.assertIn("It does not own normal source mapping, policy tuning, or managed-device promotion.", support_description)
        self.assertIn("Diagnostics now", support_description)
        self.assertIn("- Top alerts: {support_attention_summary}", support_description)
        self.assertNotIn("Live control mode:", support_description)
        self.assertNotIn("Mode summary:", support_description)
        self.assertIn("Blocker triage", support_description)
        self.assertIn("Current blocker summary: {support_attention_summary}", support_description)
        self.assertIn("Blocking mapped roles: {support_source_attention_roles}", support_description)
        self.assertIn("If Sensors owns the repair, use: {support_source_repair_step}", support_description)
        self.assertIn("For deeper source-map detail, open Sensors: {sources_path}", support_description)
        self.assertIn("Best live candidate cues for blocked roles", support_description)
        self.assertIn("Selector workaround, only if Home Assistant rejects a valid choice", support_description)
        self.assertNotIn("Current mapped roles for reference", support_description)
        self.assertNotIn("Suggested source candidates for blocked roles", support_description)
        self.assertNotIn("Other matching source candidates", support_description)
        self.assertIn("Install validation", support_description)
        self.assertIn("Exact-build next step", support_description)
        self.assertIn("Full install evidence", support_description)
        self.assertNotIn("Installed package details", support_description)
        self.assertNotIn("Live hints", support_description)
        self.assertIn("Bucket ownership and paths", support_description)
        self.assertIn("- Sensors: {sources_path}", support_description)
        self.assertIn("- Controls: {policy_path}\n- Live mode shortcut (Controls device action): {mode_path}", support_description)
        self.assertIn("- Managed Devices: {devices_path}", support_description)
        self.assertIn("- Diagnostics: {support_path}", support_description)
        self.assertIn("Primary path: {support_path}.", support_description)


if __name__ == "__main__":
    unittest.main()
