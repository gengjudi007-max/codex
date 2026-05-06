from crawlers.base_crawler import BaseCrawler


class HKEXAnnouncementCrawler(BaseCrawler):
    def extract_announcements(self, soup):
        results = []

        for link in soup.find_all('a'):
            title = link.get_text(strip=True)
            href = link.get('href')

            if title and href:
                results.append({
                    'title': title,
                    'url': href,
                    'exchange': 'HKEX'
                })

        return results

    def run(self):
        html = self.fetch()
        soup = self.parse_html(html)
        return self.extract_announcements(soup)


if __name__ == '__main__':
    crawler = HKEXAnnouncementCrawler(
        source_name='港交所披露易',
        base_url='https://www.hkexnews.hk/'
    )

    announcements = crawler.run()

    for item in announcements[:10]:
        print(item)
