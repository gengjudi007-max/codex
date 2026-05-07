#!/usr/bin/env python3
"""
通用城市土地市场 API 探索器
使用 Playwright 访问城市网站，自动监听网络请求，找到土地成交结果的 API 接口
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def explore_city_api(city_name: str, start_url: str, headless: bool = True):
    """
    探索城市土地市场 API
    
    Args:
        city_name: 城市名称（用于日志）
        start_url: 起始 URL（通常是政府网站首页）
        headless: 是否无头模式
    """
    print(f"\n{'='*80}")
    print(f"🔍 探索 {city_name} 土地市场 API")
    print(f"{'='*80}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        
        page = await context.new_page()
        
        # 存储所有网络请求
        api_requests = []
        api_responses = []
        
        # 监听所有请求
        async def log_request(request):
            url = request.url
            method = request.method
            
            # 过滤可能的 API 请求
            if any(keyword in url.lower() for keyword in ['api', 'list', 'query', 'search', 'result', 'data']):
                api_requests.append({
                    'url': url,
                    'method': method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data,
                    'timestamp': asyncio.get_event_loop().time()
                })
                print(f"📤 请求: {method} {url}")
        
        # 监听所有响应
        async def log_response(response):
            url = response.url
            status = response.status
            
            # 过滤可能的 API 响应
            if any(keyword in url.lower() for keyword in ['api', 'list', 'query', 'search', 'result', 'data']):
                try:
                    content_type = response.headers.get('content-type', '')
                    body = None
                    
                    # 尝试读取响应体
                    if 'json' in content_type:
                        body = await response.json()
                    elif 'html' in content_type or 'text' in content_type:
                        body = await response.text()
                        if len(body) > 500:
                            body = body[:500] + '...'
                    
                    api_responses.append({
                        'url': url,
                        'status': status,
                        'content_type': content_type,
                        'body': body,
                        'timestamp': asyncio.get_event_loop().time()
                    })
                    
                    print(f"📥 响应: {status} {url}")
                    if body:
                        print(f"   内容片段: {str(body)[:200]}")
                
                except Exception as e:
                    print(f"   ⚠️  读取响应失败: {e}")
        
        page.on('request', log_request)
        page.on('response', log_response)
        
        # 访问起始页面
        print(f"🌐 访问: {start_url}")
        try:
            await page.goto(start_url, wait_until='networkidle', timeout=60000)
            print(f"✅ 页面加载完成")
        except Exception as e:
            print(f"❌ 页面加载失败: {e}")
            await page.screenshot(path=f'/Users/tianguobao/WorkBuddy/Claw/{city_name}_error.png')
        
        # 等待一下，让页面完全加载
        await page.wait_for_timeout(3000)
        
        # 尝试查找"成交结果"、"出让公告"等链接并点击
        print(f"\n🔍 查找土地交易相关链接...")
        
        link_keywords = ['成交', '出让', '地块', '交易结果', '土地供应', '招拍挂']
        
        for keyword in link_keywords:
            try:
                links = await page.locator(f'a:has-text("{keyword}")').all()
                if links:
                    print(f"   找到 {len(links)} 个包含 '{keyword}' 的链接")
                    
                    # 点击第一个链接
                    if links:
                        print(f"   点击: {keyword}")
                        await links[0].click()
                        await page.wait_for_timeout(3000)
                        break
            except Exception as e:
                print(f"   查找 '{keyword}' 失败: {e}")
        
        # 最终等待
        await page.wait_for_timeout(5000)
        
        # 截图当前页面
        screenshot_path = f'/Users/tianguobao/WorkBuddy/Claw/{city_name}_final.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n📸 截图已保存: {screenshot_path}")
        
        # 打印捕获的 API 请求
        print(f"\n{'='*80}")
        print(f"📊 捕获的 API 请求 ({len(api_requests)} 个)")
        print(f"{'='*80}\n")
        
        for i, req in enumerate(api_requests[:10], 1):  # 只显示前 10 个
            print(f"{i}. {req['method']} {req['url']}")
            if req['post_data']:
                print(f"   POST Data: {req['post_data'][:200]}")
        
        # 打印捕获的 API 响应
        print(f"\n{'='*80}")
        print(f"📊 捕获的 API 响应 ({len(api_responses)} 个)")
        print(f"{'='*80}\n")
        
        for i, resp in enumerate(api_responses[:10], 1):  # 只显示前 10 个
            print(f"{i}. {resp['status']} {resp['url']}")
            print(f"   Content-Type: {resp['content_type']}")
            if resp['body']:
                print(f"   Body: {str(resp['body'])[:300]}")
            print()
        
        # 保存结果到 JSON
        result = {
            'city': city_name,
            'start_url': start_url,
            'api_requests': api_requests,
            'api_responses': api_responses
        }
        
        result_path = f'/Users/tianguobao/WorkBuddy/Claw/{city_name}_api_exploration.json'
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 结果已保存: {result_path}")
        
        await browser.close()
        
        return result


async def main():
    """测试函数"""
    # 测试广州
    await explore_city_api(
        city_name="广州",
        start_url="https://ghzyj.gz.gov.cn/",
        headless=False  # 有头模式，方便观察
    )


if __name__ == '__main__':
    asyncio.run(main())
