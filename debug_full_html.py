#!/usr/bin/env python3
"""
调试：打印页面完整 HTML
"""
import asyncio
from playwright.async_api import async_playwright


async def debug_full_html():
    """打印页面完整 HTML"""
    print("🚀 启动调试，打印页面 HTML...")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
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
            await page.wait_for_timeout(10000)  # 等待更长
            
            # 获取完整页面 HTML
            print("\n📄 获取页面完整 HTML...")
            
            html = await page.content()
            
            print(f"   HTML 长度: {len(html)}")
            
            # 检查是否包含 list_data
            if 'list_data' in html:
                print("   ✅ 找到 list_data!")
                # 提取 list_data 附近的 HTML
                import re
                match = re.search(r'(<ul[^>]*list_data[^>]*>.*?</ul>)', html, re.DOTALL)
                if match:
                    print(f"\n   list_data HTML:\n{match.group(1)[:1000]}")
            else:
                print("   ❌ 未找到 list_data")
            
            # 保存完整 HTML 到文件
            output_file = '/Users/tianguobao/WorkBuddy/Claw/shanghai_full_page.html'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"\n💾 完整 HTML 已保存: {output_file}")
            print(f"   文件大小: {len(html)} 字节")
            
            # 打印前 3000 字符
            print(f"\n📄 HTML 预览 (前 3000 字符):")
            print(html[:3000])
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()
            
            print("\n" + "=" * 60)
            print("✅ 调试完成!")


if __name__ == '__main__':
    asyncio.run(debug_full_html())
