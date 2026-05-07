#!/usr/bin/env python3
"""
调试：检查 API 响应格式
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def debug_api_response():
    """调试 API 响应"""
    print("🚀 启动调试...")
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
        
        # 访问页面
        print("\n🌐 访问全国土地市场网...")
        await page.goto(
            'https://www.landchina.com/',
            wait_until='networkidle',
            timeout=60000
        )
        print("✅ 页面加载完成")
        
        await page.wait_for_timeout(3000)
        
        # 测试1: 获取城市列表
        print("\n📍 测试1: 获取城市列表...")
        result1 = await page.evaluate("""
            async () => {
                try {
                    const response = await fetch('https://api.landchina.com/bptFieldEnum/keyCity', {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Referer': 'https://www.landchina.com/'
                        }
                    });
                    const data = await response.json();
                    return { success: true, data: data, status: response.status };
                } catch (error) {
                    return { success: false, error: error.toString() };
                }
            }
        """)
        
        print(f"   成功: {result1['success']}")
        if result1['success']:
            print(f"   状态: {result1['status']}")
            print(f"   数据: {json.dumps(result1['data'], ensure_ascii=False, indent=2)[:500]}")
        
        # 测试2: 获取土地数据（不带城市代码）
        print("\n📊 测试2: 获取土地数据（全国）...")
        result2 = await page.evaluate("""
            async () => {
                try {
                    const response = await fetch('https://api.landchina.com/epstBulletin/index/bulletin', {
                        method: 'POST',
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Content-Type': 'application/json',
                            'Referer': 'https://www.landchina.com/'
                        },
                        body: JSON.stringify({ pageNum: 1, pageSize: 3 })
                    });
                    const data = await response.json();
                    return { success: true, data: data, status: response.status };
                } catch (error) {
                    return { success: false, error: error.toString() };
                }
            }
        """)
        
        print(f"   成功: {result2['success']}")
        if result2['success']:
            print(f"   状态: {result2['status']}")
            print(f"   完整响应: {json.dumps(result2['data'], ensure_ascii=False, indent=2)}")
        
        # 测试3: 获取土地数据（上海）
        print("\n📊 测试3: 获取土地数据（上海）...")
        result3 = await page.evaluate("""
            async () => {
                try {
                    const response = await fetch('https://api.landchina.com/epstBulletin/index/bulletin', {
                        method: 'POST',
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Content-Type': 'application/json',
                            'Referer': 'https://www.landchina.com/'
                        },
                        body: JSON.stringify({ pageNum: 1, pageSize: 3, xzqDm: '31' })
                    });
                    const data = await response.json();
                    return { success: true, data: data, status: response.status };
                } catch (error) {
                    return { success: false, error: error.toString() };
                }
            }
        """)
        
        print(f"   成功: {result3['success']}")
        if result3['success']:
            print(f"   状态: {result3['status']}")
            print(f"   完整响应: {json.dumps(result3['data'], ensure_ascii=False, indent=2)}")
        
        await browser.close()
    
    print("\n" + "=" * 60)
    print("✅ 调试完成!")


if __name__ == '__main__':
    asyncio.run(debug_api_response())
