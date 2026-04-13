from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "custom_components" / "zero_net_export"
CONST_PATH = PACKAGE_ROOT / "const.py"
RELEASE_INFO_PATH = PACKAGE_ROOT / "release_info.py"


def _load_release_info_module():
    custom_components_pkg = sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
    custom_components_pkg.__path__ = [str(REPO_ROOT / "custom_components")]

    integration_pkg = sys.modules.setdefault(
        "custom_components.zero_net_export",
        types.ModuleType("custom_components.zero_net_export"),
    )
    integration_pkg.__path__ = [str(PACKAGE_ROOT)]

    const_spec = importlib.util.spec_from_file_location("custom_components.zero_net_export.const", CONST_PATH)
    assert const_spec and const_spec.loader
    const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = const_module
    const_spec.loader.exec_module(const_module)

    release_info_spec = importlib.util.spec_from_file_location(
        "custom_components.zero_net_export.release_info",
        RELEASE_INFO_PATH,
    )
    assert release_info_spec and release_info_spec.loader
    release_info_module = importlib.util.module_from_spec(release_info_spec)
    sys.modules[release_info_spec.name] = release_info_module
    release_info_spec.loader.exec_module(release_info_module)
    return release_info_module


class ReleaseInfoInstallGuidanceTests(unittest.TestCase):
    def test_build_install_validation_command_targets_custom_components_root(self) -> None:
        release_info = _load_release_info_module()
        command = release_info.build_install_validation_command(
            {"component_root": "/config/custom_components/zero_net_export"}
        )
        self.assertEqual(
            command,
            "python3 scripts/validate_install_fingerprint.py /config/custom_components",
        )

    def test_build_install_fingerprint_summary_includes_exact_validation_command(self) -> None:
        release_info = _load_release_info_module()
        summary = release_info.build_install_fingerprint_summary(
            {
                "component_root": "/config/custom_components/zero_net_export",
                "code_version": "1.2.3",
                "manifest_version": "1.2.3",
                "manifest_matches_code_version": True,
                "tracked_files": {},
            }
        )
        self.assertIn(
            "- validation_command: python3 scripts/validate_install_fingerprint.py /config/custom_components",
            summary,
        )


if __name__ == "__main__":
    unittest.main()
