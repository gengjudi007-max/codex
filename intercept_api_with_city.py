#!/usr/bin/env python3
"""
拦截全国土地市场网的真实API请求（选择城市后）
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def intercept_api_with_city_selection():
    """拦截 API 请求（先选择城市）"""
    print("🚀 启动 Playwright，拦截 API（选择城市后）...")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # 看到浏览器，方便调试
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        
        page = await context.new_page()
        
        # 存储拦截到的 API 请求和响应
        api_requests = []
        api_responses = []
        
        # 监听请求
        async def handle_request(request):
            url = request.url
            if 'api.landchina.com' in url and 'bulletin' in url:
                print(f"\n📤 拦截到 API 请求:")
                print(f"   URL: {url}")
                print(f"   方法: {request.method}")
                
                try:
                    headers = request.headers
                    print(f"   Headers: {json.dumps(headers, indent=2, ensure_ascii=False)[:500]}")
                    
                    body = request.post_data
                    if body:
                        print(f"   Body: {body}")
                except:
                    pass
                
                api_requests.append({
                    'url': url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'body': request.post_data
                })
        
        # 监听响应
        async def handle_response(response):
            url = response.url
            if 'api.landchina.com' in url and 'bulletin' in url:
                print(f"\n📥 拦截到 API 响应:")
                print(f"   URL: {url}")
                print(f"   状态: {response.status}")
                
                try:
                    body = await response.text()
                    print(f"   响应长度: {len(body)}")
                    print(f"   响应预览: {body[:500]}")
                    
                    api_responses.append({
                        'url': url,
                        'status': response.status,
                        'headers': dict(response.headers),
                        'body': body
                    })
                except Exception as e:
                    print(f"   ❌ 读取响应失败: {e}")
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        try:
            # 访问全国土地市场网
            print("\n🌐 正在访问全国土地市场网...")
            await page.goto(
                'https://www.landchina.com/',
                wait_until='networkidle',
                timeout=60000
            )
            
            print("✅ 页面加载完成")
            
            # 等待一下，让页面完全加载
            await page.wait_for_timeout(3000)
            
            # 尝试点击"公告信息"
            print("\n🖱️  尝试点击'公告信息'...")
            try:
                await page.click('text=公告信息', timeout=5000)
                await page.wait_for_timeout(2000)
                print("   ✅ 点击成功")
            except:
                print("   ⚠️  未找到'公告信息'链接")
            
            # 尝试选择城市"上海"
            print("\n🏙️  尝试选择城市'上海'...")
            
            # 方法1: 查找城市下拉框或按钮
            try:
                # 查找包含"上海"的元素
                shanghai_btn = await page.query_selector('text=上海')
                if shanghai_btn:
                    await shanghai_btn.click()
                    await page.wait_for_timeout(2000)
                    print("   ✅ 点击'上海'成功")
                else:
                    print("   ⚠️  未找到'上海'按钮")
            except Exception as e:
                print(f"   ⚠️  选择城市失败: {e}")
            
            # 等待 API 请求完成
            print("\n⏳ 等待 API 请求完成...")
            await page.wait_for_timeout(5000)
            
            # 保存拦截结果
            output_file = '/Users/tianguobao/WorkBuddy/Claw/landchina_api_with_city.json'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'requests': api_requests,
                    'responses': api_responses
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 拦截结果已保存: {output_file}")
            print(f"   请求数: {len(api_requests)}")
            print(f"   响应数: {len(api_responses)}")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
        
        finally:
            print("\n🏁 测试完成，10秒后关闭浏览器...")
            await page.wait_for_timeout(10000)
            await browser.close()


if __name__ == '__main__':
    asyncio.run(intercept_api_with_city_selection())
