import json
from pathlib import Path
import unittest


class TestCommandCenterModalCopy(unittest.TestCase):
    def test_init_modal_stays_setup_focused(self):
        integration_root = Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export"
        with (integration_root / "strings.json").open(encoding="utf-8") as handle:
            strings = json.load(handle)

        description = strings["options"]["step"]["init"]["description"]

        self.assertIn("basic setup and current operating picture only", description)
        self.assertIn("Open Managed Devices only after the current setup blockers are clear", description)
        self.assertIn("\n\nNow\n- Headline decision:", description)
        self.assertIn("\n- Top alerts: {alert_summary}", description)
        self.assertIn("\n- Recommended next step: {next_action_summary}", description)
        self.assertIn("\n\nStructured control board\n- Energy state:", description)
        self.assertIn("\n\nSetup check\n- Sensors:", description)
        self.assertIn("\n\nBasic setup paths\n- Sensors:", description)
        self.assertIn("\n- Controls, including the live mode shortcut: {policy_path} (device shortcut: {mode_path})", description)
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
