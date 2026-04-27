import re
from pathlib import Path
import unittest


class TestBugTrackerIds(unittest.TestCase):
    def test_bug_ids_are_unique(self):
        bug_tracker = Path(__file__).resolve().parents[1] / "docs" / "BUGS.md"
        content = bug_tracker.read_text(encoding="utf-8")
        ids = re.findall(r"^## (ZNE-\d+)\s+[—-]\s+", content, flags=re.MULTILINE)

        self.assertTrue(ids, "BUGS.md should contain tracked bug headings")
        self.assertEqual(len(ids), len(set(ids)), f"duplicate bug ids found in BUGS.md: {ids}")

    def test_current_active_bugs_section_contains_current_release_blockers(self):
        bug_tracker = Path(__file__).resolve().parents[1] / "docs" / "BUGS.md"
        content = bug_tracker.read_text(encoding="utf-8")

        active_heading = content.index("## Current active bugs")
        release_drift = content.index("## ZNE-439 - repo froze 0.1.94")
        current_blocker = content.index("## ZNE-429 - 0.1.91 main integration page lacks Managed Devices")
        closed_process_section = content.index("## Closed process corrections")
        historical_backlog_section = content.index("## Historical fixed-pending validation backlog")
        active_section = content[active_heading:closed_process_section]

        self.assertLess(active_heading, release_drift)
        self.assertLess(release_drift, current_blocker)
        self.assertLess(current_blocker, closed_process_section)
        self.assertLess(closed_process_section, historical_backlog_section)
        self.assertIn("should `4c0d071` / `v0.1.94` replace the documented `0.1.91` release target", active_section)
        self.assertIn("resolves the component install candidate to the frozen `4c0d071` / `v0.1.94` build", active_section)
        self.assertIn("`preferred_validation_commit: 4c0d071`", active_section)
        self.assertIn("unapproved `v0.1.94` freeze/tag", active_section)
        self.assertIn("only after that decision, ask for native-row acceptance", active_section)
        self.assertNotIn("**status:** `closed`", active_section)
        self.assertNotIn("## ZNE-438 - 0.1.91 docs still treated", active_section)
        self.assertIn("## ZNE-444 - closed ZNE-438 remained inside Current active bugs", content[closed_process_section:historical_backlog_section])
        self.assertIn("## ZNE-438 - 0.1.91 docs still treated", content[closed_process_section:historical_backlog_section])
        self.assertNotIn("helper-resolved exact `0.1.91` component boundary is now `c4802a3`", active_section)
        self.assertNotIn("repo HEAD and the fingerprint helper now resolve the install candidate to `db5c246`", active_section)
        self.assertNotIn("`git log --oneline -3` shows `db5c246", active_section)
        self.assertNotIn("should `db5c246` / `v0.1.92` replace the documented `0.1.91` release target", active_section)
        self.assertNotIn("should `026f189` / `v0.1.93` replace the documented `0.1.91` release target", active_section)
        self.assertNotIn("0.1.90 acceptance pass", active_section)
        self.assertNotIn("post-`0.1.90`", active_section)


if __name__ == "__main__":
    unittest.main()
