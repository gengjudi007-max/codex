#!/usr/bin/env python3
"""
查看全国土地市场网的页面结构 V2
"""
import asyncio
from playwright.async_api import async_playwright


async def inspect_page_v2():
    """查看页面结构 V2"""
    print("🚀 启动 Playwright，查看页面结构 V2...")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # 看到浏览器
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'  # 修正：zh-CN（大写）
        )
        
        page = await context.new_page()
        
        try:
            # 尝试多个 URL
            urls = [
                'https://www.landchina.com/',
                'https://www.landchina.com/#/',
            ]
            
            for url in urls:
                print(f"\n🌐 正在访问: {url}")
                
                try:
                    await page.goto(
                        url,
                        wait_until='load',  # 改为 'load'
                        timeout=60000
                    )
                    
                    print(f"✅ 页面加载完成: {url}")
                    
                    # 等待更长时间，让 JavaScript 执行
                    await page.wait_for_timeout(5000)
                    
                    # 截图
                    screenshot_path = f'/Users/tianguobao/WorkBuddy/Claw/landchina_{url.split("/")[-1] or "home"}.png'
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"   📸 截图已保存: {screenshot_path}")
                    
                    # 打印页面 HTML
                    html = await page.content()
                    print(f"\n   📄 页面 HTML 长度: {len(html)}")
                    
                    if len(html) > 100:
                        print(f"   📄 页面 HTML (前1000字符):")
                        print(html[:1000])
                        break  # 找到有效页面，跳出循环
                    else:
                        print(f"   ⚠️  页面内容为空，尝试下一个 URL")
                        
                except Exception as e:
                    print(f"   ❌ 访问失败: {e}")
            
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
            print("\n   5秒后关闭浏览器...")
            
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
        
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(inspect_page_v2())
