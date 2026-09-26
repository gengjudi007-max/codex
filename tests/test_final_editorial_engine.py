import unittest

from codex.services.final_editorial_engine import final_edit_report, polish_news_text


class FinalEditorialEngineTests(unittest.TestCase):
    def test_final_editorial_output(self):
        payload = {
            "text": "公司始终坚持高质量发展，全面赋能城市美好生活。",
            "subject": "保利发展",
        }

        result = final_edit_report(payload)

        self.assertEqual(result["mode"], "final_editorial_engine")
        self.assertIn("保利发展", result["edited_text"])

    def test_risk_expression_preserves_original_claim(self):
        payload = {
            "text": "武汉楼市已经彻底复苏，并必然持续上涨。",
        }

        result = final_edit_report(payload)

        self.assertIn(payload["text"], result["edited_text"])

    def test_editorial_notes(self):
        payload = {
            "text": "公司全面领先行业，并持续赋能城市发展。",
        }

        result = final_edit_report(payload)

        self.assertTrue(result["editorial_notes"])


if __name__ == "__main__":
    unittest.main()


class EditorialPreservationTests(unittest.TestCase):
    def test_quote_names_numbers_and_paragraphs_are_preserved(self):
        text = '公司表示，销售额为10.5亿元。\n\n招商局蛇口工业区控股股份有限公司称：“我们必然全面领先。”子公司完全退出项目。'
        expected = text.replace('公司表示', '保利发展表示', 1)
        self.assertEqual(polish_news_text(text, '保利发展'), expected)

    def test_no_subject_does_not_invent_attribution(self):
        text = '公司称，项目已经完全交付。'
        self.assertEqual(polish_news_text(text), text)

    def test_template_removal_keeps_quote(self):
        text = '值得注意的是，利润下降30%。受访者说：“值得注意的是，成本增加。”'
        self.assertEqual(polish_news_text(text), '利润下降30%。受访者说：“值得注意的是，成本增加。”')
