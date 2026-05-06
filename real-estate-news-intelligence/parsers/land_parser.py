import re


class LandParser:
    def extract_amounts(self, text):
        pattern = r'\d+(?:\.\d+)?亿元'
        return re.findall(pattern, text)

    def extract_area(self, text):
        pattern = r'\d+(?:\.\d+)?万平方米'
        return re.findall(pattern, text)

    def extract_companies(self, text):
        pattern = r'[\u4e00-\u9fa5]{2,20}(?:集团|地产|发展|投资|建设)'
        return list(set(re.findall(pattern, text)))

    def parse(self, text):
        return {
            'amounts': self.extract_amounts(text),
            'areas': self.extract_area(text),
            'companies': self.extract_companies(text)
        }
