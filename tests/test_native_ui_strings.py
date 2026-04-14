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
                "native_setup": "Sensors and source mapping",
                "policy": "Controls",
                "devices": "Managed devices",
                "support": "Diagnostics",
                "advanced": "Advanced JSON editor and recovery",
            },
        )
        self.assertIn("four main Configure sections", init_step["description"])
        self.assertIn("Live mode remains the nearby device-path handoff, not another Configure section.", init_step["description"])
        self.assertIn("Detailed management remains the deeper device-view handoff outside this Configure menu.", init_step["description"])
        self.assertIn("Use these native sections for the most common operator jobs:", init_step["description"])
        self.assertIn("- Fix source mapping, unavailable sensors, or stale source health: {sources_path}", init_step["description"])
        self.assertIn("- Add, review, edit, enable, disable, or remove controllable loads: {devices_path}", init_step["description"])
        self.assertIn("- Change export target, deadband, reserve, and controller defaults: {policy_path}", init_step["description"])
        self.assertIn("- Change live control mode right now: {mode_path}", init_step["description"])
        self.assertIn("- Check runtime health, install consistency, and troubleshooting guidance: {support_path}", init_step["description"])
        self.assertIn("- Sensors and source mapping: {sources_path}", init_step["description"])
        self.assertIn("- Controls: {policy_path}", init_step["description"])
        self.assertIn("- Diagnostics: {support_path}.", init_step["description"])
        self.assertIn("Why this section is recommended: {recommended_reason}", init_step["description"])
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

    def test_source_and_diagnostics_copy_emphasize_returning_to_sensors_after_repairs(self) -> None:
        payload = json.loads(STRINGS_PATH.read_text(encoding="utf-8"))
        setup_issue = payload["issues"]["setup_incomplete"]
        runtime_issue = payload["issues"]["runtime_attention"]
        sensors_step = payload["options"]["step"]["native_setup"]
        source_mapping_step = payload["options"]["step"]["native_setup_sources"]
        diagnostics_step = payload["options"]["step"]["support"]

        self.assertIn(
            "Recommended command-center section: {recommended_section}",
            setup_issue["description"],
        )
        self.assertIn(
            "Recommended native path right now: {recommended_path}",
            setup_issue["description"],
        )
        self.assertIn(
            "Why this section is recommended: {recommended_reason}",
            setup_issue["description"],
        )
        self.assertIn(
            "Current mapped roles:\n{source_mapping_summary}",
            setup_issue["description"],
        )
        self.assertIn(
            "Affected mapped roles: {source_attention_roles}",
            runtime_issue["description"],
        )
        self.assertIn(
            "Current mapped roles:\n{source_mapping_summary}",
            runtime_issue["description"],
        )
        self.assertIn(
            "Recommended command-center section: {recommended_section}",
            runtime_issue["description"],
        )
        self.assertIn(
            "Recommended native path right now: {recommended_path}",
            runtime_issue["description"],
        )
        self.assertIn(
            "Why this section is recommended: {recommended_reason}",
            runtime_issue["description"],
        )
        self.assertIn(
            "After source repairs, reopen Configure -> Sensors and source mapping to confirm live source health.",
            runtime_issue["description"],
        )
        self.assertIn(
            "After any save or reload, come back here to confirm the mapped roles are healthy again.",
            sensors_step["description"],
        )
        self.assertIn(
            "After each save, reload the integration and reopen this Sensors and source mapping screen to confirm live source health.",
            source_mapping_step["description"],
        )
        self.assertIn(
            "If you need to change setup rather than diagnose it, jump back to these native paths first:",
            diagnostics_step["description"],
        )
        self.assertIn(
            "- Sensors and source mapping for source repair: {sources_path}",
            diagnostics_step["description"],
        )
        self.assertIn(
            "- Managed devices for fleet changes: {devices_path}",
            diagnostics_step["description"],
        )
        self.assertIn(
            "- Controls for policy tuning: {policy_path}",
            diagnostics_step["description"],
        )
        self.assertIn(
            "- Live mode control on the device path: {mode_path}",
            diagnostics_step["description"],
        )
        self.assertIn(
            "Why this section is recommended: {recommended_reason}",
            diagnostics_step["description"],
        )
        self.assertIn(
            "When the blocker is source-related, finish by reopening Sensors and source mapping to confirm the mapped roles recover.",
            diagnostics_step["description"],
        )


if __name__ == "__main__":
    unittest.main()
