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
from unittest.mock import patch

from scripts import compare_install_fingerprint, deploy_exact_repo_build


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
        self.assertIn("git_branch", payload)
        self.assertIn("git_local_vs_upstream", payload)
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

    def test_compare_install_fingerprint_accepts_custom_components_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_root = Path(tmpdir) / "config"
            custom_components_root = config_root / "custom_components"
            install_root = custom_components_root / "zero_net_export"
            shutil.copytree(COMPONENT_ROOT, install_root)

            result = self.run_script("scripts/compare_install_fingerprint.py", str(custom_components_root))
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
            self.assertIn("git_branch=", result.stdout)
            self.assertIn("git_local_vs_upstream=", result.stdout)
            self.assertIn("repo_deploy_requirements_passed=true", result.stdout)
            self.assertIn("copy_ready=true", result.stdout)
            self.assertIn("restart_ready=false", result.stdout)
            self.assertIn("existing_install_present=false", result.stdout)
            self.assertIn("current_install_matches_repo=unknown", result.stdout)
            self.assertIn(f"next_command=python3 scripts/deploy_exact_repo_build.py {config_root}", result.stdout)
            self.assertIn("success_criteria=confirm repo_deploy_requirements_passed=true, copy_ready=true", result.stdout)
            self.assertIn(f"git_commit={subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=REPO_ROOT, text=True).strip()}", result.stdout)
            self.assertIn(f"validate_command=python3 scripts/validate_install_fingerprint.py {config_root / 'custom_components'}", result.stdout)
            self.assertIn("action=preview_only", result.stdout)

    def test_deploy_exact_repo_build_dry_run_accepts_custom_components_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_components_root = Path(tmpdir) / "config" / "custom_components"
            custom_components_root.mkdir(parents=True)

            result = self.run_script("scripts/deploy_exact_repo_build.py", str(custom_components_root), "--dry-run")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn(f"resolved_destination={custom_components_root / 'zero_net_export'}", result.stdout)
            self.assertIn(f"validate_command=python3 scripts/validate_install_fingerprint.py {custom_components_root}", result.stdout)

    def test_recommended_deploy_command_adds_current_safety_flags(self) -> None:
        target = Path("/config")
        self.assertEqual(
            deploy_exact_repo_build.recommended_deploy_command(target, dry_run=True, expected_commit="abc1234"),
            "python3 scripts/deploy_exact_repo_build.py /config --dry-run --expected-commit abc1234 --require-clean --require-upstream-sync",
        )
        self.assertEqual(
            deploy_exact_repo_build.recommended_deploy_command(target, dry_run=False, expected_commit="abc1234"),
            "python3 scripts/deploy_exact_repo_build.py /config --expected-commit abc1234 --require-clean --require-upstream-sync",
        )

    def test_enforce_repo_build_requirements_accepts_matching_clean_repo(self) -> None:
        with patch.object(deploy_exact_repo_build, "git_status_details", return_value=(False, [])):
            commit, dirty, changed_files = deploy_exact_repo_build.enforce_repo_build_requirements(
                root=REPO_ROOT,
                commit="abc1234",
                expected_commit="abc1234",
                require_clean=True,
                require_upstream_sync=False,
            )

        self.assertEqual(commit, "abc1234")
        self.assertFalse(dirty)
        self.assertEqual(changed_files, [])

    def test_enforce_repo_build_requirements_refuses_commit_mismatch(self) -> None:
        with patch.object(deploy_exact_repo_build, "git_status_details", return_value=(False, [])):
            with self.assertRaises(SystemExit) as exc:
                deploy_exact_repo_build.enforce_repo_build_requirements(
                    root=REPO_ROOT,
                    commit="abc1234",
                    expected_commit="deadbee",
                    require_clean=False,
                    require_upstream_sync=False,
                )

        self.assertIn("expected git commit deadbee", str(exc.exception))

    def test_enforce_repo_build_requirements_refuses_dirty_repo_when_required(self) -> None:
        with patch.object(deploy_exact_repo_build, "git_status_details", return_value=(True, ["custom_components/zero_net_export/manifest.json"])):
            with self.assertRaises(SystemExit) as exc:
                deploy_exact_repo_build.enforce_repo_build_requirements(
                    root=REPO_ROOT,
                    commit="abc1234",
                    expected_commit="abc1234",
                    require_clean=True,
                    require_upstream_sync=False,
                )

        self.assertIn("git working tree is dirty", str(exc.exception))
        self.assertIn("custom_components/zero_net_export/manifest.json", str(exc.exception))

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
            repo_commit = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=REPO_ROOT,
                text=True,
            ).strip()

            self.assertIn("discovered_config_count=", result.stdout)
            self.assertIn(str(config_root.resolve()), result.stdout)
            self.assertIn(f"git_commit={repo_commit}", result.stdout)
            self.assertIn(f"example_dry_run_command=python3 scripts/deploy_exact_repo_build.py {config_root} --dry-run", result.stdout)
            self.assertIn(
                f"recommended_dry_run_command=python3 scripts/deploy_exact_repo_build.py {config_root} --dry-run --expected-commit {repo_commit} --require-clean --require-upstream-sync",
                result.stdout,
            )
            self.assertIn(
                f"recommended_deploy_command=python3 scripts/deploy_exact_repo_build.py {config_root} --expected-commit {repo_commit} --require-clean --require-upstream-sync",
                result.stdout,
            )
            self.assertIn(
                f"recommended_validate_command=python3 scripts/validate_install_fingerprint.py {config_root / 'custom_components'}",
                result.stdout,
            )
            self.assertIn("recommended dry-run command", result.stdout)

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

    def test_enforce_repo_build_requirements_refuses_non_synced_upstream_when_required(self) -> None:
        with (
            patch.object(deploy_exact_repo_build, "git_status_details", return_value=(False, [])),
            patch.object(
                deploy_exact_repo_build,
                "git_remote_tracking_details",
                return_value={
                    "git_branch": "feature/test",
                    "git_upstream": "origin/feature/test",
                    "git_upstream_commit": "5753f33",
                    "git_local_vs_upstream": "ahead",
                    "git_ahead_count": 2,
                    "git_behind_count": 0,
                },
            ),
        ):
            with self.assertRaises(SystemExit) as exc:
                deploy_exact_repo_build.enforce_repo_build_requirements(
                    root=REPO_ROOT,
                    commit="abc1234",
                    expected_commit="abc1234",
                    require_clean=True,
                    require_upstream_sync=True,
                )

        self.assertIn("repo is not synchronized with its tracked upstream", str(exc.exception))
        self.assertIn("relation=ahead", str(exc.exception))

    def test_deploy_exact_repo_build_dry_run_refuses_when_upstream_is_not_synced(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_root = Path(tmpdir) / "config"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch.object(deploy_exact_repo_build, "git_status_details", return_value=(False, [])),
                patch.object(
                    deploy_exact_repo_build,
                    "git_remote_tracking_details",
                    return_value={
                        "git_branch": "feature/test",
                        "git_upstream": "origin/feature/test",
                        "git_upstream_commit": "5753f33",
                        "git_local_vs_upstream": "ahead",
                        "git_ahead_count": 2,
                        "git_behind_count": 0,
                    },
                ),
                patch.object(
                    sys,
                    "argv",
                    [
                        "deploy_exact_repo_build.py",
                        str(config_root),
                        "--dry-run",
                        "--require-upstream-sync",
                    ],
                ),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                with self.assertRaises(SystemExit) as exc:
                    deploy_exact_repo_build.main()

            self.assertNotEqual(exc.exception.code, 0)
            self.assertIn("repo is not synchronized with its tracked upstream", str(exc.exception))

    def test_deploy_exact_repo_build_copies_and_validates_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_root = Path(tmpdir) / "config"
            result = self.run_script("scripts/deploy_exact_repo_build.py", str(config_root))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("git_working_tree_dirty=", result.stdout)
            self.assertIn("git_working_tree_changes=", result.stdout)
            self.assertIn("git_branch=", result.stdout)
            self.assertIn("git_local_vs_upstream=", result.stdout)
            self.assertIn("repo_deploy_requirements_passed=true", result.stdout)
            self.assertIn("copy_ready=true", result.stdout)
            self.assertIn("restart_ready=true", result.stdout)
            self.assertIn("post_copy_validation=passed", result.stdout)
            self.assertIn("success_criteria=confirm post_copy_validation=passed, restart_ready=true", result.stdout)
            self.assertIn(f"validate_command=python3 scripts/validate_install_fingerprint.py {config_root / 'custom_components'}", result.stdout)
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

    def test_git_remote_tracking_details_reports_ahead_branch_state(self) -> None:
        outputs = {
            ("branch", "--show-current"): "feature/test\n",
            ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"): "origin/feature/test\n",
            ("rev-parse", "--short", "origin/feature/test"): "5753f33\n",
            ("rev-list", "--left-right", "--count", "origin/feature/test...HEAD"): "0 2\n",
        }

        def fake_check_output(args, cwd=None, text=None):
            return outputs[tuple(args[1:])]

        with patch.object(compare_install_fingerprint.subprocess, "check_output", side_effect=fake_check_output):
            tracking = compare_install_fingerprint.git_remote_tracking_details(REPO_ROOT)

        self.assertEqual(tracking["git_branch"], "feature/test")
        self.assertEqual(tracking["git_upstream"], "origin/feature/test")
        self.assertEqual(tracking["git_upstream_commit"], "5753f33")
        self.assertEqual(tracking["git_local_vs_upstream"], "ahead")
        self.assertEqual(tracking["git_ahead_count"], 2)
        self.assertEqual(tracking["git_behind_count"], 0)


if __name__ == "__main__":
    unittest.main()
