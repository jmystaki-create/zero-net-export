import json
from pathlib import Path
import unittest


class TestCommandCenterModalCopy(unittest.TestCase):
    def test_init_modal_stays_setup_focused(self):
        integration_root = Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export"
        with (integration_root / "strings.json").open(encoding="utf-8") as handle:
            strings = json.load(handle)

        description = strings["options"]["step"]["init"]["description"]

        self.assertTrue(description.startswith("Now\n- Headline decision:"))
        self.assertIn("\n\nCommand-center use\n- Live setup and current operating picture.", description)
        self.assertIn(
            "- Finish source mapping and core control checks here; when fleet work is next, continue in the Managed Devices workspace.",
            description,
        )
        self.assertNotIn("basic setup and current operating picture only", description)
        self.assertIn("\n- Alerts: {alert_summary}", description)
        self.assertIn("\n- Next action: {next_action_summary}", description)
        self.assertIn("\n- Recommended section: {recommended_section}", description)
        self.assertNotIn("{recommended_menu_hint}", description)
        self.assertNotIn("The first menu item below", description)
        self.assertNotIn("\n- Recommended path: {recommended_path}", description)
        self.assertIn("\n\nStructured control board\n- Energy state:", description)
        self.assertIn("\n\nSetup check\n- Sensors:", description)
        self.assertLess(description.index("Now\n- Headline decision:"), description.index("\n\nStructured control board"))
        self.assertLess(description.index("\n\nStructured control board"), description.index("\n\nCommand-center use"))
        self.assertIn("\n\nNative paths\n- Sensors:", description)
        self.assertIn("\n- Controls: {policy_path}\n- Live mode shortcut (Controls device action): {mode_path}", description)
        self.assertIn("\n- Managed Devices: {devices_path}", description)
        self.assertIn("\n- Diagnostics: {support_path}", description)
        self.assertIn("\n\nBucket ownership\n- Sensors owns source mapping and source health.", description)
        self.assertIn("Managed Devices owns fleet onboarding, promotion, edits, enablement, and removal: {devices_path}", description)
        self.assertNotIn("Installed package details", description)
        self.assertNotIn("Recommended path right now", description)
        self.assertNotIn("Current mapped roles:", description)
        self.assertNotIn("Live control mode:", description)
        self.assertNotIn("Not here:", description)


if __name__ == "__main__":
    unittest.main()
