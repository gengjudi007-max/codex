import unittest

from codex.services.story_architecture import build_story_architecture


class StoryArchitectureTests(unittest.TestCase):
    def test_economic_observer_structure(self):
        payload = {
            "text": "武汉土地市场继续承压，城投托底仍在持续。",
        }

        result = build_story_architecture(payload, style="economic_observer")

        self.assertEqual(result["mode"], "story_architecture")
        self.assertEqual(result["style"]["name"], "经济观察报")
        self.assertEqual(len(result["section_plan"]), 3)

    def test_caixin_style(self):
        payload = {
            "text": "保利发展净利润下降40%，经营现金流持续承压。",
            "sources": [
                {
                    "title": "保利发展2025年年报",
                    "source_type": "annual_report",
                    "content": "净利润同比下降40%。",
                }
            ],
        }

        result = build_story_architecture(payload, style="caixin")

        self.assertEqual(result["style"]["name"], "财新")
        self.assertTrue(result["evidence_plan"]["source_count"] > 0)

    def test_interview_slots(self):
        payload = {
            "text": "武汉专项债支持收储，地方平台继续托底土地市场。",
        }

        result = build_story_architecture(payload)

        self.assertTrue(result["interview_slots"])


if __name__ == "__main__":
    unittest.main()
