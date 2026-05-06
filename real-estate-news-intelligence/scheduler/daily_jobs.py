from datetime import datetime

from pipelines.ingest_pipeline import IngestPipeline
from pipelines.topic_pipeline import TopicPipeline


class DailyJobRunner:
    def __init__(self):
        self.ingest_pipeline = IngestPipeline()
        self.topic_pipeline = TopicPipeline()

    def run_policy_jobs(self):
        print(f'[{datetime.now()}] Running policy jobs...')
        # TODO: connect PolicyCrawler and PolicyParser here.

    def run_announcement_jobs(self):
        print(f'[{datetime.now()}] Running announcement jobs...')
        # TODO: connect HKEX/SSE/SZSE announcement crawlers and parsers here.

    def run_land_jobs(self):
        print(f'[{datetime.now()}] Running land transaction jobs...')
        # TODO: connect land transaction crawlers and land parser here.

    def run_report_jobs(self):
        print(f'[{datetime.now()}] Generating daily report...')
        # TODO: connect DailyReportWriter here.

    def run_all(self):
        self.run_policy_jobs()
        self.run_announcement_jobs()
        self.run_land_jobs()
        self.run_report_jobs()


if __name__ == '__main__':
    runner = DailyJobRunner()
    runner.run_all()
