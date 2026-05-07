#!/usr/bin/env python3
"""
查找正确的土地出让数据 API
导航到土地出让页面，拦截真实的 API 请求
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def find_land_transaction_api():
    """查找土地出让数据 API"""
    print("🚀 启动 Playwright，查找土地出让数据 API...")
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
        
        # 存储拦截到的 API 请求
        api_requests = []
        api_responses = []
        
        # 监听所有 API 请求
        async def handle_request(request):
            url = request.url
            if 'api.landchina.com' in url:
                print(f"\n📤 API 请求: {request.method} {url}")
                
                try:
                    body = request.post_data
                    if body:
                        print(f"   Body: {body[:200]}")
                except:
                    pass
                
                api_requests.append({
                    'url': url,
                    'method': request.method,
                    'body': request.post_data
                })
        
        # 监听所有 API 响应
        async def handle_response(response):
            url = response.url
            if 'api.landchina.com' in url:
                print(f"\n📥 API 响应: {response.status} {url}")
                
                try:
                    body = await response.text()
                    print(f"   响应长度: {len(body)}")
                    print(f"   预览: {body[:200]}")
                    
                    # 检查是否包含土地出让数据的关键字
                    if any(keyword in body for keyword in ['地块', '土地', '出让', '挂牌', '成交']):
                        print(f"   ✅ 包含土地数据关键字!")
                    
                except Exception as e:
                    print(f"   ❌ 读取响应失败: {e}")
                
                api_responses.append({
                    'url': url,
                    'status': response.status,
                    'body_length': len(body) if 'body' in dir() else 0
                })
        
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
            await page.wait_for_timeout(3000)
            
            # 查找并点击"土地出让"或相关链接
            print("\n🖱️  查找土地出让相关链接...")
            
            # 尝试多个可能的关键词
            keywords = ['土地出让', '供应信息', '交易信息', '地块信息', '成交公示']
            
            for keyword in keywords:
                try:
                    print(f"\n   尝试查找: {keyword}")
                    link = await page.query_selector(f'text={keyword}')
                    if link:
                        print(f"   ✅ 找到链接: {keyword}")
                        await link.click()
                        await page.wait_for_timeout(5000)
                        print(f"   ✅ 点击成功，等待页面加载...")
                        break
                except Exception as e:
                    print(f"   ⚠️  未找到: {e}")
            
            # 等待所有可能的 API 请求完成
            print("\n⏳ 等待 API 请求完成...")
            await page.wait_for_timeout(10000)
            
            # 保存拦截结果
            output_file = '/Users/tianguobao/WorkBuddy/Claw/land_transaction_api.json'
            
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
                    if req['body']:
                        print(f"      Body: {req['body'][:100]}")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n🏁 测试完成，10秒后关闭浏览器...")
            await page.wait_for_timeout(10000)
            await browser.close()


if __name__ == '__main__':
    asyncio.run(find_land_transaction_api())
