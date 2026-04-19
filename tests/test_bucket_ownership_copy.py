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
        self.assertIn("\n\nBasic setup paths\n- Sensors: {sources_path}", init_description)
        self.assertIn("- Controls: {policy_path}\n- Live mode shortcut (Controls device action): {mode_path}", init_description)
        self.assertIn("- Managed Devices: {devices_path}", init_description)
        self.assertIn("- Diagnostics: {support_path}", init_description)
        self.assertIn("\n\nBucket ownership\n- Sensors owns source mapping and source health.", init_description)
        self.assertIn("Sensors owns source mapping and source health.", init_description)
        self.assertIn("Managed Devices owns fleet onboarding, promotion, edits, enablement, and removal: {devices_path}", init_description)

        native_setup_description = steps["native_setup"]["description"]
        self.assertIn("Sensors owns mapped roles and source health.", native_setup_description)
        self.assertIn("not managed-device promotion or controller-policy tuning", native_setup_description)
        self.assertIn("Sensors now", native_setup_description)
        self.assertIn("Bucket ownership and paths", native_setup_description)
        self.assertIn("- Sensors: {sources_path}", native_setup_description)
        self.assertIn("- Controls: {policy_path}\n- Live mode shortcut (Controls device action): {mode_path}", native_setup_description)
        self.assertIn("- Managed Devices: {devices_path}", native_setup_description)
        self.assertIn("- Diagnostics: {support_path}", native_setup_description)

        source_mapping_description = steps["native_setup_sources"]["description"]
        self.assertIn("Sensors owns source repair and source-health work", source_mapping_description)
        self.assertIn("keep fleet onboarding in Managed Devices and controller tuning in Controls", source_mapping_description)
        self.assertIn("Sensors now", source_mapping_description)
        self.assertIn("Bucket ownership and paths", source_mapping_description)
        self.assertIn("- Sensors: {sources_path}", source_mapping_description)
        self.assertIn("- Controls: {policy_path}\n- Live mode shortcut (Controls device action): {mode_path}", source_mapping_description)
        self.assertIn("- Managed Devices: {devices_path}", source_mapping_description)
        self.assertIn("- Diagnostics: {support_path}", source_mapping_description)

        devices_description = steps["devices"]["description"]
        self.assertIn("Managed devices (top section)", devices_description)
        self.assertIn("Managed devices review:", devices_description)
        self.assertNotIn("Current managed fleet:", devices_description)
        self.assertIn("Unmanaged candidates (bottom section)", devices_description)
        self.assertIn("Top surfaced unmanaged candidate: {top_candidate}", devices_description)
        self.assertNotIn("Top unmanaged candidate right now", devices_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", devices_description)
        self.assertIn("Detailed native review path, only after the main fleet step is clear", devices_description)
        self.assertIn("Bucket ownership", devices_description)
        self.assertIn("Managed Devices owns fleet onboarding, promotion, edits, enablement, and removal.", devices_description)
        self.assertIn("Controls owns target export, reserve, deadband, and live mode.", devices_description)

        bulk_enable_description = steps["device_bulk_enable"]["description"]
        self.assertEqual(
            steps["device_bulk_enable"]["title"],
            "Review managed devices workspace and enablement",
        )
        self.assertIn("Managed Devices owns fleet enablement", bulk_enable_description)
        self.assertIn("Managed devices (top section)", bulk_enable_description)
        self.assertIn("Managed devices review:", bulk_enable_description)
        self.assertNotIn("Current managed fleet:", bulk_enable_description)
        self.assertIn("Unmanaged candidates (bottom section)", bulk_enable_description)
        self.assertIn("Top surfaced unmanaged candidate: {top_candidate}", bulk_enable_description)
        self.assertNotIn("Top unmanaged candidate right now", bulk_enable_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", bulk_enable_description)
        self.assertIn("Candidate snapshot", bulk_enable_description)
        self.assertIn("Detailed native review path, only after the main fleet step is clear", bulk_enable_description)
        self.assertIn(
            "open the Managed Devices workspace to toggle which devices stay enabled",
            steps["devices"]["data_description"]["device_action"],
        )

        edit_pick_description = steps["device_edit_pick"]["description"]
        self.assertIn("Managed Devices owns this fleet-edit workflow", edit_pick_description)
        self.assertIn("Managed devices (top section)", edit_pick_description)
        self.assertIn("Managed devices review:", edit_pick_description)
        self.assertNotIn("Current managed fleet:", edit_pick_description)
        self.assertIn("Unmanaged candidates (bottom section)", edit_pick_description)
        self.assertIn("Top surfaced unmanaged candidate: {top_candidate}", edit_pick_description)
        self.assertNotIn("Top unmanaged candidate right now", edit_pick_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", edit_pick_description)
        self.assertIn("Candidate snapshot", edit_pick_description)

        remove_description = steps["device_remove"]["description"]
        self.assertIn("Managed Devices owns this fleet-removal workflow", remove_description)
        self.assertIn("Managed devices (top section)", remove_description)
        self.assertIn("Managed devices review:", remove_description)
        self.assertNotIn("Current managed fleet:", remove_description)
        self.assertIn("Unmanaged candidates (bottom section)", remove_description)
        self.assertIn("Top surfaced unmanaged candidate: {top_candidate}", remove_description)
        self.assertNotIn("Top unmanaged candidate right now", remove_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", remove_description)
        self.assertIn("Candidate snapshot", remove_description)

        vetting_description = steps["device_vetting"]["description"]
        self.assertIn("Managed Devices owns this promotion workflow", vetting_description)
        self.assertIn("Managed devices (top section)", vetting_description)
        self.assertIn("Managed devices review:", vetting_description)
        self.assertNotIn("Current managed fleet:", vetting_description)
        self.assertIn("Unmanaged candidates (bottom section)", vetting_description)
        self.assertIn("Top surfaced unmanaged candidate: {top_candidate}", vetting_description)
        self.assertNotIn("Top unmanaged candidate right now", vetting_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", vetting_description)
        self.assertIn("Candidate snapshot", vetting_description)
        self.assertIn("Detailed native review path after promotion, only if you need deeper per-device review", vetting_description)

        template_description = steps["device_template"]["description"]
        self.assertIn("Promotion path:", template_description)
        self.assertIn("{promotion_path_summary}", template_description)
        self.assertIn("Managed Devices still owns this step", template_description)
        self.assertIn("Managed devices (top section)", template_description)
        self.assertIn("Managed devices review:", template_description)
        self.assertNotIn("Current managed fleet:", template_description)
        self.assertIn("Unmanaged candidates (bottom section)", template_description)
        self.assertIn("Top surfaced unmanaged candidate: {top_candidate}", template_description)
        self.assertNotIn("Top unmanaged candidate right now", template_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", template_description)
        self.assertIn("Candidate snapshot", template_description)

        add_description = steps["device_add"]["description"]
        self.assertIn("Promotion path:", add_description)
        self.assertIn("{promotion_path_summary}", add_description)
        self.assertIn("Managed Devices still owns this save step", add_description)
        self.assertIn("Managed devices (top section)", add_description)
        self.assertIn("Managed devices review:", add_description)
        self.assertNotIn("Current managed fleet:", add_description)
        self.assertIn("Unmanaged candidates (bottom section)", add_description)
        self.assertIn("Top surfaced unmanaged candidate: {top_candidate}", add_description)
        self.assertNotIn("Top unmanaged candidate right now", add_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", add_description)
        self.assertIn("Candidate snapshot", add_description)
        self.assertIn("Detailed native review path after save, only if you need deeper per-device review", add_description)

        shortlist_step = steps["device_pick_candidate"]
        self.assertEqual(shortlist_step["data"]["quick_pick"], "Promotion shortlist")
        shortlist_description = shortlist_step["description"]
        self.assertIn("Managed devices review:", shortlist_description)
        self.assertIn("Top surfaced unmanaged candidate: {top_candidate}", shortlist_description)
        self.assertNotIn("Top unmanaged candidate right now", shortlist_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", shortlist_description)
        self.assertNotIn("Current managed fleet:", shortlist_description)

        full_list_description = steps["device_pick_candidate_full"]["description"]
        self.assertIn("open the manual Managed Devices form from this dropdown and continue there", full_list_description)
        self.assertNotIn("continue with the native Managed Devices form", full_list_description)
        self.assertNotIn("continue with the normal native form", full_list_description)
        self.assertIn("Managed devices review:", full_list_description)

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
        self.assertIn("Top surfaced unmanaged candidate: {top_candidate}", full_list_description)
        self.assertNotIn("Top unmanaged candidate right now", full_list_description)
        self.assertIn("Ready-next unmanaged candidate: {ready_candidate}", full_list_description)
        self.assertNotIn("Current managed fleet:", full_list_description)

        policy_description = steps["policy"]["description"]
        self.assertIn("Controls owns controller behaviour", policy_description)
        self.assertIn("keep source repair in Sensors, fleet work in Managed Devices, and troubleshooting in Diagnostics", policy_description)
        self.assertIn("Controls now", policy_description)
        self.assertIn("Bucket ownership and paths", policy_description)
        self.assertIn("- Controls: {policy_path}\n- Live mode shortcut (Controls device action): {mode_path}", policy_description)
        self.assertIn("- Sensors: {sources_path}", policy_description)
        self.assertIn("- Managed Devices: {devices_path}", policy_description)
        self.assertIn("- Diagnostics: {support_path}", policy_description)
        self.assertIn("Primary path: {policy_path}.", policy_description)

        support_description = steps["support"]["description"]
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
