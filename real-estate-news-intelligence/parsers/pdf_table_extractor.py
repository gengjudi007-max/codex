import json
from pathlib import Path

import pdfplumber


class PDFTableExtractor:
    """Extract tables from announcement PDFs.

    This module is designed for annual reports, interim reports,
    bond prospectuses, and exchange announcements. It uses pdfplumber
    first because it works well with text-based PDFs. Scanned PDFs will
    require OCR and should be handled separately.
    """

    def __init__(self, file_path):
        self.file_path = Path(file_path)

    def extract_tables(self):
        tables = []

        with pdfplumber.open(self.file_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                page_tables = page.extract_tables()

                for table_index, table in enumerate(page_tables, start=1):
                    cleaned_table = self._clean_table(table)
                    if cleaned_table:
                        tables.append({
                            'page_number': page_number,
                            'table_index': table_index,
                            'rows': cleaned_table
                        })

        return tables

    def _clean_table(self, table):
        cleaned = []

        for row in table:
            if not row:
                continue

            cleaned_row = [
                (cell or '').replace('\n', ' ').strip()
                for cell in row
            ]

            if any(cleaned_row):
                cleaned.append(cleaned_row)

        return cleaned

    def save_as_json(self, output_path):
        tables = self.extract_tables()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tables, f, ensure_ascii=False, indent=2)

        return str(output_path)


if __name__ == '__main__':
    extractor = PDFTableExtractor('sample.pdf')
    tables = extractor.extract_tables()
    print(f'Extracted {len(tables)} tables')
