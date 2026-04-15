import json
from pathlib import Path
import unittest


class TestTranslationSync(unittest.TestCase):
    def test_en_translation_matches_strings_source_of_truth(self):
        integration_root = Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export"
        with (integration_root / "strings.json").open(encoding="utf-8") as handle:
            strings = json.load(handle)
        with (integration_root / "translations" / "en.json").open(encoding="utf-8") as handle:
            en = json.load(handle)

        self.assertEqual(en, strings)


if __name__ == "__main__":
    unittest.main()
