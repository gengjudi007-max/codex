import re


class FinancialMetricExtractor:
    def extract_revenue(self, text):
        pattern = r'营业收入[为：:]?\s*(\d+(?:\.\d+)?)亿元'
        return re.findall(pattern, text)

    def extract_net_profit(self, text):
        pattern = r'净利润[为：:]?\s*(\-?\d+(?:\.\d+)?)亿元'
        return re.findall(pattern, text)

    def extract_debt(self, text):
        pattern = r'有息负债[为：:]?\s*(\d+(?:\.\d+)?)亿元'
        return re.findall(pattern, text)

    def extract_cash(self, text):
        pattern = r'现金[及与]?现金等价物[为：:]?\s*(\d+(?:\.\d+)?)亿元'
        return re.findall(pattern, text)

    def parse(self, text):
        return {
            'revenue': self.extract_revenue(text),
            'net_profit': self.extract_net_profit(text),
            'interest_bearing_debt': self.extract_debt(text),
            'cash_and_equivalents': self.extract_cash(text)
        }
