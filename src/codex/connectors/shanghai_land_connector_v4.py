#!/usr/bin/env python3
"""
上海土地市场连接器 V4 (最终版)
- 使用 Playwright 访问页面
- 等待页面自动加载数据（不手动调用 API）
- 从页面 DOM 中直接提取土地数据
"""
import asyncio
import json
import re
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright


class ShanghaiLandConnectorV4:
    """
    上海土地市场连接器 V4
    
    工作原理：
    1. 访问上海土地市场页面
    2. 等待页面自动加载数据（JavaScript 会调用 API 并更新 DOM）
    3. 从页面的 DOM 中提取土地数据
    4. 如果需要更多数据，点击"下一页"按钮
    """
    
    TOKEN_URL = "https://biz.ghzyj.sh.gov.cn/shtdsc/jy/view/web/transaction/result/list_result_ywtb.html"
    
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
        
        # 访问页面
        print("🌐 访问上海土地市场...")
        await self.page.goto(
            self.TOKEN_URL,
            wait_until='networkidle',
            timeout=60000
        )
        print("✅ 页面加载完成")
        
        # 等待数据加载
        print("⏳ 等待数据加载...")
        await self.page.wait_for_timeout(5000)
    
    async def close(self):
        """关闭浏览器"""
        print("🏁 关闭浏览器...")
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def extract_land_data_from_page(self) -> List[Dict[str, Any]]:
        """
        从页面 DOM 中提取土地数据
        页面结构：<ul id="list_data"> 包含多个 <li> 元素
        """
        print("\n📊 从页面中提取土地数据...")
        
        try:
            # 等待数据加载完成
            await self.page.wait_for_selector('#list_data', timeout=10000)
            
            # 从页面中提取数据
            data = await self.page.evaluate("""
                () => {
                    const listData = document.getElementById('list_data');
                    if (!listData) {
                        return [];
                    }
                    
                    const items = [];
                    const lis = listData.querySelectorAll('li');
                    
                    lis.forEach((li, index) => {
                        try {
                            const link = li.querySelector('a');
                            const span = li.querySelector('span');
                            
                            if (link) {
                                const title = link.innerText || link.textContent;
                                const onclick = link.getAttribute('onclick') || '';
                                
                                // 提取 ID (从 onclick 中)
                                const idMatch = onclick.match(/jumpR\(&quot;([^&]+)&quot;\)/);
                                const id = idMatch ? idMatch[1] : null;
                                
                                const date = span ? (span.innerText || span.textContent) : '';
                                
                                items.push({
                                    id: id,
                                    title: title.trim(),
                                    date: date.trim(),
                                    raw_html: li.outerHTML
                                });
                            }
                        } catch (e) {
                            // 忽略单个元素的错误
                        }
                    });
                    
                    return items;
                }
            """)
            
            print(f"   ✅ 提取到 {len(data)} 条数据")
            return data
            
        except Exception as e:
            print(f"   ❌ 提取失败: {e}")
            return []
    
    async def go_to_next_page(self) -> bool:
        """
        点击"下一页"按钮
        返回：是否成功翻页
        """
        print("\n📖 翻到下一页...")
        
        try:
            # 查找"下一页"按钮
            next_button = await self.page.query_selector('a:has-text("下一页"), a:has-text(">"), .next-page')
            
            if next_button:
                await next_button.click()
                await self.page.wait_for_timeout(3000)
                print(f"   ✅ 翻页成功")
                return True
            else:
                print(f"   ⚠️  未找到下一页按钮")
                return False
                
        except Exception as e:
            print(f"   ❌ 翻页失败: {e}")
            return False
    
    async def fetch_land_data(
        self,
        max_pages: int = 1
    ) -> List[Dict[str, Any]]:
        """
        获取上海土地数据（多页）
        """
        print(f"\n📊 获取上海土地数据（最多 {max_pages} 页）...")
        
        all_data = []
        
        for page_num in range(1, max_pages + 1):
            print(f"\n   📖 第 {page_num} 页:")
            
            # 提取当前页的数据
            page_data = await self.extract_land_data_from_page()
            all_data.extend(page_data)
            
            # 如果不是最后一页，点击"下一页"
            if page_num < max_pages:
                success = await self.go_to_next_page()
                if not success:
                    print(f"   ⚠️  无法翻页，停止获取")
                    break
        
        print(f"\n✅ 总共获取 {len(all_data)} 条数据")
        return all_data
    
    def normalize_land_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化土地数据格式
        """
        return {
            'category': 'land',
            'title': raw_data.get('title') or '上海土地成交项目',
            'content': raw_data.get('title') or '',
            'city': '上海',
            'date': raw_data.get('date') or '',
            'source': '上海土地市场',
            'source_level': 'level_2',
            'verified': True,
            'raw': raw_data
        }


async def test_shanghai_land_connector_v4():
    """测试上海土地市场连接器 V4"""
    print("🧪 测试上海土地市场连接器 V4 (从页面提取数据)")
    print("=" * 60)
    
    async with ShanghaiLandConnectorV4(headless=True) as connector:
        # 测试：获取第 1 页的数据
        print("\n📍 测试：获取第 1 页数据...")
        data = await connector.fetch_land_data(max_pages=1)
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
    result = asyncio.run(test_shanghai_land_connector_v4())
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"   数据: {result['data_count']} 条")
