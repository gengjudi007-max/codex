#!/usr/bin/env python3
"""
通用土地市场连接器（使用 Playwright）
- 使用真实浏览器加载页面（绕过 SSL/JS 问题）
- 使用 JavaScript 提取列表数据（更可靠）
- 支持分页
- 可通过配置适配不同城市
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from playwright.async_api import async_playwright, Page


class UniversalLandConnector:
    """
    通用土地市场连接器
    
    使用 Playwright 加载页面并提取数据
    适配不同城市的网站结构
    """
    
    def __init__(
        self,
        city_name: str,
        base_url: str,
        list_item_selector: str,
        title_selector: str,
        date_selector: str,
        link_selector: str,
        pagination_selector: Optional[str] = None,
        headless: bool = True
    ):
        """
        初始化连接器
        
        Args:
            city_name: 城市名称
            base_url: 列表页面 URL
            list_item_selector: 列表项 CSS 选择器
            title_selector: 标题 CSS 选择器（在列表项内）
            date_selector: 日期 CSS 选择器（在列表项内）
            link_selector: 链接 CSS 选择器（在列表项内）
            pagination_selector: 下一页按钮选择器（可选）
            headless: 是否无头模式
        """
        self.city_name = city_name
        self.base_url = base_url
        self.list_item_selector = list_item_selector
        self.title_selector = title_selector
        self.date_selector = date_selector
        self.link_selector = link_selector
        self.pagination_selector = pagination_selector
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
        print(f"🚀 初始化浏览器（{self.city_name}）...")
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
        print(f"✅ 浏览器初始化完成")
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def _extract_list_data(self, page: Page) -> List[Dict[str, Any]]:
        """使用 JavaScript 提取列表数据"""
        data = await page.evaluate(f"""
            () => {{
                const items = document.querySelectorAll('{self.list_item_selector}');
                const results = [];
                
                for (const item of items) {{
                    const titleElem = item.querySelector('{self.title_selector}');
                    const dateElem = item.querySelector('{self.date_selector}');
                    const linkElem = item.querySelector('{self.link_selector}');
                    
                    if (titleElem && linkElem) {{
                        results.push({{
                            title: titleElem.innerText.trim(),
                            date: dateElem ? dateElem.innerText.trim() : '',
                            url: linkElem.href || ''
                        }});
                    }}
                }}
                
                return results;
            }}
        """)
        
        return data
    
    async def fetch_land_data(
        self,
        page_num: int = 1,
        max_pages: int = 1
    ) -> List[Dict[str, Any]]:
        """
        获取土地数据
        
        Args:
            page_num: 起始页码
            max_pages: 最大页数
        
        Returns:
            土地数据列表
        """
        all_data = []
        
        for page in range(page_num, page_num + max_pages):
            url = self.base_url
            if page > 1:
                # 尝试常见的分页模式
                if '?' in url:
                    url = f"{{url}}&page={{page}}"
                else:
                    url = f"{{url}}?page={{page}}"
            
            print(f"📊 获取第 {{page}} 页: {{url}}")
            
            try:
                await self.page.goto(url, wait_until='networkidle', timeout=60000)
                await self.page.wait_for_timeout(3000)
                
                # 提取数据
                page_data = await self._extract_list_data(self.page)
                
                # 添加到结果（过滤非土地相关条目）
                for item in page_data:
                    if any(keyword in item['title'] for keyword in ['地块', '出让', '成交', '挂牌', '公告']):
                        item['city'] = self.city_name
                        item['source'] = f"{{self.city_name}}土地市场"
                        all_data.append(item)
                
                print(f"   ✅ 提取到 {{len(page_data)}} 条数据，过滤后 {{len([i for i in page_data if any(k in i['title'] for k in ['地块', '出让'])])}} 条有效")
                
                if not page_data:
                    print(f"   ⚠️  本页无数据，停止翻页")
                    break
                
            except Exception as e:
                print(f"   ❌ 获取失败: {{e}}")
                break
            
            # 如果只获取一页，跳出循环
            if max_pages == 1:
                break
        
        return all_data
    
    def normalize_land_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化土地数据格式"""
        return {
            'category': 'land',
            'title': raw_data.get('title') or f'{{self.city_name}}土地交易公告',
            'content': f"公告：{{raw_data.get('title', '')}}}，日期：{{raw_data.get('date', '')}}}",
            'city': self.city_name,
            'date': raw_data.get('date') or '',
            'source': raw_data.get('source') or f'{{self.city_name}}土地市场',
            'source_level': 'level_2',
            'verified': True,
            'url': raw_data.get('url'),
            'raw': raw_data
        }


async def test_universal_connector():
    """测试通用连接器（以广州为例）"""
    print("🧪 测试通用土地市场连接器")
    print("=" * 60)
    
    # 广州配置
    connector = UniversalLandConnector(
        city_name="广州",
        base_url="https://ghzyj.gz.gov.cn/ywpd/tdgl/tdjysc/cjgs/index.html",
        list_item_selector="li",  # 需要根据实际页面调整
        title_selector="a",
        date_selector="span",
        link_selector="a",
        headless=True
    )
    
    async with connector:
        data = await connector.fetch_land_data(page_num=1, max_pages=1)
        print(f"\n获取到 {{len(data)}} 条数据")
        
        if data:
            print("\n前 3 条:")
            for i, item in enumerate(data[:3], 1):
                print(f"  {{i}}. {{item['title']}}")
                print(f"     日期: {{item['date']}}")
    
    return {'data_count': len(data)}


if __name__ == '__main__':
    result = asyncio.run(test_universal_connector())
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"   数据: {{result['data_count']}} 条")
