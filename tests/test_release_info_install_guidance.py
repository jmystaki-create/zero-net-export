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
        self.assertEqual(info["released_on"], "2026-05-07")
        self.assertGreaterEqual(info["highlight_count"], 1)
        self.assertLessEqual(info["highlight_count"], 10)
        self.assertGreaterEqual(info["total_highlight_count"], info["highlight_count"])
        self.assertIn("Home Assistant", info["changes_preview"])
        self.assertIn("ZNE-FR-009", info["changes_preview"])
        self.assertIn("async_remove_config_entry_device", info["changes_preview"])
        self.assertIn("ZNE-FR-010", info["changes_preview"])
        self.assertIn("subentry reconfigure", info["changes_preview"])
        self.assertNotIn("James", info["changes_preview"])
        self.assertNotIn("release-target decision", info["changes_preview"])

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
        self.assertIn("old `0.1.91` / release `1.91` scope is now superseded", freeze_section)
        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", freeze_section)
        self.assertIn("## Current execution state", freeze_section)
        self.assertIn("`v0.1.89` is now frozen and tagged at `844502b`", freeze_section)
        self.assertIn("The repo manifest now reports `0.1.89`", freeze_section)
        self.assertIn("do not ask James for permission to perform the already-completed version freeze again", freeze_section)
        self.assertIn("rerun the now-failed `0.1.89` install/restart/live-validation loop", freeze_section)
        self.assertIn("Riley's current highlighted scope in `docs/ACTIVE_USER_REQUESTS.md`", freeze_section)
        self.assertIn("- [x] Freeze the `0.1.89` version-coupled release files.", freeze_section)
        self.assertIn("- [x] Commit the approved freeze: `844502b`.", freeze_section)
        self.assertNotIn("ask James directly to approve the end-to-end `0.1.89` freeze/release/deploy/restart path", freeze_section)
        self.assertNotIn("After James approves, bump manifest/version-coupled expectations to `0.1.89`", freeze_section)
        self.assertNotIn("The next release-execution gap is James's install/restart/live-validation path", freeze_section)
        self.assertNotIn("later ordered UI polish", freeze_section)
        self.assertNotIn("validate the full `docs/UI_DESIGN.md` outcome", freeze_section)
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

        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", supervisor)
        self.assertIn("docs/BUGS.md", supervisor)
        self.assertIn("deprecated design-map requirements", supervisor)
        self.assertIn("Do not reopen old `0.1.91` / `1.91` scope unless Riley explicitly asks", supervisor)
        self.assertNotIn("Use `docs/RELEASE_0.1.91_PLAN.md` as the current release scope", supervisor)
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

    def test_validation_checklist_tracks_current_highlighted_scope(self) -> None:
        checklist = (REPO_ROOT / "docs" / "VALIDATION_CHECKLIST.md").read_text(encoding="utf-8")
        boundary = checklist.split("Repo-side helper for mixed-build checks:", 1)[0]

        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", boundary)
        self.assertIn("managed-device peer rows only", boundary)
        self.assertIn("settings/configuration access", boundary)
        self.assertIn("No peer `Un Managed — ...` unmanaged-candidate rows", boundary)
        self.assertIn("Managed Devices workflow/backlog/review surfaces", boundary)
        self.assertIn("explicit Riley approval", boundary)
        self.assertNotIn("show a `Managed Devices` list under Zero Net Export and an `Un Managed` list underneath it", boundary)
        self.assertNotIn("Managed loads and unmanaged candidates must appear as individual Home Assistant device rows", boundary)
        self.assertNotIn("approved `0.1.91` / release `1.91` scope only", boundary)
        self.assertNotIn("ask James directly to approve the `0.1.89` freeze/release/deploy/restart path", boundary)

    def test_ui_implementation_map_detailed_work_uses_0191_integration_page_scope(self) -> None:
        plan = (REPO_ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")

        self.assertIn("UI_IMPLEMENTATION_MAP.md — DEPRECATED", plan)
        self.assertIn("no longer a project source of truth", plan)
        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", plan)
        self.assertIn("managed devices only", plan)
        self.assertIn("visible settings/gear affordance", plan)
        self.assertIn("no peer `Un Managed — ...`", plan)
        self.assertNotIn("## Detailed remaining work map", plan)
        self.assertNotIn("approved `0.1.91` / release `1.91` scope", plan)

    def test_0190_release_plan_status_does_not_revive_peer_unmanaged_scope(self) -> None:
        release_plan = (REPO_ROOT / "docs" / "RELEASE_0.1.90_PLAN.md").read_text(encoding="utf-8")
        superseded_status = release_plan.split("## Purpose", 1)[0]

        self.assertIn("DEPRECATED/HISTORICAL", superseded_status)
        self.assertIn("managed-only native integration/device peer rows", superseded_status)
        self.assertIn("no peer `Un Managed — ...` unmanaged-candidate rows", superseded_status)
        self.assertIn("old `0.1.91` / release `1.91` peer-row scope is now superseded", superseded_status)
        self.assertNotIn("show `Managed Devices` and `Un Managed` device lists", superseded_status)

    def test_0191_release_plan_is_historical_not_current_peer_row_scope(self) -> None:
        release_plan = (REPO_ROOT / "docs" / "RELEASE_0.1.91_PLAN.md").read_text(encoding="utf-8")

        self.assertIn("Release Plan — DEPRECATED", release_plan)
        self.assertIn("Do not use this file as active release scope", release_plan)
        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", release_plan)
        self.assertIn("Native integration/device peer rows must be **managed-only**", release_plan)
        self.assertIn("Managed rows must visibly show a settings affordance", release_plan)
        self.assertIn("Peer `Un Managed — ...` unmanaged-candidate rows must be suppressed/removed", release_plan)
        self.assertIn("behind Managed Devices workflow/backlog/review surfaces", release_plan)
        self.assertIn("No release, deploy, restart, fingerprint validation, readiness claim, or live screenshot validation", release_plan)
        self.assertNotIn("A visible **Un Managed** group/list", release_plan)
        self.assertNotIn("unmanaged candidates as child Home Assistant devices", release_plan)
        self.assertNotIn("can be called successful only when live Home Assistant screenshot evidence shows the accepted native representation", release_plan)

    def test_0191_success_criteria_respect_accepted_native_grouping_constraint(self) -> None:
        plan = (REPO_ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
        bugs = (REPO_ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        zne_433 = bugs.split("## ZNE-433", 1)[1].split("\n## ZNE-432", 1)[0]

        self.assertIn("DEPRECATED", plan)
        self.assertIn("Current steering lives", plan)
        self.assertIn("Riley's current highlighted bugs/features", plan)
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

        self.assertIn("no longer a project source of truth", ui_design)
        self.assertIn("no longer a project source of truth", plan)
        self.assertIn("claim release readiness without explicit approval and screenshot proof", supervisor)
        self.assertIn("- **status:** `closed`", zne_434)
        self.assertIn("pre-release/pre-success acceptance boundary", zne_434)

    def test_ui_implementation_map_stage9_does_not_reopen_0190_install_loop(self) -> None:
        plan = (REPO_ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")

        self.assertIn("DEPRECATED", plan)
        self.assertNotIn("### Stage 9. Live validation and release gate", plan)
        self.assertNotIn("install/update Home Assistant to the published `v0.1.90` build", plan)
        self.assertIn("No release-readiness claim without proof", (REPO_ROOT / "docs" / "ACTIVE_USER_REQUESTS.md").read_text(encoding="utf-8"))

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

        self.assertIn("DEPRECATED", plan)
        self.assertNotIn("## Historical 0.1.89 success criteria", plan)
        self.assertNotIn("## What counts as success for 0.1.89", plan)
        self.assertIn("Current steering lives", plan)

    def test_supervisor_steering_uses_0191_integration_page_scope(self) -> None:
        supervisor = (REPO_ROOT / "docs" / "SUPERVISOR.md").read_text(encoding="utf-8")

        self.assertIn("Riley's highlighted bugs/features only", supervisor)
        self.assertIn("managed devices must be the only peer rows", supervisor)
        self.assertIn("visible settings/gear affordance", supervisor)
        self.assertIn("unmanaged candidates must not appear as peer `Un Managed — ...` rows", supervisor)
        self.assertNotIn("approved `0.1.91` / release `1.91`", supervisor)
        self.assertNotIn("ordered `0.1.90` corrective UI work", supervisor)

    def test_archived_ui_design_pointer_does_not_revive_0189_active_line(self) -> None:
        archived = (REPO_ROOT / "docs" / "UI_DESIGN-old.md").read_text(encoding="utf-8")

        self.assertIn("historical only", archived)
        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", archived)
        self.assertIn("active scope is now Riley-flagged bugs/features", archived)
        self.assertNotIn("native-only `0.1.89` follow-up", archived)
        self.assertNotIn("`0.1.90` corrective device-page Managed Devices release", archived)

    def test_ui_design_current_visible_outcomes_use_0191_integration_page_boundary(self) -> None:
        design = (REPO_ROOT / "docs" / "UI_DESIGN.md").read_text(encoding="utf-8")

        self.assertIn("UI_DESIGN.md — DEPRECATED", design)
        self.assertIn("no longer a project source of truth", design)
        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", design)
        self.assertIn("managed-only peer rows", design)
        self.assertIn("visible managed-device settings affordance", design)
        self.assertIn("suppression/removal of peer `Un Managed — ...` rows", design)
        self.assertNotIn("The current UI correction target is `0.1.91` / release `1.91`", design)

    def test_ui_implementation_map_uses_current_device_page_action_names(self) -> None:
        plan = (REPO_ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")

        self.assertIn("DEPRECATED", plan)
        self.assertIn("visible settings/gear affordance", plan)
        self.assertNotIn("### Stage 4. Managed Devices workspace redesign", plan)
        self.assertNotIn("`Review managed devices workspace`", plan)
        self.assertNotIn("`Review managed devices`", plan)

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

    def test_current_candidate_changelog_tracks_managed_device_actions_correction_scope(self) -> None:
        sections = release_info._parse_changelog_text((REPO_ROOT / "CHANGELOG.md").read_text())
        current_section = next(
            section for section in sections if section["version"] == release_info.INTEGRATION_VERSION
        )
        current_highlights = "\n".join(current_section["highlights"])

        self.assertIn("ZNE-FR-009", current_highlights)
        self.assertIn("async_remove_config_entry_device", current_highlights)
        self.assertIn("row-overflow Delete", current_highlights)
        self.assertIn("original/source HA device/entity", current_highlights)
        self.assertIn("ZNE-FR-010", current_highlights)
        self.assertIn("subentry reconfigure", current_highlights)
        self.assertNotIn("unsupported device overflow-menu injection", current_highlights.lower())
        self.assertNotIn("arbitrary custom", current_highlights.lower())
        self.assertNotIn("sidebar panel", current_highlights.lower())
        self.assertNotIn("cross-integration registry merge", current_highlights.lower())
        self.assertNotIn("Managed Devices — ⚙ Settings —", current_highlights)
        self.assertNotIn("Added `Managed Devices` and `Un Managed` suggested-area", current_highlights)
        self.assertNotIn("suggested-area/group metadata", current_highlights)
        self.assertNotIn("ask James", current_highlights.lower())
        self.assertNotIn("release-target decision", current_highlights)

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
        self.assertIn("Ask Riley for explicit approval before any release, deploy, Home Assistant restart", message)
        self.assertIn("managed-only native device-list behavior with visible settings affordance and no peer Un Managed rows", message)
        self.assertIn("do not reopen old 0.1.91/0.1.94 release-target questions", message)
        self.assertNotIn("Ask James", message)
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
        self.assertIn("ask riley for explicit approval before any release, deploy, home assistant restart", message.lower())
        self.assertIn("managed-only native device-list behavior with visible settings affordance and no peer Un Managed rows", message)
        self.assertIn("do not reopen old 0.1.91/0.1.94 release-target questions", message)
        self.assertNotIn("Ask James", message)
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
