#!/usr/bin/env python3
"""
中国土地市场网连接器（修复版）
- 使用 Playwright 访问（支持 JS 渲染）
- 覆盖全国所有城市
- 通过城市名过滤数据
"""
import asyncio
import re
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright


class ChinaLandMarketConnectorV2:
    """
    中国土地市场网连接器（使用 Playwright）
    
    数据来源：自然资源部土地市场网
    URL: https://landchina.mnr.gov.cn/land/cjgs/
    """
    
    # 成交公示的分类（从实际页面分析得出）
    CATEGORIES = {
        'xycr': '协议出让',
        'hbgd': '划拨供地',
        'zbcr': '招标出让',
        'gpcr': '挂牌出让',
        'pmcr': '拍卖出让'
    }
    
    BASE_URL = "https://landchina.mnr.gov.cn/land/cjgs"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    async def __aenter__(self):
        await self.init_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def init_browser(self):
        """初始化浏览器"""
        print("🚀 初始化浏览器...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        
        self.page = await self.context.new_page()
        print("✅ 浏览器初始化完成")
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def fetch_category(
        self,
        category_key: str,
        city_filter: Optional[str] = None,
        max_items: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取某个分类的土地数据
        
        Args:
            category_key: 分类键名（xycr, hbgd, zbcr, gpcr, pmcr）
            city_filter: 城市名过滤（可选）
            max_items: 最多获取多少条
        
        Returns:
            土地数据列表
        """
        url = f"{self.BASE_URL}/{category_key}/"
        cat_name = self.CATEGORIES.get(category_key, category_key)
        
        print(f"\n📊 获取分类: {cat_name}")
        print(f"   URL: {url}")
        
        try:
            await self.page.goto(url, wait_until='networkidle', timeout=60000)
            await self.page.wait_for_timeout(3000)
            
            # 使用 JavaScript 提取列表数据
            data = await self.page.evaluate("""
                (cityFilter) => {
                    const results = [];
                    
                    // 查找所有列表项
                    const items = document.querySelectorAll('li');
                    
                    for (const item of items) {
                        const text = item.innerText || '';
                        
                        // 检查是否包含日期（YYYY.MM.DD 或 YYYY-MM-DD）
                        if (!/20\\d{2}[.\\-]\\d{1,2}[.\\-]\\d{1,2}/.test(text)) {
                            continue;
                        }
                        
                        // 检查是否包含城市过滤关键词
                        if (cityFilter && !text.includes(cityFilter)) {
                            continue;
                        }
                        
                        // 提取链接
                        const link = item.querySelector('a');
                        if (!link) continue;
                        
                        // 提取日期
                        const dateMatch = text.match(/20\\d{2}[.\\-]\\d{1,2}[.\\-]\\d{1,2}/);
                        const date = dateMatch ? dateMatch[0] : '';
                        
                        results.push({
                            title: link.innerText.trim(),
                            url: link.href,
                            date: date,
                            raw_text: text.substring(0, 200)
                        });
                        
                        if (results.length >= 100) break;  // 限制最多100条
                    }
                    
                    return results;
                }
            """, city_filter)
            
            print(f"   ✅ 提取到 {len(data)} 条数据")
            
            # 转换为标准格式
            results = []
            for item in data[:max_items]:
                results.append({
                    'title': item['title'],
                    'url': item['url'],
                    'date': item['date'],
                    'city': city_filter if city_filter else self._extract_city(item['title']),
                    'source': '中国土地市场网',
                    'category': cat_name
                })
            
            return results
            
        except Exception as e:
            print(f"   ❌ 获取失败: {e}")
            return []
    
    def _extract_city(self, title: str) -> str:
        """从标题中提取城市名"""
        city_patterns = [
            '北京', '上海', '广州', '深圳', '杭州',
            '成都', '西安', '武汉', '天津', '重庆'
        ]
        for city in city_patterns:
            if city in title:
                return city
        return '未知'
    
    async def fetch_city_data(
        self,
        city_name: str,
        max_items: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取指定城市的所有土地数据
        
        Args:
            city_name: 城市名（如"广州"）
            max_items: 最多获取多少条
        
        Returns:
            土地数据列表
        """
        print(f"\n{'='*80}")
        print(f"🔍 获取 {city_name} 的土地成交数据")
        print(f"{'='*80}\n")
        
        all_data = []
        items_per_category = max(5, max_items // len(self.CATEGORIES))
        
        for cat_key in self.CATEGORIES.keys():
            category_data = await self.fetch_category(
                category_key=cat_key,
                city_filter=city_name,
                max_items=items_per_category
            )
            all_data.extend(category_data)
        
        # 去重（根据URL）
        seen_urls = set()
        unique_data = []
        for item in all_data:
            if item['url'] not in seen_urls:
                seen_urls.add(item['url'])
                unique_data.append(item)
        
        print(f"\n✅ 总共获取 {len(unique_data)} 条唯一数据")
        
        return unique_data
    
    def normalize_land_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化土地数据格式"""
        return {
            'category': 'land',
            'title': raw_data.get('title') or '土地成交公告',
            'content': f"公告：{raw_data.get('title', '')}，日期：{raw_data.get('date', '')}",
            'city': raw_data.get('city') or '未知',
            'date': raw_data.get('date') or '',
            'source': '中国土地市场网',
            'source_level': 'level_1',  # 国家级源
            'verified': True,
            'url': raw_data.get('url'),
            'raw': raw_data
        }


async def test_china_land_market_v2():
    """测试中国土地市场网连接器 V2"""
    print("🧪 测试中国土地市场网连接器 V2（使用 Playwright）")
    print("=" * 60)
    
    async with ChinaLandMarketConnectorV2(headless=True) as connector:
        # 测试：获取广州的数据
        print("\n📍 测试：获取广州的数据...")
        data = await connector.fetch_city_data(city_name='广州', max_items=10)
        
        if data:
            print(f"\n   前 3 条数据:")
            for i, item in enumerate(data[:3], 1):
                normalized = connector.normalize_land_data(item)
                print(f"   {i}. {normalized['title']}")
                print(f"      日期: {normalized['date']}")
                print(f"      城市: {normalized['city']}")
        
        # 测试：获取多个城市的数据
        print(f"\n{'='*80}")
        print("📍 测试：批量获取多个城市的数据...")
        
        cities = ['北京', '上海', '广州']
        results = {}
        for city in cities:
            city_data = await connector.fetch_city_data(city_name=city, max_items=5)
            results[city] = len(city_data)
            print(f"   {city}: {len(city_data)} 条")
        
        return {
            'guangzhou_count': len(data),
            'multi_city_results': results
        }


if __name__ == '__main__':
    result = asyncio.run(test_china_land_market_v2())
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"   广州数据: {result['guangzhou_count']} 条")
    print(f"   多城市测试:")
    for city, count in result['multi_city_results'].items():
        print(f"     {city}: {count} 条")
