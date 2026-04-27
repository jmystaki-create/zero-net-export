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

    def test_current_active_bugs_section_contains_091_blocker(self):
        bug_tracker = Path(__file__).resolve().parents[1] / "docs" / "BUGS.md"
        content = bug_tracker.read_text(encoding="utf-8")

        active_heading = content.index("## Current active bugs")
        current_blocker = content.index("## ZNE-429 - 0.1.91 main integration page lacks Managed Devices")
        first_closed_process_entry = content.index("## ZNE-432 - Current active bugs heading excluded")

        self.assertLess(active_heading, current_blocker)
        self.assertLess(current_blocker, first_closed_process_entry)


if __name__ == "__main__":
    unittest.main()
