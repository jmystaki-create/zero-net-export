import json
from pathlib import Path
import unittest


class TestCandidateReviewCopy(unittest.TestCase):
    def test_candidate_review_labels_use_generic_candidate_usefulness_wording(self):
        integration_root = Path(__file__).resolve().parents[1] / "custom_components" / "zero_net_export"
        with (integration_root / "strings.json").open(encoding="utf-8") as handle:
            strings = json.load(handle)

        description = strings["options"]["step"]["device_vetting"]["description"]

        self.assertIn("Candidate usefulness: {candidate_fit_usefulness}", description)
        self.assertNotIn("Likely usefulness:", description)


if __name__ == "__main__":
    unittest.main()
