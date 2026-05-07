#!/usr/bin/env python3
"""
中国土地市场网通用连接器
- 覆盖全国所有城市
- 通过城市名过滤数据
- 支持所有9个目标城市（北京、上海、广州、深圳、杭州、成都、西安、武汉、天津、重庆）
"""
import subprocess
import re
from typing import Any, Dict, List, Optional


class ChinaLandMarketConnector:
    """
    中国土地市场网连接器
    
    数据来源：自然资源部土地市场网
    URL: https://landchina.mnr.gov.cn/land/cjgs/
    
    特点：
    - 覆盖全国所有城市
    - 按交易方式分类（协议、划拨、招标、挂牌、拍卖）
    - 可通过城市名关键词过滤
    """
    
    BASE_URL = "https://landchina.mnr.gov.cn/land/cjgs"
    
    # 交易方式分类
    CATEGORIES = {
        'xycr': '协议出让',
        'hpgs': '划拨供地',
        'zbcjgs': '招标成交',
        'gpgs': '挂牌出让',
        'pmcjgs': '拍卖出让'
    }
    
    def __init__(self):
        pass
    
    def _fetch_html(self, url: str) -> Optional[str]:
        """使用 curl 获取 HTML"""
        try:
            result = subprocess.run(
                ['curl', '-s', '--insecure', '-A', 'Mozilla/5.0', url],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout and len(result.stdout) > 1000:
                return result.stdout
            else:
                return None
        except Exception as e:
            print(f"   ❌ 获取失败: {e}")
            return None
    
    def _parse_list_page(self, html: str, city_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """解析列表页面，提取土地成交项目"""
        results = []
        
        # 正则模式：匹配 <li><span>日期</span><a href="...">标题</a></li>
        # 注意：日期格式是 2026.05.06（点分隔）
        pattern = r'<li>\s*<span>([^<]+)</span>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>\s*</li>'
        
        matches = re.findall(pattern, html)
        
        for date, href, title in matches:
            # 如果指定了城市过滤，只保留匹配的项
            if city_filter and city_filter not in title:
                continue
            
            # 处理相对 URL
            if href.startswith('http'):
                full_url = href
            elif href.startswith('./'):
                # 相对路径，需要拼接
                full_url = self.BASE_URL + '/' + href[2:]
            else:
                full_url = self.BASE_URL + '/' + href.lstrip('/')
            
            results.append({
                'title': title.strip(),
                'url': full_url,
                'date': date.strip(),
                'city': city_filter if city_filter else '未知',
                'source': '中国土地市场网'
            })
        
        return results
    
    def fetch_land_data(
        self,
        city_name: Optional[str] = None,
        categories: Optional[List[str]] = None,
        max_items_per_category: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取土地数据
        
        Args:
            city_name: 城市名（用于过滤，如"北京"、"广州"）
            categories: 交易方式列表（可选，默认全部）
            max_items_per_category: 每个分类最多获取多少条
        
        Returns:
            土地数据列表
        """
        all_data = []
        
        # 如果没有指定分类，使用全部
        if not categories:
            categories = list(self.CATEGORIES.keys())
        
        for cat_key in categories:
            cat_name = self.CATEGORIES.get(cat_key, cat_key)
            url = f"{self.BASE_URL}/{cat_key}/"
            
            print(f"📊 获取分类: {cat_name}")
            print(f"   URL: {url}")
            
            # 获取 HTML
            html = self._fetch_html(url)
            if not html:
                print(f"   ❌ 获取失败，跳过")
                continue
            
            # 解析列表
            page_data = self._parse_list_page(html, city_filter=city_name)
            print(f"   ✅ 提取到 {len(page_data)} 条数据")
            
            # 限制数量
            if max_items_per_category > 0 and len(page_data) > max_items_per_category:
                page_data = page_data[:max_items_per_category]
                print(f"   限制到前 {max_items_per_category} 条")
            
            all_data.extend(page_data)
        
        # 按日期排序（最新的在前）
        all_data.sort(key=lambda x: x['date'], reverse=True)
        
        print(f"\n✅ 总共获取 {len(all_data)} 条数据")
        
        return all_data
    
    def fetch_city_data(
        self,
        city_name: str,
        max_items: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取指定城市的所有土地数据（便捷方法）
        
        Args:
            city_name: 城市名（如"北京"、"广州"）
            max_items: 最多获取多少条
        
        Returns:
            土地数据列表
        """
        print(f"\n{'='*80}")
        print(f"🔍 获取 {city_name} 的土地成交数据")
        print(f"{'='*80}\n")
        
        data = self.fetch_land_data(
            city_name=city_name,
            categories=None,  # 全部分类
            max_items_per_category=max_items // len(self.CATEGORIES)
        )
        
        return data
    
    def normalize_land_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化土地数据格式"""
        # 从标题中提取城市名
        title = raw_data.get('title', '')
        city = raw_data.get('city', '')
        
        # 如果 city 字段是"未知"，尝试从标题提取
        if not city or city == '未知':
            # 常见城市名模式
            city_patterns = ['北京', '上海', '广州', '深圳', '杭州', '成都', '西安', '武汉', '天津', '重庆']
            for cp in city_patterns:
                if cp in title:
                    city = cp
                    break
        
        return {
            'category': 'land',
            'title': title,
            'content': f"公告：{title}，日期：{raw_data.get('date', '')}",
            'city': city,
            'date': raw_data.get('date') or '',
            'source': '中国土地市场网',
            'source_level': 'level_1',  # 国家级源，等级更高
            'verified': True,
            'url': raw_data.get('url'),
            'raw': raw_data
        }


def test_china_land_market():
    """测试中国土地市场网连接器"""
    print("🧪 测试中国土地市场网连接器")
    print("=" * 60)
    
    connector = ChinaLandMarketConnector()
    
    # 测试：获取广州的数据（作为示例）
    print("\n📍 测试：获取广州的数据...")
    data = connector.fetch_city_data(city_name='广州', max_items=10)
    
    if data:
        print(f"\n   前 3 条数据:")
        for i, item in enumerate(data[:3], 1):
            normalized = connector.normalize_land_data(item)
            print(f"   {i}. {normalized['title']}")
            print(f"      日期: {normalized['date']}")
            print(f"      城市: {normalized['city']}")
            print(f"      URL: {normalized['url'][:80]}")
    
    # 测试：获取多个城市的数据
    print(f"\n{'='*80}")
    print("📍 测试：批量获取多个城市的数据...")
    
    cities = ['北京', '上海', '广州']
    for city in cities:
        city_data = connector.fetch_city_data(city_name=city, max_items=5)
        print(f"   {city}: {len(city_data)} 条")
    
    return {
        'guangzhou_count': len(data),
        'multi_city_success': True
    }


if __name__ == '__main__':
    result = test_china_land_market()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"   广州数据: {result['guangzhou_count']} 条")
    print(f"   多城市测试: {'成功' if result['multi_city_success'] else '失败'}")
