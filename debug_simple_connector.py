#!/usr/bin/env python3
"""
调试：为什么成都、西安、天津无法获取数
"""
import subprocess
import re

# 测试中国土地市场网是否真的有这些城市的数据
BASE_URL = "https://landchina.mnr.gov.cn/land/cjgs"
CATEGORIES = ['xycr', 'hbgd', 'zbcr', 'gpcr', 'pmcr']

cities = ['成都', '西安', '天津', '武汉', '重庆']

print("🔍 调试：检查中国土地市场网的数据...")
print("=" * 80)

for city in cities:
    print(f"\n📍 检查城市: {city}")
    print("-" * 80)
    
    all_found = []
    
    for cat in CATEGORIES:
        url = f"{BASE_URL}/{cat}/"
        print(f"   📊 分类: {cat}")
        
        # 使用 curl 获取 HTML
        try:
            result = subprocess.run(
                ['curl', '-s', '--insecure', '-A', 'Mozilla/5.0', url],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout and len(result.stdout) > 1000:
                html = result.stdout
                
                # 正则：匹配列表项
                pattern = r'<li>\s*<span>([^<]+)</span>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
                matches = re.findall(pattern, html)
                
                # 过滤包含城市名的数据
                city_data = [m for m in matches if city in m[2]]
                
                print(f"      总数据: {len(matches)} 条, 包含 '{city}' 的数据: {len(city_data)} 条")
                
                if city_data:
                    print(f"      样本: {city_data[0][2][:60]}")
                    all_found.extend(city_data)
                else:
                    # 如果没有匹配，打印前几条数据看看格式
                    if matches:
                        print(f"      样本数据（不含城市名）:")
                        for i, m in enumerate(matches[:3], 1):
                            print(f"         {i}. {m[2][:60]}")
            else:
                print(f"      ❌ 获取失败或HTML太短")
        
        except Exception as e:
            print(f"      ❌ 错误: {e}")
    
    if all_found:
        print(f"\n   ✅ {city} 共有 {len(all_found)} 条数据")
    else:
        print(f"\n   ⚠️  {city} 在中国土地市场网上未找到数据")
        print(f"   💡 建议：找到 {city} 本地官网，编写完整连接器")

print("\n" + "=" * 80)
print("🔍 调试完成!")
