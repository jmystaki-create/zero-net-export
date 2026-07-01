from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
COMPONENT_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"


def load_script_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


deploy_script = load_script_module("deploy_exact_repo_build", "deploy_exact_repo_build.py")
compare_script = load_script_module("compare_install_fingerprint", "compare_install_fingerprint.py")
print_expected_script = load_script_module("print_expected_install_fingerprint", "print_expected_install_fingerprint.py")
cleanup_script = load_script_module("clean_legacy_discovery_artifacts", "clean_legacy_discovery_artifacts.py")


class PrintExpectedInstallFingerprintTests(unittest.TestCase):
    def test_build_expected_payload_anchors_expected_commit_to_component_commit(self) -> None:
        def fake_check_output(command, cwd=None, text=None):
            if command == ["git", "rev-parse", "--short", "HEAD"]:
                return "repohead1\n"
            if command == [
                "git",
                "log",
                "-n",
                "1",
                "--format=%h",
                "--",
                "custom_components/zero_net_export",
            ]:
                return "component2\n"
            raise AssertionError(f"unexpected command: {command}")

        with patch.object(print_expected_script.subprocess, "check_output", side_effect=fake_check_output):
            payload = print_expected_script.build_expected_payload()

        self.assertEqual(payload["repo_head_commit"], "repohead1")
        self.assertEqual(payload["expected_commit"], "component2")
        self.assertEqual(payload["expected_component_commit"], "component2")
        self.assertEqual(payload["preferred_validation_commit"], "component2")
        self.assertEqual(payload["manifest_version"], "0.2.5")
        self.assertIn("button.py", payload["tracked_files"])


