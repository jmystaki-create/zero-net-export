from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OperatorDocsConsistencyTests(unittest.TestCase):
    def test_detailed_map_orders_current_091_scope_before_historical_workstreams(self) -> None:
        content = (ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
        current = content.index("### Current ordered 0.1.91 map")
        historical = content.index("### Historical broad UI workstreams - not the current 0.1.91 ordered map")
        workstream_a = content.index("### Workstream A. Finish the opening operator console")
        workstream_g = content.index("### Workstream G. Exact-build validation and release execution")

        self.assertLess(current, historical)
        self.assertLess(historical, workstream_a)
        self.assertLess(workstream_a, workstream_g)
        current_map = content[current:historical]
        self.assertIn("ask James directly for release/deploy/restart approval", current_map)
        self.assertIn("Settings -> Devices & Services -> Integrations -> Zero Net Export", current_map)

    def test_historical_workstreams_cannot_outrank_091_device_list_scope(self) -> None:
        content = (ROOT / "docs" / "UI_IMPLEMENTATION_MAP.md").read_text(encoding="utf-8")
        historical_note = content[
            content.index("### Historical broad UI workstreams - not the current 0.1.91 ordered map"):
            content.index("### Workstream A. Finish the opening operator console")
        ]

        self.assertIn("not eligible work ahead of the approved `0.1.91`", historical_note)
        self.assertIn("Do not let them outrank the current ordered `0.1.91` map", historical_note)


if __name__ == "__main__":
    unittest.main()
