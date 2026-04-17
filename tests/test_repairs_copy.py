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
        self.assertIn("\n\nOpen\n• Configure:", description)
        self.assertNotIn("Known selector workaround:", description)
        self.assertNotIn("Primary path:", description)

    def test_runtime_attention_copy_uses_compact_sections(self) -> None:
        runtime_attention = self.strings["issues"]["runtime_attention"]
        description = runtime_attention["description"]
        self.assertEqual(runtime_attention["title"], "Zero Net Export runtime blockers")
        self.assertIn("Now\n• Health:", description)
        self.assertIn("\n\nMapped-source blockers\n• Unavailable roles:", description)
        self.assertIn("\n\nDo next\n• Mapped-source repair path:", description)
        self.assertIn("\n\nOpen\n• Configure:", description)
        self.assertNotIn("Best native troubleshooting path right now:", description)


if __name__ == "__main__":
    unittest.main()