class CleanLegacyDiscoveryArtifactsTests(unittest.TestCase):
    def test_normalize_custom_components_root_accepts_config_custom_components_or_component_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            config_dir = root / "config"
            custom_components_dir = config_dir / "custom_components"
            component_dir = custom_components_dir / "zero_net_export"

            self.assertEqual(
                cleanup_script.normalize_custom_components_root(config_dir),
                custom_components_dir.resolve(),
            )
            self.assertEqual(
                cleanup_script.normalize_custom_components_root(custom_components_dir),
                custom_components_dir.resolve(),
            )
            self.assertEqual(
                cleanup_script.normalize_custom_components_root(component_dir),
                custom_components_dir.resolve(),
            )

    def test_scan_finds_root_and_in_component_backup_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            custom_components_dir = Path(tmp_dir) / "config" / "custom_components"
            live_component = custom_components_dir / "zero_net_export"
            backup_dir = custom_components_dir / "zero_net_export.backup_openclaw_20260415_220427"
            other_backup_dir = custom_components_dir / "zero_net_export.backup-20260415T120000Z"
            unrelated_backup = custom_components_dir / "another_component.backup_openclaw_20260415_220427"
            pycache_dir = custom_components_dir / "__pycache__"
            component_pycache_dir = live_component / "__pycache__"
            in_component_backup_dir = live_component / "backup_20260419_0009"
            in_component_backup_file = live_component / "backup_20260419_0009.py"
            legacy_backup_file = live_component / "backup.py"
            live_component.mkdir(parents=True, exist_ok=True)
            backup_dir.mkdir(parents=True, exist_ok=True)
            other_backup_dir.mkdir(parents=True, exist_ok=True)
            unrelated_backup.mkdir(parents=True, exist_ok=True)
            in_component_backup_dir.mkdir(parents=True, exist_ok=True)
            in_component_backup_file.write_text("# legacy", encoding="utf-8")
            legacy_backup_file.write_text("# stale backup module", encoding="utf-8")
            pycache_dir.mkdir(parents=True, exist_ok=True)
            component_pycache_dir.mkdir(parents=True, exist_ok=True)
            (pycache_dir / "zero_net_export.backup_openclaw_20260415_220427.cpython-313.pyc").write_bytes(b"legacy")
            (component_pycache_dir / "backup.cpython-313.pyc").write_bytes(b"legacy")
            (component_pycache_dir / "backup_20260419_0009.cpython-313.pyc").write_bytes(b"legacy")
            (pycache_dir / "another_component.cpython-313.pyc").write_bytes(b"keep")

            payload = cleanup_script.scan_artifacts(custom_components_dir)

            self.assertEqual(
                payload["legacy_backup_paths"],
                [str(other_backup_dir), str(backup_dir)],
            )
            self.assertEqual(
                payload["legacy_component_child_paths"],
                [str(legacy_backup_file), str(in_component_backup_dir), str(in_component_backup_file)],
            )
            self.assertEqual(
                payload["stale_bytecode_paths"],
                [
                    str(pycache_dir / "zero_net_export.backup_openclaw_20260415_220427.cpython-313.pyc"),
                    str(component_pycache_dir / "backup.cpython-313.pyc"),
                    str(component_pycache_dir / "backup_20260419_0009.cpython-313.pyc"),
                ],
            )

    def test_clean_removes_root_and_in_component_backup_artifacts_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            custom_components_dir = Path(tmp_dir) / "config" / "custom_components"
            live_component = custom_components_dir / "zero_net_export"
            backup_dir = custom_components_dir / "zero_net_export.backup_openclaw_20260415_220427"
            in_component_backup_dir = live_component / "backup_20260419_0009"
            in_component_backup_file = live_component / "backup_20260419_0009.py"
            legacy_backup_file = live_component / "backup.py"
            pycache_dir = custom_components_dir / "__pycache__"
            component_pycache_dir = live_component / "__pycache__"
            live_component.mkdir(parents=True, exist_ok=True)
            backup_dir.mkdir(parents=True, exist_ok=True)
            in_component_backup_dir.mkdir(parents=True, exist_ok=True)
            in_component_backup_file.write_text("# legacy", encoding="utf-8")
            legacy_backup_file.write_text("# stale backup module", encoding="utf-8")
            pycache_dir.mkdir(parents=True, exist_ok=True)
            component_pycache_dir.mkdir(parents=True, exist_ok=True)
            stale_bytecode = pycache_dir / "zero_net_export.backup_openclaw_20260415_220427.cpython-313.pyc"
            backup_module_bytecode = component_pycache_dir / "backup.cpython-313.pyc"
            nested_stale_bytecode = component_pycache_dir / "backup_20260419_0009.cpython-313.pyc"
            unrelated_bytecode = pycache_dir / "another_component.cpython-313.pyc"
            stale_bytecode.write_bytes(b"legacy")
            backup_module_bytecode.write_bytes(b"legacy")
            nested_stale_bytecode.write_bytes(b"legacy")
            unrelated_bytecode.write_bytes(b"keep")

            payload = cleanup_script.clean_artifacts(custom_components_dir)

            self.assertEqual(payload["removed_backup_paths"], [str(backup_dir)])
            self.assertEqual(
                payload["removed_component_child_paths"],
                [str(legacy_backup_file), str(in_component_backup_dir), str(in_component_backup_file)],
            )
            self.assertEqual(
                payload["removed_stale_bytecode_paths"],
                [str(stale_bytecode), str(backup_module_bytecode), str(nested_stale_bytecode)],
            )
            self.assertFalse(backup_dir.exists())
            self.assertFalse(in_component_backup_dir.exists())
            self.assertFalse(in_component_backup_file.exists())
            self.assertFalse(legacy_backup_file.exists())
            self.assertFalse(stale_bytecode.exists())
            self.assertFalse(backup_module_bytecode.exists())
            self.assertFalse(nested_stale_bytecode.exists())
            self.assertTrue(live_component.exists())
            self.assertTrue(unrelated_bytecode.exists())


