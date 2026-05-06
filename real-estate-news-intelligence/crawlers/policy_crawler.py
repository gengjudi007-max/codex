from crawlers.base_crawler import BaseCrawler


class PolicyCrawler(BaseCrawler):
    def extract_policy_links(self, soup):
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

    def run(self):
        html = self.fetch()
        soup = self.parse_html(html)
        return self.extract_policy_links(soup)


if __name__ == '__main__':
    crawler = PolicyCrawler(
        source_name='住房和城乡建设部',
        base_url='https://www.mohurd.gov.cn/'
    )

    policies = crawler.run()

    for item in policies[:10]:
        print(item)
