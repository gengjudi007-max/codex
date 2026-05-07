#!/usr/bin/env python3
"""
查看全国土地市场网的页面结构
"""
import asyncio
from playwright.async_api import async_playwright


async def inspect_page():
    """查看页面结构"""
    print("🚀 启动 Playwright，查看页面结构...")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # 看到浏览器
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        
        page = await context.new_page()
        
        try:
            # 访问全国土地市场网
            print("\n🌐 正在访问全国土地市场网...")
            await page.goto(
                'https://www.landchina.com/',
                wait_until='networkidle',
                timeout=60000
            )
            
            print("✅ 页面加载完成")
            
            # 等待一下，让页面完全渲染
            await page.wait_for_timeout(3000)
            
            # 截图
            screenshot_path = '/Users/tianguobao/WorkBuddy/Claw/landchina_homepage.png'
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"\n📸 截图已保存: {screenshot_path}")
            
            # 打印页面的所有链接
            print("\n🔗 页面链接:")
            links = await page.query_selector_all('a')
            print(f"   找到 {len(links)} 个链接")
            
            for i, link in enumerate(links[:20], 1):  # 只打印前20个
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute('href')
                    if text.strip():
                        print(f"   {i}. {text.strip()} -> {href}")
                except:
                    pass
            
            # 打印页面的所有按钮
            print("\n🔘 页面按钮:")
            buttons = await page.query_selector_all('button, input[type="button"], .btn')
            print(f"   找到 {len(buttons)} 个按钮")
            
            for i, btn in enumerate(buttons[:20], 1):  # 只打印前20个
                try:
                    text = await btn.inner_text()
                    if text.strip():
                        print(f"   {i}. {text.strip()}")
                except:
                    pass
            
            # 查找包含"公告"、"土地"、"出让"的元素
            print("\n🔍 查找关键词元素:")
            keywords = ['公告', '土地', '出让', '供应', '交易', '上海', '北京', '城市']
            
            for keyword in keywords:
                elements = await page.query_selector_all(f'text={keyword}')
                if elements:
                    print(f"   找到 {len(elements)} 个包含'{keyword}'的元素")
                    for i, elem in enumerate(elements[:3], 1):
                        try:
                            text = await elem.inner_text()
                            print(f"      {i}. {text.strip()[:50]}")
                        except:
                            pass
            
            # 打印页面的 HTML 结构（前2000个字符）
            print("\n📄 页面 HTML (前2000字符):")
            html = await page.content()
            print(html[:2000])
            
            print("\n" + "=" * 60)
            print("✅ 页面分析完成!")
            print("\n   3秒后关闭浏览器...")
            
            await page.wait_for_timeout(3000)
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
        
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(inspect_page())
