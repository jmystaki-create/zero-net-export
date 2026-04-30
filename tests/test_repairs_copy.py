import json
from pathlib import Path
import unittest


class RepairsCopyTests(unittest.TestCase):
    def setUp(self) -> None:
        integration_root = Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export"
        with (integration_root / "strings.json").open(encoding="utf-8") as handle:
            self.strings = json.load(handle)
        self.repairs_source = (integration_root / "repairs.py").read_text(encoding="utf-8")

    def test_setup_incomplete_copy_is_short_and_action_first(self) -> None:
        issue = self.strings["issues"]["setup_incomplete"]
        description = issue["description"]
        self.assertEqual(issue["title"], "Finish Zero Net Export setup")
        self.assertTrue(description.startswith("Setup incomplete — control is paused"))
        self.assertIn("\n\nDo this first\n• {next_step}", description)
        self.assertIn("\n\nMissing\n• Source roles: {missing_sources}", description)
        self.assertIn("\n• Managed devices: {device_count}", description)
        self.assertIn("\n\nOpen\n• Sensors:", description)
        self.assertIn("\n• Managed Devices:", description)
        self.assertIn("\n• Controls:", description)
        self.assertIn("\n• Diagnostics:", description)
        self.assertIn("\n\nFallback only if Home Assistant rejects a valid selector choice\n•", description)
        self.assertLess(description.index("Do this first"), description.index("Missing"))
        self.assertLess(len(description), 500)
        self.assertNotIn("Status\n• Summary:", description)
        self.assertNotIn("Command center", description)
        self.assertNotIn("Known selector workaround:", description)
        self.assertNotIn("Primary path:", description)
        self.assertNotIn("Do next\n• {next_step}\n• Selector fallback", description)
        self.assertNotIn("next_step = f\"{next_step} {setup_fallback_hint}\"", self.repairs_source)
        self.assertIn("next_step = next_step.replace(f\" {setup_fallback_hint}\", \"\").replace(setup_fallback_hint, \"\").strip()", self.repairs_source)

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
        self.assertNotIn("Installed package:", description)
        self.assertNotIn("Install consistency:", description)
        self.assertIn("\n\nActive blockers\n• Unavailable source roles:", description)
        self.assertIn("\n• Stale source roles:", description)
        self.assertIn("\n\nDo next\n• {next_step}", description)
        self.assertNotIn("Mapped-source blockers", description)
        self.assertNotIn("Mapped-source repair path", description)
        self.assertNotIn("\n• Next step:", description)
        self.assertIn("\n\nFallback, only if Home Assistant rejects a valid choice\n•", description)
        self.assertIn("\n\nOpen\n• Command center:", description)
        self.assertIn("\n• Sensors:", description)
        self.assertIn("\n• Controls:", description)
        self.assertIn("\n• Managed Devices:", description)
        self.assertIn("\n• Diagnostics:", description)
        self.assertNotIn("Best native troubleshooting path right now:", description)
        self.assertNotIn("Do next\n• Mapped-source repair path: {source_repair_step}\n• Next step: {next_step}\n• Selector fallback", description)

    def test_runtime_attention_uses_sparse_runtime_attr_helper(self) -> None:
        self.assertIn("def _runtime_attr(data: Any, attr: str, fallback: Any = None) -> Any:", self.repairs_source)
        self.assertIn("stale_data = bool(_runtime_attr(data, \"stale_data\", False))", self.repairs_source)
        self.assertIn("safe_mode = bool(_runtime_attr(data, \"safe_mode\", False))", self.repairs_source)
        self.assertIn("command_failure = bool(_runtime_attr(data, \"command_failure\", False))", self.repairs_source)
        self.assertIn("def _runtime_int(data: Any, attr: str) -> int:", self.repairs_source)
        self.assertIn("device_count = _runtime_int(data, \"device_count\")", self.repairs_source)
        self.assertIn("_runtime_attr(data, \"health_summary\") or summary", self.repairs_source)
        self.assertNotIn("if data.stale_data:", self.repairs_source)
        self.assertNotIn("if data.safe_mode:", self.repairs_source)
        self.assertNotIn("if data.command_failure:", self.repairs_source)
        self.assertNotIn("data.recommendation", self.repairs_source)
        self.assertNotIn("data.health_summary", self.repairs_source)

    def test_runtime_attention_reasons_use_source_roles_not_mapped_source_jargon(self) -> None:
        self.assertIn("Stale required source roles:", self.repairs_source)
        self.assertIn("Unavailable source roles are holding safe mode:", self.repairs_source)
        self.assertNotIn("Stale required mapped sources:", self.repairs_source)
        self.assertNotIn("Unavailable mapped sources are holding safe mode:", self.repairs_source)


if __name__ == "__main__":
    unittest.main()
