from pathlib import Path
import unittest


class TestDiagnosticsPayloadCopy(unittest.TestCase):
    def test_controller_diagnostics_use_current_next_action_key(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export" / "diagnostics.py").read_text(encoding="utf-8")

        self.assertIn('"current_native_next_action": data.recommendation', source)
        self.assertNotIn('"recommendation": data.recommendation', source)


if __name__ == "__main__":
    unittest.main()
