import json
from pathlib import Path
import unittest


class RepairsCopyTests(unittest.TestCase):
    def setUp(self) -> None:
        integration_root = Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export"
        with (integration_root / "strings.json").open(encoding="utf-8") as handle:
            self.strings = json.load(handle)

    def test_setup_incomplete_copy_uses_compact_sections(self) -> None:
        description = self.strings["issues"]["setup_incomplete"]["description"]
        self.assertIn("Status\n• Summary:", description)
        self.assertIn("\n\nDo next\n•", description)
        self.assertIn("\n\nFallback, only if Home Assistant rejects a valid choice\n•", description)
        self.assertIn("\n\nOpen\n• Command center:", description)
        self.assertIn("\n• Sensors:", description)
        self.assertIn("\n• Controls:", description)
        self.assertIn("\n• Managed Devices:", description)
        self.assertIn("\n• Diagnostics:", description)
        self.assertNotIn("Known selector workaround:", description)
        self.assertNotIn("Primary path:", description)
        self.assertNotIn("Do next\n• {next_step}\n• Selector fallback", description)

    def test_device_inventory_invalid_copy_uses_compact_sections(self) -> None:
        description = self.strings["issues"]["device_inventory_invalid"]["description"]
        self.assertIn("Status\n• Issue count:", description)
        self.assertIn("\n\nDo next\n• Repair the affected fleet entries in the Managed Devices workspace first.", description)
        self.assertNotIn("Repair the affected fleet entries in Managed Devices first.", description)
        self.assertIn("\n\nOpen\n• Managed Devices:", description)
        self.assertIn("\n• Advanced recovery:", description)
        self.assertNotIn("Primary repair path:", description)
        self.assertNotIn("Advanced recovery path:", description)

    def test_runtime_attention_copy_uses_compact_sections(self) -> None:
        runtime_attention = self.strings["issues"]["runtime_attention"]
        description = runtime_attention["description"]
        self.assertEqual(runtime_attention["title"], "Zero Net Export runtime blockers")
        self.assertIn("Now\n• Health:", description)
        self.assertIn("\n\nMapped-source blockers\n• Unavailable roles:", description)
        self.assertIn("\n\nDo next\n• Mapped-source repair path:", description)
        self.assertIn("\n\nFallback, only if Home Assistant rejects a valid choice\n•", description)
        self.assertIn("\n\nOpen\n• Command center:", description)
        self.assertIn("\n• Sensors:", description)
        self.assertIn("\n• Managed Devices:", description)
        self.assertIn("\n• Diagnostics:", description)
        self.assertNotIn("Best native troubleshooting path right now:", description)
        self.assertNotIn("Do next\n• Mapped-source repair path: {source_repair_step}\n• Next step: {next_step}\n• Selector fallback", description)


if __name__ == "__main__":
    unittest.main()
