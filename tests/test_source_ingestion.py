import unittest

from codex.services.source_ingestion import ingest_sources


class SourceIngestionTests(unittest.TestCase):
    def test_text_ingestion(self):
        payload = {
            "texts": [
                "武汉土地市场继续承压，城投托底仍在持续。"
            ]
        }

        result = ingest_sources(payload)

        self.assertEqual(result["mode"], "source_ingestion")
        self.assertGreater(result["accepted_count"], 0)

    def test_structured_item_ingestion(self):
        payload = {
            "items": [
                {
                    "title": "保利发展2025年年报",
                    "content": "净利润下降40%。",
                    "source_type": "annual_report",
                }
            ]
        }

        result = ingest_sources(payload)

        self.assertEqual(result["items"][0]["source_type"], "annual_report")

    def test_source_type_inference(self):
        payload = {
            "items": [
                {
                    "title": "专项债募集说明书",
                    "content": "专项债支持收储。",
                }
            ]
        }

        result = ingest_sources(payload)

        self.assertEqual(result["items"][0]["source_type"], "bond_prospectus")


if __name__ == "__main__":
    unittest.main()
