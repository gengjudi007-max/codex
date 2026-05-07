ANNOUNCEMENT_TYPES = {
    'annual_report': ['年度报告', '年报'],
    'profit_warning': ['盈利预警', '亏损'],
    'debt_restructuring': ['债务重组', '重组'],
    'asset_sale': ['出售资产', '资产出售'],
    'financing': ['融资', '发债'],
    'land_acquisition': ['竞得土地', '土地使用权'],
    'litigation': ['诉讼', '仲裁'],
    'liquidation': ['清盘', '清算']
}


class AnnouncementClassifier:
    def classify(self, title, text=''):
        combined = f'{title} {text}'

        matched = []

        for announcement_type, keywords in ANNOUNCEMENT_TYPES.items():
            for keyword in keywords:
                if keyword in combined:
                    matched.append(announcement_type)
                    break

        return matched or ['general_announcement']