class DeployExactRepoBuildTests(unittest.TestCase):
    def test_normalize_destination_accepts_config_custom_components_or_component_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            config_dir = root / "config"
            custom_components_dir = config_dir / "custom_components"
            component_dir = custom_components_dir / "zero_net_export"

            self.assertEqual(
                deploy_script.normalize_destination(config_dir),
                component_dir.resolve(),
            )
            self.assertEqual(
                deploy_script.normalize_destination(custom_components_dir),
                component_dir.resolve(),
            )
            self.assertEqual(
                deploy_script.normalize_destination(component_dir),
                component_dir.resolve(),
            )

    def test_planned_backup_path_uses_hidden_root_outside_custom_components(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            destination = Path(tmp_dir) / "config" / "custom_components" / "zero_net_export"
            backup_path = deploy_script.planned_backup_path(destination)

            self.assertEqual(
                backup_path.parent,
                Path(tmp_dir) / "config" / ".openclaw_backups" / "custom_components",
            )
            self.assertTrue(backup_path.name.startswith("zero_net_export.backup-"))
            self.assertNotEqual(backup_path.parent, destination.parent)

    def test_backup_component_writes_copy_outside_custom_components(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir) / "config"
            destination = config_dir / "custom_components" / "zero_net_export"
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "manifest.json").write_text('{"version": "test"}', encoding="utf-8")

            backup_path = deploy_script.backup_component(destination)

            self.assertIsNotNone(backup_path)
            assert backup_path is not None
            self.assertTrue(backup_path.exists())
            self.assertEqual((backup_path / "manifest.json").read_text(encoding="utf-8"), '{"version": "test"}')
            self.assertFalse((config_dir / "custom_components" / backup_path.name).exists())

    def test_copy_component_skips_pycache_and_bytecode_from_repo_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            destination = Path(tmp_dir) / "config" / "custom_components" / "zero_net_export"

            deploy_script.copy_component(COMPONENT_ROOT, destination)

            self.assertTrue((destination / "manifest.json").exists())
            self.assertFalse((destination / "__pycache__").exists())
            self.assertFalse((destination / "__pycache__" / "backup.cpython-311.pyc").exists())

    def test_clean_legacy_artifacts_for_destination_removes_root_nested_and_bytecode_pollution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            custom_components_dir = Path(tmp_dir) / "config" / "custom_components"
            destination = custom_components_dir / "zero_net_export"
            destination.mkdir(parents=True, exist_ok=True)
            legacy_backup_dir = custom_components_dir / "zero_net_export.backup_20260419_0009"
            nested_backup_dir = destination / "backup_20260419_0010"
            nested_backup_file = destination / "backup.py"
            custom_pycache_dir = custom_components_dir / "__pycache__"
            component_pycache_dir = destination / "__pycache__"

            legacy_backup_dir.mkdir(parents=True, exist_ok=True)
            nested_backup_dir.mkdir(parents=True, exist_ok=True)
            nested_backup_file.write_text("# legacy", encoding="utf-8")
            custom_pycache_dir.mkdir(parents=True, exist_ok=True)
            component_pycache_dir.mkdir(parents=True, exist_ok=True)
            stale_root_bytecode = custom_pycache_dir / "zero_net_export.backup_20260419_0009.cpython-313.pyc"
            stale_nested_bytecode = component_pycache_dir / "backup.cpython-313.pyc"
            stale_root_bytecode.write_bytes(b"legacy")
            stale_nested_bytecode.write_bytes(b"legacy")

            payload = deploy_script.clean_legacy_artifacts_for_destination(destination)

            self.assertEqual(payload["removed_backup_paths"], [str(legacy_backup_dir)])
            self.assertEqual(
                payload["removed_component_child_paths"],
                [str(nested_backup_file), str(nested_backup_dir)],
            )
            self.assertEqual(
                payload["removed_stale_bytecode_paths"],
                [str(stale_root_bytecode), str(stale_nested_bytecode)],
            )
            self.assertFalse(legacy_backup_dir.exists())
            self.assertFalse(nested_backup_dir.exists())
            self.assertFalse(nested_backup_file.exists())
            self.assertFalse(stale_root_bytecode.exists())
            self.assertFalse(stale_nested_bytecode.exists())

    def test_deploy_script_cleans_legacy_artifacts_before_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir) / "config"
            custom_components_dir = config_dir / "custom_components"
            destination = custom_components_dir / "zero_net_export"
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "manifest.json").write_text('{"version": "0.0.0-test"}', encoding="utf-8")
            legacy_backup_dir = custom_components_dir / "zero_net_export.backup_20260419_0009"
            nested_backup_file = destination / "backup.py"
            component_pycache_dir = destination / "__pycache__"
            legacy_backup_dir.mkdir(parents=True, exist_ok=True)
            nested_backup_file.write_text("# legacy", encoding="utf-8")
            component_pycache_dir.mkdir(parents=True, exist_ok=True)
            (component_pycache_dir / "backup.cpython-313.pyc").write_bytes(b"legacy")

            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "deploy_exact_repo_build.py"),
                    str(config_dir),
                    "--no-backup",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("Legacy cleanup:", result.stdout)
            self.assertFalse(legacy_backup_dir.exists())
            self.assertFalse(nested_backup_file.exists())
            self.assertFalse((component_pycache_dir / "backup.cpython-313.pyc").exists())

    def test_ensure_safe_destination_rejects_repo_local_destinations(self) -> None:
        repo_root = REPO_ROOT.resolve()
        source_root = COMPONENT_ROOT.resolve()

        with self.assertRaises(SystemExit) as exact_match:
            deploy_script.ensure_safe_destination(repo_root, source_root, source_root, argparse_parser())
        self.assertEqual(exact_match.exception.code, 2)

        nested_destination = source_root / "fake_home_assistant" / "custom_components" / "zero_net_export"
        with self.assertRaises(SystemExit) as nested_match:
            deploy_script.ensure_safe_destination(repo_root, source_root, nested_destination, argparse_parser())
        self.assertEqual(nested_match.exception.code, 2)

        repo_local_install = repo_root / "tmp" / "fake_home_assistant" / "custom_components" / "zero_net_export"
        with self.assertRaises(SystemExit) as repo_local_match:
            deploy_script.ensure_safe_destination(repo_root, source_root, repo_local_install, argparse_parser())
        self.assertEqual(repo_local_match.exception.code, 2)

    def test_ensure_expected_commit_accepts_matching_short_prefix(self) -> None:
        with patch.object(deploy_script, "git_commit_full", return_value="abcdef1234567890"):
            deploy_script.ensure_expected_commit(REPO_ROOT, "abcdef12", argparse_parser())

    def test_ensure_expected_commit_rejects_mismatch(self) -> None:
        with patch.object(deploy_script, "git_commit_full", return_value="abcdef1234567890"):
            with self.assertRaises(SystemExit) as mismatch:
                deploy_script.ensure_expected_commit(REPO_ROOT, "deadbeef", argparse_parser())

        self.assertEqual(mismatch.exception.code, 2)

    def test_ensure_expected_component_commit_accepts_matching_short_prefix(self) -> None:
        with patch.object(deploy_script, "git_component_commit", return_value="1234567890abcdef"):
            deploy_script.ensure_expected_component_commit(REPO_ROOT, "12345678", argparse_parser())

    def test_ensure_expected_component_commit_rejects_mismatch(self) -> None:
        with patch.object(deploy_script, "git_component_commit", return_value="1234567890abcdef"):
            with self.assertRaises(SystemExit) as mismatch:
                deploy_script.ensure_expected_component_commit(REPO_ROOT, "deadbeef", argparse_parser())

        self.assertEqual(mismatch.exception.code, 2)

    def test_ensure_clean_repo_rejects_dirty_status_output(self) -> None:
        with patch.object(deploy_script.subprocess, "check_output", return_value="?? tmp-ha-config/\n"):
            with self.assertRaises(SystemExit) as dirty:
                deploy_script.ensure_clean_repo(REPO_ROOT, argparse_parser())

        self.assertEqual(dirty.exception.code, 2)

    def test_ensure_upstream_sync_requires_matching_upstream_commit(self) -> None:
        def fake_check_output(command, cwd=None, text=None, stderr=None):
            if command[:3] == ["git", "rev-parse", "--abbrev-ref"]:
                return "origin/main\n"
            if command == ["git", "rev-parse", "HEAD"]:
                return "abcdef1234567890\n"
            if command == ["git", "rev-parse", "origin/main"]:
                return "abcdef1234567890\n"
            raise AssertionError(f"unexpected command: {command}")

        with patch.object(deploy_script.subprocess, "check_output", side_effect=fake_check_output):
            deploy_script.ensure_upstream_sync(REPO_ROOT, argparse_parser())

    def test_ensure_upstream_sync_rejects_diverged_upstream_commit(self) -> None:
        def fake_check_output(command, cwd=None, text=None, stderr=None):
            if command[:3] == ["git", "rev-parse", "--abbrev-ref"]:
                return "origin/main\n"
            if command == ["git", "rev-parse", "HEAD"]:
                return "abcdef1234567890\n"
            if command == ["git", "rev-parse", "origin/main"]:
                return "deadbeef12345678\n"
            raise AssertionError(f"unexpected command: {command}")

        with patch.object(deploy_script.subprocess, "check_output", side_effect=fake_check_output):
            with self.assertRaises(SystemExit) as mismatch:
                deploy_script.ensure_upstream_sync(REPO_ROOT, argparse_parser())

        self.assertEqual(mismatch.exception.code, 2)


