#!/usr/bin/env python3
"""
跑通测试：所有城市的土地数据连接器
测试北京、上海、广州、深圳、杭州、成都、西安、武汉、天津、重庆
"""
import sys
import os
import subprocess
import json
from typing import Any, Dict, List, Optional

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 80)
print("🧪 跑通测试：所有城市土地数据连接器")
print("=" * 80)

# 测试结果
test_results = {}

# ========== 1. 测试北京 ==========
print("\n📍 1. 测试北京连接器 (beijing_api)...")
print("-" * 80)

try:
    # 北京连接器使用函数式接口，不是类
    from codex.connectors.beijing_land_connector import fetch_beijing_land_items
    
    # 获取前 1 页，每页 10 条
    data = fetch_beijing_land_items(max_pages=1, limit=10)
    
    if data:
        print(f"   ✅ 成功获取 {len(data)} 条数据")
        print(f"   前 3 条:")
        for i, item in enumerate(data[:3], 1):
            print(f"   {i}. {item.get('title', '')[:60]}")
            print(f"      日期: {item.get('date', '')}")
        
        test_results['北京'] = {
            'status': '✅ 成功',
            'count': len(data),
            'sample': data[0] if data else None
        }
    else:
        print(f"   ⚠️  获取成功但未解析到数据")
        test_results['北京'] = {
            'status': '⚠️ 无数据',
            'count': 0
        }
        
except Exception as e:
    print(f"   ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    test_results['北京'] = {
        'status': f'❌ 失败: {e}',
        'count': 0
    }

# ========== 2. 测试上海 ==========
print("\n📍 2. 测试上海连接器 (shanghai_playwright)...")
print("-" * 80)

try:
    from codex.connectors.shanghai_land_connector import ShanghaiLandConnector
    import asyncio
    
    async def test_shanghai():
        connector = ShanghaiLandConnector(headless=True)
        await connector.init_browser()
        
        try:
            # 上海连接器不支持 max_pages，只获取 1 页
            data = await connector.fetch_land_data(page_num=1, page_size=10)
            return data
        finally:
            await connector.close()
    
    data = asyncio.run(test_shanghai())
    
    if data:
        print(f"   ✅ 成功获取 {len(data)} 条数据")
        print(f"   前 3 条:")
        for i, item in enumerate(data[:3], 1):
            # 上海连接器返回的数据格式可能不同，需要检查
            if isinstance(item, dict):
                title = item.get('title', item.get('地块名称', ''))
                date = item.get('date', item.get('成交时间', ''))
                print(f"   {i}. {title[:60]}")
                print(f"      日期: {date}")
        
        test_results['上海'] = {
            'status': '✅ 成功',
            'count': len(data),
            'sample': data[0] if data else None
        }
    else:
        print(f"   ⚠️  获取成功但未解析到数据")
        test_results['上海'] = {
            'status': '⚠️ 无数据',
            'count': 0
        }
        
except Exception as e:
    print(f"   ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    test_results['上海'] = {
        'status': f'❌ 失败: {e}',
        'count': 0
    }

# ========== 3. 测试广州 ==========
print("\n📍 3. 测试广州连接器 (guangzhou_curl_regex)...")
print("-" * 80)

try:
    from codex.connectors.guangzhou_land_connector import GuangzhouLandConnector
    
    connector = GuangzhouLandConnector()
    data = connector.fetch_land_data(page_num=1, max_pages=1)
    
    if data:
        print(f"   ✅ 成功获取 {len(data)} 条数据")
        print(f"   前 3 条:")
        for i, item in enumerate(data[:3], 1):
            normalized = connector.normalize_land_data(item)
            print(f"   {i}. {normalized['title'][:60]}")
            print(f"      日期: {normalized['date']}")
        
        test_results['广州'] = {
            'status': '✅ 成功',
            'count': len(data),
            'sample': data[0] if data else None
        }
    else:
        print(f"   ⚠️  获取成功但未解析到数据")
        test_results['广州'] = {
            'status': '⚠️ 无数据',
            'count': 0
        }
        
except Exception as e:
    print(f"   ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    test_results['广州'] = {
        'status': f'❌ 失败: {e}',
        'count': 0
    }

# ========== 4. 测试深圳 ==========
print("\n📍 4. 测试深圳连接器 (shenzhen_curl_regex)...")
print("-" * 80)

