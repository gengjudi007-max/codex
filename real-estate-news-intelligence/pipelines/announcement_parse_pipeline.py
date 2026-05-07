from parsers.pdf_parser import PDFParser
from parsers.announcement_parser import AnnouncementParser
from parsers.announcement_classifier import AnnouncementClassifier
from parsers.financial_metric_extractor import FinancialMetricExtractor
from parsers.risk_extractor import RiskExtractor


class AnnouncementParsePipeline:
    def __init__(self):
        self.announcement_parser = AnnouncementParser()
        self.classifier = AnnouncementClassifier()
        self.metric_extractor = FinancialMetricExtractor()
        self.risk_extractor = RiskExtractor()

    def parse_pdf(self, file_path, title=''):
        pdf_parser = PDFParser(file_path)
        text = pdf_parser.extract_text()

        parsed = self.announcement_parser.parse(text)
        announcement_types = self.classifier.classify(title, text)
        metrics = self.metric_extractor.parse(text)
        risks = self.risk_extractor.extract(text)

        return {
            'title': title,
            'announcement_types': announcement_types,
            'companies': parsed.get('companies'),
            'amounts': parsed.get('amounts'),
            'risk_keywords': parsed.get('risk_keywords'),
            'financial_metrics': metrics,
            'risks': risks,
            'text_preview': text[:3000]
        }
