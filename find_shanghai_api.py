#!/usr/bin/env python3
"""
上海土地市场 - 完整网络监听
监听所有请求，找到真实的 API 端点
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def find_shanghai_api():
    """找到上海土地市场的真实 API 端点"""
    print("🚀 启动上海土地市场 API 搜索...")
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
        
        # 监听所有请求
        async def log_request(request):
            url = request.url
            all_requests.append({
                'url': url,
                'method': request.method,
                'headers': dict(request.headers),
                'post_data': request.post_data
            })
        
        # 监听所有响应
        async def log_response(response):
            url = response.url
            
            try:
                status = response.status
                headers = dict(response.headers)
                
                # 只记录可能有数据的响应
                content_type = headers.get('content-type', '')
                
                all_responses.append({
                    'url': url,
                    'status': status,
                    'content_type': content_type
                })
                
                # 打印可能的 API 响应
                if any(keyword in url.lower() for keyword in ['api', 'list', 'query', 'data', 'result']):
                    print(f"\n✅ [响应] {url}")
                    print(f"   状态: {status}")
                    try:
                        body = await response.text()
                        print(f"   长度: {len(body)}")
                        print(f"   预览: {body[:300]}")
                        
                        # 如果是 JSON，解析并打印结构
                        try:
                            json_data = json.loads(body)
                            print(f"   JSON 键: {list(json_data.keys()) if isinstance(json_data, dict) else 'array'}")
                        except:
                            pass
                    except:
                        pass
            except Exception as e:
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
            
            # 查找并点击所有可能的按钮
            print("\n🔍 查找可点击的元素...")
            
            # 查找所有按钮和链接
            buttons = await page.query_selector_all('button, input[type="button"], input[type="submit"], a')
            print(f"   找到 {len(buttons)} 个可点击元素")
            
            # 尝试点击包含"查询"的按钮
            for i, btn in enumerate(buttons):
                try:
                    text = await btn.inner_text()
                    if '查询' in text or '搜索' in text:
                        print(f"   ✅ 找到按钮: {text}")
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
            
            # 列出所有包含关键字的请求
            api_requests = [r for r in all_requests if any(k in r['url'].lower() for k in ['api', 'list', 'query', 'data', 'result', 'page'])]
            if api_requests:
                print(f"\n📡 包含关键字的请求 ({len(api_requests)} 个):")
                for req in api_requests[:20]:  # 只显示前 20 个
                    print(f"   {req['method']} {req['url'][:150]}")
                    if req['post_data']:
                        print(f"      数据: {req['post_data'][:200]}")
            
            # 列出所有包含关键字的响应
            api_responses = [r for r in all_responses if any(k in r['url'].lower() for k in ['api', 'list', 'query', 'data', 'result', 'page'])]
            if api_responses:
                print(f"\n✅ 包含关键字的响应 ({len(api_responses)} 个):")
                for resp in api_responses[:20]:  # 只显示前 20 个
                    print(f"   {resp['status']} {resp['url'][:150]}")
            
            print("\n" + "=" * 60)
            print("💡 提示:")
            print("   查看上面的请求和响应，找到真实的 API 端点")
            print("   然后更新连接器代码")
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()
            print("\n👋 浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(find_shanghai_api())
