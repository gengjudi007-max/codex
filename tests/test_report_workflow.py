import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import urllib.error

from codex.interaction import analyze_payload
from codex.services.deep_report_drafter import draft_deep_report
from codex.services.final_editorial_engine import final_edit_report
from codex.services.model_writer import generate_model_report, validate_model_report
from codex.services.grounded_report import source_records, write_grounded_report
from codex.services.newsroom_orchestrator import run_newsroom_orchestrator

ROOT = Path(__file__).resolve().parents[1]


class RealPolicyReportTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads((ROOT / 'examples/policy_828.json').read_text())

    def test_prior_zero_topic_case_now_triggers_and_writes(self):
        result = analyze_payload({**self.payload, 'mode': 'report'})['result']
        self.assertGreater(result['topic_pipeline']['topic_count'], 0)
        rules = {t['rule_name'] for t in result['topic_pipeline']['topics']}
        self.assertIn('housing_sales_implementation', rules)
        self.assertIn('project_credit_implementation', rules)
        self.assertIn('35.61亿元', result['article_text'])
        self.assertNotIn('【待补', result['article_text'])
        self.assertNotIn('这一部分应', result['article_text'])
        self.assertFalse(result['verification_gate']['publishable'])
        lookup = {s['id']: s for s in result['sources']}
        for paragraph in result['paragraphs']:
            self.assertIn(paragraph['excerpt'], lookup[paragraph['source_id']]['content'])
            self.assertEqual(result['article_text'].count(paragraph['text']), 1)

    def test_sources_only_routes_without_network(self):
        with patch('urllib.request.urlopen', side_effect=AssertionError('no network')):
            result = analyze_payload({'sources': self.payload['sources']})
        self.assertEqual(result['mode'], 'report')
        self.assertTrue(result['result']['article_text'])

    def test_source_only_orchestrator_has_topics_and_article(self):
        with TemporaryDirectory() as tmp:
            result = run_newsroom_orchestrator({'sources': self.payload['sources'], 'memory_path': str(Path(tmp)/'memory.jsonl')})
        self.assertGreater(result['topics']['topic_count'], 0)
        self.assertTrue(result['article']['article_text'])

    def test_existing_writer_entrypoints_produce_body(self):
        for result in (draft_deep_report(self.payload), final_edit_report(self.payload)):
            self.assertIn('35.61亿元', result['article_text'])
            self.assertNotIn('【待补', result['article_text'])

    def test_missing_content_is_blocked(self):
        result = write_grounded_report({'sources': [{'url':'https://example.org/a','title':'文件'}]})
        self.assertEqual(result['article_text'], '')
        self.assertEqual(result['verification_gate']['status'], 'blocked_missing_source_content')

    def test_duplicate_sources_and_sentences(self):
        p = {'sources': self.payload['sources'] * 2}
        result = write_grounded_report(p)
        self.assertEqual(len(result['sources']), 3)
        self.assertEqual(len({x['excerpt'] for x in result['paragraphs']}), len(result['paragraphs']))

    def test_bad_source_returns_clear_error(self):
        for value in ['bad', [None], [{'content': ['not text']}]]:
            self.assertIn('error', analyze_payload({'mode':'report','sources':value}))

    def test_unrelated_text_does_not_create_real_estate_topic(self):
        result = analyze_payload({'items':[{'title':'晚餐安排','summary':'今晚吃面条。'}]})
        self.assertEqual(result['result']['topic_count'], 0)

    def test_quotes_and_decimals_survive(self):
        text = '受访者表示：“我们不会提前回款。项目仍需贷款。”成交额35.61亿元。'
        report = write_grounded_report({'sources':[{'title':'采访记录','content':text}]})
        self.assertIn('“我们不会提前回款。项目仍需贷款。”', report['article_text'])
        self.assertIn('35.61亿元', report['article_text'])

    def test_cli_actual_export(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp)/'article.md'
            run = subprocess.run([sys.executable,'-m','codex.cli','report','--input',str(ROOT/'examples/policy_828.json'),'--output',str(output)], cwd=ROOT, env={**os.environ,'PYTHONPATH':str(ROOT/'src')}, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('35.61亿元', output.read_text())


class ModelWriterTests(unittest.TestCase):
    def setUp(self):
        self.sources = source_records({'sources':[{'title':'公告','content':'项目成交35.61亿元。','url':'https://example.org/a'}]})
        self.draft = {'headline':'项目成交', 'paragraphs':[{'section':'', 'text':'公告显示，项目成交35.61亿元。','kind':'fact','evidence':[{'source_id':'S1','quote':'项目成交35.61亿元。'}]}]}

    def test_missing_configuration_is_not_silent_fallback(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, '未配置'):
                generate_model_report(self.sources)

    def test_api_request_and_completed_response(self):
        response = {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(self.draft)}]}]}
        with patch.dict(os.environ, {'OPENAI_API_KEY':'test-only', 'CODEX_WRITER_MODEL':'test-model'}):
            with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(response).encode())) as call:
                result = generate_model_report(self.sources)
        request = call.call_args.args[0]
        body = json.loads(request.data)
        self.assertFalse(body['store'])
        self.assertEqual(body['text']['format']['type'],'json_schema')
        self.assertEqual(result['writer'], 'model')
        self.assertFalse(result['verification_gate']['publishable'])

    def test_unknown_source_or_quote_or_number_is_rejected(self):
        for field,value in [('source_id','S9'),('quote','项目成交100亿元。')]:
            draft=copy.deepcopy(self.draft); draft['paragraphs'][0]['evidence'][0][field]=value
            with self.assertRaises(ValueError): validate_model_report(draft,self.sources)
        draft=copy.deepcopy(self.draft); draft['paragraphs'][0]['text']='成交999亿元。'
        with self.assertRaises(ValueError): validate_model_report(draft,self.sources)

    def test_incomplete_response_is_rejected(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY':'test-only','CODEX_WRITER_MODEL':'test-model'}):
            with patch('urllib.request.urlopen', return_value=io.BytesIO(b'{"status":"incomplete"}')):
                with self.assertRaisesRegex(ValueError,'未完成'): generate_model_report(self.sources)

    def test_http_error_does_not_expose_provider_body(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY':'test-only','CODEX_WRITER_MODEL':'test-model'}):
            with patch('urllib.request.urlopen', side_effect=urllib.error.HTTPError('x',401,'private provider message',{},None)):
                with self.assertRaisesRegex(ValueError,'HTTP 401') as error: generate_model_report(self.sources)
        self.assertNotIn('private',str(error.exception))
