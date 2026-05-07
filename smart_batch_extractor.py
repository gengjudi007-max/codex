#!/usr/bin/env python3
"""
智能批量城市土地数据提取器
- 使用 Playwright 自动加载页面
- 使用 JavaScript 智能识别列表结构
- 无需手动分析 HTML
"""
import asyncio
import json
import re
from typing import Dict, List, Optional
from playwright.async_api import async_playwright


async def smart_extract_city_data(
    city_name: str,
    url: str,
    headless: bool = True
) -> Dict:
    """
    智能提取城市土地数据
    
    策略：
    1. 加载页面
    2. 使用 JS 查找包含"日期+链接"的列表项
    3. 自动识别列表结构
    4. 提取数据
    """
    print(f"\n🔍 智能分析 {city_name}")
    print(f"   URL: {url}")
    print("=" * 80)
    
    result = {
        'city': city_name,
        'url': url,
        'success': False,
        'data_count': 0,
        'sample_data': [],
        'page_type': 'unknown',  # static, dynamic, or unknown
        'notes': ''
    }
    
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
        
        try:
            # 访问页面
            print(f"🌐 加载页面...")
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)
            print(f"✅ 页面加载完成")
            
            # 使用 JavaScript 智能提取数据
            print(f"🧠 智能识别列表结构...")
            
            data = await page.evaluate("""
                () => {
                    const results = [];
                    
                    // 策略1: 查找所有包含日期的列表项
                    const allElements = document.querySelectorAll('*');
                    const dateRegex = /20\\d{2}[-年]\\d{1,2}[-月]\\d{1,2}/;
                    
                    for (const elem of allElements) {
                        const text = elem.innerText || '';
                        
                        // 检查是否包含日期
                        if (dateRegex.test(text)) {
                            // 查找这个元素内的链接
                            const links = elem.querySelectorAll('a');
                            
                            for (const link of links) {
                                const linkText = link.innerText || '';
                                
                                // 检查链接文本是否包含土地关键词
                                if (linkText.includes('地块') || 
                                    linkText.includes('出让') || 
                                    linkText.includes('成交') ||
                                    linkText.includes('挂牌')) {
                                    
                                    const dateMatch = text.match(dateRegex);
                                    
                                    results.push({
                                        title: linkText.trim(),
                                        url: link.href || '',
                                        date: dateMatch ? dateMatch[0] : '',
                                        source_text: text.substring(0, 200)
                                    });
                                    
                                    if (results.length >= 10) break;
                                }
                            }
                            
                            if (results.length >= 10) break;
                        }
                    }
                    
                    return results;
                }
            """)
            
            print(f"✅ 提取到 {len(data)} 条样本数据")
            
            if data:
                result['success'] = True
                result['data_count'] = len(data)
                result['sample_data'] = data
                
                # 显示前3条
                print(f"\n   前 3 条样本:")
                for i, item in enumerate(data[:3], 1):
                    print(f"   {i}. {item['title'][:50]}")
                    print(f"      日期: {item['date']}")
                    print(f"      URL: {item['url'][:80]}")
            
            # 判断页面类型
            is_dynamic = await page.evaluate("""
                () => {
                    return window.performance.getEntriesByType('resource')
                        .some(r => r.initiatorType === 'xmlhttprequest' || 
                               r.initiatorType === 'fetch');
                }
            """)
            
            result['page_type'] = 'dynamic' if is_dynamic else 'static'
            print(f"\n📊 页面类型: {'动态(AJAX)' if is_dynamic else '静态(HTML)'}")
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            result['error'] = str(e)
        
        await browser.close()
    
    return result


async def batch_smart_extract():
    """批量智能提取所有城市"""
    
    # 城市列表（名称，URL）
    # 注意：URL 需要是实际的土地成交结果页面
    cities = [
        ("成都", "https://www.cdggzy.com/"),
        ("西安", "https://www.xa.gov.cn/"),  # 需要找到具体页面
        ("武汉", "https://www.whtdsc.com/"),
        ("天津", "https://www.tj.gov.cn/"),  # 需要找到具体页面
        ("重庆", "https://www.cq.gov.cn/"),  # 需要找到具体页面
    ]
    
    results = []
    
    for city_name, url in cities:
        result = await smart_extract_city_data(city_name, url, headless=True)
        results.append(result)
        
        # 保存单个结果
        output_path = f'/Users/tianguobao/WorkBuddy/Claw/{city_name}_smart_analysis.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 分析结果已保存: {output_path}\n")
    
    # 保存汇总
    summary_path = '/Users/tianguobao/WorkBuddy/Claw/batch_smart_analysis.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ 批量分析完成!")
    print(f"   成功: {sum(1 for r in results if r['success'])} 个城市")
    print(f"   失败: {sum(1 for r in results if not r['success'])} 个城市")
    print(f"💾 汇总结果: {summary_path}")
    
    return results


if __name__ == '__main__':
    print("🚀 启动智能批量城市土地数据提取器")
    print("=" * 80)
    
    results = asyncio.run(batch_smart_extract())
