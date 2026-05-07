import unittest

from codex.services.final_editorial_engine import final_edit_report


class FinalEditorialEngineTests(unittest.TestCase):
    def test_final_editorial_output(self):
        payload = {
            "text": "公司始终坚持高质量发展，全面赋能城市美好生活。",
            "subject": "保利发展",
        }

        result = final_edit_report(payload)

        self.assertEqual(result["mode"], "final_editorial_engine")
        self.assertIn("保利发展", result["edited_text"])

    def test_risk_expression_softening(self):
        payload = {
            "text": "武汉楼市已经彻底复苏，并必然持续上涨。",
        }

        result = final_edit_report(payload)

        self.assertIn("可能", result["edited_text"])

    def test_editorial_notes(self):
        payload = {
            "text": "公司全面领先行业，并持续赋能城市发展。",
        }

        result = final_edit_report(payload)

        self.assertTrue(result["editorial_notes"])


if __name__ == "__main__":
    unittest.main()
