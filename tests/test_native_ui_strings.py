from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STRINGS_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "strings.json"
TRANSLATIONS_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "translations" / "en.json"


class NativeUiStringsTests(unittest.TestCase):
    maxDiff = None

    def test_en_translation_matches_strings_file(self) -> None:
        strings_payload = json.loads(STRINGS_PATH.read_text(encoding="utf-8"))
        translation_payload = json.loads(TRANSLATIONS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(strings_payload, translation_payload)

    def test_command_center_uses_current_native_sections(self) -> None:
        payload = json.loads(STRINGS_PATH.read_text(encoding="utf-8"))
        init_step = payload["options"]["step"]["init"]
        self.assertEqual(
            init_step["menu_options"],
            {
                "native_setup": "Sensors",
                "policy": "Controls",
                "devices": "Managed devices",
                "support": "Diagnostics",
                "advanced": "Advanced JSON editor and recovery",
            },
        )
        self.assertIn("four main Configure sections", init_step["description"])
        self.assertIn("Detailed management remains the deeper device-view handoff outside this Configure menu.", init_step["description"])
        self.assertIn("- Sensors: {sources_path}", init_step["description"])
        self.assertIn("- Controls: {policy_path}", init_step["description"])
        self.assertIn("- Diagnostics: {support_path}.", init_step["description"])
        self.assertNotIn("- Detailed management:", init_step["description"])
        self.assertNotIn("{detailed_management_summary}", init_step["description"])
        self.assertNotIn("{detailed_management_path}", init_step["description"])

    def test_managed_devices_step_clarifies_detailed_management_handoff(self) -> None:
        payload = json.loads(STRINGS_PATH.read_text(encoding="utf-8"))
        devices_step = payload["options"]["step"]["devices"]
        self.assertIn(
            "Detailed management remains the deeper device-view handoff for per-device status, reset actions, and support details, not another Configure menu option.",
            devices_step["description"],
        )
        self.assertIn("Primary path: {configure_path}.", devices_step["description"])
        self.assertNotIn("Detailed management handoff:", devices_step["description"])
        self.assertNotIn("Detailed management path:", devices_step["description"])
        self.assertNotIn("{detailed_management_summary}", devices_step["description"])
        self.assertNotIn("{detailed_management_path}", devices_step["description"])


if __name__ == "__main__":
    unittest.main()
