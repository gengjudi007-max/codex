import requests
from bs4 import BeautifulSoup
from datetime import datetime


class BaseCrawler:
    def __init__(self, source_name, base_url):
        self.source_name = source_name
        self.base_url = base_url

    def fetch(self, url=None):
        target_url = url or self.base_url
        response = requests.get(target_url, timeout=30)
        response.raise_for_status()
        return response.text

    def parse_html(self, html):
        return BeautifulSoup(html, 'lxml')

    def build_document(self, title, source_url, content):
        return {
            'source_name': self.source_name,
            'title': title,
            'source_url': source_url,
            'content': content,
            'fetched_at': datetime.now().isoformat()
        }
