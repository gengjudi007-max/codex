#!/usr/bin/env python3
"""
拦截全国土地市场网的真实API请求
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def intercept_landchina_api():
    """拦截 api.landchina.com 的真实请求"""
    print("🚀 启动 Playwright，拦截全国土地市场网 API...")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # 看到浏览器，方便调试
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
            if 'api.landchina.com' in url:
                print(f"\n📤 拦截到 API 请求:")
                print(f"   URL: {url}")
                print(f"   方法: {request.method}")
                
                try:
                    headers = request.headers
                    print(f"   Headers: {json.dumps(headers, indent=2, ensure_ascii=False)[:500]}")
                    
                    body = request.post_data
                    if body:
                        print(f"   Body: {body[:500]}")
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
            if 'api.landchina.com' in url:
                print(f"\n📥 拦截到 API 响应:")
                print(f"   URL: {url}")
                print(f"   状态: {response.status}")
                
                try:
                    body = await response.text()
                    print(f"   响应长度: {len(body)}")
                    print(f"   响应预览: {body[:200]}")
                    
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
            
            # 尝试点击"公告信息"或相关链接
            print("\n🖱️  尝试点击公告信息...")
            try:
                await page.click('text=公告信息', timeout=5000)
                await page.wait_for_timeout(3000)
            except:
                print("   未找到'公告信息'链接")
            
            # 尝试点击"土地出让"或相关链接
            print("\n🖱️  尝试点击土地出让...")
            try:
                await page.click('text=土地出让', timeout=5000)
                await page.wait_for_timeout(3000)
            except:
                print("   未找到'土地出让'链接")
            
            # 等待所有可能的 API 请求完成
            print("\n⏳ 等待 API 请求完成...")
            await page.wait_for_timeout(5000)
            
            # 保存拦截结果
            output_file = '/Users/tianguobao/WorkBuddy/Claw/landchina_api_intercepted.json'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'requests': api_requests,
                    'responses': api_responses
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 拦截结果已保存: {output_file}")
            print(f"   请求数: {len(api_requests)}")
            print(f"   响应数: {len(api_responses)}")
            
            # 打印所有拦截到的 API URL
            if api_requests:
                print("\n📋 拦截到的 API 请求:")
                for i, req in enumerate(api_requests, 1):
                    print(f"   {i}. {req['method']} {req['url']}")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
        
        finally:
            print("\n🏁 测试完成，5秒后关闭浏览器...")
            await page.wait_for_timeout(5000)
            await browser.close()


if __name__ == '__main__':
    asyncio.run(intercept_landchina_api())
