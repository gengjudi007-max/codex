from __future__ import annotations

from typing import Any, Dict, List

from codex.services.text_utils import unique


COMMON_VERIFICATION_STEPS = [
    "核对原始文件发布日期、发布主体和适用范围，避免引用二手转述替代原文。",
    "至少交叉核验两个独立来源，区分事实、观点和推测。",
    "所有同比、占比、金额和面积数据保留原始口径，并注明统计区间。",
]


def build_materials(topic: Dict[str, Any]) -> Dict[str, Any]:
    """围绕选题生成可执行的资料清单。"""
    category = topic.get("category", "")
    base_materials = topic.get("materials", [])
    trigger = topic.get("trigger", "")

    plan = {
        "must_have": unique(base_materials + _category_materials(category)),
        "data_points": _data_points(category, trigger),
        "source_channels": _source_channels(category),
        "verification_steps": COMMON_VERIFICATION_STEPS + _category_checks(category),
        "missing_data_risks": _missing_data_risks(category),
    }
    return plan


def _category_materials(category: str) -> List[str]:
    mapping = {
        "政策解读": ["政策全文", "历史同类政策", "地方执行细则", "监管部门答记者问"],
        "房企经营": ["年报/中报", "业绩说明会纪要", "债券公告", "评级报告", "现金流量表"],
        "土地市场": ["成交确认书", "出让公告", "竞得方工商信息", "地块规划条件", "开竣工状态"],
        "城市更新与住房问题": ["实施方案", "招投标文件", "居民安置方案", "项目资金平衡测算"],
        "不动产金融": ["募集说明书", "底层资产清单", "现金流预测", "交易所问询回复"],
        "物业服务": ["物业公司年报", "在管项目清单", "应收账款明细", "业委会或业主反馈"],
    }
    return mapping.get(category, ["原始材料", "历史报道", "行业数据", "专家访谈"])


def _data_points(category: str, trigger: str) -> List[str]:
    common = ["事件发生时间", "涉及主体", "影响范围", "历史对比口径"]
    if category == "土地市场":
        return common + ["成交金额", "成交建面", "溢价率", "流拍率", "城投拿地占比", "开工/闲置状态"]
    if category == "房企经营":
        return common + ["营收", "净利润", "毛利率", "资产减值", "经营现金流", "现金短债比"]
    if category == "政策解读":
        return common + ["新增措辞", "删除措辞", "执行主体", "地方跟进节奏", "成交和价格变化"]
    if "REITs" in str(trigger) or category == "不动产金融":
        return common + ["融资规模", "期限", "利率", "底层资产现金流", "增信安排"]
    return common + ["核心指标", "同比变化", "区域差异", "可采访对象"]


def _source_channels(category: str) -> List[str]:
    channels = ["政府官网", "交易所公告", "上市公司公告", "行业数据库", "公开报道"]
    if category == "土地市场":
        channels.extend(["自然资源和规划局", "土地交易中心", "城投公司债券募集说明书"])
    if category == "房企经营":
        channels.extend(["港交所/上交所/深交所", "评级机构", "企业业绩会"])
    if category == "政策解读":
        channels.extend(["中国政府网", "住建部", "央行", "金融监管总局", "地方住建部门"])
    return unique(channels)


def _category_checks(category: str) -> List[str]:
    if category == "土地市场":
        return ["拆分城投、央国企、民企买方属性，避免只看成交总额。", "检查地块是否实际开工，防止把托底成交误读为市场修复。"]
    if category == "房企经营":
        return ["区分主营改善、减值减少、投资收益和一次性收益。", "用经营现金流和销售回款验证利润质量。"]
    if category == "政策解读":
        return ["逐句对比前次政策文本，避免过度解读单个词。", "观察地方执行和银行端落地，而非只看政策发布。"]
    return []


def _missing_data_risks(category: str) -> List[str]:
    if category == "土地市场":
        return ["缺少地块级开工状态会削弱对托底属性的判断。", "缺少竞得方穿透信息会影响买方结构判断。"]
    if category == "房企经营":
        return ["缺少项目结转结构会导致利润归因不完整。", "缺少债务期限结构会低估流动性风险。"]
    return ["缺少原始文件或统计口径时，只能作为线索，不能作为结论。"]
