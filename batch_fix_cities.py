#!/usr/bin/env python3
"""
批量修复剩余城市连接器
- 使用 Playwright + JavaScript 智能提取
- 无需手动分析 HTML
- 一次性处理：成都、西安、武汉、天津、重庆
"""
import asyncio
import json
from typing import Any, Dict, List
from playwright.async_api import async_playwright


# 城市配置
CITIES = [
    {
        'name': '成都',
        'url': 'https://www.cdggzy.com/',  # 成都公共资源交易服务中心
        'search_keywords': ['地块', '出让', '成交', '矿权']
    },
    {
        'name': '西安',
        'url': 'https://www.xa.gov.cn/',  # 西安市人民政府（需要找到土地交易页面）
        'search_keywords': ['地块', '出让', '成交', '交易']
    },
    {
        'name': '武汉',
        'url': 'https://www.whtdsc.com/',  # 武汉土地市场网
        'search_keywords': ['地块', '出让', '成交', '公示']
    },
    {
        'name': '天津',
        'url': 'https://www.tj.gov.cn/',  # 天津市政府（需要找到土地交易页面）
        'search_keywords': ['地块', '出让', '成交', '交易']
    },
    {
        'name': '重庆',
        'url': 'https://www.cq.gov.cn/',  # 重庆市政府（需要找到土地交易页面）
        'search_keywords': ['地块', '出让', '成交', '交易']
    },
]


async def smart_extract_land_data(page, city_config: Dict) -> List[Dict[str, Any]]:
    """
    智能提取土地数据（通用方法）
    
    策略：
    1. 等待页面加载
    2. 查找包含"地块"、"出让"等关键词的链接
    3. 提取标题、URL、日期
    """
    keywords = city_config['search_keywords']
    
    # 使用 JavaScript 智能提取
    data = await page.evaluate("""
        (keywords) => {
            const results = [];
            const dateRegex = /20\\d{2}[.\\-]\\d{1,2}[.\\-]\\d{1,2}/;
            
            // 查找所有链接
            const allLinks = document.querySelectorAll('a');
            
            for (const link of allLinks) {
                const text = link.innerText || '';
                const href = link.href || '';
                
                // 检查是否包含土地关键词
                const hasKeyword = keywords.some(kw => text.includes(kw));
                if (!hasKeyword) continue;
                
                // 检查是否包含日期
                const dateMatch = text.match(dateRegex);
                if (!dateMatch) {
                    // 在父元素中查找日期
                    const parent = link.parentElement;
                    if (parent) {
                        const parentText = parent.innerText || '';
                        const parentDateMatch = parentText.match(dateRegex);
                        if (parentDateMatch) {
                            results.push({
                                title: text.trim(),
                                url: href,
                                date: parentDateMatch[0],
                                source_text: parentText.substring(0, 200)
                            });
                            if (results.length >= 20) break;
                            continue;
                        }
                    }
                    continue;
                }
                
                results.push({
                    title: text.trim(),
                    url: href,
                    date: dateMatch[0],
                    source_text: text.substring(0, 200)
                });
                
                if (results.length >= 20) break;
            }
            
            return results;
        }
    """, keywords)
    
    # 添加城市信息
    for item in data:
        item['city'] = city_config['name']
        item['source'] = f"{city_config['name']}土地市场"
    
    return data


async def process_city(city_config: Dict, headless: bool = True) -> Dict:
    """处理单个城市"""
    city_name = city_config['name']
    url = city_config['url']
    
    print(f"\n{'='*80}")
    print(f"🔍 处理城市: {city_name}")
    print(f"   URL: {url}")
    print(f"{'='*80}\n")
    
    result = {
        'city': city_name,
        'url': url,
        'success': False,
        'data_count': 0,
        'sample_data': []
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
            print(f"🌐 访问页面...")
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)
            print(f"✅ 页面加载完成")
            
            # 智能提取数据
            print(f"🧠 智能提取数据...")
            data = await smart_extract_land_data(page, city_config)
            
            print(f"✅ 提取到 {len(data)} 条数据")
            
            if data:
                result['success'] = True
                result['data_count'] = len(data)
                result['sample_data'] = data[:5]
                
                # 显示前3条
                print(f"\n   前 3 条样本:")
                for i, item in enumerate(data[:3], 1):
                    print(f"   {i}. {item['title'][:50]}")
                    print(f"      日期: {item['date']}")
                    print(f"      URL: {item['url'][:80]}")
            else:
                print(f"   ⚠️  未提取到数据，可能需要点击进入子页面")
                
                # 尝试查找"成交公示"、"出让公告"等链接并点击
                print(f"   🔍 尝试查找土地交易相关链接...")
                
                clicked = await page.evaluate("""
                    () => {
                        const keywords = ['成交', '出让', '交易', '地块'];
                        const links = document.querySelectorAll('a');
                        
                        for (const link of links) {
                            const text = link.innerText || '';
                            if (keywords.some(kw => text.includes(kw))) {
                                link.click();
                                return link.href;
                            }
                        }
                        return null;
                    }
                """)
                
                if clicked:
                    print(f"   ✅ 点击了链接: {clicked}")
                    await page.wait_for_timeout(5000)
                    
                    # 重新提取
                    data = await smart_extract_land_data(page, city_config)
                    print(f"   ✅ 重新提取到 {len(data)} 条数据")
                    
                    if data:
                        result['success'] = True
                        result['data_count'] = len(data)
                        result['sample_data'] = data[:5]
            
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
            result['error'] = str(e)
        
        await browser.close()
    
    return result


async def batch_process_cities():
    """批量处理所有城市"""
    print("🚀 启动批量城市处理器")
    print("=" * 80)
    
    results = []
    
    for city_config in CITIES:
        result = await process_city(city_config, headless=True)
        results.append(result)
        
        # 保存中间结果
        output_path = f'/Users/tianguobao/WorkBuddy/Claw/{city_config["name"]}_final.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"💾 结果已保存: {output_path}\n")
    
    # 保存汇总
    summary_path = '/Users/tianguobao/WorkBuddy/Claw/batch_final_results.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ 批量处理完成!")
    print(f"   成功: {sum(1 for r in results if r['success'])} 个城市")
    print(f"   失败: {sum(1 for r in results if not r['success'])} 个城市")
    print(f"💾 汇总结果: {summary_path}")
    
    return results


if __name__ == '__main__':
    print("🚀 启动批量城市土地数据提取器")
    print("=" * 80)
    
    results = asyncio.run(batch_process_cities())
