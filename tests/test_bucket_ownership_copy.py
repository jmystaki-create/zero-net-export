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
        self.assertIn("- Controls, including the live mode shortcut: {policy_path} (device shortcut: {mode_path})", init_description)
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
        self.assertIn("- Controls, including the live mode shortcut: {policy_path} (device shortcut: {mode_path})", native_setup_description)
        self.assertIn("- Managed Devices: {devices_path}", native_setup_description)
        self.assertIn("- Diagnostics: {support_path}", native_setup_description)

        source_mapping_description = steps["native_setup_sources"]["description"]
        self.assertIn("Sensors owns source repair and source-health work", source_mapping_description)
        self.assertIn("keep fleet onboarding in Managed Devices and controller tuning in Controls", source_mapping_description)
        self.assertIn("Sensors now", source_mapping_description)
        self.assertIn("Bucket ownership and paths", source_mapping_description)
        self.assertIn("- Sensors: {sources_path}", source_mapping_description)
        self.assertIn("- Controls, including the live mode shortcut: {policy_path} (device shortcut: {mode_path})", source_mapping_description)
        self.assertIn("- Managed Devices: {devices_path}", source_mapping_description)
        self.assertIn("- Diagnostics: {support_path}", source_mapping_description)

        devices_description = steps["devices"]["description"]
        self.assertIn("Managed devices (top section)", devices_description)
        self.assertIn("Managed devices review:", devices_description)
        self.assertNotIn("Current managed fleet:", devices_description)
        self.assertIn("Unmanaged candidates (bottom section)", devices_description)
        self.assertIn("Detailed native review path, only after the main fleet step is clear", devices_description)
        self.assertIn("Bucket ownership", devices_description)
        self.assertIn("Managed Devices owns fleet onboarding, promotion, edits, enablement, and removal.", devices_description)
        self.assertIn("Controls owns target export, reserve, deadband, and live mode.", devices_description)

        bulk_enable_description = steps["device_bulk_enable"]["description"]
        self.assertIn("Managed Devices owns fleet enablement", bulk_enable_description)
        self.assertIn("Managed devices (top section)", bulk_enable_description)
        self.assertIn("Managed devices review:", bulk_enable_description)
        self.assertNotIn("Current managed fleet:", bulk_enable_description)
        self.assertIn("Unmanaged candidates (bottom section)", bulk_enable_description)
        self.assertIn("Candidate snapshot", bulk_enable_description)
        self.assertIn("Detailed native review path, only after the main fleet step is clear", bulk_enable_description)

        edit_pick_description = steps["device_edit_pick"]["description"]
        self.assertIn("Managed Devices owns this fleet-edit workflow", edit_pick_description)
        self.assertIn("Managed devices (top section)", edit_pick_description)
        self.assertIn("Managed devices review:", edit_pick_description)
        self.assertNotIn("Current managed fleet:", edit_pick_description)
        self.assertIn("Unmanaged candidates (bottom section)", edit_pick_description)
        self.assertIn("Candidate snapshot", edit_pick_description)

        remove_description = steps["device_remove"]["description"]
        self.assertIn("Managed Devices owns this fleet-removal workflow", remove_description)
        self.assertIn("Managed devices (top section)", remove_description)
        self.assertIn("Managed devices review:", remove_description)
        self.assertNotIn("Current managed fleet:", remove_description)
        self.assertIn("Unmanaged candidates (bottom section)", remove_description)
        self.assertIn("Candidate snapshot", remove_description)

        vetting_description = steps["device_vetting"]["description"]
        self.assertIn("Managed Devices owns this promotion workflow", vetting_description)
        self.assertIn("Managed devices (top section)", vetting_description)
        self.assertIn("Managed devices review:", vetting_description)
        self.assertNotIn("Current managed fleet:", vetting_description)
        self.assertIn("Unmanaged candidates (bottom section)", vetting_description)
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
        self.assertIn("Candidate snapshot", template_description)

        add_description = steps["device_add"]["description"]
        self.assertIn("Promotion path:", add_description)
        self.assertIn("{promotion_path_summary}", add_description)
        self.assertIn("Managed Devices still owns this save step", add_description)
        self.assertIn("Managed devices (top section)", add_description)
        self.assertIn("Managed devices review:", add_description)
        self.assertNotIn("Current managed fleet:", add_description)
        self.assertIn("Unmanaged candidates (bottom section)", add_description)
        self.assertIn("Candidate snapshot", add_description)
        self.assertIn("Detailed native review path after save, only if you need deeper per-device review", add_description)

        shortlist_step = steps["device_pick_candidate"]
        self.assertEqual(shortlist_step["data"]["quick_pick"], "Promotion shortlist")
        shortlist_description = shortlist_step["description"]
        self.assertIn("Managed devices review:", shortlist_description)
        self.assertNotIn("Current managed fleet:", shortlist_description)

        full_list_description = steps["device_pick_candidate_full"]["description"]
        self.assertIn("continue with the native Managed Devices form", full_list_description)
        self.assertNotIn("continue with the normal native form", full_list_description)
        self.assertIn("Managed devices review:", full_list_description)
        self.assertNotIn("Current managed fleet:", full_list_description)

        policy_description = steps["policy"]["description"]
        self.assertIn("Controls owns controller behaviour", policy_description)
        self.assertIn("keep source repair in Sensors, fleet work in Managed Devices, and troubleshooting in Diagnostics", policy_description)
        self.assertIn("Controls now", policy_description)
        self.assertIn("Bucket ownership and paths", policy_description)
        self.assertIn("- Controls, including the live mode shortcut: {policy_path} (device shortcut: {mode_path})", policy_description)
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
        self.assertIn("Mapped-source triage", support_description)
        self.assertIn("Suggested source candidates for blocked roles", support_description)
        self.assertIn("Other matching source candidates", support_description)
        self.assertIn("Selector workaround, only if Home Assistant rejects a valid choice", support_description)
        self.assertIn("Install validation", support_description)
        self.assertIn("Exact-build next step", support_description)
        self.assertIn("Full install evidence", support_description)
        self.assertNotIn("Installed package details", support_description)
        self.assertNotIn("Live hints", support_description)
        self.assertIn("Bucket ownership and paths", support_description)
        self.assertIn("- Sensors: {sources_path}", support_description)
        self.assertIn("- Controls, including the live mode shortcut: {policy_path} (device shortcut: {mode_path})", support_description)
        self.assertIn("- Managed Devices: {devices_path}", support_description)
        self.assertIn("- Diagnostics: {support_path}", support_description)
        self.assertIn("Primary path: {support_path}.", support_description)


if __name__ == "__main__":
    unittest.main()
