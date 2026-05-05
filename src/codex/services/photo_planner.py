from __future__ import annotations

from typing import Any, Dict, List

from codex.services.text_utils import unique


def plan_photography(topic: Dict[str, Any]) -> Dict[str, Any]:
    """为房地产财经报道生成摄影策划。"""
    category = str(topic.get("category", ""))
    trigger = str(topic.get("trigger", "相关线索"))

    return {
        "visual_thesis": _visual_thesis(category, trigger),
        "must_shoot": unique(_must_shoot(category)),
        "optional_shots": unique(_optional_shots(category)),
        "people_and_permissions": _people_and_permissions(category),
        "caption_checklist": _caption_checklist(category),
        "risk_notes": _risk_notes(category),
    }


def _visual_thesis(category: str, trigger: str) -> str:
    mapping = {
        "土地市场": "用地块现状、周边配套和施工进度呈现土地成交背后的真实开发温度。",
        "房企经营": "用项目现场、售楼处客流和企业公开材料把财务压力落到可感知的经营场景。",
        "政策解读": "用办事窗口、销售现场和典型社区呈现政策从文本到执行端的传导。",
        "不动产金融": "用底层资产运营现场和现金流场景解释金融工具是否有真实资产支撑。",
        "城市更新与住房问题": "用居民生活、施工边界和片区肌理呈现改造收益与代价。",
        "物业服务": "用小区公共空间、服务现场和业主互动呈现物业企业质量经营压力。",
    }
    return mapping.get(category, f"围绕“{trigger}”拍到事实现场、关键主体和影响对象。")


def _must_shoot(category: str) -> List[str]:
    mapping = {
        "土地市场": [
            "涉事地块全景和四至边界",
            "地块公示牌、围挡或施工状态",
            "周边道路、地铁、学校、商业等配套",
            "相邻在售或已交付项目现场",
        ],
        "房企经营": [
            "公司重点项目售楼处或施工现场",
            "项目销售公示、价格牌和区位沙盘",
            "交付社区公共空间与入住状态",
            "公开业绩会、公告或交易所材料截图留档",
        ],
        "政策解读": [
            "地方住建、不动产登记或银行办理窗口",
            "典型售楼处看房和签约场景",
            "代表性新房、二手房社区外景",
            "政策发布页面或线下宣传材料",
        ],
        "不动产金融": [
            "底层资产外观和运营动线",
            "租户、客流或经营场景",
            "物业管理与收费场景",
            "融资公告、募集说明书关键页留档",
        ],
        "城市更新与住房问题": [
            "改造片区全景和街巷肌理",
            "居民生活空间与公共设施短板",
            "施工围挡、安置房或过渡房现场",
            "项目公示牌、规划图和征询公告",
        ],
        "物业服务": [
            "小区入口、公共区域和设施维护状态",
            "物业服务中心或公告栏",
            "业主报修、缴费或议事场景",
            "退出或更换物业项目的现场痕迹",
        ],
    }
    return mapping.get(category, ["事件现场全景", "关键主体公开标识", "受影响对象", "原始文件留档"])


def _optional_shots(category: str) -> List[str]:
    common = ["同区域对照样本", "历史照片或街景截图对照", "数据图表可视化底图"]
    if category == "土地市场":
        return common + ["待开发地块航拍视角", "周边库存项目和中介门店"]
    if category == "城市更新与住房问题":
        return common + ["居民旧物、楼道、管线等细节", "改造前后同机位对比"]
    if category == "房企经营":
        return common + ["客流稀疏或促销活动现场", "项目停工、缓建或交付细节"]
    return common


def _people_and_permissions(category: str) -> List[str]:
    base = [
        "拍摄居民、购房者、工作人员正脸前取得明确同意。",
        "进入工地、售楼处、办公楼和小区内部前确认管理方许可。",
        "涉及未成年人、住户门牌、车牌和合同信息时做匿名化处理。",
    ]
    if category in {"不动产金融", "房企经营"}:
        base.append("拍摄企业办公、租户经营和财务文件时避免暴露非公开商业信息。")
    return base


def _caption_checklist(category: str) -> List[str]:
    return [
        "写清拍摄时间、地点、主体和画面所示事实。",
        "区分现场观察和受访者判断，避免图片说明替代事实核验。",
        "涉及金额、面积、占比和政策效果时在图注中标明数据来源。",
        f"图注要回扣{category or '报道'}的核心矛盾，而不是只描述画面物体。",
    ]


def _risk_notes(category: str) -> List[str]:
    notes = ["避免把单个现场的冷清或热闹直接推断为整体市场结论。"]
    if category == "土地市场":
        notes.append("空地、围挡和停工状态需用规划、开工或施工许可材料交叉核验。")
    if category == "城市更新与住房问题":
        notes.append("居民困境画面要保护隐私，避免制造猎奇化叙事。")
    return notes
