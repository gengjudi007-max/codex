#!/usr/bin/env python3
"""
使用全国土地市场网 (landchina.com) 获取所有城市的土地数据
从浏览器内部调用 API（绕过反爬虫限制）
"""
import asyncio
import json
from typing import Any, Dict, List
from playwright.async_api import async_playwright, Page


class LandChinaAPI:
    """全国土地市场网 API 客户端（使用 Playwright 绕过限制）"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.init()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def init(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        self.page = await self.context.new_page()
        
        # 访问全国土地市场网，获取必要的 cookies
        print("🌐 正在访问全国土地市场网...")
        await self.page.goto(
            "https://www.landchina.com/",
            wait_until='networkidle',
            timeout=60000
        )
        print("✅ 页面加载完成，已获取 cookies")
        
        await self.page.wait_for_timeout(3000)
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
    
    async def get_cities(self) -> List[Dict[str, Any]]:
        """
        获取主要城市列表
        API: /bptFieldEnum/keyCity
        """
        print("\n📍 获取主要城市列表...")
        
        # 从浏览器上下文中调用 API
        result = await self.page.evaluate("""
            async () => {
                try {
                    const response = await fetch('https://api.landchina.com/bptFieldEnum/keyCity', {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json',
                            'Referer': 'https://www.landchina.com/'
                        }
                    });
                    const data = await response.json();
                    return { success: true, data: data };
                } catch (error) {
                    return { success: false, error: error.message };
                }
            }
        """)
        
        if result['success']:
            data = result['data']
            if data.get('code') == 200 or data.get('msg') == '操作成功':
                cities = data.get('data', [])
                print(f"   ✅ 找到 {len(cities)} 个城市")
                return cities
            else:
                print(f"   ❌ 获取失败: {data.get('msg')}")
                return []
        else:
            print(f"   ❌ 请求失败: {result.get('error')}")
            return []
    
    async def get_land_data(
        self,
        city_code: str = None,
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        获取土地数据
        API: /epstBulletin/index/bulletin
        
        Args:
            city_code: 城市代码（例如：'11' 代表北京，'31' 代表上海）
            page: 页码
            limit: 每页数量
        """
        print(f"\n📊 获取土地数据（城市代码: {city_code or '全国'}, 页码: {page}）...")
        
        # 构建请求参数
        params = {
            'page': page,
            'limit': limit
        }
        
        if city_code:
            params['xzqDm'] = city_code
        
        # 构建 URL
        url = 'https://api.landchina.com/epstBulletin/index/bulletin?' + '&'.join([f'{k}={v}' for k, v in params.items()])
        
        # 从浏览器上下文中调用 API
        result = await self.page.evaluate("""
            async (url) => {
                try {
                    const response = await fetch(url, {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Referer': 'https://www.landchina.com/',
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    });
                    const text = await response.text();
                    return { success: true, text: text, status: response.status };
                } catch (error) {
                    return { success: false, error: error.message };
                }
            }
        """, url)
        
        if result['success']:
            try:
                data = json.loads(result['text'])
                print(f"   ✅ API 响应状态: {result['status']}")
                return data
            except json.JSONDecodeError:
                print(f"   ⚠️  API 响应不是有效的 JSON")
                print(f"   预览: {result['text'][:200]}")
                return {}
        else:
            print(f"   ❌ 请求失败: {result.get('error')}")
            return {}
    
    async def get_land_data_by_city(
        self,
        city_name: str,
        page: int = 1,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        根据城市名称获取土地数据
        """
        # 先获取城市列表
        cities = await self.get_cities()
        
        # 查找城市代码
        city_code = None
        for city in cities:
            if city_name in city.get('enumName', ''):
                city_code = city.get('enumValue')
                break
        
        if not city_code:
            print(f"   ⚠️  未找到城市: {city_name}")
            return []
        
        print(f"   ✅ 找到城市 {city_name} (代码: {city_code})")
        
        # 获取该城市的土地数据
        data = await self.get_land_data(city_code, page, limit)
        
        if data.get('code') == 200:
            return data.get('data', {}).get('list', [])
        else:
            print(f"   ⚠️  获取数据失败: {data.get('msg')}")
            return []


async def test_landchina_api():
    """测试全国土地市场网 API"""
    print("🧪 测试全国土地市场网 API（使用 Playwright 绕过限制）")
    print("=" * 60)
    
    async with LandChinaAPI(headless=True) as api:
        # 测试1: 获取城市列表
        cities = await api.get_cities()
        
        if cities:
            print(f"\n   前 10 个城市:")
            for city in cities[:10]:
                print(f"   - {city['enumName']} (代码: {city['enumValue']})")
        
        # 测试2: 获取上海的土地数据
        print("\n" + "="*60)
        print("📊 测试2: 获取上海土地数据...")
        shanghai_data = await api.get_land_data_by_city('上海', page=1, limit=5)
        print(f"   获取到 {len(shanghai_data)} 条数据")
        
        if shanghai_data:
            print("\n   前 3 条数据:")
            for i, item in enumerate(shanghai_data[:3], 1):
                print(f"\n   {i}. {item.get('title', 'N/A')}")
                print(f"      日期: {item.get('createTime', 'N/A')}")
                print(f"      地区: {item.get('xzqName', 'N/A')}")
        
        # 测试3: 获取北京的土地数据
        print("\n" + "="*60)
        print("📊 测试3: 获取北京土地数据...")
        beijing_data = await api.get_land_data_by_city('北京', page=1, limit=5)
        print(f"   获取到 {len(beijing_data)} 条数据")
        
        return {
            'cities_count': len(cities),
            'shanghai_count': len(shanghai_data),
            'beijing_count': len(beijing_data)
        }


if __name__ == "__main__":
    result = asyncio.run(test_landchina_api())
    
    print("\n" + "="*60)
    print("✅ 测试完成!")
    print("="*60)
    print(f"   城市总数: {result['cities_count']}")
    print(f"   上海数据: {result['shanghai_count']} 条")
    print(f"   北京数据: {result['beijing_count']} 条")
