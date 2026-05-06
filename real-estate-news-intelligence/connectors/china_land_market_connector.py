from bs4 import BeautifulSoup

from connectors.http_client import HTTPClient


class ChinaLandMarketConnector:
    BASE_URL = 'https://www.landchina.com/'

    def __init__(self):
        self.client = HTTPClient(request_interval=2)

    def fetch_homepage(self):
        response = self.client.get(self.BASE_URL)
        return response.text

    def parse_land_links(self, html):
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

    def get_latest_land_transactions(self):
        html = self.fetch_homepage()
        return self.parse_land_links(html)
