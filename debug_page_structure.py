#!/usr/bin/env python3
"""
调试：检查上海土地市场页面结构
"""
import asyncio
from playwright.async_api import async_playwright


async def debug_page_structure():
    """调试页面结构"""
    print("🚀 启动调试，检查页面结构...")
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
            # 访问页面
            print("\n🌐 访问上海土地市场...")
            await page.goto(
                'https://biz.ghzyj.sh.gov.cn/shtdsc/jy/view/web/transaction/result/list_result_ywtb.html',
                wait_until='networkidle',
                timeout=60000
            )
            
            print("✅ 页面加载完成")
            await page.wait_for_timeout(10000)  # 等待更长时间
            
            # 截图
            screenshot_path = '/Users/tianguobao/WorkBuddy/Claw/shanghai_page_debug.png'
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"\n📸 截图已保存: {screenshot_path}")
            
            # 检查页面中是否有 #list_data
            print("\n🔍 检查页面结构...")
            
            result = await page.evaluate("""
                () => {
                    const results = {};
                    
                    // 1. 检查是否存在 #list_data
                    const listData = document.getElementById('list_data');
                    results.has_list_data = !!listData;
                    results.list_data_html = listData ? listData.outerHTML.substring(0, 500) : null;
                    
                    // 2. 检查是否存在 iframe
                    const iframes = document.querySelectorAll('iframe');
                    results.iframe_count = iframes.length;
                    results.iframe_srcs = Array.from(iframes).map(f => f.src);
                    
                    // 3. 打印页面中所有 li 元素
                    const lis = document.querySelectorAll('li');
                    results.li_count = lis.length;
                    results.first_3_lis = Array.from(lis).slice(0, 3).map(li => li.outerHTML.substring(0, 200));
                    
                    // 4. 打印页面 HTML（前2000字符）
                    results.page_html_preview = document.body.innerHTML.substring(0, 2000);
                    
                    return results;
                }
            """)
            
            print(f"   1️⃣ 存在 #list_data: {result['has_list_data']}")
            if result['has_list_data']:
                print(f"      HTML: {result['list_data_html']}")
            
            print(f"\n   2️⃣ iframe 数量: {result['iframe_count']}")
            if result['iframe_count'] > 0:
                print(f"      iframe src: {result['iframe_srcs']}")
            
            print(f"\n   3️⃣ <li> 元素数量: {result['li_count']}")
            if result['first_3_lis']:
                print(f"      前3个 <li>:")
                for i, li_html in enumerate(result['first_3_lis'], 1):
                    print(f"      {i}. {li_html}")
            
            print(f"\n   4️⃣ 页面 HTML（前2000字符）:")
            print(result['page_html_preview'])
            
            # 等待用户手动操作
            print("\n" + "=" * 60)
            print("✅ 调试完成!")
            print("\n💡 浏览器将保持打开 30 秒，您可以手动检查页面...")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(debug_page_structure())
