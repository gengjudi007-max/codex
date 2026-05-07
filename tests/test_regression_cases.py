import json
import unittest
from pathlib import Path

from codex.interaction import analyze_payload


class RegressionCasesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture_path = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "regression_cases.json"
        )
        with fixture_path.open("r", encoding="utf-8") as handle:
            cls.cases = json.load(handle)

    def test_regression_cases(self):
        for case in self.cases:
            with self.subTest(case=case["name"]):
                response = analyze_payload(case["payload"])

                self.assertEqual(response["mode"], case["expected_mode"])
                self.assertNotIn("error", response)

                result = response["result"]

                if response["mode"] == "annual_report":
                    topics = result["topic_pipeline"]["topics"]
                else:
                    topics = result["topics"]

                self.assertTrue(topics)

                top_topic = topics[0]
                self.assertEqual(top_topic["category"], case["expected_category"])

                text = " ".join(
                    [
                        str(top_topic.get("topic", "")),
                        str(top_topic.get("angle", "")),
                        str(top_topic.get("reason", "")),
                        str(top_topic.get("materials", "")),
                        str(top_topic.get("interview_targets", "")),
                        str(top_topic.get("questions", "")),
                        str(top_topic.get("material_plan", "")),
                        str(top_topic.get("interview_plan", "")),
                    ]
                )

                for keyword in case["expected_topic_keywords"]:
                    self.assertIn(keyword, text)


if __name__ == "__main__":
    unittest.main()
