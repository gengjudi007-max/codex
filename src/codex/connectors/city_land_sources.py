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
        parser="shanghai_playwright",
        api_url="https://biz.ghzyj.sh.gov.cn/shtdsc/jy/api/result/listForPage",
        notes="已修复（使用Playwright绕过SSL错误）。",
    ),
    "深圳": CityLandSource(
        city="深圳",
        source="深圳公共资源交易中心/深圳市规划和自然资源局",
        url="https://www.szggzy.com/",
        notes="待补充土地交易XHR/API接口。",
    ),
    "广州": CityLandSource(
        city="广州",
        source="广州市规划和自然资源局",
        url="https://ghzyj.gz.gov.cn/ywpd/tdgl/tdjysc/cjgs/index.html",
        parser="guangzhou_curl_regex",
        notes="已修复（使用curl + 正则表达式）。",
    ),
    "深圳": CityLandSource(
        city="深圳",
        source="深圳市规划和自然资源局",
        url="https://pnr.sz.gov.cn/ywzy/tdjygs/index.html",
        parser="shenzhen_curl_regex",
        notes="已修复（使用curl + 正则表达式）。",
    ),
    "杭州": CityLandSource(
        city="杭州",
        source="杭州市人民政府门户网站",
        url="https://www.hangzhou.gov.cn/col/col1228974784/index.html",
        parser="hangzhou_curl_regex",
        notes="已修复（使用curl + 正则表达式）。",
    ),
    "成都": CityLandSource(
        city="成都",
        source="中国土地市场网",
        url="https://landchina.mnr.gov.cn/land/cjgs/",
        parser="china_land_market",
        notes="简化版（使用中国土地市场网，数据较少）。",
    ),
    "西安": CityLandSource(
        city="西安",
        source="中国土地市场网",
        url="https://landchina.mnr.gov.cn/land/cjgs/",
        parser="china_land_market",
        notes="简化版（使用中国土地市场网，数据较少）。",
    ),
    "武汉": CityLandSource(
        city="武汉",
        source="中国土地市场网",
        url="https://landchina.mnr.gov.cn/land/cjgs/",
        parser="china_land_market",
        notes="简化版（使用中国土地市场网，数据较少）。",
    ),
    "天津": CityLandSource(
        city="天津",
        source="中国土地市场网",
        url="https://landchina.mnr.gov.cn/land/cjgs/",
        parser="china_land_market",
        notes="简化版（使用中国土地市场网，数据较少）。",
    ),
    "重庆": CityLandSource(
        city="重庆",
        source="中国土地市场网",
        url="https://landchina.mnr.gov.cn/land/cjgs/",
        parser="china_land_market",
        notes="简化版（使用中国土地市场网，数据较少）。",
    ),
}


def get_city_land_sources(cities: Optional[List[str]] = None) -> List[CityLandSource]:
    if not cities:
        return list(CITY_LAND_SOURCES.values())
    return [CITY_LAND_SOURCES[city] for city in cities if city in CITY_LAND_SOURCES]
