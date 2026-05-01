from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]


class OperatorDocsConsistencyTests(unittest.TestCase):
    def test_active_user_requests_is_current_source_of_truth(self) -> None:
        content = (ROOT / "docs" / "ACTIVE_USER_REQUESTS.md").read_text(encoding="utf-8")

        self.assertIn("current project steering source of truth", content)
        self.assertIn("`docs/UI_DESIGN.md` and `docs/UI_IMPLEMENTATION_MAP.md` are deprecated", content)
        self.assertIn("Managed-device list must be managed-only", content)
        self.assertIn("Managed rows need the settings gear in the native right-side action location", content)
        self.assertIn("Unmanaged candidates stay behind workflow/backlog surfaces", content)
        self.assertIn("No release-readiness claim without proof", content)
        self.assertIn("When project docs, tests, old release plans, cron prompts, or watchdog/supervisor guidance conflict with this file, this file wins", content)

    def test_ui_design_doc_is_deprecated_not_source_of_truth(self) -> None:
        content = (ROOT / "docs" / "UI_DESIGN.md").read_text(encoding="utf-8")

        self.assertIn("UI_DESIGN.md — DEPRECATED", content)
        self.assertIn("no longer a project source of truth", content)
        self.assertIn("Do not use the previous UI design roadmap", content)
        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", content)
        self.assertNotIn("Single source of truth for the intended native Home Assistant UI design", content)

    def test_ui_implementation_map_is_deprecated_not_source_of_truth(self) -> None:
        content = (ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")

        self.assertIn("UI_IMPLEMENTATION_MAP.md — DEPRECATED", content)
        self.assertIn("no longer a project source of truth", content)
        self.assertIn("Do not use the old ordered workstreams", content)
        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", content)
        self.assertNotIn("Current ordered 0.1.91 map", content)
        self.assertNotIn("Workstream A. Finish the opening operator console", content)

    def test_archived_ui_design_snapshot_points_to_active_requests_not_deprecated_docs(self) -> None:
        content = (ROOT / "docs" / "UI_DESIGN-old.md").read_text(encoding="utf-8")
        source_list = content[content.index("The current source-of-truth files are:"):content.index("This archived file intentionally")]

        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", source_list)
        self.assertIn("docs/BUGS.md", source_list)
        self.assertIn("docs/WATCHDOG.md", source_list)
        self.assertIn("historical references only", source_list)
        self.assertNotIn("docs/UI_DESIGN.md` for product design", source_list)
        self.assertNotIn("docs/UI_IMPLEMENTATION_MAP.md` for implementation strategy", source_list)

    def test_historical_research_docs_do_not_restore_deprecated_ui_sources(self) -> None:
        research = (ROOT / "docs" / "UI_RESEARCH.md").read_text(encoding="utf-8")
        matrix = (ROOT / "docs" / "REFERENCE_MATRIX.md").read_text(encoding="utf-8")

        self.assertIn("CURRENT STATUS: DEPRECATED/HISTORICAL", research)
        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", research)
        self.assertIn("docs/BUGS.md", research)
        self.assertIn("historical reference only: `docs/UI_DESIGN.md`", research)
        self.assertIn("historical reference only: `docs/UI_IMPLEMENTATION_MAP.md`", research)
        self.assertIn("managed-only peer rows", research)
        self.assertNotIn("producing a rewritten `docs/UI_DESIGN.md`", research)

        self.assertIn("CURRENT STATUS: DEPRECATED/HISTORICAL", matrix)
        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", matrix)
        self.assertIn("docs/BUGS.md", matrix)
        self.assertIn("current product strategy defined by `docs/ACTIVE_USER_REQUESTS.md` and `docs/BUGS.md`", matrix)
        self.assertNotIn("product strategy defined in `docs/UI_DESIGN.md`", matrix)

    def test_supervisor_tracks_current_user_flagged_scope(self) -> None:
        content = (ROOT / "docs" / "SUPERVISOR.md").read_text(encoding="utf-8")

        source = content[content.index("## Source of truth"):content.index("## Current mission")]
        mission = content[content.index("## Current mission"):content.index("## Run behavior")]
        gates = content[content.index("## User approval gates"):]

        self.assertIn("`docs/ACTIVE_USER_REQUESTS.md`", source)
        self.assertIn("`docs/BUGS.md`", source)
        self.assertIn("Deprecated and non-authoritative", source)
        self.assertIn("`docs/UI_DESIGN.md`", source)
        self.assertIn("`docs/UI_IMPLEMENTATION_MAP.md`", source)
        self.assertIn("managed devices must be the only peer rows", mission)
        self.assertIn("visible settings/gear affordance", mission)
        self.assertIn("unmanaged candidates must not appear as peer `Un Managed — ...` rows", mission)
        self.assertIn("without explicit approval and screenshot proof", mission)
        self.assertIn("deploying to Home Assistant", gates)
        self.assertIn("tagging or publishing a release", gates)
        self.assertNotIn("current ordered `0.1.91` map", content)
        self.assertNotIn("Active release-target hold", content)

    def test_watchdog_tracks_current_user_flagged_scope(self) -> None:
        content = (ROOT / "docs" / "WATCHDOG.md").read_text(encoding="utf-8")

        source = content[content.index("## Source of truth"):content.index("## Current audit target")]
        audit = content[content.index("## Current audit target"):content.index("## Watchdog behavior")]
        behavior = content[content.index("## Watchdog behavior"):]

        self.assertIn("`docs/ACTIVE_USER_REQUESTS.md`", source)
        self.assertIn("`docs/BUGS.md`", source)
        self.assertIn("Deprecated and non-authoritative", source)
        self.assertIn("managed-only peer rows", audit)
        self.assertIn("visible settings/gear affordance", audit)
        self.assertIn("no peer `Un Managed — ...` unmanaged-candidate rows", audit)
        self.assertIn("no release/deploy/readiness claim without tests, approval, and screenshot proof", audit)
        self.assertIn("catches stale docs/cron/tests restoring deprecated UI-map behavior", behavior)
        self.assertNotIn("current ordered `0.1.91` map", content)
        self.assertNotIn("0.1.89 implementation runway", content)

    def test_bugs_overrides_old_release_scope(self) -> None:
        content = (ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        override = content[content.index("## Current approved scope override"):content.index("## Current active bugs")]

        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", override)
        self.assertIn("old `0.1.91` / release `1.91`", override)
        self.assertIn("superseded", override)
        self.assertIn("managed devices only", override)
        self.assertIn("visible managed-device settings/gear affordance", override)
        self.assertIn("suppress/remove peer `Un Managed — ...`", override)

    def test_steering_bug_records_deprecated_docs_fix(self) -> None:
        content = (ROOT / "docs" / "BUGS.md").read_text(encoding="utf-8")
        bug = content[content.index("## ZNE-514"):content.index("## ZNE-513")]

        self.assertIn("status:** `fixed_pending_validation`", bug)
        self.assertIn("docs/UI_DESIGN.md", bug)
        self.assertIn("docs/UI_IMPLEMENTATION_MAP.md", bug)
        self.assertIn("docs/ACTIVE_USER_REQUESTS.md", bug)
        self.assertIn("updated cron payloads", bug)

    def test_readme_points_to_active_requests_not_deprecated_ui_docs(self) -> None:
        content = (ROOT / "README.md").read_text(encoding="utf-8")
        docs = content[content.index("## 📚 Documentation"):content.index("## 🚧 Development Status")]
        status = content[content.index("## 🚧 Development Status"):]

        self.assertIn("ACTIVE_USER_REQUESTS.md", docs)
        self.assertIn("BUGS.md", docs)
        self.assertIn("deprecated", docs.lower())
        self.assertIn("managed-only", status)
        self.assertIn("visible settings/gear", status)
        self.assertIn("no peer `Un Managed — ...` rows", status)
        self.assertNotIn("Those two files are the UI source of truth", content)

    def test_project_status_tracks_current_user_request_boundary(self) -> None:
        content = (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")

        self.assertIn("ZNE-578", content)
        self.assertIn("ZNE-582", content)
        self.assertIn("supported path", content)
        self.assertIn("0.1.98", content)
        self.assertIn("Release `0.1.100`", content)
        self.assertIn("invalidFlowCount=0", content)
        self.assertNotIn("release `1.91`", content)
        self.assertNotIn("source-of-truth docs still approve only `0.1.91`", content)

    def test_cron_jobs_follow_active_user_requests_and_not_deprecated_docs(self) -> None:
        for name in ["zero-net-export-supervisor-cron.json", "zero-net-export-watchdog-cron.json"]:
            data = json.loads((WORKSPACE / name).read_text(encoding="utf-8"))
            message = data["payload"]["message"]

            self.assertIn("ACTIVE_USER_REQUESTS.md", message)
            self.assertIn("BUGS.md", message)
            self.assertIn("Deprecated docs", message)
            self.assertIn("do not use docs/UI_DESIGN.md or docs/UI_IMPLEMENTATION_MAP.md", message)
            self.assertIn("managed", message)
            self.assertIn("settings/gear affordance", message)
            self.assertIn("no peer Un Managed", message)
            self.assertIn("no", message.lower())
            self.assertNotIn("current ordered `0.1.91` map", message)
            self.assertNotIn("0.1.87 implementation runway", message)


if __name__ == "__main__":
    unittest.main()
