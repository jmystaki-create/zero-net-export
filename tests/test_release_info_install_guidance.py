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
        self.assertEqual(info["released_on"], "2026-04-28")
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

    def test_0189_release_plan_tracks_post_freeze_and_superseded_state(self) -> None:
        plan = (REPO_ROOT / "docs" / "RELEASE_0.1.89_PLAN.md").read_text(encoding="utf-8")
        freeze_section = plan.split("### B. Publish", 1)[0]
        install_section = plan.split("### C. James install/test path", 1)[1].split("## Acceptance outcomes", 1)[0]
        failure_section = plan.split("## Validation failure outcome", 1)[1]

        self.assertIn("## Superseded status", freeze_section)
        self.assertIn("This plan is historical", freeze_section)
        self.assertIn("The corrective `0.1.90` device-info-page release plan and `ZNE-411` validation loop are historical and insufficient", freeze_section)
        self.assertIn("The active approved scope is `0.1.91` / release `1.91`", freeze_section)
        self.assertIn("## Current execution state", freeze_section)
        self.assertIn("`v0.1.89` is now frozen and tagged at `844502b`", freeze_section)
        self.assertIn("The repo manifest now reports `0.1.89`", freeze_section)
        self.assertIn("do not ask James for permission to perform the already-completed version freeze again", freeze_section)
        self.assertIn("rerun the now-failed `0.1.89` install/restart/live-validation loop", freeze_section)
        self.assertIn("- [x] Freeze the `0.1.89` version-coupled release files.", freeze_section)
        self.assertIn("- [x] Commit the approved freeze: `844502b`.", freeze_section)
        self.assertNotIn("ask James directly to approve the end-to-end `0.1.89` freeze/release/deploy/restart path", freeze_section)
        self.assertNotIn("After James approves, bump manifest/version-coupled expectations to `0.1.89`", freeze_section)
        self.assertNotIn("The next release-execution gap is James's install/restart/live-validation path", freeze_section)
        self.assertIn("historical, completed and failed", install_section)
        self.assertIn("James's live screenshot showed the device page did not visibly deliver the requested Managed Devices surface", install_section)
        self.assertIn("Do not use this historical checklist to ask James to repeat the `0.1.89` install/restart/live-validation loop", install_section)
        self.assertIn("The `0.1.90` approval, freeze, deploy, restart, fingerprint, screenshot, and Managed Devices action-drill-down path is now complete", install_section)
        self.assertIn("screenshot, and Managed Devices action-drill-down path is now complete", install_section)
        self.assertNotIn("remaining release-execution gap is screenshot-grade", install_section)
        self.assertNotIn("- [ ] James refreshes HACS metadata", install_section)
        self.assertNotIn("- [ ] James installs/updates to `v0.1.89`", install_section)
        self.assertIn("Validation did fail on the device-page Managed Devices outcome", failure_section)
        self.assertIn("Do not fix or republish another `0.1.89` candidate", failure_section)
        self.assertIn("Do not continue through the completed `docs/RELEASE_0.1.90_PLAN.md` / `ZNE-411` screenshot loop", failure_section)



    def test_zne_403_process_bug_no_longer_reopens_completed_freeze_release_boundary(self) -> None:
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        zne_403 = bugs.split("## ZNE-403", 1)[1].split("\n## ZNE-402", 1)[0]

        self.assertIn("- **status:** `closed`", zne_403)
        self.assertIn("already-completed `0.1.89` freeze or GitHub publication", zne_403)
        self.assertIn("Do not ask James to reinstall `v0.1.89`", zne_403)
        self.assertIn("Do not ask James to reinstall `v0.1.89` or reopen completed `0.1.90` release/deploy/restart approval", zne_403)
        self.assertIn("capturing screenshot-grade device-page Managed Devices evidence", zne_403)
        self.assertNotIn("ask James directly to approve the `0.1.89` freeze/release/deploy/restart path", zne_403)
        self.assertNotIn("ask James to approve the `0.1.89` freeze/release/deploy/restart path", zne_403)

    def test_zne_411_next_action_is_live_install_validation_not_more_repo_surface_churn(self) -> None:
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        zne_411 = bugs.split("## ZNE-411", 1)[1].split("\n## ZNE-410", 1)[0]

        self.assertIn("- **status:** `closed`", zne_411)
        self.assertIn("installed, fingerprint-matched `v0.1.90` build at `d94436a`", zne_411)
        self.assertIn("live API reported `sensor.zero_net_export_installed_version = 0.1.90`", zne_411)
        self.assertIn("`overall_match: true`", zne_411)
        self.assertIn("docs/evidence/0.1.90-device-page-managed-devices-surface.png", zne_411)
        self.assertIn("docs/evidence/0.1.90-managed-devices-workspace-notification.png", zne_411)
        self.assertIn("do not reopen the completed `0.1.90` install/restart/fingerprint/screenshot loop", zne_411)
        self.assertNotIn("repo-side corrective candidate is ready for release approval", zne_411)
        self.assertNotIn("ask James directly for `0.1.90` release/deploy/restart validation approval", zne_411)
        self.assertNotIn("finish any remaining native device-page surface implementation", zne_411)
        self.assertNotIn("release as `0.1.90`, deploy/restart", zne_411)
        self.assertNotIn("Screenshot-grade device-page proof and action drill-down validation remain required", zne_411)

    def test_zne_427_supervisor_no_longer_reopens_closed_0190_delivery_target(self) -> None:
        supervisor = (REPO_ROOT / "docs" / "SUPERVISOR.md").read_text(encoding="utf-8")
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        zne_427 = bugs.split("## ZNE-427", 1)[1].split("\n## ZNE-426", 1)[0]

        self.assertIn("0.1.91 / release 1.91 approved scope", supervisor)
        self.assertIn("Use `docs/RELEASE_0.1.91_PLAN.md` as the current release scope", supervisor)
        self.assertIn("Treat `0.1.90` device-info-page work as historical and insufficient", supervisor)
        self.assertIn("the approved `0.1.91` / release `1.91` integration-main-page device-list scope", supervisor)
        self.assertNotIn("Treat `docs/RELEASE_0.1.90_PLAN.md` and `ZNE-411` as the current delivery target", supervisor)
        self.assertNotIn("ordered `0.1.90` corrective UI work", supervisor)
        self.assertIn("- **status:** `closed`", zne_427)
        self.assertIn("Supervisor still treated closed ZNE-411 as the current delivery target", zne_427)
        self.assertIn("no Home Assistant live validation is required for this process-state correction", zne_427)

    def test_active_bug_next_actions_do_not_reopen_closed_zne_411_screenshot_loop(self) -> None:
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        entries = ["## ZNE-" + entry for entry in bugs.split("\n## ZNE-")[1:]]
        active_fixed_pending = [
            entry
            for entry in entries
            if "- **status:** `fixed_pending_validation`" in entry
        ]
        active_next_actions = "\n".join(
            line
            for entry in active_fixed_pending
            for line in entry.splitlines()
            if line.startswith("- **next action:**")
        )

        self.assertIn("## ZNE-428 - Active tracker tails still reopened closed ZNE-411 screenshot validation", bugs)
        self.assertIn("- **status:** `closed`", bugs.split("## ZNE-428", 1)[1].split("\n## ZNE-427", 1)[0])
        self.assertIn("include these Configure Managed Devices workspace labels in the next installed-build/browser acceptance pass", active_next_actions)
        self.assertIn("include this Managed Devices review/workspace capitalization", active_next_actions)
        self.assertNotIn("continue `ZNE-411`", active_next_actions)
        self.assertNotIn("capturing screenshot-grade device-page Managed Devices evidence", active_next_actions)
        self.assertNotIn("capture screenshot-grade device-page Managed Devices evidence", active_next_actions)

    def test_bug_tracker_no_longer_points_active_next_actions_at_0189_install_loop(self) -> None:
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        active_entries = bugs.split("## ZNE-416", 1)[1].split("## ZNE-415", 1)[1]

        self.assertNotIn("next exact `0.1.89` deploy", active_entries)
        self.assertNotIn("already-published `v0.1.89` install/restart/live-validation pass", active_entries)
        self.assertNotIn("James installs/updates to `v0.1.89`", active_entries)
        self.assertNotIn("Live Home Assistant validation remains pending on deploy/restart of the exact `0.1.89` candidate", active_entries)
        self.assertIn("recheck it opportunistically during the installed, fingerprint-matched `0.1.90` acceptance pass", bugs)
        self.assertIn("Do not ask James to reinstall `v0.1.89`", bugs)
        self.assertNotIn("ask James directly for `0.1.90` release/deploy/restart validation approval", bugs)
        self.assertNotIn("release/deploy/restart validation approval once the corrective repo candidate is ready", bugs)
        self.assertNotIn("release approval once the repo candidate is ready", bugs)
        self.assertIn("do not reopen the completed release/deploy/restart approval boundary", bugs)

    def test_release_bug_entries_no_longer_reopen_old_mixed_build_or_hacs_targets(self) -> None:
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        zne_037 = bugs.split("## ZNE-037", 1)[1].split("\n## ZNE-038", 1)[0]
        zne_022 = bugs.split("## ZNE-022", 1)[1].split("\n## ZNE-065", 1)[0]

        self.assertIn("- **status:** `open`", zne_037)
        self.assertIn("verify the repository row surfaces `v0.1.90`", zne_037)
        self.assertIn("should be checked only when there is a materially new HACS refresh/release-management step", zne_037)
        self.assertNotIn("`v0.1.88` until `v0.1.89`", zne_037)
        self.assertNotIn("ongoing `0.1.89` UI implementation work", zne_037)

        self.assertIn("- **status:** `closed`", zne_022)
        self.assertIn("historical mixed-build fingerprint mismatch", zne_022)
        self.assertIn("Home Assistant reported `sensor.zero_net_export_installed_version = 0.1.90`", zne_022)
        self.assertIn("current component boundary is now `b01da73`", zne_022)
        self.assertIn("do not request another `0.1.89` install/restart", zne_022)
        self.assertNotIn("live `manifest_version` remains `0.1.86`", zne_022)
        self.assertNotIn("future exact-build proof through the `0.1.89` freeze", zne_022)

    def test_validation_checklist_tracks_0191_integration_page_boundary(self) -> None:
        checklist = (REPO_ROOT / "docs" / "VALIDATION_CHECKLIST.md").read_text(encoding="utf-8")
        boundary = checklist.split("Repo-side helper for mixed-build checks:", 1)[0]

        self.assertIn("approved `0.1.91` / release `1.91` scope only", boundary)
        self.assertIn("`v0.1.89` and `v0.1.90` are historical", boundary)
        self.assertIn("Zero Net Export **main integration page**", boundary)
        self.assertIn("show a `Managed Devices` list under Zero Net Export and an `Un Managed` list underneath it", boundary)
        self.assertIn("Managed loads and unmanaged candidates must appear as individual Home Assistant device rows", boundary)
        self.assertIn("No release/deploy validation is approved by this documentation update alone", boundary)
        self.assertNotIn("mapped `0.1.89` workstream order", boundary)
        self.assertNotIn("mapped `0.1.90` corrective device-page Managed Devices workstream order", boundary)
        self.assertNotIn("ask James directly to approve the `0.1.89` freeze/release/deploy/restart path", boundary)
        self.assertNotIn("Only after approval, freeze the helper-resolved candidate as `0.1.89`", boundary)

    def test_ui_implementation_map_detailed_work_uses_0191_integration_page_scope(self) -> None:
        plan = (REPO_ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
        detailed_map = plan.split("## Detailed remaining work map", 1)[1].split("### Stage 0.", 1)[0]

        self.assertIn("approved `0.1.91` / release `1.91` scope", detailed_map)
        self.assertIn("managed and unmanaged device lists on the Zero Net Export main integration page", detailed_map)
        self.assertIn("Workstream G. Exact-build validation and release execution", detailed_map)
        self.assertIn("Treat the repo-side native child-device implementation as present", detailed_map)
        self.assertIn("Capture screenshot-grade live evidence from `Settings -> Devices & Services -> Integrations -> Zero Net Export`", detailed_map)
        self.assertIn("ZNE-429 and `docs/RELEASE_0.1.91_PLAN.md` as the active implementation scope", detailed_map)
        release_target = detailed_map.index("Resolve the release-target mismatch")
        native_acceptance = detailed_map.index("After the release-target decision, ask James directly whether the closest Home Assistant-native device-registry representation is acceptable")
        order_summary_target = detailed_map.index("Ask James directly for the release-target decision first")
        order_summary_acceptance = detailed_map.index("After that target decision")

        self.assertLess(release_target, native_acceptance)
        self.assertLess(order_summary_target, order_summary_acceptance)
        self.assertIn("ask James directly whether this closest native representation is acceptable for the chosen target", detailed_map)
        self.assertIn("froze `v0.1.92` at `db5c246` and `v0.1.93` at `026f189`", detailed_map)
        self.assertIn("helper now resolves the frozen candidate to `4c0d071` / `v0.1.94`", detailed_map)
        self.assertIn("ask James directly whether `v0.1.94` replaces the documented `0.1.91` target", detailed_map)
        self.assertIn("`7217f3b`, the post-tag `c4802a3` component boundary, the unapproved `db5c246` / `v0.1.92` freeze, the unapproved `026f189` / `v0.1.93` freeze, and the newer `4c0d071` / `v0.1.94` freeze are not deploy approval", detailed_map)
        self.assertNotIn("Only after a repo implementation exists should the project enter `0.1.91` release/fingerprint/live-screenshot execution", detailed_map)
        self.assertNotIn("future `0.1.91` / release `1.91` integration-main-page device-list implementation", detailed_map)
        self.assertNotIn("published `v0.1.90` corrective release", detailed_map)
        self.assertNotIn("convert the published `v0.1.90` corrective release into a real installed", detailed_map)
        self.assertNotIn("freeze version-coupled metadata as `0.1.90`", detailed_map)
        self.assertNotIn("convert the repo candidate into a real shipped and validated `0.1.89` release", detailed_map)
        self.assertNotIn("Publish/deploy the approved `v0.1.89` candidate", detailed_map)

    def test_0191_release_plan_and_bug_tracker_make_human_boundary_explicit(self) -> None:
        release_plan = (REPO_ROOT / "docs" / "RELEASE_0.1.91_PLAN.md").read_text(encoding="utf-8")
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        zne_429 = bugs.split("## ZNE-429", 1)[1].split("\n## ZNE-432", 1)[0]

        self.assertIn("later `v0.1.94` at `4c0d071`", release_plan)
        self.assertIn("Do not deploy, restart, fingerprint-validate, or call successful either the old `7217f3b` tag", release_plan)
        self.assertIn("until James explicitly decides whether `v0.1.94` replaces the documented `0.1.91` release target", release_plan)
        self.assertIn("do not treat the `v0.1.91` freeze/tag, the unapproved `v0.1.92` freeze/tag, the unapproved `v0.1.93` freeze/tag, or the unapproved `v0.1.94` freeze/tag", zne_429)
        self.assertIn("Ask James directly whether `4c0d071` / `v0.1.94` should replace", zne_429)
        self.assertIn("only after that decision, ask for native-row acceptance and exact release/deploy/restart approval", zne_429)
        self.assertIn("If James rejects the closest native child-device representation", release_plan)
        self.assertIn("visible `Managed Devices — ...` and `Un Managed — ...` device row/model grouping", release_plan)
        self.assertIn("now resolves as manifest `0.1.94` / preferred validation commit `4c0d071`", zne_429)
        self.assertNotIn("review whether the closest native device-info representation is acceptable", zne_429)
        self.assertNotIn("if accepted, freeze `0.1.91`", zne_429)
        self.assertNotIn("before freezing/deploying `0.1.91`", zne_429)
        self.assertIn("ZNE-438 - 0.1.91 docs still treated the pre-fix tag as the exact deploy boundary", zne_429)

    def test_0191_success_criteria_respect_accepted_native_grouping_constraint(self) -> None:
        plan = (REPO_ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
        success = plan.split("## What counts as success for 0.1.91 / release 1.91", 1)[1].split(
            "See `docs/RELEASE_0.1.91_PLAN.md`", 1
        )[0]
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        zne_433 = bugs.split("## ZNE-433", 1)[1].split("\n## ZNE-432", 1)[0]

        self.assertIn("accepted native child-device representation", success)
        self.assertIn("James-accepted native `Managed Devices — ...` row/model grouping", success)
        self.assertIn("James-accepted native `Un Managed — ...` row/model grouping", success)
        self.assertIn("if James rejects the native child-device representation", zne_433)
        self.assertIn("closed with repo-side source-of-truth/test validation", zne_433)

    def test_0191_platform_constraint_boundary_is_pre_release_not_pre_implementation(self) -> None:
        ui_design = (REPO_ROOT / "docs" / "UI_DESIGN.md").read_text(encoding="utf-8")
        plan = (REPO_ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
        supervisor = (REPO_ROOT / "docs" / "SUPERVISOR.md").read_text(encoding="utf-8")
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        zne_434 = bugs.split("## ZNE-434", 1)[1].split("\n## ZNE-433", 1)[0]

        for text in (ui_design, plan, supervisor):
            self.assertNotIn("before implementation and the closest native representation", text)
            self.assertNotIn("before implementation substitutes another representation", text)
            self.assertIn("before release execution", text)

        self.assertIn("agreed before the candidate is called successful", ui_design)
        self.assertIn("ask James whether the closest native device-registry representation is acceptable", plan)
        self.assertIn("- **status:** `closed`", zne_434)
        self.assertIn("pre-release/pre-success acceptance boundary", zne_434)

    def test_ui_implementation_map_stage9_does_not_reopen_0190_install_loop(self) -> None:
        plan = (REPO_ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
        stage9 = plan.split("### Stage 9. Live validation and release gate", 1)[1].split(
            "## Historical 0.1.89 release rollout view", 1
        )[0]

        self.assertIn("Home Assistant reports `sensor.zero_net_export_installed_version = 0.1.90`", stage9)
        self.assertIn("`overall_match: true`", stage9)
        self.assertIn("live API state exposes the `Managed Devices surface` row", stage9)
        self.assertIn("pressed `button.zero_net_export_show_fleet_console` and `button.zero_net_export_show_managed_device_review`", stage9)
        self.assertIn("docs/evidence/0.1.90-device-page-managed-devices-surface.png", stage9)
        self.assertIn("docs/evidence/0.1.90-managed-devices-workspace-notification.png", stage9)
        self.assertIn("do not keep repeating API-only button.press checks", stage9)
        self.assertIn("no remaining `0.1.90` install/fingerprint/screenshot gate", stage9)
        self.assertNotIn("install/update Home Assistant to the published `v0.1.90` build", stage9)

    def test_zne_424_closes_api_only_action_drilldown_loop(self) -> None:
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        zne_424 = bugs.split("## ZNE-424", 1)[1].split("\n## ZNE-423", 1)[0]

        self.assertIn("- **status:** `closed`", zne_424)
        self.assertIn("button.zero_net_export_show_fleet_console", zne_424)
        self.assertIn("button.zero_net_export_show_managed_device_review", zne_424)
        self.assertIn("no `persistent_notification.*` state", zne_424)
        self.assertIn("browser-visible native notification/review proof", zne_424)
        self.assertIn("do not repeat the completed `0.1.90` install/restart/fingerprint or API-only button-press loops", zne_424)

    def test_zne_423_closes_stale_stage9_install_loop(self) -> None:
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        zne_423 = bugs.split("## ZNE-423", 1)[1].split("\n## ZNE-422", 1)[0]

        self.assertIn("- **status:** `closed`", zne_423)
        self.assertIn("still listed `install/update Home Assistant", zne_423)
        self.assertIn("button.zero_net_export_show_managed_device_review", zne_423)
        self.assertIn("screenshot-grade proof remains open", zne_423)
        self.assertIn("do not reopen the completed `0.1.90` install/restart/fingerprint loop", zne_423)

    def test_ui_implementation_map_keeps_0189_success_gate_historical(self) -> None:
        plan = (REPO_ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
        current_success = plan.split("### Still blocked or incomplete", 1)[1].split(
            "## What counts as success for 0.1.91 / release 1.91", 1
        )[0]

        self.assertIn("## Historical 0.1.89 success criteria (failed on device-page evidence)", current_success)
        self.assertIn("Keep this section as historical evidence only", current_success)
        self.assertIn("The clarified active target is now `0.1.91` integration-main-page device lists", current_success)
        self.assertNotIn("## What counts as success for 0.1.89", current_success)
        self.assertNotIn("`0.1.89` should not be called a successful UI release", current_success)

    def test_supervisor_steering_uses_0191_integration_page_scope(self) -> None:
        supervisor = (REPO_ROOT / "docs" / "SUPERVISOR.md").read_text(encoding="utf-8")
        optimization_target = supervisor.split("## Project optimization target", 1)[1].split("## What counts as real progress", 1)[0]
        acceptance_stance = supervisor.split("## Acceptance stance", 1)[1].split("## Release behavior", 1)[0]

        self.assertIn("approved `0.1.91` / release `1.91` integration-page Managed Devices and Un Managed device-list scope", optimization_target)
        self.assertIn("the approved `0.1.91` / release `1.91` integration-main-page device-list scope", acceptance_stance)
        self.assertIn("Zero Net Export main integration page visibly shows a Managed Devices device list and an Un Managed device list", acceptance_stance)
        self.assertNotIn("remaining `0.1.90` corrective device-page Managed Devices UI rollout", optimization_target)
        self.assertNotIn("ordered `0.1.90` corrective UI work", acceptance_stance)
        self.assertNotIn("remaining `0.1.89` UI rollout", optimization_target)
        self.assertNotIn("ordered `0.1.89` UI work", acceptance_stance)

    def test_archived_ui_design_pointer_does_not_revive_0189_active_line(self) -> None:
        archived = (REPO_ROOT / "docs" / "UI_DESIGN-old.md").read_text(encoding="utf-8")

        self.assertIn("historical only", archived)
        self.assertIn("native-only `0.1.91` / release `1.91` integration-main-page Managed Devices and Un Managed device-list scope", archived)
        self.assertIn("docs/RELEASE_0.1.91_PLAN.md", archived)
        self.assertNotIn("native-only `0.1.89` follow-up", archived)
        self.assertNotIn("`0.1.90` corrective device-page Managed Devices release", archived)

    def test_ui_design_current_visible_outcomes_use_0191_integration_page_boundary(self) -> None:
        design = (REPO_ROOT / "docs" / "UI_DESIGN.md").read_text(encoding="utf-8")
        visible_outcomes = design.split(
            "## The four required visible outcomes for the current UI correction line", 1
        )[1].split("## UX principles", 1)[0]
        integration_page = design.split("## Integration-page Managed Devices device lists", 1)[1].split(
            "## Managed Devices workspace", 1
        )[0]

        self.assertIn("The current UI correction target is `0.1.91` / release `1.91`", visible_outcomes)
        self.assertIn("or `0.1.90` wording", visible_outcomes)
        self.assertIn("main integration page", integration_page)
        self.assertIn("Managed Devices", integration_page)
        self.assertIn("Un Managed", integration_page)
        self.assertIn("does not satisfy this design target", integration_page)
        self.assertNotIn("The current UI correction target is `0.1.90`", visible_outcomes)
        self.assertNotIn("The current UI correction target is `0.1.89`", visible_outcomes)
        self.assertNotIn("these three visible outcomes", visible_outcomes)

    def test_ui_implementation_map_uses_current_device_page_action_names(self) -> None:
        plan = (REPO_ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
        active_stages = plan.split("### Stage 4. Managed Devices workspace redesign", 1)[1].split(
            "## Historical 0.1.89 release rollout view", 1
        )[0]

        self.assertIn("`Open Managed Devices workspace`", active_stages)
        self.assertIn("`Open Managed Devices review`", active_stages)
        self.assertNotIn("`Review managed devices workspace`", active_stages)
        self.assertNotIn("`Review managed devices`", active_stages)

    def test_release_0190_plan_marks_release_published_and_live_validation_pending(self) -> None:
        plan = (REPO_ROOT / "docs" / "RELEASE_0.1.90_PLAN.md").read_text(encoding="utf-8")
        checklist = plan.split("## Candidate implementation checklist", 1)[1].split(
            "## Acceptance test", 1
        )[0]

        self.assertIn(
            "corrective repo candidate has been frozen, tagged, pushed, published as `v0.1.90` at `d94436a`, installed in Home Assistant",
            checklist,
        )
        self.assertIn("browser-validated with screenshot-grade Managed Devices device-page plus action-drill-down evidence", checklist)
        self.assertIn("- [x] Add or adjust a dedicated device-page Managed Devices summary row/entity if needed.", checklist)
        self.assertIn("- [x] Run full tests for the repo candidate.", checklist)
        self.assertIn("- [x] Ask James directly for `0.1.90` release/deploy/restart validation approval.", checklist)
        self.assertIn("- [x] Commit, tag `v0.1.90`, push, and publish GitHub release only after approval/release readiness.", checklist)
        self.assertIn("- [x] Deploy exact `0.1.90` build to Home Assistant or verify HACS installs it.", checklist)
        self.assertIn("- [x] Validate install fingerprint `overall_match: true` against `d94436a` over the documented SSH path.", checklist)
        self.assertIn("- [x] Capture screenshot-grade proof of the device page showing the Managed Devices surface", checklist)
        self.assertIn("- [x] Verify pressing the Managed Devices action opens the expected notification/review/window", checklist)
        self.assertNotIn("- [ ] Add or adjust a dedicated device-page Managed Devices summary row/entity if needed.", checklist)
        self.assertNotIn("- [ ] Capture screenshot-grade proof of the device page showing the Managed Devices surface.", checklist)

    def test_current_changelog_records_0191_integration_page_device_list_fix(self) -> None:
        sections = release_info._parse_changelog_text((REPO_ROOT / "CHANGELOG.md").read_text())
        current_section = next(section for section in sections if section["version"] == "0.1.91")
        current_highlights = "\n".join(current_section["highlights"])

        self.assertIn("main integration page", current_highlights)
        self.assertIn("Managed Devices", current_highlights)
        self.assertIn("Un Managed", current_highlights)
        self.assertIn("integration-page device rows", current_highlights)

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
