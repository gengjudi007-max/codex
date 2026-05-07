#!/usr/bin/env python3
"""
单独修复成都连接器
1. 访问四川土地矿权交易信息网
2. 提取成都的土地成交数据
"""
import asyncio
import re
from playwright.async_api import async_playwright


async def fix_chengdu():
    """修复成都连接器"""
    print("🔧 修复成都土地市场连接器")
    print("=" * 80)
    
    # 四川土地矿权交易信息网
    url = "http://202.61.89.138:800/sitefiles/services/cms/page.aspx?s=1"
    
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
            print(f"\n🌐 访问: {url}")
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)
            print(f"✅ 页面加载完成")
            
            # 截图看看页面结构
            screenshot_path = '/Users/tianguobao/WorkBuddy/Claw/chengdu_page.png'
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 截图已保存: {screenshot_path}")
            
            # 查找"土地出让结果"或类似链接
            print(f"\n🔍 查找土地交易相关链接...")
            
            links = await page.evaluate("""
                () => {
                    const results = [];
                    const keywords = ['出让', '成交', '公示', '挂牌'];
                    
                    const allLinks = document.querySelectorAll('a');
                    for (const link of allLinks) {
                        const text = link.innerText || '';
                        if (keywords.some(kw => text.includes(kw))) {
                            results.push({
                                text: text.trim(),
                                href: link.href
                            });
                        }
                    }
                    
                    return results.slice(0, 10);
                }
            """)
            
            print(f"   找到 {len(links)} 个相关链接:\n")
            for i, link in enumerate(links, 1):
                print(f"   {i}. {link['text'][:50]}")
                print(f"      URL: {link['href'][:80]}")
            
            # 如果有"土地出让结果"之类的链接，点击它
            if links:
                print(f"\n🖱️  点击第一个相关链接...")
                await page.goto(links[0]['href'], wait_until='networkidle', timeout=60000)
                await page.wait_for_timeout(5000)
                print(f"✅ 已进入子页面")
                
                # 提取列表数据
                print(f"\n📊 提取列表数据...")
                
                data = await page.evaluate("""
                    () => {
                        const results = [];
                        const dateRegex = /20\\d{2}[.\\-]\\d{1,2}[.\\-]\\d{1,2}/;
                        
                        // 查找所有列表项
                        const items = document.querySelectorAll('li, tr');
                        
                        for (const item of items) {
                            const text = item.innerText || '';
                            
                            // 检查是否包含日期和城市名
                            if (dateRegex.test(text) && text.includes('成都')) {
                                const link = item.querySelector('a');
                                const dateMatch = text.match(dateRegex);
                                
                                results.push({
                                    title: link ? link.innerText.trim() : text.substring(0, 50),
                                    url: link ? link.href : '',
                                    date: dateMatch ? dateMatch[0] : '',
                                    raw_text: text.substring(0, 200)
                                });
                                
                                if (results.length >= 10) break;
                            }
                        }
                        
                        return results;
                    }
                """)
                
                print(f"   ✅ 提取到 {len(data)} 条成都的数据")
                
                if data:
                    print(f"\n   前 3 条:")
                    for i, item in enumerate(data[:3], 1):
                        print(f"   {i}. {item['title']}")
                        print(f"      日期: {item['date']}")
                        print(f"      URL: {item['url'][:80]}")
                    
                    return {'success': True, 'data': data}
            
        except Exception as e:
            print(f"\n❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
        
        await browser.close()
    
    return {'success': False, 'data': []}


if __name__ == '__main__':
    print("🚀 启动成都连接器修复")
    print("=" * 80)
    
    result = asyncio.run(fix_chengdu())
    
    print("\n" + "=" * 80)
    print("✅ 修复完成!")
    print(f"   成功: {'是' if result['success'] else '否'}")
    print(f"   数据条数: {len(result['data'])}")
