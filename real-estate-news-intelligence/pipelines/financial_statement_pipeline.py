import json

from pipelines.database import Database
from parsers.financial_statement_extractor import FinancialStatementExtractor


class FinancialStatementPipeline:
    def __init__(self):
        self.db = Database()
        self.db.initialize()

    def process(self, file_path, company_name='', report_period=''):
        extractor = FinancialStatementExtractor(file_path)
        tables = extractor.extract()

        for table in tables:
            table_types = ','.join(table.get('table_types', []))

            query = '''
            INSERT INTO financial_statement_tables (
                company_name,
                report_period,
                table_type,
                page_number,
                table_index,
                raw_json,
                source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            '''

            self.db.execute(query, [
                company_name,
                report_period,
                table_types,
                table.get('page_number'),
                table.get('table_index'),
                json.dumps(table.get('normalized_rows'), ensure_ascii=False),
                file_path
            ])

        return tables
