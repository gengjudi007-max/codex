from __future__ import annotations

import json
import asyncio
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, Browser, Page


BASE_URL = "https://biz.ghzyj.sh.gov.cn"
SOURCE = "上海土地市场"
API_URL = "https://biz.ghzyj.sh.gov.cn/shtdsc/jy/result/listForPage"


async def fetch_shanghai_land_with_playwright(
    max_pages: int = 1
) -> List[Dict[str, Any]]:
    """
    使用 Playwright 拦截上海土地市场的真实 API 请求
    
    工作原理：
    1. 启动浏览器访问上海土地市场页面
    2. 监听网络请求，拦截真实的 API 调用（包含动态生成的 token）
    3. 提取 API 响应数据
    """
    results = []
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(
            headless=True,  # 生产环境使用 headless 模式
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        # 存储拦截到的 API 数据
        api_responses = []
        
        # 监听响应事件
        async def handle_response(response):
            if 'listForPage' in response.url:
                try:
                    body = await response.text()
                    api_responses.append({
                        'url': response.url,
                        'status': response.status,
                        'body': body
                    })
                    print(f"✅ 拦截到 API 响应: {response.url}")
                    print(f"   状态: {response.status}")
                    print(f"   数据长度: {len(body)}")
                except Exception as e:
                    print(f"❌ 读取响应失败: {e}")
        
        page.on('response', handle_response)
        
        try:
            # 访问上海土地市场页面（正确网址）
            print(f"🌐 正在访问: https://biz.ghzyj.sh.gov.cn/shtdsc/wz/ywtb/index.jhtml")
            await page.goto(
                "https://biz.ghzyj.sh.gov.cn/shtdsc/wz/ywtb/index.jhtml",
                wait_until='networkidle',
                timeout=60000
            )
            
            print("✅ 页面加载完成")
            
            # 等待页面完全渲染（让 JavaScript 执行并生成 token）
            await page.wait_for_timeout(3000)
            
            # 尝试点击"查询"按钮（如果存在）
            try:
                query_button = await page.query_selector('button:has-text("查询")')
                if query_button:
                    print("🖱️  点击查询按钮...")
                    await query_button.click()
                    await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"⚠️  未找到查询按钮: {e}")
            
            # 如果没有拦截到 API 请求，尝试直接访问 API
            if not api_responses:
                print("\n⚠️  未能自动拦截 API 请求，尝试手动触发...")
                
                # 执行页面上的 JavaScript 来触发 API 请求
                await page.evaluate("""
                    () => {
                        // 尝试找到并触发查询函数
                        if (typeof queryData === 'function') {
                            queryData();
                        }
                        if (typeof search === 'function') {
                            search();
                        }
                    }
                """)
                
                await page.wait_for_timeout(3000)
            
            # 解析拦截到的数据
            for resp in api_responses:
                try:
                    data = json.loads(resp['body'])
                    rows = extract_rows(data)
                    
                    for row in rows:
                        item = normalize_row(row)
                        if item:
                            results.append(item)
                            
                    print(f"✅ 成功提取 {len(rows)} 条数据")
                    
                except json.JSONDecodeError:
                    print(f"⚠️  API 响应不是有效的 JSON: {resp['body'][:200]}")
            
            if not results:
                print("\n⚠️  未能获取数据，可能需要:")
                print("   1. 检查页面 URL 是否正确")
                print("   2. 检查是否需要登录")
                print("   3. 检查 token 生成逻辑是否变化")
        
        except Exception as e:
            print(f"❌ 错误: {e}")
            raise
        
        finally:
            await browser.close()
    
    return results


def fetch_shanghai_land_items(
    api_url: str = API_URL,
    payload: Optional[Dict[str, Any]] = None,
    max_pages: int = 1,
    use_playwright: bool = True,
) -> List[Dict[str, Any]]:
    """
    获取上海土地数据（主入口函数）
    
    Args:
        api_url: API 地址
        payload: 请求参数（使用 Playwright 时忽略）
        max_pages: 最大页数
        use_playwright: 是否使用 Playwright（推荐）
    """
    if use_playwright:
        # 使用 Playwright 拦截真实请求
        return asyncio.run(fetch_shanghai_land_with_playwright(max_pages))
    else:
        # 使用原有的 requests 方式（可能失败）
        from .shanghai_land_connector import fetch_shanghai_land_items as _fetch
        return _fetch(api_url, payload, max_pages)


def extract_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从 API 响应中提取数据行"""
    for key in ["data", "rows", "list", "result"]:
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            for nested_key in ["data", "rows", "list", "records"]:
                nested = value.get(nested_key)
                if isinstance(nested, list):
                    return nested
    return []


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """标准化数据行"""
    land_name = pick(row, ["title", "landName", "zdmc", "xmmc", "name", "noticeTitle"])
    district = pick(row, ["county", "district", "qx", "xzq", "regionName"])
    land_use = pick(row, ["landuse", "landUse", "tdyt", "ghyt", "useType"])
    date = pick(row, ["date", "cjsj", "fbsj", "pubdate", "createTime", "dealTime"])
    buyer = pick(row, ["buyer", "jdr", "竞得人", "companyName", "winner"])
    
    metrics = {}
    for key, aliases in {
        "land_area": ["tdmj", "ydmj", "landArea", "area"],
        "planned_gfa": ["jzmj", "ghjzmj", "buildingArea", "gfa"],
        "land_amount": ["cjj", "cjje", "price", "amount", "dealPrice"],
        "floor_price": ["floorPrice", "loudijia", "cjlmj"],
        "premium_rate": ["premiumRate", "yjl", "premium"],
    }.items():
        value = to_number(pick(row, aliases))
        if value is not None:
            metrics[key] = value
    
    content_parts = []
    if land_name:
        content_parts.append(f"地块名称为{land_name}")
    if district:
        content_parts.append(f"所在区域为{district}")
    if land_use:
        content_parts.append(f"规划用途为{land_use}")
    if buyer:
        content_parts.append(f"竞得方为{buyer}")
    
    return {
        "category": "land",
        "title": land_name or "上海土地成交项目",
        "content": "，".join(content_parts) + "。" if content_parts else "上海土地成交项目。",
        "city": "上海",
        "date": date,
        "source": SOURCE,
        "source_level": "level_2",
        "verified": True,
        "metrics": metrics,
        "raw": row,
    }


def pick(row: Dict[str, Any], keys: List[str]) -> Optional[Any]:
    """从多个可能的键中选择第一个存在的值"""
    for key in keys:
        if key in row and row[key] not in [None, ""]:
            return row[key]
    return None


def to_number(value: Any) -> Optional[float]:
    """转换为数字"""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace("%", "")
    try:
        return float(text)
    except ValueError:
        return None


if __name__ == "__main__":
    # 测试代码
    print("🚀 开始测试上海土地数据爬虫（Playwright 版本）")
    print("=" * 60)
    
    results = fetch_shanghai_land_items(use_playwright=True)
    
    print("\n" + "=" * 60)
    print(f"✅ 测试完成，共获取 {len(results)} 条数据")
    
    if results:
        print("\n前 3 条数据:")
        for i, item in enumerate(results[:3], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   内容: {item['content']}")
            print(f"   日期: {item['date']}")
