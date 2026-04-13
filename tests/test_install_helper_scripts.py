from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


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

    def test_ensure_safe_destination_rejects_repo_source_and_nested_destinations(self) -> None:
        source_root = COMPONENT_ROOT.resolve()

        with self.assertRaises(SystemExit) as exact_match:
            deploy_script.ensure_safe_destination(source_root, source_root, argparse_parser())
        self.assertEqual(exact_match.exception.code, 2)

        nested_destination = source_root / "fake_home_assistant" / "custom_components" / "zero_net_export"
        with self.assertRaises(SystemExit) as nested_match:
            deploy_script.ensure_safe_destination(source_root, nested_destination, argparse_parser())
        self.assertEqual(nested_match.exception.code, 2)


class CompareInstallFingerprintTests(unittest.TestCase):
    def test_normalize_component_root_finds_component_from_parent_paths(self) -> None:
        self.assertEqual(
            compare_script.normalize_component_root(REPO_ROOT / "custom_components"),
            COMPONENT_ROOT.resolve(),
        )
        self.assertEqual(
            compare_script.normalize_component_root(REPO_ROOT),
            COMPONENT_ROOT.resolve(),
        )
        self.assertEqual(
            compare_script.normalize_component_root(COMPONENT_ROOT),
            COMPONENT_ROOT.resolve(),
        )

    def test_compare_reports_match_for_identical_fingerprints(self) -> None:
        expected = compare_script.fingerprint(COMPONENT_ROOT)
        actual = compare_script.fingerprint(COMPONENT_ROOT)

        comparison = compare_script.compare(expected, actual)

        self.assertTrue(comparison["manifest_version_matches"])
        self.assertTrue(comparison["all_tracked_files_match"])
        self.assertTrue(comparison["overall_match"])
        self.assertEqual(comparison["mismatches"], [])

    def test_compare_reports_mismatch_when_manifest_and_file_hash_differ(self) -> None:
        expected = compare_script.fingerprint(COMPONENT_ROOT)
        actual = json.loads(json.dumps(expected))
        actual["manifest_version"] = "0.0.0-test"
        actual["tracked_files"]["manifest.json"]["sha256_12"] = "deadbeefcafe"

        comparison = compare_script.compare(expected, actual)

        self.assertFalse(comparison["manifest_version_matches"])
        self.assertFalse(comparison["all_tracked_files_match"])
        self.assertFalse(comparison["overall_match"])
        self.assertEqual(comparison["manifest_mismatch"]["actual"], "0.0.0-test")
        self.assertEqual(comparison["mismatches"][0]["file"], "manifest.json")

    def test_cli_compare_matches_repo_component_and_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "compare.json"
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "compare_install_fingerprint.py"),
                    str(COMPONENT_ROOT),
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
            self.assertTrue(output_path.exists())

    def test_cli_validate_matches_repo_component_and_writes_json_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            expected_path = Path(tmp_dir) / "expected.json"
            compare_path = Path(tmp_dir) / "compare.json"
            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPTS_DIR / "validate_install_fingerprint.py"),
                    str(COMPONENT_ROOT),
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
