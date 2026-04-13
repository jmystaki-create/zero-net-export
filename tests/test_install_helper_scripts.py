from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import deploy_exact_repo_build


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
        self.assertIn("working_tree_dirty", payload)
        self.assertIn("working_tree_changes", payload)
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
            self.assertIn("git_working_tree_dirty=", result.stdout)
            self.assertIn("git_working_tree_changes=", result.stdout)
            self.assertIn("existing_install_present=false", result.stdout)
            self.assertIn("current_install_matches_repo=unknown", result.stdout)
            self.assertIn("action=preview_only", result.stdout)

    def test_deploy_exact_repo_build_discover_home_assistant_config_uses_env_hint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_root = Path(tmpdir) / "ha-config"
            config_root.mkdir(parents=True)
            (config_root / "configuration.yaml").write_text("default_config:\n", encoding="utf-8")

            env = os.environ.copy()
            env["HOME_ASSISTANT_CONFIG"] = str(config_root)
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "deploy_exact_repo_build.py"), "--discover-home-assistant-config"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                env=env,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("discovered_config_count=", result.stdout)
            self.assertIn(str(config_root.resolve()), result.stdout)
            self.assertIn("next_step=rerun this script with one discovered config path", result.stdout)

    def test_deploy_exact_repo_build_dry_run_reports_existing_install_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_root = Path(tmpdir) / "config"
            install_root = config_root / "custom_components" / "zero_net_export"
            shutil.copytree(COMPONENT_ROOT, install_root)

            manifest_path = install_root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["version"] = "9.9.9"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

            result = self.run_script("scripts/deploy_exact_repo_build.py", str(config_root), "--dry-run")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("existing_install_present=true", result.stdout)
            self.assertIn("current_install_manifest_version=9.9.9", result.stdout)
            self.assertIn("current_install_matches_repo=false", result.stdout)
            self.assertIn("current_install_mismatches=manifest.json", result.stdout)

    def test_deploy_exact_repo_build_copies_and_validates_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_root = Path(tmpdir) / "config"
            result = self.run_script("scripts/deploy_exact_repo_build.py", str(config_root))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("git_working_tree_dirty=", result.stdout)
            self.assertIn("git_working_tree_changes=", result.stdout)
            self.assertIn("post_copy_validation=passed", result.stdout)
            self.assertTrue((config_root / "custom_components" / "zero_net_export" / "manifest.json").exists())

    def test_deploy_exact_repo_build_restores_backup_when_validation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_root = Path(tmpdir) / "config"
            install_root = config_root / "custom_components" / "zero_net_export"
            shutil.copytree(COMPONENT_ROOT, install_root)
            sentinel = install_root / "sentinel.txt"
            sentinel.write_text("keep me", encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = deploy_exact_repo_build.perform_deploy(
                    install_root,
                    source_root=COMPONENT_ROOT,
                    commit="test-commit",
                    validate_fn=lambda _: 1,
                )

            self.assertEqual(rc, 1)
            self.assertIn("post_copy_validation=failed", stderr.getvalue())
            self.assertTrue(sentinel.exists())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep me")
            self.assertFalse(any(install_root.parent.glob("zero_net_export.backup-*")))


if __name__ == "__main__":
    unittest.main()
