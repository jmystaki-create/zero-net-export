from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_DIR = REPO_ROOT / "custom_components" / "zero_net_export"


def load_integration_module(module_name: str, filename: str):
    package_roots = {
        "custom_components": REPO_ROOT / "custom_components",
        "custom_components.zero_net_export": INTEGRATION_DIR,
    }
    for name, path in package_roots.items():
        if name not in sys.modules:
            package = types.ModuleType(name)
            package.__path__ = [str(path)]
            sys.modules[name] = package

    qualified_name = f"custom_components.zero_net_export.{module_name}"
    spec = importlib.util.spec_from_file_location(qualified_name, INTEGRATION_DIR / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified_name] = module
    spec.loader.exec_module(module)
    return module


release_info = load_integration_module("release_info", "release_info.py")


class ReleaseInfoInstallGuidanceTests(unittest.TestCase):
    def tearDown(self) -> None:
        release_info._cached_install_provenance.cache_clear()
        release_info._INSTALL_PROVENANCE_SNAPSHOT = None

    def test_parse_changelog_text_keeps_indented_bullets_under_release_sections(self) -> None:
        sections = release_info._parse_changelog_text(
            "\n".join(
                [
                    "## [0.1.81] - 2026-04-13",
                    "",
                    "### Fixed",
                    "  - First shipped fix",
                    "    - Follow-up detail still counts as a highlight",
                    "",
                    "## [Unreleased]",
                ]
            )
        )

        self.assertEqual(sections[0]["version"], "0.1.81")
        self.assertEqual(
            sections[0]["highlights"],
            ["First shipped fix", "Follow-up detail still counts as a highlight"],
        )

    def test_build_release_info_uses_current_release_changelog_entry_with_release_date(self) -> None:
        info = release_info.build_release_info(release_info.INTEGRATION_VERSION)

        self.assertEqual(info["current_version"], release_info.INTEGRATION_VERSION)
        self.assertTrue(info["has_changelog"])
        self.assertEqual(info["released_on"], "2026-04-27")
        self.assertGreaterEqual(info["highlight_count"], 1)
        self.assertLessEqual(info["highlight_count"], 10)
        self.assertGreaterEqual(info["total_highlight_count"], info["highlight_count"])
        self.assertIn("Home Assistant", info["changes_preview"])

    def test_0189_changelog_carries_post_tag_ui_fixes(self) -> None:
        sections = release_info._parse_changelog_text((REPO_ROOT / "CHANGELOG.md").read_text())
        unreleased_section = next(section for section in sections if section["version"] == "0.1.89")
        unreleased_highlights = "\n".join(unreleased_section["highlights"])

        self.assertIn("0.1.89", unreleased_highlights)
        self.assertIn("Source blockers", unreleased_highlights)
        self.assertIn("Managed Devices", unreleased_highlights)
        self.assertIn("Diagnostics", unreleased_highlights)
        self.assertIn("Home Assistant", unreleased_highlights)
        self.assertLessEqual(len(unreleased_section["highlights"]), 10)
        self.assertNotIn("mapped-source", unreleased_highlights.lower())
        self.assertNotIn("mapped-role", unreleased_highlights.lower())
        self.assertNotIn("source-mapping", unreleased_highlights.lower())
        self.assertNotIn("source mapping", unreleased_highlights.lower())
        self.assertNotIn("0.1.83", unreleased_highlights)
        self.assertNotIn("suggested candidates", unreleased_highlights.lower())
        self.assertNotIn("Suggested preset", unreleased_highlights)
        self.assertNotIn("Recommended next step", unreleased_highlights)
        self.assertNotIn("recommendation", unreleased_highlights.lower())
        self.assertNotIn("0.1.88 candidate", unreleased_highlights)

    def test_0189_release_plan_tracks_post_freeze_state(self) -> None:
        plan = (REPO_ROOT / "docs" / "RELEASE_0.1.89_PLAN.md").read_text(encoding="utf-8")
        freeze_section = plan.split("### B. Publish", 1)[0]

        self.assertIn("## Current execution state", freeze_section)
        self.assertIn("`v0.1.89` is now frozen and tagged at `844502b`", freeze_section)
        self.assertIn("The repo manifest now reports `0.1.89`", freeze_section)
        self.assertIn("do not ask James for permission to perform the already-completed version freeze again", freeze_section)
        self.assertIn("- [x] Freeze the `0.1.89` version-coupled release files.", freeze_section)
        self.assertIn("- [x] Commit the approved freeze: `844502b`.", freeze_section)
        self.assertNotIn("ask James directly to approve the end-to-end `0.1.89` freeze/release/deploy/restart path", freeze_section)
        self.assertNotIn("After James approves, bump manifest/version-coupled expectations to `0.1.89`", freeze_section)



    def test_zne_403_process_bug_no_longer_reopens_completed_freeze_release_boundary(self) -> None:
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        zne_403 = bugs.split("## ZNE-403", 1)[1].split("\n## ZNE-402", 1)[0]

        self.assertIn("- **status:** `closed`", zne_403)
        self.assertIn("already-completed `0.1.89` freeze or GitHub publication", zne_403)
        self.assertIn("James installs/updates to `v0.1.89`", zne_403)
        self.assertNotIn("ask James directly to approve the `0.1.89` freeze/release/deploy/restart path", zne_403)
        self.assertNotIn("ask James to approve the `0.1.89` freeze/release/deploy/restart path", zne_403)

    def test_validation_checklist_tracks_published_0189_state(self) -> None:
        checklist = (REPO_ROOT / "docs" / "VALIDATION_CHECKLIST.md").read_text(encoding="utf-8")
        boundary = checklist.split("Repo-side helper for mixed-build checks:", 1)[0]

        self.assertIn("`v0.1.89` is already frozen at `844502b`, tagged, pushed, and published", boundary)
        self.assertIn("Do not ask James to approve the already-completed freeze or GitHub publication again", boundary)
        self.assertIn("James installing/updating to `v0.1.89` and approving the Home Assistant restart/live-validation pass", boundary)
        self.assertNotIn("ask James directly to approve the `0.1.89` freeze/release/deploy/restart path", boundary)
        self.assertNotIn("Only after approval, freeze the helper-resolved candidate as `0.1.89`", boundary)

    def test_current_candidate_changelog_avoids_stale_ranking_or_deeper_path_wording(self) -> None:
        sections = release_info._parse_changelog_text((REPO_ROOT / "CHANGELOG.md").read_text())
        current_section = next(
            section for section in sections if section["version"] == release_info.INTEGRATION_VERSION
        )
        current_highlights = "\n".join(current_section["highlights"])

        self.assertNotIn("top candidate", current_highlights)
        self.assertNotIn("top-candidate", current_highlights)
        self.assertNotIn("runtime-ranked", current_highlights)
        self.assertNotIn("fleet-console", current_highlights)
        self.assertNotIn("back into Configure -> Managed Devices", current_highlights)
        self.assertNotIn("back into the full Settings", current_highlights)
        self.assertNotIn("deeper review", current_highlights)
        self.assertNotIn("deep-review", current_highlights)
        self.assertNotIn("active `0.1.86` release line", current_highlights)
        self.assertNotIn("active UI-correction line", current_highlights)
        self.assertNotIn("0.1.86` release line", current_highlights)
        self.assertNotIn("recommended section reason", current_highlights.lower())
        self.assertNotIn("recommended configure section", current_highlights.lower())
        self.assertNotIn("recommended native section", current_highlights.lower())
        self.assertNotIn("recommended next section", current_highlights.lower())
        self.assertNotIn("recommended next device action", current_highlights.lower())
        self.assertNotIn("mapped-source", current_highlights.lower())
        self.assertNotIn("source mapping", current_highlights.lower())

    def test_cli_steps_use_parent_custom_components_path_for_component_root(self) -> None:
        steps = release_info.build_install_validation_cli_steps(
            {"component_root": "/tmp/ha config/custom_components/zero_net_export"}
        )

        self.assertEqual(steps["compare_target"], "/tmp/ha config/custom_components")
        self.assertIn("'/tmp/ha config/custom_components'", steps["deploy_command"])
        self.assertIn("'/tmp/ha config/custom_components'", steps["combined_command"])

    def test_install_repair_step_for_manifest_mismatch_names_resolved_target_and_commands(self) -> None:
        message = release_info.build_install_repair_step(
            {
                "component_root": "/srv/homeassistant/config/custom_components/zero_net_export",
                "manifest_matches_code_version": False,
            }
        )

        self.assertIn("/srv/homeassistant/config/custom_components", message)
        self.assertIn("Ask James directly to approve deploy/restart", message)
        self.assertIn("--dry-run", message)
        self.assertIn("deploy_exact_repo_build.py", message)
        self.assertIn("validate_install_fingerprint.py", message)
        self.assertIn("one synchronized build", message)

    def test_install_repair_step_for_manifest_error_mentions_same_live_install_path(self) -> None:
        message = release_info.build_install_repair_step(
            {
                "component_root": "/srv/homeassistant/config/custom_components/zero_net_export",
                "manifest_error": "missing manifest",
            }
        )

        self.assertIn("Confirm the exact live Zero Net Export install path", message)
        self.assertIn("ask James directly to approve deploy/restart", message)
        self.assertIn("/srv/homeassistant/config/custom_components", message)
        self.assertIn("that same live install path", message)

    def test_install_fingerprint_summary_includes_compare_target(self) -> None:
        summary = release_info.build_install_fingerprint_summary(
            {
                "component_root": "/srv/homeassistant/config/custom_components/zero_net_export",
                "code_version": "0.1.80",
                "manifest_version": "0.1.79",
                "manifest_matches_code_version": False,
                "tracked_files": {},
            }
        )

        self.assertIn(
            "- validation_compare_target: /srv/homeassistant/config/custom_components",
            summary,
        )
        self.assertIn("deploy_exact_build_dry_run_command", summary)
        self.assertIn("combined_validation_command", summary)

    def test_build_install_provenance_returns_pending_snapshot_until_async_prime_runs(self) -> None:
        release_info._cached_install_provenance.cache_clear()
        release_info._INSTALL_PROVENANCE_SNAPSHOT = None

        result = release_info.build_install_provenance()

        self.assertTrue(result["pending_async_refresh"])
        self.assertEqual(result["code_version"], release_info.INTEGRATION_VERSION)
        self.assertEqual(result["tracked_files"], {})

    def test_async_prime_install_provenance_warms_snapshot_via_executor(self) -> None:
        release_info._cached_install_provenance.cache_clear()
        release_info._INSTALL_PROVENANCE_SNAPSHOT = None
        calls: list[object] = []

        class DummyHass:
            async def async_add_executor_job(self, target):
                calls.append(target)
                return target()

        result = asyncio.run(release_info.async_prime_install_provenance(DummyHass()))

        self.assertEqual(calls, [release_info._collect_install_provenance])
        self.assertEqual(result["code_version"], release_info.INTEGRATION_VERSION)
        self.assertIn("__init__.py", result["tracked_files"])
        self.assertIn("button.py", result["tracked_files"])
        self.assertIn("candidate_utils.py", result["tracked_files"])
        self.assertIn("diagnostics.py", result["tracked_files"])
        self.assertIn("repairs.py", result["tracked_files"])
        self.assertIn("release_info.py", result["tracked_files"])
        self.assertIn("sensor.py", result["tracked_files"])
        self.assertNotIn("__pycache__/sensor.cpython-311.pyc", result["tracked_files"])
        self.assertIsNotNone(release_info._INSTALL_PROVENANCE_SNAPSHOT)
        self.assertEqual(release_info._cached_install_provenance.cache_info().currsize, 0)


if __name__ == "__main__":
    unittest.main()
