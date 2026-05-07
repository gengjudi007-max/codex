from __future__ import annotations

from typing import Any, Dict, List

from codex.services.text_utils import unique


def plan_interview(topic: Dict[str, Any]) -> Dict[str, Any]:
    """生成分层采访方案。"""
    targets = unique(topic.get("interview_targets", []) + _extra_targets(topic.get("category", "")))
    questions = unique(topic.get("questions", []) + _extra_questions(topic))

    return {
        "targets": targets,
        "question_groups": {
            "fact_check": _fact_check_questions(topic),
            "cause_and_mechanism": questions,
            "impact_and_follow_up": _impact_questions(topic),
        },
        "order": [
            "先联系原始信息发布方或事件主体核实事实。",
            "再采访第三方研究者或分析师建立行业坐标。",
            "最后补充一线对象或交易对手，验证真实执行情况。",
        ],
        "red_lines": [
            "避免要求受访者确认未经公开披露的敏感交易细节。",
            "涉及债务、融资和监管事项时，应给相关主体充分回应机会。",
            "匿名信源需说明身份类型和利益关系，不能替代关键事实文件。",
        ],
    }


def _extra_targets(category: str) -> List[str]:
    mapping = {
        "土地市场": ["土地交易中心人士", "代建企业拓展负责人", "城投债承销人士"],
        "房企经营": ["审计人士", "债权人或固收研究员", "项目公司人士"],
        "政策解读": ["地方执行部门人士", "商业银行房地产金融人士"],
        "不动产金融": ["交易所相关业务人士", "底层资产运营方"],
        "城市更新与住房问题": ["居民代表", "街道/社区工作人员", "项目施工方"],
    }
    return mapping.get(category, ["行业研究员", "事件相关主体"])


def _extra_questions(topic: Dict[str, Any]) -> List[str]:
    category = topic.get("category", "")
    if category == "土地市场":
        return [
            "竞得方资金来源是什么，是否承担地方托底任务？",
            "地块后续由谁操盘开发，是否已有代建或合作安排？",
            "成交结构变化会如何影响地方政府性基金收入？",
        ]
    if category == "房企经营":
        return [
            "利润变化中有多少来自结算节奏，有多少来自减值和融资成本？",
            "销售回款和经营现金流是否同步改善？",
            "企业是否调整拿地、产品或城市布局策略？",
        ]
    if category == "政策解读":
        return [
            "政策落地需要哪些部门和金融机构配合？",
            "哪些城市或企业最先受影响？",
            "市场预期变化是否已经反映在成交和价格数据中？",
        ]
    return ["这个变化是否具备持续性？", "还有哪些数据可以验证这一判断？"]


def _fact_check_questions(topic: Dict[str, Any]) -> List[str]:
    return [
        f"触发信息“{topic.get('trigger', '相关信息')}”的原始出处和发布时间是什么？",
        "关键数字的统计区间、口径和样本范围是什么？",
        "是否存在后续更正、补充公告或不同口径数据？",
    ]


def _impact_questions(topic: Dict[str, Any]) -> List[str]:
    return [
        "该事件对企业、地方财政、购房者或金融机构分别意味着什么？",
        "未来一到两个季度最值得跟踪的先行指标是什么？",
        "如果判断错误，最可能被哪个反向信号证伪？",
    ]
