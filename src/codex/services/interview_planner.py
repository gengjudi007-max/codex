def plan_interview(topic):
    """生成采访对象与问题"""
    return {
        "targets": ["房企高管", "分析师", "政策专家"],
        "questions": [
            "该政策/事件的核心变化是什么？",
            "对市场和企业意味着什么？",
            "未来趋势如何判断？"
        ]
    }
