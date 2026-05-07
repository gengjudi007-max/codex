import unittest

from codex.services.contradiction_engine import detect_contradictions


class ContradictionEngineTests(unittest.TestCase):
    def test_number_conflict(self):
        texts = [
            "保利发展2025年净利润下降40%。",
            "保利发展2025年净利润下降25%。",
        ]

        result = detect_contradictions(texts)

        self.assertEqual(result["severity"], "high")
        self.assertTrue(result["contradictions"])

    def test_time_conflict(self):
        texts = [
            "武汉项目2022年停工。",
            "武汉项目2023年停工。",
        ]

        result = detect_contradictions(texts)

        contradiction_types = [item["type"] for item in result["contradictions"]]

        self.assertIn("time_conflict", contradiction_types)

    def test_unsupported_strong_claim(self):
        texts = [
            "武汉楼市已经彻底复苏，并必然持续上涨。"
        ]

        result = detect_contradictions(texts)

        contradiction_types = [item["type"] for item in result["contradictions"]]

        self.assertIn("unsupported_strong_claim", contradiction_types)


if __name__ == "__main__":
    unittest.main()
