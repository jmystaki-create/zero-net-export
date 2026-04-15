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
        self.assertIn("Not here:", description)
        self.assertIn("Managed Devices and candidate promotion", description)
        self.assertNotIn("Installed package details", description)
        self.assertNotIn("Recommended path right now", description)


if __name__ == "__main__":
    unittest.main()
