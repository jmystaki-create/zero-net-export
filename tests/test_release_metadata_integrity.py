from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "custom_components" / "zero_net_export" / "manifest.json"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
README_PATH = REPO_ROOT / "README.md"
TEST_INSTALL_MANIFEST_PATH = REPO_ROOT / "tmp" / "test-ha-config" / "custom_components" / "zero_net_export" / "manifest.json"


class ReleaseMetadataIntegrityTests(unittest.TestCase):
    maxDiff = None

    def _manifest_version(self, path: Path) -> str:
        return str(json.loads(path.read_text(encoding="utf-8"))["version"])

    def test_current_manifest_version_has_changelog_entry(self) -> None:
        version = self._manifest_version(MANIFEST_PATH)
        changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
        self.assertIn(f"## [{version}]", changelog)
        self.assertNotIn(f"## [{version}]\n\n### Fixed\n- Integration version advanced", changelog)

    def test_test_install_fixture_manifest_matches_repo_manifest(self) -> None:
        self.assertEqual(
            self._manifest_version(TEST_INSTALL_MANIFEST_PATH),
            self._manifest_version(MANIFEST_PATH),
        )

    def test_readme_current_highest_value_next_step_points_to_current_remote_sync_then_exact_deploy_flow(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "**Current highest-value next step:** push the intended deploy-helper commit to the tracked remote branch",
            readme,
        )


if __name__ == "__main__":
    unittest.main()
