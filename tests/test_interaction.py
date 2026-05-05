import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from codex.interaction import analyze_payload
from codex.services.source_store import write_jsonl


class InteractionTests(unittest.TestCase):
    def test_free_text_land_topic_infers_city(self):
        response = analyze_payload({"message": "杭州土地市场溢价率回升，民企重新参与核心地块竞拍。"})

        self.assertNotIn("error", response)
        self.assertEqual(response["mode"], "topic_pipeline")
        topics = response["result"]["topics"]
        self.assertEqual(len(topics), 1)
        self.assertIn("杭州土地市场变化", topics[0]["topic"])
        self.assertIn("material_plan", topics[0])
        self.assertIn("interview_plan", topics[0])
        self.assertIn("photo_plan", topics[0])
        self.assertIn("evidence", topics[0])
        self.assertIn("verification_status", topics[0])
        self.assertTrue(topics[0]["photo_plan"]["must_shoot"])

    def test_bad_items_returns_error(self):
        response = analyze_payload({"items": "not-a-list"})

        self.assertEqual(response["mode"], "topic_pipeline")
        self.assertIn("error", response)

    def test_developer_compare_requires_list(self):
        response = analyze_payload({"mode": "developer_compare", "companies": {}})

        self.assertEqual(response["mode"], "developer_compare")
        self.assertIn("error", response)

    def test_city_investment_land_requires_list_fields(self):
        response = analyze_payload({"mode": "city_investment_land", "yearly": {}})

        self.assertEqual(response["mode"], "city_investment_land")
        self.assertIn("error", response)

    def test_annual_report_routes_into_topic_pipeline(self):
        response = analyze_payload({
            "report": {
                "company": "保利发展",
                "year": "2025",
                "metrics": {
                    "net_profit_yoy": -40,
                    "impairment_loss": 35,
                    "operating_cash_flow": -10,
                },
            }
        })

        self.assertEqual(response["mode"], "annual_report")
        pipeline = response["result"]["topic_pipeline"]
        self.assertGreaterEqual(pipeline["topic_count"], 1)

    def test_draft_edit_mode(self):
        response = analyze_payload({"mode": "draft_edit", "text": "相关数据显示，销售金额下降30%。"})

        self.assertEqual(response["mode"], "draft_edit")
        self.assertGreater(response["result"]["character_count"], 0)
        self.assertTrue(response["result"]["headline_options"])

    def test_signal_monitor_routes_tracking_items(self):
        response = analyze_payload({
            "tracking": True,
            "items": [
                {
                    "source": "land",
                    "title": "武汉土拍城投拿地占比超过70%",
                    "summary": "多宗地块底价成交，地方平台继续托底土地市场。",
                },
                {
                    "source": "policy",
                    "title": "多地优化限购政策",
                    "summary": "新政后成交是否回升仍待观察。",
                },
            ],
        })

        self.assertEqual(response["mode"], "signal_monitor")
        self.assertEqual(response["result"]["valid_count"], 2)
        self.assertTrue(response["result"]["signals"])
        self.assertIn("土地", response["result"]["domain_summary"])
        self.assertIn("verification_status", response["result"]["signals"][0])

    def test_import_terminal_mode_runs_pipeline(self):
        path = Path(__file__).resolve().parents[1] / "examples" / "sample_land_terminal.csv"
        response = analyze_payload({"mode": "import_terminal", "path": str(path), "source": "sample"})

        self.assertEqual(response["mode"], "import_terminal")
        self.assertEqual(response["result"]["record_count"], 2)
        self.assertIsNotNone(response["result"]["city_land_compare"])

    def test_parse_documents_mode_runs_monitor(self):
        path = Path(__file__).resolve().parents[1] / "examples" / "sample_policy.txt"
        response = analyze_payload({"mode": "parse_documents", "paths": [str(path)]})

        self.assertEqual(response["mode"], "parse_documents")
        self.assertEqual(len(response["result"]["items"]), 1)
        self.assertTrue(response["result"]["signal_monitor"]["signals"])

    def test_ifind_query_without_sdk_returns_clear_error(self):
        response = analyze_payload({
            "mode": "ifind_query",
            "function": "edb",
            "codes": "SAMPLE_CODE",
        })

        self.assertEqual(response["mode"], "ifind_query")
        self.assertIn("error", response)

    def test_search_store_and_summary_modes(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "items.jsonl")
            write_jsonl(
                path,
                [
                    {"source": "draft", "title": "城投拿地退潮", "summary": "土地市场托底力量减弱"},
                    {"source": "report", "title": "房企销售榜", "summary": "销售分化"},
                ],
            )
            search = analyze_payload({"mode": "search_store", "path": path, "query": "城投 土地"})
            inferred_search = analyze_payload({"path": path, "query": "房企"})
            summary = analyze_payload({"mode": "store_summary", "path": path})

        self.assertEqual(search["mode"], "search_store")
        self.assertEqual(search["result"]["matched"], 1)
        self.assertEqual(inferred_search["mode"], "search_store")
        self.assertEqual(inferred_search["result"]["matched"], 1)
        self.assertEqual(summary["result"]["total"], 2)


if __name__ == "__main__":
    unittest.main()
