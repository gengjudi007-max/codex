RISK_KEYWORDS = [
    '亏损',
    '违约',
    '清盘',
    '展期',
    '重组',
    '出售资产',
    '债务',
    '无法偿还'
]


class AnnouncementMonitor:
    def detect_risk(self, title):
        matched = []

        for keyword in RISK_KEYWORDS:
            if keyword in title:
                matched.append(keyword)

        return matched


if __name__ == '__main__':
    monitor = AnnouncementMonitor()

    title = '某房企发布债务重组及出售资产公告'

    print(monitor.detect_risk(title))
