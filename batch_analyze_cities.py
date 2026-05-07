#!/usr/bin/env python3
"""
批量城市土地市场分析器
自动分析所有城市的网站结构，输出可复用的连接器配置
"""
import asyncio
import json
import re
from typing import Dict, List, Optional
from playwright.async_api import async_playwright


async def analyze_city_website(city_name: str, url: str) -> Dict:
    """
    分析单个城市的土地市场网站
    
    返回：
    {
        'city': city_name,
        'url': url,
        'success': True/False,
        'page_structure': {...},  # 页面结构分析
        'list_pattern': 'regex pattern',  # 列表匹配模式
        'sample_data': [...]  # 样本数据
    }
    """
    print(f"\n🔍 分析 {city_name}: {url}")
    
    result = {
        'city': city_name,
        'url': url,
        'success': False,
        'page_structure': {},
        'list_pattern': None,
        'sample_data': []
    }
    
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
            # 访问页面
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(3000)
            
            # 获取 HTML
            html = await page.content()
            print(f"   ✅ HTML 长度: {len(html)} 字符")
            
            # 分析页面结构
            # 1. 检查是否有日期模式
            date_pattern = r'20\d{2}-\d{2}-\d{2}'
            dates = re.findall(date_pattern, html)
            has_dates = len(dates) > 0
            print(f"   日期数量: {len(dates)}")
            
            # 2. 检查是否有列表项
            li_count = html.count('<li')
            print(f"   <li> 数量: {li_count}")
            
            # 3. 检查是否有表格
            tr_count = html.count('<tr')
            print(f"   <tr> 数量: {tr_count}")
            
            # 4. 提取样本数据
            sample_data = []
            
            if has_dates and (li_count > 5 or tr_count > 5):
                # 使用 JavaScript 提取列表数据
                sample_data = await page.evaluate("""
                    () => {
                        const results = [];
                        
                        // 尝试查找包含日期的列表项
                        const items = document.querySelectorAll('li, tr');
                        
                        for (const item of items) {
                            const text = item.innerText || '';
                            
                            // 检查是否包含日期和土地关键词
                            if (/20\\d{2}-\\d{2}-\\d{2}/.test(text) && 
                                (text.includes('地块') || text.includes('出让') || text.includes('成交'))) {
                                
                                const link = item.querySelector('a');
                                const dateMatch = text.match(/20\\d{2}-\\d{2}-\\d{2}/);
                                
                                results.push({
                                    title: link ? link.innerText.trim() : text.substring(0, 50),
                                    url: link ? link.href : '',
                                    date: dateMatch ? dateMatch[0] : '',
                                    raw_text: text.substring(0, 100)
                                });
                                
                                if (results.length >= 5) break;
                            }
                        }
                        
                        return results;
                    }
                """)
                
                print(f"   样本数据: {len(sample_data)} 条")
            
            # 5. 判断网站类型
            is_dynamic = await page.evaluate("""
                () => {
                    // 检查是否有 XHR/fetch 请求（动态加载）
                    return window.performance.getEntriesByType('resource')
                        .some(r => r.initiatorType === 'xmlhttprequest' || r.initiatorType === 'fetch');
                }
            """)
            
            result['success'] = len(sample_data) > 0
            result['page_structure'] = {
                'has_dates': has_dates,
                'li_count': li_count,
                'tr_count': tr_count,
                'is_dynamic': is_dynamic,
                'html_length': len(html)
            }
            result['sample_data'] = sample_data
            
            # 6. 生成建议的正则模式
            if sample_data:
                # 基于样本数据生成正则
                result['list_pattern'] = 'generated from sample'
            
        except Exception as e:
            print(f"   ❌ 分析失败: {e}")
            result['error'] = str(e)
        
        await browser.close()
    
    return result


async def batch_analyze_cities():
    """批量分析所有城市"""
    
    # 城市列表（需要分析的）
    cities = [
        ("成都", "https://www.cdggzy.com/"),
        ("西安", "https://www.xa.gov.cn/"),  # 需要搜索实际土地交易页面
        ("武汉", "https://www.whtdsc.com/"),  # 武汉土地市场网
        ("天津", "https://www.tj.gov.cn/"),  # 需要搜索实际土地交易页面
        ("重庆", "https://www.cq.gov.cn/"),  # 需要搜索实际土地交易页面
    ]
    
    results = []
    
    for city_name, url in cities:
        result = await analyze_city_website(city_name, url)
        results.append(result)
        
        # 保存中间结果
        with open(f'/Users/tianguobao/WorkBuddy/Claw/{city_name}_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"   💾 分析结果已保存: {city_name}_analysis.json")
    
    # 保存汇总结果
    summary_path = '/Users/tianguobao/WorkBuddy/Claw/batch_analysis_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 汇总结果已保存: {summary_path}")
    
    return results


if __name__ == '__main__':
    print("🚀 启动批量城市土地市场分析器")
    print("=" * 80)
    
    results = asyncio.run(batch_analyze_cities())
    
    print("\n" + "=" * 80)
    print("✅ 批量分析完成!")
    print(f"   成功: {sum(1 for r in results if r['success'])} 个城市")
    print(f"   失败: {sum(1 for r in results if not r['success'])} 个城市")
