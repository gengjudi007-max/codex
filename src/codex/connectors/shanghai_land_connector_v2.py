#!/usr/bin/env python3
"""
上海土地市场连接器 V2 (使用 Playwright)
解决 SSL 错误，使用真实浏览器获取 token 和调用 API
"""
import asyncio
import json
import re
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright


class ShanghaiLandConnectorV2:
    """
    上海土地市场连接器 V2
    使用 Playwright 处理动态 token 和 SSL 问题
    """
    
    BASE_URL = "https://biz.ghzyj.sh.gov.cn"
    TOKEN_URL = "https://biz.ghzyj.sh.gov.cn/shtdsc/jy/view/web/transaction/result/list_result_ywtb.html"
    API_URL = "https://biz.ghzyj.sh.gov.cn/shtdsc/jy/result/listForPage"  # 假设的 API URL
    
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
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        
        self.page = await self.context.new_page()
        
        # 访问页面，让浏览器加载 JavaScript
        print("🌐 访问上海土地市场...")
        await self.page.goto(
            self.TOKEN_URL,
            wait_until='networkidle',
            timeout=60000
        )
        print("✅ 页面加载完成")
        
        # 等待页面完全渲染
        await self.page.wait_for_timeout(5000)
    
    async def close(self):
        """关闭浏览器"""
        print("🏁 关闭浏览器...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def fetch_dynamic_token(self) -> Optional[str]:
        """
        从页面中获取动态 token (MmEwMD)
        使用 Playwright 在页面上下文中执行 JavaScript
        """
        print("\n🔑 获取动态 token...")
        
        try:
            # 方法1: 从页面的 input 元素中获取
            token = await self.page.evaluate("""
                () => {
                    // 尝试多种可能的位置
                    const sources = [
                        () => document.getElementById('MmEwMD')?.value,
                        () => document.getElementsByName('MmEwMD')[0]?.value,
                        () => window['MmEwMD'],
                        () => eval('MmEwMD'),  // 某些网站将 token 设置为全局变量
                    ];
                    
                    for (const getToken of sources) {
                        try {
                            const token = getToken();
                            if (token && token.length > 5) {
                                return token;
                            }
                        } catch (e) {
                            // 忽略错误，继续尝试下一个来源
                        }
                    }
                    
                    return null;
                }
            """)
            
            if token:
                print(f"   ✅ 获取到 token: {token[:20]}...")
                return token
            else:
                print(f"   ⚠️  未找到 token，尝试拦截网络请求...")
                return None
                
        except Exception as e:
            print(f"   ❌ 获取 token 失败: {e}")
            return None
    
    async def fetch_land_data(
        self,
        token: Optional[str] = None,
        page_num: int = 1,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取上海土地数据
        使用 Playwright 在页面上下文中直接调用 API
        """
        print(f"\n📊 获取上海土地数据 (页码: {page_num})...")
        
        try:
            # 如果还没有 token，尝试获取
            if not token:
                token = await self.fetch_dynamic_token()
            
            # 在页面上下文中调用 API
            result = await self.page.evaluate("""
                async (params) => {
                    try {
                        const response = await fetch('https://biz.ghzyj.sh.gov.cn/shtdsc/jy/result/listForPage', {
                            method: 'POST',
                            headers: {
                                'Accept': 'application/json, text/plain, */*',
                                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                'X-Requested-With': 'XMLHttpRequest',
                                'Referer': 'https://biz.ghzyj.sh.gov.cn/shtdsc/jy/view/web/transaction/result/list_result_ywtb.html?tabIndex=1'
                            },
                            body: new URLSearchParams(params).toString()
                        });
                        const data = await response.json();
                        return { success: true, data: data };
                    } catch (error) {
                        return { success: false, error: error.toString() };
                    }
                }
            """, {
                'page': page_num,
                'limit': page_size,
                'busType': '转让地块',
                'MmEwMD': token or ''
            })
            
            if result['success']:
                data = result['data']
                print(f"   ✅ API 调用成功")
                print(f"   响应 keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # 提取数据行
                rows = []
                for key in ['data', 'rows', 'list', 'result']:
                    if isinstance(data.get(key), list):
                        rows = data[key]
                        break
                
                print(f"   数据行数: {len(rows)}")
                return rows
            else:
                print(f"   ❌ API 调用失败: {result['error']}")
                return []
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def normalize_land_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化土地数据格式
        """
        return {
            'category': 'land',
            'title': raw_data.get('title') or raw_data.get('landName') or '上海土地成交项目',
            'content': raw_data.get('content') or '',
            'city': '上海',
            'date': raw_data.get('date') or raw_data.get('cjsj') or '',
            'source': '上海土地市场',
            'source_level': 'level_2',
            'verified': True,
            'raw': raw_data
        }


async def test_shanghai_land_connector_v2():
    """测试上海土地市场连接器 V2"""
    print("🧪 测试上海土地市场连接器 V2 (Playwright)")
    print("=" * 60)
    
    async with ShanghaiLandConnectorV2(headless=True) as connector:
        # 测试1: 获取动态 token
        print("\n📍 测试1: 获取动态 token...")
        token = await connector.fetch_dynamic_token()
        print(f"   Token: {token or '❌ 获取失败'}")
        
        # 测试2: 获取土地数据
        print("\n📊 测试2: 获取土地数据...")
        data = await connector.fetch_land_data(token=token, page_num=1, page_size=5)
        print(f"   获取到 {len(data)} 条数据")
        
        if data:
            print("\n   前 3 条数据:")
            for i, item in enumerate(data[:3], 1):
                normalized = connector.normalize_land_data(item)
                print(f"   {i}. {normalized['title']}")
                print(f"      日期: {normalized['date']}")
        
        return {
            'token': token,
            'data_count': len(data)
        }


if __name__ == "__main__":
    result = asyncio.run(test_shanghai_land_connector_v2())
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"   Token: {'✅ 成功' if result['token'] else '❌ 失败'}")
    print(f"   数据: {result['data_count']} 条")
