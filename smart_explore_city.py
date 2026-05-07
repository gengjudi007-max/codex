#!/usr/bin/env python3
"""
智能城市土地市场探索器 v2
- 自动判断网站类型（静态HTML / 动态API）
- 静态HTML：直接解析分页和列表
- 动态API：拦截XHR请求
"""
import asyncio
import json
import re
from playwright.async_api import async_playwright


async def smart_explore_city(city_name: str, start_url: str, headless: bool = False):
    """
    智能探索城市土地市场
    
    策略：
    1. 访问页面，等待加载
    2. 检查是否有翻页（判断是静态还是动态）
    3. 如果是静态HTML：直接读取HTML并解析
    4. 如果是动态加载：监听XHR请求
    """
    print(f"\n{'='*80}")
    print(f"🧠 智能探索 {city_name} 土地市场")
    print(f"   URL: {start_url}")
    print(f"{'='*80}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        
        page = await context.new_page()
        
        # 存储捕获的 API 请求
        api_calls = []
        
        async def capture_api_response(response):
            """捕获可能的 API 响应"""
            url = response.url
            # 过滤 XHR/fetch 请求
            if any(kw in url.lower() for kw in ['api', 'ajax', 'query', 'list', 'search', 'result']):
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type or 'javascript' in content_type:
                        body = await response.json()
                        api_calls.append({
                            'url': url,
                            'status': response.status,
                            'type': 'json',
                            'data': body
                        })
                        print(f"📥 捕获 JSON API: {url}")
                except:
                    pass
        
        page.on('response', capture_api_response)
        
        # 访问起始页面
        print(f"🌐 访问页面...")
        try:
            await page.goto(start_url, wait_until='networkidle', timeout=60000)
            print(f"✅ 页面加载完成")
        except Exception as e:
            print(f"❌ 页面加载失败: {e}")
            await browser.close()
            return None
        
        await page.wait_for_timeout(3000)
        
        # 获取页面 HTML
        html = await page.content()
        print(f"📄 HTML 长度: {len(html)} 字符")
        
        # 分析页面结构
        print(f"\n🔍 分析页面结构...")
        
        # 检查是否有翻页组件
        pagination_keywords = ['下一页', '下页', 'next', '更多', '加载更多', 'pagination']
        has_pagination = any(kw in html.lower() for kw in pagination_keywords)
        print(f"   翻页组件: {'是' if has_pagination else '否'}")
        
        # 检查是否有列表内容
        list_keywords = ['<li', '<tr', '地块', '出让', '成交']
        has_list = any(kw in html for kw in list_keywords)
        print(f"   列表内容: {'是' if has_list else '否'}")
        
        # 提取所有链接
        links = await page.locator('a').all()
        print(f"   链接数量: {len(links)}")
        
        # 查找包含"成交"、"出让"等关键词的链接
        land_links = []
        for link in links[:50]:  # 限制前50个
            try:
                text = await link.inner_text()
                href = await link.get_attribute('href')
                if any(kw in text for kw in ['成交', '出让', '地块']) and href:
                    full_url = href if href.startswith('http') else (
                        start_url.rstrip('/') + '/' + href.lstrip('/') if not href.startswith('/') else 
                        'https://' + start_url.split('/')[2] + href
                    )
                    land_links.append({'text': text.strip(), 'url': full_url})
            except:
                pass
        
        print(f"   土地相关链接: {len(land_links)} 个")
        for i, link in enumerate(land_links[:5], 1):
            print(f"      {i}. {link['text']} -> {link['url'][:80]}")
        
        # 判断网站类型
        is_dynamic = len(api_calls) > 0
        is_static = has_list and not is_dynamic
        
        print(f"\n📊 网站类型判断:")
        print(f"   动态API: {'是' if is_dynamic else '否'}")
        print(f"   静态HTML: {'是' if is_static else '否'}")
        
        # 如果是静态HTML，尝试解析列表
        if is_static:
            print(f"\n📋 解析静态HTML列表...")
            
            # 使用正则表达式提取列表项
            # 模式1: <li> 包含链接
            li_pattern = r'<li[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
            li_matches = re.findall(li_pattern, html)
            
            if li_matches:
                print(f"   找到 {len(li_matches)} 个 <li> 列表项")
                for i, (href, text) in enumerate(li_matches[:5], 1):
                    print(f"      {i}. {text.strip()[:50]} -> {href[:60]}")
            
            # 模式2: 表格行
            tr_pattern = r'<tr[^>]*>\s*<td[^>]*>([^<]+)</td>'
            tr_matches = re.findall(tr_pattern, html)
            
            if tr_matches:
                print(f"   找到 {len(tr_matches)} 个 <tr> 表格行")
        
        # 截图
        screenshot_path = f'/Users/tianguobao/WorkBuddy/Claw/{city_name}_page.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n📸 截图已保存: {screenshot_path}")
        
        # 保存 HTML 供分析
        html_path = f'/Users/tianguobao/WorkBuddy/Claw/{city_name}_page.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"💾 HTML 已保存: {html_path}")
        
        # 汇总结果
        result = {
            'city': city_name,
            'url': start_url,
            'type': 'dynamic_api' if is_dynamic else ('static_html' if is_static else 'unknown'),
            'has_pagination': has_pagination,
            'has_list': has_list,
            'api_calls': api_calls,
            'land_links': land_links[:10],
            'html_length': len(html)
        }
        
        result_path = f'/Users/tianguobao/WorkBuddy/Claw/{city_name}_exploration.json'
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        print(f"💾 探索结果已保存: {result_path}")
        
        await browser.close()
        
        return result


async def main():
    """测试"""
    # 测试广州
    await smart_explore_city(
        city_name="广州",
        start_url="https://ghzyj.gz.gov.cn/ywpd/tdgl/tdjysc/cjgs/",
        headless=False
    )


if __name__ == '__main__':
    asyncio.run(main())
