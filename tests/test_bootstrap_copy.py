import json
from pathlib import Path
import unittest


class TestBootstrapCopy(unittest.TestCase):
    def test_add_integration_copy_uses_exact_native_configure_path(self):
        integration_root = Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export"
        with (integration_root / "strings.json").open(encoding="utf-8") as handle:
            strings = json.load(handle)

        user_step = strings["config"]["step"]["user"]
        description = user_step["description"]
        name_help = user_step["data_description"]["name"]
        expected_path = "Settings -> Devices & Services -> Integrations -> Zero Net Export -> Configure"

        self.assertIn(expected_path, description)
        self.assertIn(expected_path, name_help)
        self.assertNotIn("normal Configure flow", description)
        self.assertNotIn("integration's Configure screens", name_help)


if __name__ == "__main__":
    unittest.main()
