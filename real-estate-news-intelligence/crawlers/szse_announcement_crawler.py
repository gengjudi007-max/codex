from crawlers.base_crawler import BaseCrawler


class SZSEAnnouncementCrawler(BaseCrawler):
    def extract_announcements(self, soup):
        results = []

        for link in soup.find_all('a'):
            title = link.get_text(strip=True)
            href = link.get('href')

            if title and href:
                results.append({
                    'title': title,
                    'url': href,
                    'exchange': 'SZSE'
                })

        return results

    def run(self):
        html = self.fetch()
        soup = self.parse_html(html)
        return self.extract_announcements(soup)
