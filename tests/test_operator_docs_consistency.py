from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"
UI_MAP_PATH = REPO_ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md"


class OperatorDocsConsistencyTests(unittest.TestCase):
    def test_readme_uses_current_source_mapping_section_name(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        self.assertIn("Use **Sensors and source mapping** to map your source entities", readme)
        self.assertNotIn("Use **Sensors** to map your source entities", readme)

    def test_ui_implementation_map_uses_current_command_center_labels(self) -> None:
        ui_map = UI_MAP_PATH.read_text(encoding="utf-8")
        self.assertIn("**Sensors and source mapping**", ui_map)
        self.assertIn("four supported Configure sections", ui_map)
        self.assertNotIn("around **Controls**, **Sensors**, **Managed Devices**, **Diagnostics**, plus a deeper **Detailed Management** path", ui_map)


if __name__ == "__main__":
    unittest.main()
