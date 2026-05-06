class FinancialReportAnalyzer:
    def analyze(self, extracted_tables):
        insights = []

        for table in extracted_tables:
            table_types = table.get('table_types', [])

            if 'balance_sheet' in table_types:
                insights.append('发现资产负债表，可进一步分析负债规模与现金情况。')

            if 'income_statement' in table_types:
                insights.append('发现利润表，可进一步分析收入与利润变化。')

            if 'cash_flow_statement' in table_types:
                insights.append('发现现金流量表，可进一步分析经营性现金流。')

        return insights
