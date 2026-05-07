CHENGTOU_KEYWORDS = [
    '城投',
    '城市建设',
    '国资',
    '开发投资',
    '建设投资',
    '国有资本',
    '城乡建设'
]


class ChengtouIdentifier:
    def is_chengtou(self, company_name):
        if not company_name:
            return False

        for keyword in CHENGTOU_KEYWORDS:
            if keyword in company_name:
                return True

        return False


if __name__ == '__main__':
    identifier = ChengtouIdentifier()

    companies = [
        '杭州城市建设投资集团',
        '保利发展',
        '武汉城投集团',
        '龙湖集团'
    ]

    for company in companies:
        print(company, identifier.is_chengtou(company))