class CompareInstallFingerprintTests(unittest.TestCase):
    def test_remote_fingerprint_uses_ssh_without_remote_python(self) -> None:
        responses = {"manifest": "0.1.86", "legacy": "stale_bytecode_paths\t/config/custom_components/zero_net_export/__pycache__/backup.cpython-313.pyc"}
        for index, name in enumerate(compare_script.TRACKED_FILES, start=1):
            responses[name] = (
                f"1\t{200 + index}\tsha{index:09d}\t/config/custom_components/zero_net_export/{name}"
            )
        responses.update(
            {
                "manifest.json": "1\t321\tabc123def456\t/config/custom_components/zero_net_export/manifest.json",
                "__init__.py": "1\t432\taaa111bbb222\t/config/custom_components/zero_net_export/__init__.py",
                "button.py": "1\t245\tbutton111222\t/config/custom_components/zero_net_export/button.py",
                "candidate_utils.py": "1\t346\tcand333444555\t/config/custom_components/zero_net_export/candidate_utils.py",
                "config_flow.py": "1\t654\tbbb222ccc333\t/config/custom_components/zero_net_export/config_flow.py",
                "coordinator.py": "1\t888\tddd444eee555\t/config/custom_components/zero_net_export/coordinator.py",
                "diagnostics.py": "1\t432\tdiag666777888\t/config/custom_components/zero_net_export/diagnostics.py",
                "native_support.py": "1\t777\tccc333ddd444\t/config/custom_components/zero_net_export/native_support.py",
                "release_info.py": "1\t543\tccc999ddd000\t/config/custom_components/zero_net_export/release_info.py",
                "sensor.py": "1\t654\tsensor999000\t/config/custom_components/zero_net_export/sensor.py",
                "strings.json": "1\t999\teee555fff666\t/config/custom_components/zero_net_export/strings.json",
                "translations/en.json": "1\t111\tfff666aaa777\t/config/custom_components/zero_net_export/translations/en.json",
            }
        )

        def fake_run(host: str, port: int | None, command: str) -> str:
            self.assertEqual(host, "root@example")
            self.assertEqual(port, 2222)
            if "sed -n" in command:
                return responses["manifest"]
            if "legacy_backup_paths" in command:
                return responses["legacy"]
            for name in compare_script.TRACKED_FILES:
                if name in command:
                    return responses[name]
            raise AssertionError(f"unexpected command: {command}")

        with patch.object(compare_script, "run_ssh_command", side_effect=fake_run):
            payload = compare_script.remote_fingerprint(
                "/config/custom_components/zero_net_export",
                "root@example",
                2222,
            )

        self.assertEqual(payload["manifest_version"], "0.1.86")
        self.assertEqual(payload["inspection_transport"], "ssh")
        self.assertEqual(payload["tracked_files"]["__init__.py"]["sha256_12"], "aaa111bbb222")
        self.assertEqual(payload["tracked_files"]["button.py"]["sha256_12"], "button111222")
        self.assertEqual(payload["tracked_files"]["candidate_utils.py"]["size_bytes"], 346)
        self.assertEqual(payload["tracked_files"]["config_flow.py"]["sha256_12"], "bbb222ccc333")
        self.assertEqual(payload["tracked_files"]["diagnostics.py"]["sha256_12"], "diag666777888")
        self.assertEqual(payload["tracked_files"]["release_info.py"]["size_bytes"], 543)
        self.assertEqual(payload["tracked_files"]["sensor.py"]["sha256_12"], "sensor999000")
        self.assertEqual(payload["tracked_files"]["translations/en.json"]["size_bytes"], 111)
        self.assertEqual(
            payload["legacy_artifacts"]["stale_bytecode_paths"],
            ["/config/custom_components/zero_net_export/__pycache__/backup.cpython-313.pyc"],
        )

    def test_tracked_files_cover_all_source_files_and_skip_pycache(self) -> None:
        tracked = set(compare_script.TRACKED_FILES)

        self.assertIn("binary_sensor.py", tracked)
        self.assertIn("repairs.py", tracked)
        self.assertIn("select.py", tracked)
        self.assertIn("switch.py", tracked)
        self.assertIn("translations/en.json", tracked)
        self.assertNotIn("__pycache__/sensor.cpython-311.pyc", tracked)

    def make_live_install_tree(self, root: Path) -> Path:
        config_dir = root / "config"
        destination = config_dir / "custom_components" / "zero_net_export"
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "python3",
                str(SCRIPTS_DIR / "deploy_exact_repo_build.py"),
                str(config_dir),
                "--no-backup",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return destination.resolve()

    def test_normalize_component_root_finds_component_from_parent_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            live_component = self.make_live_install_tree(Path(tmp_dir))
            live_custom_components = live_component.parent
            live_config = live_custom_components.parent

            self.assertEqual(
                compare_script.normalize_component_root(live_custom_components),
                live_component,
            )
            self.assertEqual(
                compare_script.normalize_component_root(live_config),
                live_component,
            )
            self.assertEqual(
                compare_script.normalize_component_root(live_component),
                live_component,
            )

    def test_git_commit_accepts_custom_git_args(self) -> None:
        with patch.object(compare_script.subprocess, "check_output", return_value="component2\n") as mock_check_output:
            result = compare_script.git_commit(REPO_ROOT, "log", "-n", "1", "--format=%h", "--", "custom_components/zero_net_export")

        self.assertEqual(result, "component2")
        mock_check_output.assert_called_once_with(
            ["git", "log", "-n", "1", "--format=%h", "--", "custom_components/zero_net_export"],
            cwd=REPO_ROOT,
            text=True,
        )

    def test_compare_reports_match_for_identical_fingerprints(self) -> None:
        expected = compare_script.fingerprint(COMPONENT_ROOT)
        actual = compare_script.fingerprint(COMPONENT_ROOT)
        actual["legacy_artifacts"] = {
            "legacy_backup_paths": [],
            "legacy_component_child_paths": [],
            "stale_bytecode_paths": [],
        }

        comparison = compare_script.compare(expected, actual)

        self.assertTrue(comparison["manifest_version_matches"])
        self.assertTrue(comparison["all_tracked_files_match"])
        self.assertTrue(comparison["legacy_artifacts_match"])
        self.assertTrue(comparison["overall_match"])
        self.assertEqual(comparison["mismatches"], [])

    def test_compare_reports_mismatch_when_manifest_and_file_hash_differ(self) -> None:
        expected = compare_script.fingerprint(COMPONENT_ROOT)
        actual = json.loads(json.dumps(expected))
        actual["manifest_version"] = "0.0.0-test"
        actual["tracked_files"]["manifest.json"]["sha256_12"] = "deadbeefcafe"
        actual["legacy_artifacts"] = {
            "legacy_backup_paths": [],
            "legacy_component_child_paths": [],
            "stale_bytecode_paths": [],
        }

        comparison = compare_script.compare(expected, actual)

        self.assertFalse(comparison["manifest_version_matches"])
        self.assertFalse(comparison["all_tracked_files_match"])
        self.assertFalse(comparison["overall_match"])
        self.assertEqual(comparison["manifest_mismatch"]["actual"], "0.0.0-test")
        self.assertEqual(comparison["mismatches"][0]["file"], "manifest.json")

    def test_compare_reports_legacy_artifacts_even_when_tracked_files_match(self) -> None:
        expected = compare_script.fingerprint(COMPONENT_ROOT)
        actual = json.loads(json.dumps(expected))
        actual["legacy_artifacts"] = {
            "legacy_backup_paths": [],
            "legacy_component_child_paths": [],
            "stale_bytecode_paths": ["/config/custom_components/zero_net_export/__pycache__/backup.cpython-313.pyc"],
        }

        comparison = compare_script.compare(expected, actual)

        self.assertTrue(comparison["manifest_version_matches"])
        self.assertTrue(comparison["all_tracked_files_match"])
        self.assertFalse(comparison["legacy_artifacts_match"])
        self.assertFalse(comparison["overall_match"])
        self.assertIn("clean_legacy_discovery_artifacts.py", comparison["recommendation"])

    def test_cli_compare_rejects_repo_local_paths(self) -> None:
        source_result = subprocess.run(
            [
                "python3",
                str(SCRIPTS_DIR / "compare_install_fingerprint.py"),
                str(COMPONENT_ROOT),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(source_result.returncode, 2)
        self.assertIn("repo's source component directory", source_result.stderr)

        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "tmp") as tmp_dir:
            repo_local_component = Path(tmp_dir) / "custom_components" / "zero_net_export"
            repo_local_component.mkdir(parents=True, exist_ok=True)
            (repo_local_component / "manifest.json").write_text(
                (COMPONENT_ROOT / "manifest.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            repo_local_result = subprocess.run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "compare_install_fingerprint.py"),
                    str(repo_local_component),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(repo_local_result.returncode, 2)
        self.assertIn("inside this repo", repo_local_result.stderr)

    def test_cli_compare_matches_live_install_copy_and_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            live_component = self.make_live_install_tree(Path(tmp_dir))
            output_path = Path(tmp_dir) / "compare.json"
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "compare_install_fingerprint.py"),
                    str(live_component),
                    "--write-json",
                    str(output_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["comparison"]["overall_match"])
            self.assertTrue(payload["comparison"]["legacy_artifacts_match"])
            self.assertTrue(output_path.exists())

    def test_cli_validate_matches_live_install_copy_and_writes_json_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            live_component = self.make_live_install_tree(Path(tmp_dir))
            expected_path = Path(tmp_dir) / "expected.json"
            compare_path = Path(tmp_dir) / "compare.json"
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "validate_install_fingerprint.py"),
                    str(live_component),
                    "--expected-json",
                    str(expected_path),
                    "--compare-json",
                    str(compare_path),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["overall_match"])
            self.assertTrue(expected_path.exists())
            self.assertTrue(compare_path.exists())


def argparse_parser():
    import argparse

    return argparse.ArgumentParser(prog="test-parser")


if __name__ == "__main__":
    unittest.main()
