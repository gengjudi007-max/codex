#!/usr/bin/env python3
"""
批量扩展更多城市的土地数据连接器
使用简化版连接器（支持翻页）
"""
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from codex.connectors.simple_city_land_connector import SimpleCityLandConnector

# 需要扩展的重点城市
NEW_CITIES = [
    '南京', '苏州', '厦门', '郑州', '青岛',
    '宁波', '无锡', '佛山', '东莞', '昆明',
    '合肥', '福州', '济南', '沈阳', '长春',
    '哈尔滨', '石家庄', '太原', '兰州', '西宁'
]

print("=" * 80)
print("🚀 批量扩展城市土地数据连接器")
print("=" * 80)
print(f"计划扩展城市数: {len(NEW_CITIES)}")
print(f"使用连接器: SimpleCityLandConnector (翻页模式)")
print("=" * 80)

# 测试结果
results = {}

for i, city in enumerate(NEW_CITIES, 1):
    print(f"\n📍 {i}/{len(NEW_CITIES)} 测试城市: {city}")
    print("-" * 80)
    
    try:
        connector = SimpleCityLandConnector(city_name=city, max_pages=5)
        data = connector.fetch_data()
        
        if data and len(data) > 0:
            print(f"   ✅ 成功获取 {len(data)} 条数据")
            print(f"   样本: {data[0]['title'][:60]}")
            
            results[city] = {
                'status': '✅ 成功',
                'count': len(data),
                'sample': data[0]['title'][:60]
            }
        else:
            print(f"   ⚠️  未找到数据（可能需要编写完整连接器）")
            results[city] = {
                'status': '⚠️ 无数据',
                'count': 0
            }
    
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        results[city] = {
            'status': f'❌ 失败: {str(e)[:50]}',
            'count': 0
        }

# 打印汇总报告
print("\n" + "=" * 80)
print("📊 扩展结果汇总")
print("=" * 80)

print(f"\n{'序号':<6} {'城市':<10} {'状态':<20} {'数据条数':<10} {'样本'}")
print("-" * 80)

success_count = 0
total_count = 0

for i, (city, result) in enumerate(results.items(), 1):
    status = result['status']
    count = result['count']
    sample = result.get('sample', '')
    
    if '✅' in status:
        success_count += 1
        total_count += count
    
    print(f"{i:<6} {city:<10} {status:<20} {count:<10} {sample}")

print("-" * 80)
print(f"\n📈 统计:")
print(f"   - 扩展城市数: {len(NEW_CITIES)}")
print(f"   - 成功城市数: {success_count}/{len(NEW_CITIES)}")
print(f"   - 总数据条数: {total_count}")

# 保存结果
import json
output_file = '/Users/tianguobao/WorkBuddy/Claw/expand_cities_result.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n💾 结果已保存到: {output_file}")

print("\n" + "=" * 80)
if success_count == len(NEW_CITIES):
    print("🎉 完美！所有城市都成功获取数据！")
else:
    print(f"⚠️  有 {len(NEW_CITIES) - success_count} 个城市需要编写完整连接器")
    print("   建议：为这些城市找到本地官网，参考广州/深圳/杭州的模式")
print("=" * 80)
