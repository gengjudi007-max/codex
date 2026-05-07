#!/usr/bin/env python3
"""
使用 Playwright 拦截上海土地市场 API
从真实的网络请求中提取 token 和响应数据
"""
import asyncio
import json
import re
from playwright.async_api import async_playwright


async def intercept_realtime():
    """实时拦截 API 请求和响应"""
    print("🚀 启动 Playwright，实时拦截 API...")
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
        
        # 存储拦截到的信息
        intercept_data = {
            'token': None,
            'api_request': None,
            'api_response': None
        }
        
        # 监听所有请求，查找包含 token 的 API 请求
        async def handle_request(request):
            url = request.url
            if 'listForPage' in url:
                print(f"\n📤 拦截到 API 请求:")
                print(f"   URL: {url}")
                print(f"   方法: {request.method}")
                
                # 从 URL 中提取 token
                match = re.search(r'MmEwMD=([^&]+)', url)
                if match:
                    intercept_data['token'] = match.group(1)
                    print(f"   ✅ 提取到 Token: {intercept_data['token'][:30]}...")
                
                # 保存请求信息
                intercept_data['api_request'] = {
                    'url': url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'body': request.post_data
                }
                
                print(f"   Headers: {json.dumps(dict(request.headers), ensure_ascii=False)[:300]}")
                if request.post_data:
                    print(f"   Body: {request.post_data}")
        
        # 监听所有响应，查找 API 响应
        async def handle_response(response):
            url = response.url
            if 'listForPage' in url:
                print(f"\n📥 拦截到 API 响应:")
                print(f"   URL: {url}")
                print(f"   状态: {response.status}")
                
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        body = await response.json()
                        print(f"   ✅ JSON 响应: {json.dumps(body, ensure_ascii=False)[:300]}")
                        intercept_data['api_response'] = body
                    else:
                        body = await response.text()
                        print(f"   ⚠️  HTML 响应 (前300字符): {body[:300]}")
                        intercept_data['api_response'] = {'html': body}
                except Exception as e:
                    print(f"   ❌ 读取响应失败: {e}")
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        try:
            # 访问页面
            print("\n🌐 正在访问上海土地市场...")
            await page.goto(
                'https://biz.ghzyj.sh.gov.cn/shtdsc/jy/view/web/transaction/result/list_result_ywtb.html',
                wait_until='networkidle',
                timeout=60000
            )
            
            print("✅ 页面加载完成")
            
            # 等待 API 请求完成
            print("\n⏳ 等待 API 请求完成...")
            await page.wait_for_timeout(10000)
            
            # 保存拦截结果
            output_file = '/Users/tianguobao/WorkBuddy/Claw/shanghai_realtime_intercept.json'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(intercept_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 拦截结果已保存: {output_file}")
            print(f"   Token: {'✅ ' + intercept_data['token'][:30] + '...' if intercept_data['token'] else '❌ 未找到'}")
            print(f"   API 请求: {'✅ 已捕获' if intercept_data['api_request'] else '❌ 未捕获'}")
            print(f"   API 响应: {'✅ 已捕获' if intercept_data['api_response'] else '❌ 未捕获'}")
            
            # 如果捕获到响应，打印详细信息
            if intercept_data['api_response']:
                print(f"\n📋 API 响应详情:")
                if 'html' in intercept_data['api_response']:
                    html = intercept_data['api_response']['html']
                    print(f"   HTML 长度: {len(html)}")
                    print(f"   前500字符: {html[:500]}")
                else:
                    print(f"   JSON: {json.dumps(intercept_data['api_response'], ensure_ascii=False, indent=2)[:500]}")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()
            
            print("\n" + "=" * 60)
            print("✅ 拦截完成!")


if __name__ == '__main__':
    asyncio.run(intercept_realtime())
