from bs4 import BeautifulSoup

from connectors.http_client import HTTPClient


class HKEXConnector:
    BASE_URL = 'https://www.hkexnews.hk/'

    def __init__(self):
        self.client = HTTPClient()

    def fetch_homepage(self):
        response = self.client.get(self.BASE_URL)
        return response.text

    def parse_latest_links(self, html):
        soup = BeautifulSoup(html, 'lxml')
        results = []

        for link in soup.find_all('a'):
            title = link.get_text(strip=True)
            href = link.get('href')

            if title and href:
                results.append({
                    'title': title,
                    'url': href
                })

        return results

    def get_latest_announcements(self):
        html = self.fetch_homepage()
        return self.parse_latest_links(html)
