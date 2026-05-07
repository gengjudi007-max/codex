#!/usr/bin/env python3
"""
上海土地市场连接器 V3 (修复版)
- 使用正确的 API URL
- Token 作为 URL 查询参数传递
- POST body 使用 URL 编码
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright


class ShanghaiLandConnectorV3:
    """
    上海土地市场连接器 V3
    
    正确的 API 调用方式:
    POST https://biz.ghzyj.sh.gov.cn/shtdsc/jy/api/result/listForPage?MmEwMD={token}
    Body: page=1&limit=10&busType=出让地块
    """
    
    BASE_URL = "https://biz.ghzyj.sh.gov.cn"
    TOKEN_URL = "https://biz.ghzyj.sh.gov.cn/shtdsc/jy/view/web/transaction/result/list_result_ywtb.html"
    API_PATH = "/shtdsc/jy/api/result/listForPage"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.token = None
    
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
        
        # 访问页面，让浏览器加载 JavaScript 并获取 token
        print("🌐 访问上海土地市场...")
        await self.page.goto(
            self.TOKEN_URL,
            wait_until='networkidle',
            timeout=60000
        )
        print("✅ 页面加载完成")
        
        # 等待页面完全渲染
        await self.page.wait_for_timeout(5000)
        
        # 从页面中提取 token
        await self.extract_token()
    
    async def extract_token(self):
        """从页面中提取 MmEwMD token"""
        print("\n🔑 提取动态 token...")
        
        try:
            # 方法1: 从 URL 参数中提取（拦截到的请求中，token 在 URL 中）
            current_url = self.page.url
            print(f"   当前 URL: {current_url}")
            
            # 如果 URL 中有 MmEwMD 参数，直接提取
            if 'MmEwMD' in current_url:
                import re
                match = re.search(r'MmEwMD=([^&]+)', current_url)
                if match:
                    self.token = match.group(1)
                    print(f"   ✅ 从 URL 中提取到 token: {self.token[:30]}...")
                    return
            
            # 方法2: 从页面的 JavaScript 变量中提取
            token = await self.page.evaluate("""
                () => {
                    // 尝试多种可能的位置
                    const sources = [
                        () => document.getElementById('MmEwMD')?.value,
                        () => document.getElementsByName('MmEwMD')[0]?.value,
                        () => window['MmEwMD'],
                        () => eval('MmEwMD'),
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
                self.token = token
                print(f"   ✅ 从页面中提取到 token: {token[:30]}...")
            else:
                print(f"   ⚠️  未找到 token，将尝试拦截网络请求...")
                
        except Exception as e:
            print(f"   ❌ 提取 token 失败: {e}")
    
    async def close(self):
        """关闭浏览器"""
        print("🏁 关闭浏览器...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def fetch_land_data(
        self,
        page_num: int = 1,
        page_size: int = 10,
        bus_type: str = "出让地块"
    ) -> List[Dict[str, Any]]:
        """
        获取上海土地数据
        
        正确的 API 调用方式:
        POST https://biz.ghzyj.sh.gov.cn/shtdsc/jy/api/result/listForPage?MmEwMD={token}
        Body: page=1&limit=10&busType=出让地块
        """
        print(f"\n📊 获取上海土地数据 (页码: {page_num}, 类型: {bus_type})...")
        
        if not self.token:
            print(f"   ⚠️  没有 token，尝试重新获取...")
            await self.extract_token()
            if not self.token:
                print(f"   ❌ 无法获取 token，API 调用可能失败")
        
        try:
            # 构建 API URL（token 作为查询参数）
            api_url = f"{self.BASE_URL}{self.API_PATH}?MmEwMD={self.token or ''}"
            
            # 构建 POST body（URL 编码格式）
            post_body = f"page={page_num}&limit={page_size}&busType={bus_type}"
            
            print(f"   API URL: {api_url[:80]}...")
            print(f"   POST Body: {post_body}")
            
            # 在页面上下文中调用 API
            result = await self.page.evaluate("""
                async (params) => {
                    try {
                        const response = await fetch(params.apiUrl, {
                            method: 'POST',
                            headers: {
                                'Accept': 'application/json, text/plain, */*',
                                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                'X-Requested-With': 'XMLHttpRequest',
                                'Referer': params.referer
                            },
                            body: params.body
                        });
                        
                        const contentType = response.headers.get('content-type');
                        if (contentType && contentType.includes('application/json')) {
                            const data = await response.json();
                            return { success: true, data: data, status: response.status };
                        } else {
                            const text = await response.text();
                            return { success: true, data: text, status: response.status };
                        }
                    } catch (error) {
                        return { success: false, error: error.toString() };
                    }
                }
            """, {
                'apiUrl': api_url,
                'body': post_body,
                'referer': self.TOKEN_URL
            })
            
            if result['success']:
                data = result['data']
                status = result['status']
                print(f"   ✅ API 调用成功 (状态码: {status})")
                
                # 处理响应数据
                if isinstance(data, dict):
                    print(f"   响应 keys: {list(data.keys())}")
                    
                    # 提取数据行
                    rows = []
                    for key in ['data', 'rows', 'list', 'result', 'records']:
                        if isinstance(data.get(key), list):
                            rows = data[key]
                            break
                    
                    print(f"   数据行数: {len(rows)}")
                    return rows
                else:
                    # 字符串响应，可能是 HTML 或文本
                    print(f"   响应 (文本): {data[:200]}")
                    return []
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


async def test_shanghai_land_connector_v3():
    """测试上海土地市场连接器 V3"""
    print("🧪 测试上海土地市场连接器 V3 (修复版)")
    print("=" * 60)
    
    async with ShanghaiLandConnectorV3(headless=True) as connector:
        # 测试1: 获取动态 token
        print("\n📍 测试1: 动态 token")
        print(f"   Token: {connector.token[:30] if connector.token else '❌ 获取失败'}...")
        
        # 测试2: 获取土地数据（出让地块）
        print("\n📊 测试2: 获取土地数据（出让地块）...")
        data1 = await connector.fetch_land_data(page_num=1, page_size=5, bus_type="出让地块")
        print(f"   获取到 {len(data1)} 条数据")
        
        if data1:
            print("\n   前 3 条数据:")
            for i, item in enumerate(data1[:3], 1):
                normalized = connector.normalize_land_data(item)
                print(f"   {i}. {normalized['title']}")
                print(f"      日期: {normalized['date']}")
        
        # 测试3: 获取土地数据（转让地块）
        print("\n📊 测试3: 获取土地数据（转让地块）...")
        data2 = await connector.fetch_land_data(page_num=1, page_size=5, bus_type="转让地块")
        print(f"   获取到 {len(data2)} 条数据")
        
        return {
            'token': connector.token,
            'churang_count': len(data1),
            'zhuanrang_count': len(data2)
        }


if __name__ == "__main__":
    result = asyncio.run(test_shanghai_land_connector_v3())
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"   Token: {'✅ 成功' if result['token'] else '❌ 失败'}")
    print(f"   出让地块: {result['churang_count']} 条")
    print(f"   转让地块: {result['zhuanrang_count']} 条")
