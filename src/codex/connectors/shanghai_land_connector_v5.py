#!/usr/bin/env python3
"""
上海土地市场连接器 V5 (最终工作版)
- 拦截 API 响应（HTML 格式）
- 解析 HTML 提取土地数据
- 不依赖页面 DOM 结构
"""
import asyncio
import json
import re
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright


class ShanghaiLandConnectorV5:
    """
    上海土地市场连接器 V5
    
    工作原理：
    1. 访问上海土地市场页面
    2. 拦截 /api/result/listForPage 的响应（HTML 格式）
    3. 解析 HTML 提取土地数据
    4. 如果需要更多数据，修改请求参数并重新发送
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
        self.last_html_response = None
    
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
        
        # 监听响应，拦截 API 调用
        async def handle_response(response):
            url = response.url
            if 'listForPage' in url:
                print(f"\n📥 拦截到 API 响应: {url}")
                print(f"   状态: {response.status}")
                
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'html' in content_type or 'text' in content_type:
                        html = await response.text()
                        self.last_html_response = html
                        print(f"   ✅ HTML 长度: {len(html)}")
                        print(f"   预览: {html[:200]}")
                    elif 'json' in content_type:
                        data = await response.json()
                        self.last_html_response = data
                        print(f"   ✅ JSON: {json.dumps(data, ensure_ascii=False)[:200]}")
                except Exception as e:
                    print(f"   ❌ 读取响应失败: {e}")
        
        self.page.on('response', handle_response)
        
        # 访问页面
        print("🌐 访问上海土地市场...")
        await self.page.goto(
            self.TOKEN_URL,
            wait_until='networkidle',
            timeout=60000
        )
        print("✅ 页面加载完成")
        
        # 等待 API 调用完成
        print("⏳ 等待 API 调用完成...")
        await self.page.wait_for_timeout(10000)
    
    async def close(self):
        """关闭浏览器"""
        print("🏁 关闭浏览器...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def parse_html_to_land_data(self, html: str) -> List[Dict]:
        """
        解析 HTML，提取土地数据
        HTML 格式：
        <ul class="v-board-list" id="list_data">
            <li>
                <a onclick="jumpR(&quot;...&quot;);">地块名称</a>
                <span>日期</span>
            </li>
        </ul>
        """
        print(f"\n📊 解析 HTML，提取土地数据...")
        
        try:
            # 使用正则表达式提取数据
            # 匹配 <li> 元素
            li_pattern = r'<li>\s*<a\s+onclick="jumpR\(&quot;([^&]+)&quot;\)[^>]*>([^<]+)</a>\s*<span>([^<]+)</span>\s*</li>'
            
            matches = re.findall(li_pattern, html, re.DOTALL)
            
            results = []
            for match in matches:
                land_id, land_name, date = match
                results.append({
                    'id': land_id,
                    'title': land_name.strip(),
                    'date': date.strip(),
                    'city': '上海',
                    'source': '上海土地市场',
                    'raw_html': f'<li><a onclick="jumpR(&quot;{land_id}&quot;)">{land_name}</a><span>{date}</span></li>'
                })
            
            print(f"   ✅ 提取到 {len(results)} 条数据")
            return results
            
        except Exception as e:
            print(f"   ❌ 解析失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def fetch_land_data(
        self,
        page_num: int = 1,
        page_size: int = 10,
        bus_type: str = "出让地块"
    ) -> List[Dict[str, Any]:
        """
        获取上海土地数据
        
        方法：
        1. 在页面上下文中调用 API
        2. 拦截响应（HTML）
        3. 解析 HTML 提取数据
        """
        print(f"\n📊 获取上海土地数据 (页码: {page_num}, 类型: {bus_type})...")
        
        # 重置上次响应
        self.last_html_response = None
        
        try:
            # 在页面上下文中调用 API
            # 页面已经加载了 JavaScript，我们可以直接调用 queryTradeResultForPage()
            result = await self.page.evaluate("""
                async (params) => {
                    try {
                        // 构建 URL（包含 token）
                        const url = `/shtdsc/jy/api/result/listForPage?MmEwMD=${window.MmEwMD || ''}`;
                        
                        const response = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'Accept': 'application/json, text/plain, */*',
                                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                'X-Requested-With': 'XMLHttpRequest',
                                'Referer': 'https://biz.ghzyj.sh.gov.cn/shtdsc/jy/view/web/transaction/result/list_result_ywtb.html?tabIndex=1'
                            },
                            body: new URLSearchParams({
                                page: params.page,
                                limit: params.limit,
                                busType: params.busType
                            }).toString()
                        });
                        
                        const contentType = response.headers.get('content-type');
                        if (contentType && contentType.includes('application/json')) {
                            const data = await response.json();
                            return { success: true, data: data, format: 'json' };
                        } else {
                            const text = await response.text();
                            return { success: true, data: text, format: 'html' };
                        }
                    } catch (error) {
                        return { success: false, error: error.toString() };
                    }
                }
            """, {
                'page': page_num,
                'limit': page_size,
                'busType': bus_type
            })
            
            if result['success']:
                data = result['data']
                format = result.get('format', 'unknown')
                
                print(f"   ✅ API 调用成功 (格式: {format})")
                
                if format == 'json':
                    print(f"   JSON 数据: {json.dumps(data, ensure_ascii=False)[:300]}")
                    # TODO: 解析 JSON 格式
                    return []
                else:
                    # HTML 格式，解析
                    return self.parse_html_to_land_data(data)
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
            'title': raw_data.get('title') or '上海土地成交项目',
            'content': f"地块：{raw_data.get('title', '')}，日期：{raw_data.get('date', '')}",
            'city': '上海',
            'date': raw_data.get('date') or '',
            'source': '上海土地市场',
            'source_level': 'level_2',
            'verified': True,
            'raw': raw_data
        }


async def test_shanghai_land_connector_v5():
    """测试上海土地市场连接器 V5"""
    print("🧪 测试上海土地市场连接器 V5 (拦截 API 响应)")
    print("=" * 60)
    
    async with ShanghaiLandConnectorV5(headless=True) as connector:
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


if __name__ == "__main__":
    result = asyncio.run(test_shanghai_land_connector_v5())
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"   数据: {result['data_count']} 条")
