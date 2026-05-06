from connectors.hkex_connector import HKEXConnector
from connectors.mohurd_connector import MOHURDConnector
from connectors.china_land_market_connector import ChinaLandMarketConnector
from pipelines.ingest_pipeline import IngestPipeline


class RealDataPipeline:
    def __init__(self):
        self.ingest_pipeline = IngestPipeline()
        self.hkex = HKEXConnector()
        self.mohurd = MOHURDConnector()
        self.landchina = ChinaLandMarketConnector()

    def ingest_hkex(self):
        announcements = self.hkex.get_latest_announcements()

        for item in announcements[:20]:
            self.ingest_pipeline.save_raw_document({
                'source_name': 'HKEX',
                'source_type': 'announcement',
                'source_url': item.get('url'),
                'title': item.get('title'),
                'publish_time': '',
                'raw_text': item.get('title'),
                'raw_html': ''
            })

    def ingest_mohurd(self):
        policies = self.mohurd.get_latest_policies()

        for item in policies[:20]:
            self.ingest_pipeline.save_raw_document({
                'source_name': 'MOHURD',
                'source_type': 'policy',
                'source_url': item.get('url'),
                'title': item.get('title'),
                'publish_time': '',
                'raw_text': item.get('title'),
                'raw_html': ''
            })

    def ingest_landchina(self):
        lands = self.landchina.get_latest_land_transactions()

        for item in lands[:20]:
            self.ingest_pipeline.save_raw_document({
                'source_name': 'LandChina',
                'source_type': 'land_transaction',
                'source_url': item.get('url'),
                'title': item.get('title'),
                'publish_time': '',
                'raw_text': item.get('title'),
                'raw_html': ''
            })

    def run(self):
        self.ingest_hkex()
        self.ingest_mohurd()
        self.ingest_landchina()


if __name__ == '__main__':
    pipeline = RealDataPipeline()
    pipeline.run()
    print('Real data ingestion completed.')
