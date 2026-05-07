import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from codex.interaction import analyze_payload
from codex.services.source_store import append_jsonl, search_jsonl, write_jsonl
from codex.services.text_utils import compact_text, infer_city, normalize_text


class RobustnessTests(unittest.TestCase):
    def test_non_dict_payload_returns_clear_error(self):
        response = analyze_payload([{"message": "not an object"}])

        self.assertEqual(response["mode"], "unknown")
        self.assertIn("error", response)

    def test_free_text_without_keywords_returns_warning_not_crash(self):
        response = analyze_payload({"message": "今天没有明确房地产行业信息。"})

        self.assertEqual(response["mode"], "topic_pipeline")
        self.assertEqual(response["result"]["input_count"], 1)
        self.assertIn("warnings", response["result"])

    def test_text_utils_normalize_and_compact_mixed_values(self):
        self.assertEqual(normalize_text([" 房地产\n", None, "  土地  "]), "房地产  土地")
        compacted = compact_text("abcdef", 4)
        self.assertTrue(compacted.startswith("abc"))
        self.assertTrue(compacted.endswith("..."))
        self.assertEqual(infer_city("苏州土拍热度回升"), "苏州")

    def test_append_jsonl_deduplicates_existing_items(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "items.jsonl")
            first = append_jsonl(path, [{"source": "land", "title": "武汉土拍", "summary": "城投托底"}])
            second = append_jsonl(path, [{"source": "land", "title": "武汉土拍", "summary": "城投托底"}])

        self.assertEqual(first["written"], 1)
        self.assertEqual(second["written"], 0)
        self.assertEqual(second["total"], 1)

    def test_search_jsonl_supports_offset_and_empty_query(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "items.jsonl")
            write_jsonl(
                path,
                [
                    {"source": "a", "title": "城投拿地", "summary": "土地市场"},
                    {"source": "b", "title": "房企销售", "summary": "分化"},
                ],
            )
            empty = search_jsonl(path, query="", limit=1, offset=1)
            matched = search_jsonl(path, query="城投 土地")

        self.assertEqual(empty["matched"], 2)
        self.assertEqual(empty["returned"], 1)
        self.assertEqual(matched["matched"], 1)


if __name__ == "__main__":
    unittest.main()
