#!/usr/bin/env python3
"""
拦截上海土地市场的真实API请求
找到正确的 API 端点
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def intercept_shanghai_api():
    """拦截上海土地市场的真实API请求"""
    print("🚀 启动 Playwright，拦截上海土地市场 API...")
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
        
        # 存储拦截到的 API 请求和响应
        api_requests = []
        api_responses = []
        
        # 监听请求
        async def handle_request(request):
            url = request.url
            # 只关注 API 请求
            if any(keyword in url for keyword in ['api', 'result', 'list', 'query', 'search', 'jt', 'jy']):
                print(f"\n📤 API 请求: {request.method} {url}")
                
                try:
                    headers = request.headers
                    print(f"   Headers: {json.dumps(dict(headers), ensure_ascii=False)[:300]}")
                    
                    body = request.post_data
                    if body:
                        print(f"   Body: {body[:200]}")
                except Exception as e:
                    print(f"   读取请求失败: {e}")
                
                api_requests.append({
                    'url': url,
                    'method': request.method,
                    'headers': dict(headers),
                    'body': body
                })
        
        # 监听响应
        async def handle_response(response):
            url = response.url
            # 只关注 API 响应
            if any(keyword in url for keyword in ['api', 'result', 'list', 'query', 'search', 'jt', 'jy']):
                print(f"\n📥 API 响应: {response.status} {url}")
                
                try:
                    # 只处理 JSON 响应
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        body = await response.json()
                        print(f"   响应: {json.dumps(body, ensure_ascii=False)[:300]}")
                        
                        api_responses.append({
                            'url': url,
                            'status': response.status,
                            'body': body
                        })
                except Exception as e:
                    # 不是 JSON，跳过
                    pass
        
        page.on('request', handle_request)
        page.on('response', handle_response)
        
        try:
            # 访问上海土地市场页面
            print("\n🌐 正在访问上海土地市场...")
            await page.goto(
                'https://biz.ghzyj.sh.gov.cn/shtdsc/jy/view/web/transaction/result/list_result_ywtb.html',
                wait_until='networkidle',
                timeout=60000
            )
            
            print("✅ 页面加载完成")
            
            # 等待页面完全渲染，触发所有 API 请求
            print("\n⏳ 等待 API 请求完成...")
            await page.wait_for_timeout(10000)
            
            # 尝试点击"查询"按钮（如果有）
            print("\n🖱️  尝试点击查询按钮...")
            try:
                # 查找可能的查询按钮
                buttons = await page.query_selector_all('button, input[type="button"], .btn, .search-btn')
                for btn in buttons[:10]:
                    try:
                        text = await btn.inner_text()
                        if '查询' in text or '搜索' in text or 'query' in text.lower():
                            print(f"   找到按钮: {text}")
                            await btn.click()
                            await page.wait_for_timeout(3000)
                            break
                    except:
                        pass
            except Exception as e:
                print(f"   ⚠️  未找到查询按钮: {e}")
            
            # 再次等待 API 请求完成
            await page.wait_for_timeout(5000)
            
            # 保存拦截结果
            output_file = '/Users/tianguobao/WorkBuddy/Claw/shanghai_intercepted_api.json'
            
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
            
            if api_responses:
                print("\n📋 拦截到的 API 响应:")
                for i, resp in enumerate(api_responses, 1):
                    print(f"   {i}. {resp['status']} {resp['url']}")
                    print(f"      响应预览: {json.dumps(resp['body'], ensure_ascii=False)[:100]}")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n🏁 测试完成，10秒后关闭浏览器...")
            await page.wait_for_timeout(10000)
            await browser.close()


if __name__ == '__main__':
    asyncio.run(intercept_shanghai_api())
