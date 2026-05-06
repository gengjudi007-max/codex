FINANCIAL_TABLE_KEYWORDS = {
    'balance_sheet': [
        '资产负债表',
        '资产总计',
        '负债合计',
        '所有者权益'
    ],
    'income_statement': [
        '利润表',
        '营业收入',
        '营业利润',
        '净利润'
    ],
    'cash_flow_statement': [
        '现金流量表',
        '经营活动产生的现金流量',
        '投资活动产生的现金流量',
        '筹资活动产生的现金流量'
    ]
}


class FinancialTableClassifier:
    def classify(self, table_rows):
        combined_text = ' '.join([
            ' '.join(row)
            for row in table_rows[:10]
        ])

        matched = []

        for table_type, keywords in FINANCIAL_TABLE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    matched.append(table_type)
                    break

        return matched or ['unknown_table']
