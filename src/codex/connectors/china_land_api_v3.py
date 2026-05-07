#!/usr/bin/env python3
"""
全国土地市场网数据连接器 V3 (使用 Playwright + 直接调用API)
让浏览器自动处理动态 hash，稳定获取所有城市的土地数据
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class ChinaLandAPIConnectorV3:
    """
    全国土地市场网 API 连接器 V3
    
    使用 Playwright 在页面上下文中直接调用 API，
    让浏览器自动处理动态 hash，无需拦截请求
    """
    
    BASE_URL = "https://www.landchina.com"
    API_BASE = "https://api.landchina.com"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.init_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
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
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        
        self.page = await self.context.new_page()
        
        # 访问页面，让浏览器加载必要的 JavaScript
        print("🌐 访问全国土地市场网...")
        await self.page.goto(
            self.BASE_URL,
            wait_until='networkidle',
            timeout=60000
        )
        print("✅ 页面加载完成")
        
        # 等待一下，确保 JavaScript 完全加载
        await self.page.wait_for_timeout(3000)
    
    async def close(self):
        """关闭浏览器"""
        print("🏁 关闭浏览器...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def get_cities(self) -> List[Dict[str, Any]]:
        """
        获取主要城市列表
        API: /bptFieldEnum/keyCity
        """
        print("\n📍 获取城市列表...")
        
        try:
            # 使用 JavaScript 在页面上下文中调用 API
            result = await self.page.evaluate("""
                async () => {
                    try {
                        const response = await fetch('https://api.landchina.com/bptFieldEnum/keyCity', {
                            method: 'GET',
                            headers: {
                                'Accept': 'application/json, text/plain, */*',
                                'Referer': 'https://www.landchina.com/'
                            }
                        });
                        const data = await response.json();
                        return { success: true, data: data };
                    } catch (error) {
                        return { success: false, error: error.toString() };
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
                    print(f"   ⚠️  API 返回错误: {data.get('msg')}")
                    return []
            else:
                print(f"   ❌ 调用 API 失败: {result['error']}")
                return []
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return []
    
    async def get_land_data(
        self,
        city_code: Optional[str] = None,
        page_num: int = 1,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取土地数据
        API: /epstBulletin/index/bulletin (POST)
        
        Args:
            city_code: 城市代码（例如：'11' 代表北京，'31' 代表上海）
            page_num: 页码
            page_size: 每页数量
        """
        print(f"\n📊 获取土地数据 (城市代码: {city_code}, 页码: {page_num})...")
        
        try:
            # 构建请求参数
            params = {
                'pageNum': page_num,
                'pageSize': page_size
            }
            
            if city_code:
                params['xzqDm'] = city_code
            
            # 使用 JavaScript 在页面上下文中调用 API
            result = await self.page.evaluate("""
                async (params) => {
                    try {
                        const response = await fetch('https://api.landchina.com/epstBulletin/index/bulletin', {
                            method: 'POST',
                            headers: {
                                'Accept': 'application/json, text/plain, */*',
                                'Content-Type': 'application/json',
                                'Referer': 'https://www.landchina.com/'
                            },
                            body: JSON.stringify(params)
                        });
                        const data = await response.json();
                        return { success: true, data: data };
                    } catch (error) {
                        return { success: false, error: error.toString() };
                    }
                }
            """, params)
            
            if result['success']:
                data = result['data']
                if data.get('code') == 200 or data.get('msg') == '操作成功':
                    # 注意：返回格式可能是 { data: { list: [...] } }
                    records = data.get('data', {})
                    if isinstance(records, dict):
                        records = records.get('list', [])
                    elif isinstance(records, list):
                        pass  # 已经是列表
                    else:
                        records = []
                    
                    print(f"   ✅ 获取到 {len(records)} 条数据")
                    return records
                else:
                    print(f"   ⚠️  API 返回错误: {data.get('msg')}")
                    return []
            else:
                print(f"   ❌ 调用 API 失败: {result['error']}")
                return []
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            return []
    
    async def get_land_data_by_city(
        self,
        city_name: str,
        page_num: int = 1,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        根据城市名称获取土地数据
        
        Args:
            city_name: 城市名称（如 '北京', '上海'）
            page_num: 页码
            page_size: 每页数量
            
        Returns:
            土地数据列表
        """
        # 先获取城市列表，找到对应的城市代码
        cities = await self.get_cities()
        
        city_code = None
        for city in cities:
            if city_name in city.get('enumName', ''):
                city_code = city.get('enumValue')
                break
        
        if not city_code:
            print(f"⚠️  未找到城市: {city_name}")
            return []
        
        print(f"✅ 找到城市 {city_name} (代码: {city_code})")
        
        # 获取该城市的土地数据
        data = await self.get_land_data(city_code, page_num, page_size)
        return data
    
    def normalize_land_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化土地数据格式
        """
        return {
            'category': 'land',
            'title': raw_data.get('title', ''),
            'content': raw_data.get('content', ''),
            'city': raw_data.get('xzqName', ''),
            'date': raw_data.get('createTime', ''),
            'source': '全国土地市场网',
            'source_level': 'level_1',
            'verified': True,
            'raw': raw_data
        }


async def test_china_land_api_v3():
    """测试全国土地市场网 API V3"""
    print("🧪 测试全国土地市场网 API V3 (Playwright + 直接调用API)")
    print("=" * 60)
    
    async with ChinaLandAPIConnectorV3(headless=True) as connector:
        # 测试1: 获取城市列表
        print("\n📍 测试1: 获取主要城市列表...")
        cities = await connector.get_cities()
        print(f"   找到 {len(cities)} 个城市")
        
        if cities:
            print("\n   前 10 个城市:")
            for city in cities[:10]:
                print(f"   - {city['enumName']} (代码: {city['enumValue']})")
        
        # 测试2: 获取上海的土地数据
        print("\n📊 测试2: 获取上海土地数据...")
        shanghai_data = await connector.get_land_data_by_city('上海', page_num=1, page_size=5)
        print(f"   获取到 {len(shanghai_data)} 条数据")
        
        if shanghai_data:
            print("\n   前 3 条数据:")
            for i, item in enumerate(shanghai_data[:3], 1):
                print(f"   {i}. {item.get('title', 'N/A')}")
                print(f"      日期: {item.get('createTime', 'N/A')}")
                print(f"      地区: {item.get('xzqName', 'N/A')}")
        
        # 测试3: 获取北京的土地数据
        print("\n📊 测试3: 获取北京土地数据...")
        beijing_data = await connector.get_land_data_by_city('北京', page_num=1, page_size=5)
        print(f"   获取到 {len(beijing_data)} 条数据")
        
        if beijing_data:
            print("\n   前 3 条数据:")
            for i, item in enumerate(beijing_data[:3], 1):
                print(f"   {i}. {item.get('title', 'N/A')}")
                print(f"      日期: {item.get('createTime', 'N/A')}")
        
        return {
            'cities_count': len(cities),
            'shanghai_count': len(shanghai_data),
            'beijing_count': len(beijing_data)
        }


if __name__ == "__main__":
    result = asyncio.run(test_china_land_api_v3())
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"   城市总数: {result['cities_count']}")
    print(f"   上海数据: {result['shanghai_count']} 条")
    print(f"   北京数据: {result['beijing_count']} 条")
