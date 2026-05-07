#!/usr/bin/env python3
"""
统一土地数据爬虫 - 使用 Playwright 拦截所有城市的真实 API 请求
支持：北京、上海、广州、深圳、杭州、成都、西安、武汉、天津、重庆
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright, Page, Browser


# 城市配置
CITY_CONFIGS = {
    "北京": {
        "url": "https://yewu.ghzrzyw.beijing.gov.cn/gwxxfb/tdsc/tdzpgxm.html",
        "api_url": "https://yewu.ghzrzyw.beijing.gov.cn/zkdncms/tdgltdsc/tdzpgxm/esSearchList",
        "method": "GET",
        "notes": "已确认 XHR 接口，可稳定抓取"
    },
    "上海": {
        "url": "https://biz.ghzyj.sh.gov.cn/shtdsc/wz/ywtb/index.jhtml",
        "api_keyword": "listForPage",
        "method": "POST",
        "notes": "需要拦截动态 token"
    },
    "深圳": {
        "url": "https://www.szggzy.com/",
        "api_keyword": "land\|transaction\|trade",
        "method": "未知",
        "notes": "待分析"
    },
    "广州": {
        "url": "https://ghzyj.gz.gov.cn/",
        "api_keyword": "land\|td\|交易",
        "method": "未知",
        "notes": "待分析"
    },
    # 其他城市配置...
}


class UnifiedLandScraper:
    """统一土地数据爬虫"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.results = {}
    
    async def scrape_city(self, city: str) -> List[Dict[str, Any]]:
        """
        爬取单个城市的土地数据
        
        工作原理：
        1. 访问城市土地市场页面
        2. 监听网络请求，拦截真实的 API 调用
        3. 提取 API 响应数据
        """
        config = CITY_CONFIGS.get(city)
        if not config:
            print(f"⚠️  未找到城市配置: {city}")
            return []
        
        print(f"\n📍 开始爬取：{city}")
        print(f"   URL: {config['url']}")
        print(f"   说明: {config['notes']}")
        print("-" * 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN'
            )
            
            page = await context.new_page()
            
            # 存储拦截到的 API 数据
            api_responses = []
            
            # 监听响应事件
            async def handle_response(response):
                url = response.url
                
                # 根据配置的关键字过滤 API 请求
                keywords = config.get('api_keyword', 'api\|list\|query\|data')
                if any(kw in url.lower() for kw in keywords.split('|')):
                    try:
                        body = await response.text()
                        api_responses.append({
                            'url': url,
                            'status': response.status,
                            'headers': dict(response.headers),
                            'body': body
                        })
                        print(f"✅ 拦截到 API 响应: {url}")
                        print(f"   状态: {response.status}")
                        print(f"   数据长度: {len(body)}")
                    except Exception as e:
                        print(f"❌ 读取响应失败: {e}")
            
            page.on('response', handle_response)
            
            try:
                # 访问页面
                print(f"🌐 正在访问...")
                await page.goto(
                    config['url'],
                    wait_until='networkidle',
                    timeout=60000
                )
                
                print(f"✅ 页面加载完成")
                
                # 等待页面完全渲染
                await page.wait_for_timeout(5000)
                
                # 尝试点击查询按钮（如果存在）
                await self._try_click_query_button(page)
                
                # 等待 API 请求完成
                await page.wait_for_timeout(3000)
                
                # 解析拦截到的数据
                city_data = []
                for resp in api_responses:
                    try:
                        data = json.loads(resp['body'])
                        rows = self._extract_rows(data)
                        
                        for row in rows:
                            item = self._normalize_row(row, city)
                            if item:
                                city_data.append(item)
                        
                        print(f"✅ 成功提取 {len(rows)} 条数据")
                        
                    except json.JSONDecodeError:
                        print(f"⚠️  响应不是有效的 JSON")
                
                if not city_data:
                    print(f"⚠️  未能获取数据")
                    print(f"   拦截到 {len(api_responses)} 个 API 响应")
                
                return city_data
                
            except Exception as e:
                print(f"❌ 错误: {e}")
                return []
            
            finally:
                await browser.close()
    
    async def _try_click_query_button(self, page: Page):
        """尝试点击查询按钮"""
        try:
            # 查找可能的查询按钮
            buttons = await page.query_selector_all('button, input[type="button"], a.btn')
            
            for btn in buttons[:10]:
                text = await btn.inner_text()
                if any(keyword in text for keyword in ['查询', '搜索', '提交', '查询数据']):
                    print(f"🖱️  找到按钮: {text}")
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    return
        
        except Exception as e:
            print(f"⚠️  点击按钮失败: {e}")
    
    def _extract_rows(self, data: Dict) -> List[Dict]:
        """从 API 响应中提取数据行"""
        for key in ["data", "rows", "list", "result", "records"]:
            value = data.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                for nested_key in ["data", "rows", "list", "records"]:
                    nested = value.get(nested_key)
                    if isinstance(nested, list):
                        return nested
        return []
    
    def _normalize_row(self, row: Dict, city: str) -> Dict[str, Any]:
        """标准化数据行"""
        return {
            "category": "land",
            "city": city,
            "raw": row,
            "title": row.get("title") or row.get("bt") or row.get("name") or f"{city}土地项目",
            "source": f"{city}土地市场",
            "source_level": "level_2",
            "verified": True
        }
    
    async def scrape_all_cities(self, cities: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """爬取所有城市的土地数据"""
        if not cities:
            cities = list(CITY_CONFIGS.keys())
        
        print("🚀 启动统一土地数据爬虫")
        print("=" * 60)
        print(f"目标城市: {', '.join(cities)}")
        print("=" * 60)
        
        results = {}
        
        for city in cities:
            data = await self.scrape_city(city)
            results[city] = data
            print(f"\n📊 {city}: 获取到 {len(data)} 条数据")
        
        print("\n" + "=" * 60)
        print("✅ 爬取完成!")
        print("=" * 60)
        
        total = sum(len(data) for data in results.values())
        print(f"总计: {total} 条数据")
        
        return results


async def main():
    """主函数"""
    scraper = UnifiedLandScraper(headless=True)
    
    # 测试单个城市
    # data = await scraper.scrape_city("北京")
    
    # 爬取所有城市
    results = await scraper.scrape_all_cities()
    
    # 保存结果
    output_file = "/Users/tianguobao/WorkBuddy/Claw/data/all_city_land_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 数据已保存: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
