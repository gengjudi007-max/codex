import unittest

from codex.services.deep_report_drafter import draft_deep_report


class DeepReportDrafterTests(unittest.TestCase):
    def test_economic_observer_draft(self):
        payload = {
            "text": "武汉土地市场继续承压，城投托底仍在持续。",
        }

        result = draft_deep_report(payload, style="economic_observer")

        self.assertEqual(result["mode"], "deep_report_draft")
        self.assertEqual(result["style"]["name"], "经济观察报")
        self.assertEqual(len(result["sections"]), 3)

    def test_caixin_draft(self):
        payload = {
            "text": "保利发展净利润下降40%，经营现金流承压。",
            "sources": [
                {
                    "title": "保利发展2025年年报",
                    "source_type": "annual_report",
                    "content": "净利润同比下降40%。",
                }
            ],
        }

        result = draft_deep_report(payload, style="caixin")

        self.assertEqual(result["style"]["name"], "财新")
        self.assertIn("证据", result["lead"]["text"])

    def test_draft_status(self):
        payload = {
            "text": "武汉楼市已经彻底复苏，并必然持续上涨。",
        }

        result = draft_deep_report(payload)

        self.assertIn("status", result["draft_status"])


if __name__ == "__main__":
    unittest.main()
