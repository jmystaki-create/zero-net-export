from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPONENT_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"


class InstallHelperScriptsTests(unittest.TestCase):
    maxDiff = None

    def run_script(self, relative_path: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / relative_path), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )

    def test_print_expected_install_fingerprint_reports_current_repo(self) -> None:
        result = self.run_script("scripts/print_expected_install_fingerprint.py")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["component_root"], str(COMPONENT_ROOT))
        self.assertIn("manifest.json", payload["tracked_files"])
        self.assertTrue(payload["tracked_files"]["manifest.json"]["exists"])
        self.assertEqual(payload["tracked_files"]["translations/en.json"]["path"], str(COMPONENT_ROOT / "translations" / "en.json"))

    def test_compare_install_fingerprint_matches_copied_install_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_root = Path(tmpdir) / "config"
            install_root = config_root / "custom_components" / "zero_net_export"
            shutil.copytree(COMPONENT_ROOT, install_root)

            result = self.run_script("scripts/compare_install_fingerprint.py", str(config_root))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["comparison"]["overall_match"])
            self.assertEqual(payload["actual"]["component_root"], str(install_root))

    def test_compare_install_fingerprint_refuses_repo_source_tree(self) -> None:
        result = self.run_script("scripts/compare_install_fingerprint.py", str(COMPONENT_ROOT))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to compare against the repo source tree itself", result.stderr)

    def test_deploy_exact_repo_build_dry_run_resolves_target_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_root = Path(tmpdir) / "config"
            result = self.run_script("scripts/deploy_exact_repo_build.py", str(config_root), "--dry-run")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(f"resolved_destination={config_root / 'custom_components' / 'zero_net_export'}", result.stdout)
            self.assertIn("action=preview_only", result.stdout)

    def test_deploy_exact_repo_build_copies_and_validates_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_root = Path(tmpdir) / "config"
            result = self.run_script("scripts/deploy_exact_repo_build.py", str(config_root))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("post_copy_validation=passed", result.stdout)
            self.assertTrue((config_root / "custom_components" / "zero_net_export" / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