try:
    from codex.connectors.shenzhen_land_connector import ShenzhenLandConnector
    
    connector = ShenzhenLandConnector()
    data = connector.fetch_land_data(page_num=1, max_pages=1)
    
    if data:
        print(f"   ✅ 成功获取 {len(data)} 条数据")
        print(f"   前 3 条:")
        for i, item in enumerate(data[:3], 1):
            normalized = connector.normalize_land_data(item)
            print(f"   {i}. {normalized['title'][:60]}")
            print(f"      日期: {normalized['date']}")
        
        test_results['深圳'] = {
            'status': '✅ 成功',
            'count': len(data),
            'sample': data[0] if data else None
        }
    else:
        print(f"   ⚠️  获取成功但未解析到数据")
        test_results['深圳'] = {
            'status': '⚠️ 无数据',
            'count': 0
        }
        
except Exception as e:
    print(f"   ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    test_results['深圳'] = {
        'status': f'❌ 失败: {e}',
        'count': 0
    }

# ========== 5. 测试杭州 ==========
print("\n📍 5. 测试杭州连接器 (hangzhou_curl_regex)...")
print("-" * 80)

try:
    from codex.connectors.hangzhou_land_connector import HangzhouLandConnector
    
    connector = HangzhouLandConnector()
    data = connector.fetch_land_data(page_num=1, max_pages=1)
    
    if data:
        print(f"   ✅ 成功获取 {len(data)} 条数据")
        print(f"   前 3 条:")
        for i, item in enumerate(data[:3], 1):
            normalized = connector.normalize_land_data(item)
            print(f"   {i}. {normalized['title'][:60]}")
            print(f"      日期: {normalized['date']}")
        
        test_results['杭州'] = {
            'status': '✅ 成功',
            'count': len(data),
            'sample': data[0] if data else None
        }
    else:
        print(f"   ⚠️  获取成功但未解析到数据")
        test_results['杭州'] = {
            'status': '⚠️ 无数据',
            'count': 0
        }
        
except Exception as e:
    print(f"   ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    test_results['杭州'] = {
        'status': f'❌ 失败: {e}',
        'count': 0
    }

# ========== 6. 测试简化版城市（成都、西安、武汉、天津、重庆）==========
print("\n📍 6. 测试简化版连接器 (china_land_market)...")
print("-" * 80)
print("   这些城市使用中国土地市场网，数据较少（1-3 条/城市）")
print("-" * 80)

simple_cities = ['成都', '西安', '武汉', '天津', '重庆']

for city in simple_cities:
    print(f"\n   📍 测试 {city}...")
    
    try:
        from codex.connectors.simple_city_land_connector import SimpleCityLandConnector
        
        connector = SimpleCityLandConnector(city_name=city)
        # 简化版连接器使用 fetch_data() 方法，不是 fetch_land_data()
        data = connector.fetch_data(max_per_category=3)
        
        if data:
            print(f"      ✅ 成功获取 {len(data)} 条数据")
            if data:
                normalized = connector.normalize_land_data(data[0])
                print(f"      样本: {normalized['title'][:60]}")
            
            test_results[city] = {
                'status': '✅ 成功',
                'count': len(data)
            }
        else:
            print(f"      ⚠️  获取成功但未解析到数据")
            test_results[city] = {
                'status': '⚠️ 无数据',
                'count': 0
            }
            
    except Exception as e:
        print(f"      ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        test_results[city] = {
            'status': f'❌ 失败: {e}',
            'count': 0
        }

# ========== 打印测试报告 ==========
print("\n" + "=" * 80)
print("📊 测试报告")
print("=" * 80)

print(f"\n{'城市':<10} {'状态':<20} {'数据条数':<10}")
print("-" * 80)

total_count = 0
success_count = 0

for city, result in test_results.items():
    status = result['status']
    count = result['count']
    total_count += count
    
    if '✅' in status:
        success_count += 1
    
    print(f"{city:<10} {status:<20} {count:<10}")

print("-" * 80)
print(f"\n📈 统计:")
print(f"   - 测试城市数: {len(test_results)}")
print(f"   - 成功城市数: {success_count}/{len(test_results)}")
print(f"   - 总数据条数: {total_count}")

print("\n" + "=" * 80)
print("✅ 跑通测试完成!")
print("=" * 80)

# 保存测试结果
output_file = '/Users/tianguobao/WorkBuddy/Claw/test_all_connectors_result.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(test_results, f, ensure_ascii=False, indent=2)

print(f"\n💾 测试结果已保存到: {output_file}")
