class FinancialTableNormalizer:
    def normalize(self, table_rows):
        if not table_rows:
            return []

        headers = table_rows[0]
        normalized = []

        for row in table_rows[1:]:
            row_data = {}

            for index, header in enumerate(headers):
                value = row[index] if index < len(row) else ''
                row_data[header] = value

            normalized.append(row_data)

        return normalized
