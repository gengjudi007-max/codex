import re


POLICY_KEYWORDS = [
    '房地产',
    '保障房',
    '收储',
    '专项债',
    '限购',
    '公积金',
    '土地',
    '城市更新'
]


class PolicyParser:
    def extract_keywords(self, text):
        results = []

        for keyword in POLICY_KEYWORDS:
            if keyword in text:
                results.append(keyword)

        return results

    def extract_amounts(self, text):
        pattern = r'\d+(?:\.\d+)?亿元'
        return re.findall(pattern, text)

    def extract_dates(self, text):
        pattern = r'\d{4}年\d{1,2}月\d{1,2}日'
        return re.findall(pattern, text)

    def parse(self, text):
        return {
            'keywords': self.extract_keywords(text),
            'amounts': self.extract_amounts(text),
            'dates': self.extract_dates(text)
        }
