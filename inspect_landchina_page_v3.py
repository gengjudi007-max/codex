#!/usr/bin/env python3
"""
查看全国土地市场网的页面结构 V3
等待页面完全渲染
"""
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


async def inspect_page_v3():
    """查看页面结构 V3 - 等待页面完全渲染"""
    print("🚀 启动 Playwright，查看页面结构 V3...")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # 看到浏览器
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',  # 修正：zh-CN（大写）
            timezone_id='Asia/Shanghai'
        )
        
        page = await context.new_page()
        
        # 监听控制台信息
        page.on('console', lambda msg: print(f"   控制台 [{msg.type}]: {msg.text}"))
        
        # 监听页面错误
        page.on('pageerror', lambda error: print(f"   ❌ 页面错误: {error}"))
        
        try:
            print("\n🌐 正在访问: https://www.landchina.com/")
            
            await page.goto(
                'https://www.landchina.com/',
                wait_until='domcontentloaded',  # 改为 domcontentloaded
                timeout=60000
            )
            
            print("✅ 初始页面加载完成")
            
            # 等待页面完全渲染（等待某个元素出现）
            print("\n⏳ 等待页面完全渲染...")
            
            try:
                # 等待 body 有内容
                await page.wait_for_selector('body *', timeout=10000)
                print("   ✅ 页面有内容了")
            except PlaywrightTimeout:
                print("   ⚠️  超时：页面没有渲染任何内容")
            
            # 再等待 10 秒，让 JavaScript 完全执行
            print("   等待 10 秒，让 JavaScript 执行...")
            await page.wait_for_timeout(10000)
            
            # 截图
            screenshot_path = '/Users/tianguobao/WorkBuddy/Claw/landchina_homepage_v3.png'
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"\n📸 截图已保存: {screenshot_path}")
            
            # 打印页面 HTML
            html = await page.content()
            print(f"\n📄 页面 HTML 长度: {len(html)}")
            
            if len(html) > 100:
                print(f"\n   前 2000 字符:")
                print(html[:2000])
            else:
                print(f"   ⚠️  页面内容仍然为空: {html}")
            
            # 查找所有链接
            print("\n🔗 查找页面链接:")
            links = await page.query_selector_all('a')
            print(f"   找到 {len(links)} 个链接")
            
            for i, link in enumerate(links[:20], 1):
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute('href')
                    if text.strip():
                        print(f"   {i}. {text.strip()[:30]} -> {href[:50] if href else 'None'}")
                except:
                    pass
            
            print("\n" + "=" * 60)
            print("✅ 页面分析完成!")
            print("\n   10秒后关闭浏览器...")
            
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
        
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(inspect_page_v3())
