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

    def test_current_active_bugs_section_tracks_current_highlighted_scope(self):
        bug_tracker = Path(__file__).resolve().parents[1] / "docs" / "BUGS.md"
        content = bug_tracker.read_text(encoding="utf-8")

        active_heading = content.index("## Current active bugs")
        managed_settings = content.index("## ZNE-521 - managed-device config actions lacked visible settings labels")
        unmanaged_suppression = content.index("## ZNE-515 - setup still created peer Un Managed candidate rows")
        superseded_heading = content.index("## Superseded historical release/peer-row bugs retained for context")
        historical_release_scope = content.index("## ZNE-439 - historical release-target mismatch superseded")
        historical_peer_scope = content.index("## ZNE-429 - historical 0.1.91 peer Un Managed device-list scope superseded")
        closed_entries_section = content.index("## Closed bugs and process corrections")
        historical_backlog_section = content.index("## Historical fixed-pending validation backlog")
        active_section = content[active_heading:superseded_heading]
        superseded_section = content[superseded_heading:closed_entries_section]
        zne_439 = content[historical_release_scope:historical_peer_scope]
        zne_429 = content[historical_peer_scope:content.index("## ZNE-498", historical_peer_scope)]

        self.assertLess(active_heading, managed_settings)
        self.assertLess(managed_settings, unmanaged_suppression)
        self.assertLess(unmanaged_suppression, superseded_heading)
        self.assertLess(superseded_heading, historical_release_scope)
        self.assertLess(historical_release_scope, historical_peer_scope)
        self.assertLess(historical_peer_scope, closed_entries_section)
        self.assertLess(closed_entries_section, historical_backlog_section)
        self.assertIn("visible `⚙ Settings` labels", active_section)
        self.assertIn("stops adding unmanaged candidate peer-row entities", active_section)
        self.assertIn("no peer `Un Managed — ...` rows", active_section)
        self.assertIn("not the current work queue", superseded_section)
        self.assertIn("## ZNE-538 - superseded ZNE-439 still reopened the old release-target approval loop", active_section)
        self.assertIn("**status:** `deferred`", zne_439)
        self.assertIn("Riley's explicit approval", zne_439)
        self.assertNotIn("- **status:** `open`", zne_439)
        self.assertNotIn("ask James directly", zne_439)
        self.assertNotIn("release-target decision remains open", zne_439)
        self.assertNotIn("ZNE-439 still blocks deploy/restart/fingerprint/screenshot validation", active_section)
        self.assertNotIn("until James decides the release target", active_section)
        self.assertNotIn("after ZNE-439 is resolved", active_section)
        self.assertIn("Riley-approved live screenshot evidence", zne_429)
        self.assertIn("**status:** `deferred`", zne_429)
        self.assertIn("Do not use the old `0.1.91` peer-row acceptance criteria", zne_429)
        self.assertNotIn("**status:** `closed`", active_section)
        self.assertNotIn("## ZNE-439 - repo froze 0.1.94", active_section)
        self.assertNotIn("only after that decision, ask for native-row acceptance", zne_429)
        self.assertNotIn("must make the Zero Net Export main integration page show", zne_429)
        self.assertIn("## ZNE-466 - closed managed-device code fixes sat under a process-only heading", content[closed_entries_section:historical_backlog_section])
        self.assertIn("## ZNE-444 - closed ZNE-438 remained inside Current active bugs", content[closed_entries_section:historical_backlog_section])
        self.assertIn("## ZNE-438 - 0.1.91 docs still treated", content[closed_entries_section:historical_backlog_section])
        self.assertNotIn("helper-resolved exact `0.1.91` component boundary is now `c4802a3`", active_section)
        self.assertNotIn("repo HEAD and the fingerprint helper now resolve the install candidate to `db5c246`", active_section)
        self.assertNotIn("`git log --oneline -3` shows `db5c246", active_section)
        self.assertNotIn("should `db5c246` / `v0.1.92` replace the documented `0.1.91` release target", active_section)
        self.assertNotIn("should `026f189` / `v0.1.93` replace the documented `0.1.91` release target", active_section)
        self.assertNotIn("0.1.90 acceptance pass", active_section)
        self.assertNotIn("post-`0.1.90`", active_section)

        self.assertIn("## ZNE-550 - historical unmanaged peer-row backlog still carried stale validation gates", active_section)
        self.assertNotIn("ZNE-439 still blocks deploy/restart/fingerprint/screenshot validation", superseded_section)
        self.assertNotIn("until James decides the release target", superseded_section)
        self.assertNotIn("after ZNE-439 is resolved", superseded_section)
        self.assertNotIn("newly discovered `Un Managed — ...` native row entities are added", superseded_section)
        self.assertNotIn("validate on the approved build that `Managed Devices — ...` and `Un Managed — ...` rows still appear", superseded_section)


if __name__ == "__main__":
    unittest.main()
