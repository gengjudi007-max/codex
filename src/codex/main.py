from codex.services.topic_finder import find_topics


def main():
    """运行房地产选题规则系统（第一版）"""

    input_data = {
        "items": [
            {
                "source": "policy",
                "title": "政治局会议提出努力稳定房地产市场",
                "summary": "政策强调努力稳定房地产市场，支持合理住房需求",
            },
            {
                "source": "company_announcement",
                "company": "某大型房企",
                "title": "某大型房企发布年报，净利润大幅下降",
                "summary": "公司净利润同比下降40%，计提大额减值",
            },
            {
                "source": "land_market",
                "city": "杭州",
                "title": "杭州多宗土地底价成交，城投平台成为拿地主力",
                "summary": "城投拿地占比提升，土地市场持续低温",
            },
        ]
    }

    topics = find_topics(input_data)

    print("=== Real Estate Topic Engine v1 ===")
    for i, topic in enumerate(topics, 1):
        print(f"\n[{i}] {topic['topic']}")
        print("类别:", topic["category"])
        print("角度:", topic["angle"])
        print("原因:", topic["reason"])
        print("建议采访对象:", topic["interview_targets"])
        print("关键问题:", topic["questions"])


if __name__ == "__main__":
    main()
