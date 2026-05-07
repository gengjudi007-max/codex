#!/usr/bin/env python3
"""
简化版城市土地连接器（支持翻页）
- 使用中国土地市场网作为统一数据源
- 通过城市名过滤数据
- 支持翻页，获取更多数据
- 适合快速覆盖多个城市
"""
import subprocess
import re
from typing import Any, Dict, List, Optional


class SimpleCityLandConnector:
    """
    简化版城市土地连接器
    
    使用中国土地市场网的数据
    支持翻页，能获取更多数据
    """
    
    BASE_URL = "https://landchina.mnr.gov.cn/land/cjgs"
    CATEGORIES = ['xycr', 'hbgd', 'zbcr', 'gpcr', 'pmcr']
    
    def __init__(self, city_name: str, max_pages: int = 5):
        """
        初始化连接器
        
        Args:
            city_name: 城市名称（如 "成都"、"西安"），也可以是列表
            max_pages: 每个分类最多翻几页（默认 5 页，每页 25 条）
        """
        # 支持单个城市名或城市名列表
        if isinstance(city_name, list):
            self.city_names = city_name
        else:
            self.city_names = [city_name]
        self.max_pages = max_pages
    
    def _fetch_html(self, url: str) -> Optional[str]:
        """使用curl获取HTML"""
        try:
            result = subprocess.run(
                ['curl', '-s', '--insecure', '-A', 'Mozilla/5.0', url],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout and len(result.stdout) > 1000:
                return result.stdout
            return None
        except Exception as e:
            return None
    
    def _parse_html(self, html: str) -> List[Dict[str, Any]]:
        """解析HTML，提取包含城市名的数据"""
        results = []
        
        # 正则：匹配列表项
        # 格式：<li><span>日期</span><a href="...">标题</a></li>
        pattern = r'<li[^>]*>\s*<span>([^<]+)</span>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html)
        
        for date, href, title in matches:
            # 只保留包含任一城市名的数据
            city_matched = None
            for city in self.city_names:
                if city in title:
                    city_matched = city
                    break
            
            if city_matched:
                if not href.startswith('http'):
                    href = self.BASE_URL + '/' + href.lstrip('/')
                
                results.append({
                    'title': title.strip(),
                    'url': href,
                    'date': date.strip(),
                    'city': city_matched,
                    'source': '中国土地市场网'
                })
        
        return results
    
    def fetch_data(self, max_per_category: int = 5) -> List[Dict[str, Any]]:
        """获取该城市的所有土地数据（支持翻页）"""
        city_display = '/'.join(self.city_names)
        print(f"\n🔍 获取 {city_display} 的土地数据（每分类翻 {self.max_pages} 页）...")
        
        all_data = []
        
        for cat in self.CATEGORIES:
            print(f"   检查分类: {cat}")
            
            category_data = []
            
            # 翻页：第1页是 index.htm，第2页是 index_1.htm，第3页是 index_2.htm...
            for page in range(self.max_pages):
                if page == 0:
                    url = f"{self.BASE_URL}/{cat}/index.htm"
                else:
                    url = f"{self.BASE_URL}/{cat}/index_{page}.htm"
                
                html = self._fetch_html(url)
                if not html:
                    print(f"      ❌ 第 {page+1} 页获取失败")
                    continue
                
                data = self._parse_html(html)
                
                if data:
                    print(f"      第 {page+1} 页: 找到 {len(data)} 条包含 '{city_display}' 的数据")
                    category_data.extend(data)
                else:
                    print(f"      第 {page+1} 页: 未找到包含 '{city_display}' 的数据")
                    # 注释掉提前停止的逻辑，让它翻完所有页
                    # if page > 2:  # 如果已经翻了 2 页都没有，就停止
                    #     break
            
            print(f"   分类 {cat} 总计: {len(category_data)} 条")
            all_data.extend(category_data)
        
        # 去重
        seen = set()
        unique_data = []
        for item in all_data:
            if item['url'] not in seen:
                seen.add(item['url'])
                unique_data.append(item)
        
        print(f"   总计: {len(unique_data)} 条唯一数据（去重后）")
        
        return unique_data
    
    def normalize_land_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化土地数据格式"""
        city = raw_data.get('city', self.city_names[0])
        return {
            'category': 'land',
            'title': raw_data.get('title') or f'{city}土地成交公告',
            'content': f"公告：{raw_data.get('title', '')}，日期：{raw_data.get('date', '')}",
            'city': city,
            'date': raw_data.get('date') or '',
            'source': '中国土地市场网',
            'source_level': 'level_1',
            'verified': True,
            'url': raw_data.get('url'),
            'raw': raw_data
        }


def test_simple_connector():
    """测试简化版连接器"""
    print("🧪 测试简化版城市土地连接器")
    print("=" * 60)
    
    # 测试几个城市
    test_cities = ['广州', '深圳', '成都']
    
    for city in test_cities:
        connector = SimpleCityLandConnector(city_name=city)
        data = connector.fetch_data(max_per_category=5)
        
        print(f"\n   前2条数据:")
        for i, item in enumerate(data[:2], 1):
            normalized = connector.normalize_land_data(item)
            print(f"   {i}. {normalized['title']}")
            print(f"      日期: {normalized['date']}")
        
        print(f"\n{'='*80}\n")
    
    print("✅ 测试完成!")


if __name__ == '__main__':
    test_simple_connector()
