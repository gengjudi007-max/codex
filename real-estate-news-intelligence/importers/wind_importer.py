import csv

from pipelines.database import Database


class WindImporter:
    def __init__(self):
        self.db = Database()
        self.db.initialize()

    def import_csv(self, file_path):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                query = '''
                INSERT INTO financial_indicators (
                    company_name,
                    stock_code,
                    report_period,
                    revenue,
                    net_profit,
                    source_name,
                    source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                '''

                self.db.execute(query, [
                    row.get('company_name'),
                    row.get('stock_code'),
                    row.get('report_period'),
                    row.get('revenue'),
                    row.get('net_profit'),
                    'Wind',
                    'manual_import'
                ])
