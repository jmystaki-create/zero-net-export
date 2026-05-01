import json
from pathlib import Path
import unittest


class TestCommandCenterModalCopy(unittest.TestCase):
    def test_init_modal_is_native_guided_flow_launcher(self):
        integration_root = Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export"
        with (integration_root / "strings.json").open(encoding="utf-8") as handle:
            strings = json.load(handle)

        step = strings["options"]["step"]["init"]
        description = step["description"]

        self.assertEqual(step["title"], "Zero Net Export guided setup")
        self.assertTrue(description.startswith("Choose the next native Home Assistant workflow"))
        self.assertIn("\n\nGuided workflows\n- Sensors: map source roles", description)
        self.assertIn("- Controls: tune target export, deadband, reserve, and refresh interval.", description)
        self.assertIn("- Managed Devices: add, review, enable, edit, or remove controllable loads.", description)
        self.assertIn("- Diagnostics: review blockers, install evidence, and repair hints.", description)
        self.assertIn("Recommended section: {recommended_section}", description)
        self.assertIn("Recommended path: {recommended_path}.", description)
        self.assertNotIn("Structured control board", description)
        self.assertNotIn("Bucket ownership", description)
        self.assertNotIn("Command-center use", description)
        self.assertNotIn("The first menu item below", description)


if __name__ == "__main__":
    unittest.main()
