from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OperatorDocsConsistencyTests(unittest.TestCase):
    def test_detailed_map_orders_current_091_scope_before_historical_workstreams(self) -> None:
        content = (ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
        current = content.index("### Current ordered 0.1.91 map")
        historical = content.index("### Historical broad UI workstreams - not the current 0.1.91 ordered map")
        workstream_a = content.index("### Workstream A. Finish the opening operator console")
        workstream_g = content.index("### Workstream G. Exact-build validation and release execution")

        self.assertLess(current, historical)
        self.assertLess(historical, workstream_a)
        self.assertLess(workstream_a, workstream_g)
        current_map = content[current:historical]
        release_target = current_map.index("Resolve the release-target mismatch")
        native_acceptance = current_map.index("After the release-target decision")
        deploy_gate = current_map.index("Only after that release-target decision, native-row acceptance")

        self.assertLess(release_target, native_acceptance)
        self.assertLess(native_acceptance, deploy_gate)
        self.assertIn("`v0.1.94` at `4c0d071`", current_map)
        self.assertIn("helper must resolve the current manifest `0.1.94` component boundary at decision/deploy time", current_map)
        self.assertIn("ask James directly for release/deploy/restart approval", current_map)
        self.assertIn("Settings -> Devices & Services -> Integrations -> Zero Net Export", current_map)

    def test_historical_workstreams_cannot_outrank_091_device_list_scope(self) -> None:
        content = (ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
        status_summary = content[
            content.index("## Status summary"):
            content.index("## Historical 0.1.89 success criteria")
        ]
        historical_note = content[
            content.index("### Historical broad UI workstreams - not the current 0.1.91 ordered map"):
            content.index("### Workstream A. Finish the opening operator console")
        ]

        self.assertIn("not eligible work ahead of the approved `0.1.91`", historical_note)
        self.assertIn("Do not let them outrank the current ordered `0.1.91` map", historical_note)
        order_from_here = content[
            content.index("### Order of execution from here"):
            content.index("### Stage 0. Baseline and source-of-truth consolidation")
        ]
        release_target = order_from_here.index("Ask James directly for the release-target decision first")
        native_acceptance = order_from_here.index("After that target decision")

        self.assertIn("current ordered `0.1.91` map", status_summary)
        self.assertLess(release_target, native_acceptance)
        self.assertNotIn("mapped Workstream A-D/F gap", status_summary)

    def test_supervisor_release_hold_names_all_frozen_candidates(self) -> None:
        content = (ROOT / "docs" / "SUPERVISOR.md").read_text(encoding="utf-8")
        hold = content[
            content.index("## Active release-target hold"):
            content.index("\n\nThis file is the steering guide")
        ]

        self.assertIn("earlier `v0.1.92` and `v0.1.93` freezes", hold)
        self.assertIn("`v0.1.94` at `4c0d071`", hold)
        self.assertIn("`7217f3b`, `c4802a3`, `db5c246`, `026f189`, `4c0d071`, or the current helper-resolved component boundary", hold)
        self.assertNotIn("earlier `v0.1.92` and `v0.1.94` freezes", hold)

    def test_supervisor_churn_rules_do_not_reopen_historical_a_to_f_workstreams(self) -> None:
        content = (ROOT / "docs" / "SUPERVISOR.md").read_text(encoding="utf-8")
        churn_rules = content[
            content.index("### Rule 5: Update source-of-truth only when it changes a real decision"):
            content.index("### Rule 7: Release approval is edge-triggered")
        ]

        self.assertIn("current ordered repo work from the `0.1.91` map", churn_rules)
        self.assertIn("current ordered `0.1.91` map work", churn_rules)
        self.assertNotIn("higher ordered A-D/F", churn_rules)
        self.assertNotIn("earlier mapped A-D/F", churn_rules)

    def test_project_status_tracks_current_091_approval_boundary(self) -> None:
        content = (ROOT / "project_status.md").read_text(encoding="utf-8")

        next_action = content[
            content.index("next_action:"):
            content.index("\n\n# Current blocker or none")
        ]
        blocker = content[
            content.index("blocker:"):
            content.index("\n\n# Exact user action needed or none")
        ]
        target_decision = next_action.index("whether the current helper-resolved manifest `0.1.94` component boundary should replace")
        native_acceptance = next_action.index("only after that target decision")
        live_evidence = next_action.index("before integration-main-page screenshot evidence")
        blocker_target = blocker.index("release-target decision")
        blocker_native = blocker.index("closest native child-device representation acceptance")
        blocker_deploy = blocker.index("release/deploy/restart approval")

        self.assertIn("`0.1.91`", content)
        self.assertIn("ask James directly", content)
        self.assertIn("release/deploy/restart approval", content)
        self.assertIn("native child-device representation", content)
        self.assertIn("`4c0d071` / `v0.1.94` freezes", content)
        self.assertLess(target_decision, native_acceptance)
        self.assertLess(native_acceptance, live_evidence)
        self.assertLess(blocker_target, blocker_native)
        self.assertLess(blocker_native, blocker_deploy)
        self.assertNotIn("release-target acceptance plus release/deploy/restart approval", blocker)
        self.assertNotIn("`0.1.89`", content)
        self.assertNotIn("published `v0.1.88`", content)
        self.assertNotIn("A-D/F", content)

    def test_readme_tracks_current_091_release_target_hold(self) -> None:
        content = (ROOT / "README.md").read_text(encoding="utf-8")
        status = content[content.index("## 🚧 Development Status"):]

        self.assertIn("main integration page", status)
        self.assertIn("`Managed Devices — ...`", status)
        self.assertIn("`Un Managed — ...`", status)
        self.assertIn("the current helper-resolved manifest `0.1.94` component boundary", status)
        self.assertIn("`v0.1.94` at `4c0d071`", status)
        self.assertIn("documented `0.1.91` release target", status)
        self.assertIn("ask James directly", status)
        self.assertNotIn("0.1.89", status)
        self.assertNotIn("0.1.88", status)
        self.assertNotIn("A-D/F", status)

    def test_readme_manual_deploy_guidance_keeps_approval_order(self) -> None:
        content = (ROOT / "README.md").read_text(encoding="utf-8")
        install = content[
            content.index("## 📦 Installation"):
            content.index("## ⚙️ Configuration")
        ]

        self.assertIn("do not make deploy/restart the first approval ask", install)
        self.assertIn("do not skip the current release-target and native-row acceptance boundaries", install)
        self.assertIn("whether the current helper-resolved manifest `0.1.94` component boundary replaces the documented `0.1.91` release target", install)
        self.assertIn("after that target decision, ask whether the closest native `Managed Devices — ...` / `Un Managed — ...` child-device representation is acceptable", install)
        self.assertIn("then ask for exact release/deploy/restart approval for that accepted target", install)
        self.assertIn("Only after those approvals, run `python3 scripts/deploy_exact_repo_build.py", install)
        self.assertIn("only after James has made the current release-target decision, accepted the closest native child-device representation, and approved exact deploy/restart", content)
        self.assertNotIn("ask James directly to approve deploy/restart first", install)
        self.assertNotIn("after James approves deploy/restart, can pin", content)

    def test_watchdog_tracks_current_091_scope_not_historical_runway(self) -> None:
        content = (ROOT / "docs" / "WATCHDOG.md").read_text(encoding="utf-8")
        source_order = content[
            content.index("## Source-of-truth order"):
            content.index("## Core watchdog rules")
        ]
        rule_6 = content[
            content.index("### Rule 6: Treat repeated unchanged live validation as secondary while ordered repo work remains"):
            content.index("### Rule 7: Use available access before escalating")
        ]
        source_docs = content[content.index("## Source documents"):]

        self.assertIn("`docs/SUPERVISOR.md`", source_order)
        self.assertIn("current ordered `0.1.91` map work", rule_6)
        self.assertIn("ZNE-429/ZNE-439 decision boundary", rule_6)
        self.assertIn("integration-main-page device-list scope", rule_6)
        self.assertIn("`docs/SUPERVISOR.md`", source_docs)
        self.assertNotIn("`SUPERVISOR.md`", source_order)
        self.assertNotIn("0.1.89 implementation runway", rule_6)
        self.assertNotIn("0.1.88 implementation runway", rule_6)
        self.assertNotIn("0.1.87 implementation runway", rule_6)

    def test_validation_checklist_keeps_release_target_decision_before_live_validation(self) -> None:
        content = (ROOT / "docs" / "VALIDATION_CHECKLIST.md").read_text(encoding="utf-8")
        boundary = content[
            content.index("## Next validation boundary"):
            content.index("## Pre-Installation Checks")
        ]

        target_decision = boundary.index("whether the current helper-resolved manifest `0.1.94` component boundary replaces the documented `0.1.91` release target")
        native_acceptance = boundary.index("Only after that release-target decision")
        validation_steps = boundary.index("For `0.1.91`, validation is only about the main integration page device lists")

        self.assertIn("the current helper-resolved manifest `0.1.94` component boundary", boundary)
        self.assertIn("before any Home Assistant install, restart, fingerprint validation, or screenshot claim", boundary)
        self.assertIn("exact release/deploy/restart validation", boundary)
        self.assertIn("do not make deploy/restart the first approval ask", boundary)
        self.assertIn("after that target decision, ask whether the closest native `Managed Devices — ...` / `Un Managed — ...` child-device representation is acceptable", boundary)
        self.assertIn("Only after those approvals, run `python3 scripts/deploy_exact_repo_build.py", boundary)
        self.assertNotIn("ask James directly to approve deploy/restart before using deploy commands", boundary)
        self.assertLess(target_decision, native_acceptance)
        self.assertLess(native_acceptance, validation_steps)


if __name__ == "__main__":
    unittest.main()
