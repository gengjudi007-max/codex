from parsers.pdf_table_extractor import PDFTableExtractor
from parsers.financial_table_classifier import FinancialTableClassifier
from parsers.financial_table_normalizer import FinancialTableNormalizer


class FinancialStatementExtractor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.table_extractor = PDFTableExtractor(file_path)
        self.classifier = FinancialTableClassifier()
        self.normalizer = FinancialTableNormalizer()

    def extract(self):
        extracted_tables = self.table_extractor.extract_tables()
        results = []

        for table in extracted_tables:
            rows = table.get('rows', [])
            table_types = self.classifier.classify(rows)
            normalized_rows = self.normalizer.normalize(rows)

            results.append({
                'page_number': table.get('page_number'),
                'table_index': table.get('table_index'),
                'table_types': table_types,
                'normalized_rows': normalized_rows
            })

        return results
