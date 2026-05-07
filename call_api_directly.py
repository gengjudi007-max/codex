#!/usr/bin/env python3
"""
使用 Playwright 直接调用全国土地市场网 API
让浏览器自动处理动态 hash
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def call_api_directly():
    """直接在浏览器中调用 API"""
    print("🚀 启动 Playwright，直接调用 API...")
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
            # 访问页面，让浏览器加载 JavaScript
            print("\n🌐 访问全国土地市场网...")
            await page.goto(
                'https://www.landchina.com/',
                wait_until='networkidle',
                timeout=60000
            )
            
            print("✅ 页面加载完成")
            await page.wait_for_timeout(5000)
            
            # 测试1: 获取城市列表
            print("\n📍 测试1: 获取城市列表...")
            
            result1 = await page.evaluate("""
                async () => {
                    const response = await fetch('https://api.landchina.com/bptFieldEnum/keyCity', {
                        method: 'GET',
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Referer': 'https://www.landchina.com/'
                        }
                    });
                    const data = await response.json();
                    return data;
                }
            """)
            
            print(f"   状态: 成功")
            cities = result1.get('data', [])
            print(f"   城市数量: {len(cities)}")
            
            if cities:
                print(f"   前 5 个城市:")
                for city in cities[:5]:
                    print(f"      - {city['enumName']} (代码: {city['enumValue']})")
            
            # 测试2: 获取全国土地数据
            print("\n📊 测试2: 获取全国土地数据...")
            
            result2 = await page.evaluate("""
                async () => {
                    const response = await fetch('https://api.landchina.com/epstBulletin/index/bulletin', {
                        method: 'POST',
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Content-Type': 'application/json',
                            'Referer': 'https://www.landchina.com/'
                        },
                        body: JSON.stringify({
                            pageNum: 1,
                            pageSize: 5
                        })
                    });
                    const data = await response.json();
                    return data;
                }
            """)
            
            print(f"   状态: {result2.get('msg', 'Unknown')}")
            print(f"   数据键: {list(result2.keys()) if isinstance(result2, dict) else 'Not a dict'}")
            
            # 打印完整的响应结构
            print(f"\n   完整响应 (前1500字符):")
            print(json.dumps(result2, ensure_ascii=False, indent=2)[:1500])
            
            # 测试3: 获取上海土地数据
            print("\n📊 测试3: 获取上海土地数据 (代码: 31)...")
            
            result3 = await page.evaluate("""
                async () => {
                    const response = await fetch('https://api.landchina.com/epstBulletin/index/bulletin', {
                        method: 'POST',
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Content-Type': 'application/json',
                            'Referer': 'https://www.landchina.com/'
                        },
                        body: JSON.stringify({
                            pageNum: 1,
                            pageSize: 5,
                            xzqDm: '31'  // 上海的城市代码
                        })
                    });
                    const data = await response.json();
                    return data;
                }
            """)
            
            print(f"   状态: {result3.get('msg', 'Unknown')}")
            print(f"   数据键: {list(result3.keys()) if isinstance(result3, dict) else 'Not a dict'}")
            
            # 打印完整的响应结构
            print(f"\n   完整响应 (前1500字符):")
            print(json.dumps(result3, ensure_ascii=False, indent=2)[:1500])
            
            # 保存结果
            output = {
                'cities': result1,
                'national_data': result2,
                'shanghai_data': result3
            }
            
            output_file = '/Users/tianguobao/WorkBuddy/Claw/api_direct_call_result.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 结果已保存: {output_file}")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()
            
            print("\n" + "=" * 60)
            print("✅ 测试完成!")


if __name__ == '__main__':
    asyncio.run(call_api_directly())
