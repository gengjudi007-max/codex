#!/usr/bin/env python3
"""
上海土地市场 - 增强版监听
1. 监听所有网络请求
2. 查找 iframe 并监听其中的请求
3. 尝试所有可能的用户交互
"""
import asyncio
import json
from playwright.async_api import async_playwright, Frame


async def enhanced_shanghai_listen():
    """增强版上海土地市场监听"""
    print("🚀 启动增强版监听...")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        # 存储所有网络请求和响应
        all_requests = []
        all_responses = []
        api_requests = []
        api_responses = []
        
        # 监听所有请求
        async def log_request(request):
            url = request.url
            all_requests.append(url)
            
            # 记录可能的 API 请求
            if any(kw in url.lower() for kw in ['api', 'list', 'query', 'search', 'data', 'result', 'page', 'ajax']):
                req_data = {
                    'url': url,
                    'method': request.method,
                    'post_data': request.post_data
                }
                api_requests.append(req_data)
                print(f"\n📡 [API 请求] {request.method} {url}")
                if request.post_data:
                    print(f"   数据: {request.post_data[:200]}")
        
        # 监听所有响应
        async def log_response(response):
            url = response.url
            all_responses.append(url)
            
            # 记录可能的 API 响应
            if any(kw in url.lower() for kw in ['api', 'list', 'query', 'search', 'data', 'result', 'page']):
                try:
                    status = response.status
                    body = await response.text()
                    
                    resp_data = {
                        'url': url,
                        'status': status,
                        'body': body
                    }
                    api_responses.append(resp_data)
                    
                    print(f"\n✅ [API 响应] {status} {url}")
                    print(f"   长度: {len(body)}")
                    print(f"   预览: {body[:200]}")
                except:
                    pass
        
        page.on('request', log_request)
        page.on('response', log_response)
        
        try:
            # 访问上海土地市场页面
            print("\n🌐 正在访问: https://biz.ghzyj.sh.gov.cn/shtdsc/wz/ywtb/index.jhtml")
            await page.goto(
                "https://biz.ghzyj.sh.gov.cn/shtdsc/wz/ywtb/index.jhtml",
                wait_until='networkidle',
                timeout=60000
            )
            
            print("✅ 页面加载完成")
            
            # 等待页面完全渲染
            print("\n⏳ 等待 10 秒，让页面完全加载...")
            await page.wait_for_timeout(10000)
            
            # 检查 iframe
            print("\n🔍 检查 iframe...")
            frames = page.frames
            print(f"   找到 {len(frames)} 个 frame (包括主 frame)")
            
            for i, frame in enumerate(frames):
                print(f"   Frame {i}: {frame.url[:100]}")
            
            # 查找并点击所有可能的按钮
            print("\n🔍 查找可点击的元素...")
            
            # 查找所有按钮和链接
            buttons = await page.query_selector_all('button, input[type="button"], input[type="submit"], a')
            print(f"   找到 {len(buttons)} 个可点击元素")
            
            # 尝试点击包含"查询"的按钮
            for i, btn in enumerate(buttons):
                try:
                    text = await btn.inner_text()
                    if '查询' in text or '搜索' in text or '提交' in text:
                        print(f"\n   ✅ 找到按钮: {text}")
                        print(f"   🖱️  点击按钮...")
                        await btn.click()
                        await page.wait_for_timeout(3000)
                        break
                except:
                    pass
            
            # 等待可能的 AJAX 请求
            print("\n⏳ 等待 AJAX 请求完成...")
            await page.wait_for_timeout(5000)
            
            # 打印统计信息
            print("\n" + "=" * 60)
            print("📊 统计信息:")
            print(f"   总请求数: {len(all_requests)}")
            print(f"   总响应数: {len(all_responses)}")
            print(f"   API 请求数: {len(api_requests)}")
            print(f"   API 响应数: {len(api_responses)}")
            
            # 列出所有 API 请求
            if api_requests:
                print(f"\n📡 API 请求列表:")
                for req in api_requests[:20]:  # 只显示前 20 个
                    print(f"   {req['method']} {req['url'][:150]}")
                    if req['post_data']:
                        print(f"      数据: {req['post_data'][:200]}")
            
            # 列出所有 API 响应
            if api_responses:
                print(f"\n✅ API 响应列表:")
                for resp in api_responses[:20]:  # 只显示前 20 个
                    print(f"   {resp['status']} {resp['url'][:150]}")
                    print(f"      长度: {len(resp['body'])}")
            
            # 保存 API 响应到文件
            if api_responses:
                output_file = '/Users/tianguobao/WorkBuddy/Claw/shanghai_api_responses.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(api_responses, f, ensure_ascii=False, indent=2)
                print(f"\n💾 API 响应已保存: {output_file}")
            
            print("\n" + "=" * 60)
            print("💡 提示:")
            print("   查看上面的 API 请求和响应，找到真实的 API 端点")
            print("   然后更新连接器代码")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()
            print("\n👋 浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(enhanced_shanghai_listen())
