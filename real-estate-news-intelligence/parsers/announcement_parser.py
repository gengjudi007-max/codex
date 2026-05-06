import re


RISK_KEYWORDS = [
    '亏损',
    '债务',
    '重组',
    '违约',
    '出售资产',
    '展期',
    '清盘'
]


class AnnouncementParser:
    def extract_risk_keywords(self, text):
        matched = []

        for keyword in RISK_KEYWORDS:
            if keyword in text:
                matched.append(keyword)

        return matched

    def extract_company_names(self, text):
        pattern = r'[\u4e00-\u9fa5]{2,20}(?:集团|地产|发展|物业|控股|股份)'
        return list(set(re.findall(pattern, text)))

    def extract_amounts(self, text):
        pattern = r'\d+(?:\.\d+)?亿元'
        return re.findall(pattern, text)

    def parse(self, text):
        return {
            'risk_keywords': self.extract_risk_keywords(text),
            'companies': self.extract_company_names(text),
            'amounts': self.extract_amounts(text)
        }
