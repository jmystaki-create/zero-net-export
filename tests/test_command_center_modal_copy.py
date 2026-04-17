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
        self.assertIn("Structured control board:", description)
        self.assertIn("Setup check:", description)
        self.assertIn("Not here:", description)
        self.assertIn("Managed Devices and candidate promotion", description)
        self.assertNotIn("Installed package details", description)
        self.assertNotIn("Recommended path right now", description)
        self.assertNotIn("Current mapped roles:", description)
        self.assertNotIn("Live control mode:", description)


if __name__ == "__main__":
    unittest.main()
