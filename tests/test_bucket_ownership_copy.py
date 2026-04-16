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
        self.assertIn("Bucket ownership:", init_description)
        self.assertIn("Sensors owns source mapping and source health.", init_description)
        self.assertIn("Managed Devices owns fleet onboarding, edits, enablement, and removal.", init_description)

        native_setup_description = steps["native_setup"]["description"]
        self.assertIn("Sensors owns mapped roles and source health.", native_setup_description)
        self.assertIn("not managed-device promotion or controller-policy tuning", native_setup_description)

        source_mapping_description = steps["native_setup_sources"]["description"]
        self.assertIn("Sensors owns source repair and source-health work", source_mapping_description)
        self.assertIn("keep fleet onboarding in Managed Devices and controller tuning in Controls", source_mapping_description)

        devices_description = steps["devices"]["description"]
        self.assertIn("Managed devices (top section)", devices_description)
        self.assertIn("Unmanaged candidates (bottom section)", devices_description)
        self.assertIn("Not here:", devices_description)
        self.assertIn("Target export, reserve, deadband, and live mode stay under Controls.", devices_description)

        bulk_enable_description = steps["device_bulk_enable"]["description"]
        self.assertIn("Managed Devices owns fleet enablement", bulk_enable_description)
        self.assertIn("Managed devices (top section)", bulk_enable_description)
        self.assertIn("Unmanaged candidates (bottom section)", bulk_enable_description)

        edit_pick_description = steps["device_edit_pick"]["description"]
        self.assertIn("Managed Devices owns this fleet-edit workflow", edit_pick_description)
        self.assertIn("Managed devices (top section)", edit_pick_description)
        self.assertIn("Unmanaged candidates (bottom section)", edit_pick_description)

        remove_description = steps["device_remove"]["description"]
        self.assertIn("Managed Devices owns this fleet-removal workflow", remove_description)
        self.assertIn("Managed devices (top section)", remove_description)
        self.assertIn("Unmanaged candidates (bottom section)", remove_description)

        vetting_description = steps["device_vetting"]["description"]
        self.assertIn("Managed Devices owns this promotion workflow", vetting_description)
        self.assertIn("Managed devices (top section)", vetting_description)
        self.assertIn("Unmanaged candidates (bottom section)", vetting_description)

        template_description = steps["device_template"]["description"]
        self.assertIn("Managed Devices still owns this step", template_description)
        self.assertIn("Managed devices (top section)", template_description)
        self.assertIn("Unmanaged candidates (bottom section)", template_description)

        add_description = steps["device_add"]["description"]
        self.assertIn("Managed Devices still owns this save step", add_description)
        self.assertIn("Managed devices (top section)", add_description)
        self.assertIn("Unmanaged candidates (bottom section)", add_description)

        policy_description = steps["policy"]["description"]
        self.assertIn("Controls owns controller behaviour", policy_description)
        self.assertIn("keep source repair in Sensors, fleet work in Managed Devices, and troubleshooting in Diagnostics", policy_description)

        support_description = steps["support"]["description"]
        self.assertIn("Diagnostics owns troubleshooting, repairs, and install validation", support_description)
        self.assertIn("not normal source mapping, policy tuning, or managed-device promotion", support_description)


if __name__ == "__main__":
    unittest.main()
