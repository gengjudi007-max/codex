#!/usr/bin/env python3
"""
上海土地市场连接器（最终工作版）
- 拦截 API 响应（HTML 格式）
- 解析 HTML 提取土地数据
- 支持翻页（重新发送 API 请求）
"""
import asyncio
import json
import re
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright


class ShanghaiLandConnector:
    """
    上海土地市场连接器
    
    工作原理：
    1. 访问上海土地市场页面，获取 token
    2. 在页面上下文中调用 API
    3. 拦截 API 响应（HTML 格式）
    4. 解析 HTML 提取土地数据
    """
    
    TOKEN_URL = "https://biz.ghzyj.sh.gov.cn/shtdsc/jy/view/web/transaction/result/list_result_ywtb.html"
    API_PATH = "/shtdsc/jy/api/result/listForPage"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.token = None
        self.last_html = None
    
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
        
        # 访问页面，获取 token
        print("🌐 访问上海土地市场...")
        await self.page.goto(
            self.TOKEN_URL,
            wait_until='networkidle',
            timeout=60000
        )
        print("✅ 页面加载完成")
        
        # 等待一下，让 JavaScript 执行
        await self.page.wait_for_timeout(5000)
        
        # 从页面中提取 token（从全局变量或 URL 中）
        await self._extract_token()
    
    async def _extract_token(self):
        """从页面中提取 MmEwMD token"""
        print("\n🔑 提取动态 token...")
        
        try:
            # 方法1：从网络请求中拦截（最直接）
            # 我们需要重新加载页面并拦截请求
            self.token = None
            
            # 方法2：从页面的 JavaScript 变量中获取
            token = await self.page.evaluate("""
                () => {
                    // 尝试多种可能的位置
                    const sources = [
                        () => window['MmEwMD'],
                        () => eval('MmEwMD'),
                        () => document.querySelector('#MmEwMD')?.value,
                        () => document.querySelector('[name="MmEwMD"]')?.value,
                    ];
                    
                    for (const getToken of sources) {
                        try {
                            const token = getToken();
                            if (token && token.length > 5) {
                                return token;
                            }
                        } catch (e) {
                            // 忽略错误
                        }
                    }
                    
                    return null;
                }
            """)
            
            if token:
                self.token = token
                print(f"   ✅ 获取到 token: {token[:30]}...")
            else:
                print(f"   ⚠️  未找到 token，将尝试拦截网络请求...")
                
        except Exception as e:
            print(f"   ❌ 获取 token 失败: {e}")
    
    async def close(self):
        """关闭浏览器"""
        print("\n🏁 关闭浏览器...")
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
        
        方法：
        1. 在页面上下文中调用 API
        2. 拦截响应（HTML）
        3. 解析 HTML 提取数据
        """
        print(f"\n📊 获取上海土地数据 (页码: {page_num}, 类型: {bus_type})...")
        
        # 确保有 token
        if not self.token:
            await self._extract_token()
        
        # 在页面上下文中调用 API 并拦截响应
        html = await self._call_api_and_get_html(page_num, page_size, bus_type)
        
        if not html:
            print(f"   ❌ 未获取到 HTML 响应")
            return []
        
        # 解析 HTML 提取数据
        data = self._parse_html(html)
        print(f"   ✅ 提取到 {len(data)} 条数据")
        
        return data
    
    async def _call_api_and_get_html(
        self,
        page_num: int,
        page_size: int,
        bus_type: str
    ) -> Optional[str]:
        """调用 API 并获取 HTML 响应"""
        
        html_response = None
        
        # 监听响应，拦截 API 调用
        async def handle_response(response):
            nonlocal html_response
            url = response.url
            if 'listForPage' in url:
                print(f"   📥 拦截到 API 响应: {response.status}")
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'html' in content_type or 'text' in content_type:
                        html_response = await response.text()
                        print(f"      HTML 长度: {len(html_response)}")
                except Exception as e:
                    print(f"      ❌ 读取响应失败: {e}")
        
        self.page.on('response', handle_response)
        
        try:
            # 在页面上下文中调用 API
            await self.page.evaluate("""
                async (params) => {
                    const url = `/shtdsc/jy/api/result/listForPage?MmEwMD=${params.token || ''}`;
                    
                    try {
                        const response = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'Accept': 'application/json, text/plain, */*',
                                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                'X-Requested-With': 'XMLHttpRequest',
                            },
                            body: new URLSearchParams({
                                page: params.page,
                                limit: params.limit,
                                busType: params.busType
                            }).toString()
                        });
                        
                        // 消耗响应（让 response 事件触发）
                        await response.text();
                    } catch (error) {
                        console.error('API call failed:', error);
                    }
                }
            """, {
                'token': self.token or '',
                'page': page_num,
                'limit': page_size,
                'busType': bus_type
            })
            
            # 等待响应被拦截
            await self.page.wait_for_timeout(3000)
            
            return html_response
            
        except Exception as e:
            print(f"   ❌ API 调用失败: {e}")
            return None
        finally:
            # 移除监听器
            self.page.remove_listener('response', handle_response)
    
    def _parse_html(self, html: str) -> List[Dict[str, Any]]:
        """解析 HTML，提取土地数据"""
        print(f"   📊 解析 HTML ({len(html)} 字符)...")
        
        results = []
        
        try:
            # 使用正则表达式提取 <li> 元素
            # 格式：<li><a onclick="jumpR(&quot;ID&quot;);">地块名称</a><span>日期</span></li>
            li_pattern = r'<li>\s*<a\s+onclick="jumpR\(&quot;([^&]+)&quot;\)[^>]*>([^<]+)</a>\s*<span>([^<]+)</span>\s*</li>'
            
            matches = re.findall(li_pattern, html, re.DOTALL)
            
            for match in matches:
                land_id, title, date = match
                results.append({
                    'id': land_id,
                    'title': title.strip(),
                    'date': date.strip(),
                    'city': '上海',
                    'source': '上海土地市场'
                })
            
            return results
            
        except Exception as e:
            print(f"   ❌ 解析失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def normalize_land_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化土地数据格式"""
        return {
            'category': 'land',
            'title': raw_data.get('title') or '上海土地成交项目',
            'content': f"地块：{raw_data.get('title', '')}，日期：{raw_data.get('date', '')}",
            'city': '上海',
            'date': raw_data.get('date') or '',
            'source': '上海土地市场',
            'source_level': 'level_2',
            'verified': True,
            'raw': raw_data
        }


async def test_shanghai_land_connector():
    """测试上海土地市场连接器"""
    print("🧪 测试上海土地市场连接器（最终版）")
    print("=" * 60)
    
    async with ShanghaiLandConnector(headless=True) as connector:
        # 测试：获取第 1 页的数据
        print("\n📍 测试：获取第 1 页数据（出让地块）...")
        data = await connector.fetch_land_data(page_num=1, page_size=5, bus_type="出让地块")
        print(f"   获取到 {len(data)} 条数据")
        
        if data:
            print("\n   前 3 条数据:")
            for i, item in enumerate(data[:3], 1):
                normalized = connector.normalize_land_data(item)
                print(f"   {i}. {normalized['title']}")
                print(f"      日期: {normalized['date']}")
        
        return {
            'data_count': len(data)
        }


if __name__ == '__main__':
    result = asyncio.run(test_shanghai_land_connector())
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"   数据: {result['data_count']} 条")
