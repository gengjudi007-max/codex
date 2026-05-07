from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CityLandSource:
    city: str
    source: str
    url: str
    parser: str = "api_placeholder"
    source_level: str = "level_2"
    api_url: Optional[str] = None
    notes: Optional[str] = None


CITY_LAND_SOURCES: Dict[str, CityLandSource] = {
    "北京": CityLandSource(
        city="北京",
        source="北京市规划和自然资源委员会",
        url="https://yewu.ghzrzyw.beijing.gov.cn/gwxxfb/tdsc/tdzpgxm.html",
        parser="beijing_api",
        api_url="https://yewu.ghzrzyw.beijing.gov.cn/zkdncms/tdgltdsc/tdzpgxm/esSearchList",
        notes="已确认XHR接口，可稳定抓取。",
    ),
    "上海": CityLandSource(
        city="上海",
        source="上海土地市场",
        url="https://www.shtdsc.com/",
        notes="待补充成交结果XHR/API接口。",
    ),
    "深圳": CityLandSource(
        city="深圳",
        source="深圳公共资源交易中心/深圳市规划和自然资源局",
        url="https://www.szggzy.com/",
        notes="待补充土地交易XHR/API接口。",
    ),
    "广州": CityLandSource(
        city="广州",
        source="广州市规划和自然资源局/广州公共资源交易中心",
        url="https://ghzyj.gz.gov.cn/",
        notes="待补充土地成交结果XHR/API接口。",
    ),
    "杭州": CityLandSource(
        city="杭州",
        source="杭州市规划和自然资源局/浙江省土地使用权网上交易系统",
        url="https://ghzy.hangzhou.gov.cn/",
        notes="待补充土地成交结果XHR/API接口。",
    ),
    "成都": CityLandSource(
        city="成都",
        source="成都市公共资源交易服务中心/成都市规划和自然资源局",
        url="https://www.cdggzy.com/",
        notes="待补充土地矿权交易成交公示XHR/API接口。",
    ),
    "西安": CityLandSource(
        city="西安",
        source="西安市自然资源和规划局/西安市公共资源交易中心",
        url="https://zygh.xa.gov.cn/",
        notes="待补充国有建设用地使用权成交公示XHR/API接口。",
    ),
    "武汉": CityLandSource(
        city="武汉",
        source="武汉市自然资源和城乡建设局/武汉土地市场网",
        url="https://zrzyhgh.wuhan.gov.cn/",
        notes="待补充土地市场成交公告XHR/API接口。",
    ),
    "天津": CityLandSource(
        city="天津",
        source="天津市规划和自然资源局/天津土地交易中心",
        url="https://ghhzrzy.tj.gov.cn/",
        notes="待补充土地出让成交结果XHR/API接口。",
    ),
    "重庆": CityLandSource(
        city="重庆",
        source="重庆市规划和自然资源局/重庆市公共资源交易网",
        url="https://ghzrzyj.cq.gov.cn/",
        notes="待补充土地交易成交公示XHR/API接口。",
    ),
}


def get_city_land_sources(cities: Optional[List[str]] = None) -> List[CityLandSource]:
    if not cities:
        return list(CITY_LAND_SOURCES.values())
    return [CITY_LAND_SOURCES[city] for city in cities if city in CITY_LAND_SOURCES]
