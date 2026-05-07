from codex.services.topic_finder import find_topics
from codex.services.topic_scoring import score_topics


def run_daily_topic_engine():
    """每日自动选题主程序"""

    input_data = {
        "items": [
            {
                "source": "policy",
                "title": "政治局会议提出努力稳定房地产市场",
                "summary": "政策强调努力稳定房地产市场",
            },
            {
                "source": "announcement",
                "company": "保利发展",
                "title": "保利发展净利润同比下降40%",
                "summary": "利润下滑与减值增加",
            },
            {
                "source": "land",
                "city": "武汉",
                "title": "武汉土拍城投占比超70%",
                "summary": "土地市场仍依赖托底",
            },
        ]
    }

    topics = find_topics(input_data)
    scored_topics = score_topics(topics)

    print("=== 今日房地产选题清单 ===")

    for i, topic in enumerate(scored_topics, 1):
        print(f"\n[{i}] {topic['topic']}")
        print("优先级:", topic["priority"])
        print("评分:", topic["final_score"])
        print("角度:", topic["angle"])
        print("采访对象:", topic["interview_targets"])
        print("问题:", topic["questions"])


if __name__ == "__main__":
    run_daily_topic_engine()
