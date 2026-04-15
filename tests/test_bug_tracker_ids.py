import re
from pathlib import Path
import unittest


class TestBugTrackerIds(unittest.TestCase):
    def test_bug_ids_are_unique(self):
        bug_tracker = Path(__file__).resolve().parents[1] / "docs" / "BUGS.md"
        content = bug_tracker.read_text(encoding="utf-8")
        ids = re.findall(r"^## (ZNE-\d+) — ", content, flags=re.MULTILINE)

        self.assertTrue(ids, "BUGS.md should contain tracked bug headings")
        self.assertEqual(len(ids), len(set(ids)), f"duplicate bug ids found in BUGS.md: {ids}")


if __name__ == "__main__":
    unittest.main()
