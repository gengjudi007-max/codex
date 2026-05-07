import unittest
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory

from codex.services.city_land_comparator import compare_city_land_markets
from codex.services.city_investment_land_model import build_city_investment_land_model
from codex.services.document_parser import parse_document
from codex.services.draft_editor import edit_draft
from codex.services.evidence import attach_credibility, source_quality
from codex.services.ifind_client import IFIndClient, IFIndQuery, ifind_result_to_items
from codex.services.material_builder import build_materials
from codex.services.photo_planner import plan_photography
from codex.services.signal_monitor import monitor_signals
from codex.services.source_store import (
    append_jsonl,
    load_jsonl,
    search_jsonl,
    summarize_jsonl,
    write_jsonl,
    write_jsonl_stream,
)
from codex.services.terminal_importer import import_terminal_file
from codex.services.topic_finder import find_topics
from codex.services.topic_scoring import score_topics


class ServiceTests(unittest.TestCase):
    def test_topic_pipeline_scores_land_item(self):
        topics = find_topics({
            "items": [{
                "source": "land",
                "city": "武汉",
                "title": "武汉土拍城投拿地占比超70%",
                "summary": "多宗地块底价成交。",
            }]
        })
        scored = score_topics(topics)

        self.assertEqual(scored[0]["priority"], "重点选题")
        self.assertGreater(scored[0]["final_score"], 80)
        self.assertIn("data_value", scored[0]["score_breakdown"])

    def test_topic_scoring_counts_data_value_in_final_score(self):
        topic = {
            "topic": "测试选题",
            "category": "物业服务",
            "trigger": "物业项目调整",
            "score": 60,
            "interview_targets": [],
            "questions": [],
        }
        topic_with_data = {
            **topic,
            "trigger": "物业项目调整，金额10亿元，占比20%",
            "materials": ["项目清单", "金额口径"],
        }

        score_without_data = score_topics([topic])[0]["final_score"]
        score_with_data = score_topics([topic_with_data])[0]["final_score"]

        self.assertGreater(score_with_data, score_without_data)

    def test_material_builder_returns_verification_plan(self):
        topic = {
            "category": "土地市场",
            "trigger": "武汉土拍城投占比超70%",
            "materials": ["自然资源部门成交公告"],
        }
        plan = build_materials(topic)

        self.assertIn("自然资源部门成交公告", plan["must_have"])
        self.assertTrue(plan["verification_steps"])
        self.assertTrue(plan["missing_data_risks"])

    def test_photo_planner_returns_land_shot_list(self):
        plan = plan_photography({
            "category": "土地市场",
            "trigger": "武汉土拍城投占比超70%",
        })

        self.assertIn("涉事地块全景和四至边界", plan["must_shoot"])
        self.assertTrue(plan["caption_checklist"])
        self.assertTrue(plan["risk_notes"])

    def test_signal_monitor_ranks_risk_signals(self):
        result = monitor_signals([
            {
                "source": "announcement",
                "title": "某房企公告债务展期",
                "summary": "公司流动性压力扩大，涉及金额超过20亿元。",
            }
        ])

        signal = result["signals"][0]
        self.assertIn("企业", signal["domains"])
        self.assertIn("金融", signal["domains"])
        self.assertEqual(signal["priority"], "立即核验")

    def test_city_land_compare_handles_missing_metrics(self):
        result = compare_city_land_markets([{
            "city": "武汉",
            "metrics": {
                "total_land_amount": 100,
                "city_investment_land_amount": 70,
            },
        }])

        profile = result["city_profiles"][0]
        self.assertEqual(profile["dependency_level"], "high")
        self.assertEqual(profile["metrics"]["city_investment_amount_share"], 70)

    def test_draft_editor_flags_missing_attribution(self):
        result = edit_draft("销售金额下降30%，净利润减少20亿元。")

        issue_types = {issue["type"] for issue in result["issues"]}
        self.assertIn("missing_attribution", issue_types)
        self.assertTrue(result["fact_check_queue"])

    def test_evidence_marks_single_unsourced_item_as_needs_check(self):
        result = attach_credibility(
            {"topic": "武汉土地市场变化", "materials": ["自然资源部门成交公告"]},
            {"source": "land", "title": "武汉土拍城投占比超过70%", "summary": "底价成交。"},
        )

        self.assertIn("evidence", result)
        self.assertIn(result["verification_status"], {"needs_check", "insufficient_source"})
        self.assertTrue(result["limitations"])

    def test_source_quality_identifies_government_site(self):
        quality = source_quality("https://www.mohurd.gov.cn/example.html", "住建部")

        self.assertEqual(quality["source_type"], "government")
        self.assertFalse(quality["requires_cross_check"])

    def test_terminal_importer_reads_land_csv(self):
        path = Path(__file__).resolve().parents[1] / "examples" / "sample_land_terminal.csv"
        result = import_terminal_file(str(path), source="sample_terminal")

        self.assertEqual(result["record_count"], 2)
        self.assertEqual(result["city_land_payload"]["cities"][0]["city"], "武汉")
        self.assertEqual(
            result["city_land_payload"]["cities"][0]["metrics"]["city_investment_amount_share"],
            62,
        )

    def test_terminal_importer_keeps_province_and_parcel_tables(self):
        with TemporaryDirectory() as tmpdir:
            province_path = Path(tmpdir) / "province.csv"
            province_path.write_text(
                "省份,溢价率,流拍率,出让面积,出让金额,成交面积,成交单价\n"
                "江苏,1.54,20.3,6657.93,4237.44,4540.66,9332\n",
                encoding="utf-8",
            )
            parcel_path = Path(tmpdir) / "parcel.csv"
            parcel_path.write_text(
                "城市,区县,地块名称,规划用途,总用地面积(㎡),规划建筑面积(㎡),成交价(万元),成交楼面价(元/㎡),竞得方\n"
                "北京市,海淀区,110108017001GB00510,住宅,42734.16,102561.98,915200,89233.8467,华润置地开发(北京)有限公司\n",
                encoding="utf-8",
            )

            province = import_terminal_file(str(province_path), source="province_terminal")
            parcel = import_terminal_file(str(parcel_path), source="parcel_terminal")

        self.assertEqual(province["record_count"], 1)
        self.assertEqual(province["items"][0]["province"], "江苏")
        self.assertEqual(province["items"][0]["metrics"]["transfer_amount"], 4237.44)
        self.assertEqual(parcel["record_count"], 1)
        self.assertEqual(parcel["items"][0]["metrics"]["deal_price_wan"], 915200)
        self.assertEqual(parcel["items"][0]["bidder"], "华润置地开发(北京)有限公司")

    def test_document_parser_reads_text_file(self):
        path = Path(__file__).resolve().parents[1] / "examples" / "sample_policy.txt"
        item = parse_document(str(path), source="sample_document")

        self.assertEqual(item["status"], "ok")
        self.assertEqual(item["city"], "武汉")
        self.assertTrue(item["metrics"]["percentages"])

    def test_source_store_dedupes_items(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "items.jsonl")
            items = [
                {"source": "sample", "title": "武汉土拍", "summary": "城投拿地占比超过60%"},
                {"source": "sample", "title": "武汉土拍", "summary": "城投拿地占比超过60%"},
            ]
            result = append_jsonl(path, items)

            self.assertEqual(result["written"], 1)
            self.assertEqual(len(load_jsonl(path)), 1)

    def test_source_store_can_overwrite_clean_items(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "items.jsonl")
            write_jsonl(path, [{"source": "old", "title": "旧数据"}])
            result = write_jsonl(path, [{"source": "new", "title": "新数据"}])
            records = load_jsonl(path)

            self.assertEqual(result["total"], 1)
            self.assertEqual(records[0]["source"], "new")

    def test_source_store_searches_and_summarizes_large_files(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "items.jsonl")
            result = write_jsonl_stream(
                path,
                [
                    {"source": "draft", "title": "杭州土地市场", "summary": "民企回归核心地块"},
                    {"source": "report", "title": "北京办公楼", "summary": "租金仍承压"},
                    {"source": "draft", "title": "杭州土地市场", "summary": "民企回归核心地块"},
                ],
            )
            summary = summarize_jsonl(path)
            matches = search_jsonl(path, "杭州 民企", limit=5)

            self.assertEqual(result["total"], 2)
            self.assertEqual(summary["total"], 2)
            self.assertEqual(summary["source_counts"]["draft"], 1)
            self.assertEqual(matches["matched"], 1)
            self.assertIn("杭州土地市场", matches["items"][0]["title"])

    def test_source_store_search_paginates_matches(self):
        with TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "items.jsonl")
            write_jsonl(
                path,
                [
                    {"source": "draft", "title": "杭州土地市场一", "summary": "民企回归"},
                    {"source": "draft", "title": "杭州土地市场二", "summary": "溢价率回升"},
                    {"source": "draft", "title": "杭州土地市场三", "summary": "城投减少"},
                ],
            )
            matches = search_jsonl(path, "杭州", limit=1, offset=1)

            self.assertEqual(matches["matched"], 3)
            self.assertEqual(matches["returned"], 1)
            self.assertIn("二", matches["items"][0]["title"])

    def test_ifind_client_normalizes_fake_sdk_result(self):
        class FakeSDK:
            def THS_EDB(self, codes, params, start_date, end_date):
                return SimpleNamespace(
                    errorcode=0,
                    data=[
                        {"date": "2025-01-01", "city": "武汉", "value": 62.0},
                        {"date": "2025-02-01", "city": "武汉", "value": 58.0},
                    ],
                )

        client = IFIndClient(sdk=FakeSDK())
        result = client.query(
            IFIndQuery(
                function="edb",
                codes="SAMPLE_CODE",
                start_date="2025-01-01",
                end_date="2025-02-01",
            )
        )
        items = ifind_result_to_items(result)

        self.assertEqual(result["row_count"], 2)
        self.assertEqual(items[0]["source"], "同花顺iFinD")
        self.assertEqual(items[0]["city"], "武汉")

    def test_city_investment_land_model_adds_risk_and_shares(self):
        result = build_city_investment_land_model({
            "city": "武汉",
            "yearly": [
                {
                    "year": 2021,
                    "total_land_transaction_amount": 100,
                    "city_investment_land_amount": 10,
                    "total_land_gfa": 100,
                    "city_investment_land_gfa": 10,
                },
                {
                    "year": 2024,
                    "total_land_transaction_amount": 100,
                    "city_investment_land_amount": 70,
                    "total_land_gfa": 100,
                    "city_investment_land_gfa": 75,
                },
            ],
            "disposal": [
                {"disposal_type": "idle_or_unstarted", "amount": 60, "gfa": 50},
                {"disposal_type": "entrusted_construction", "amount": 40, "gfa": 50},
            ],
            "special_bonds": [
                {
                    "special_bond_issued_amount": 100,
                    "land_reserve_repurchase_amount": 40,
                    "idle_land_repurchase_amount": 20,
                    "related_city_investment_land_book_value": 100,
                }
            ],
        })

        self.assertEqual(result["subject"]["city"], "武汉")
        self.assertTrue(result["executive_summary"])
        self.assertGreater(result["risk_assessment"]["score"], 40)
        idle = result["disposal_summary"]["summary"]["idle_or_unstarted"]
        self.assertEqual(idle["amount_share"], 60)


if __name__ == "__main__":
    unittest.main()
