#!/usr/bin/env python3
"""
全国土地市场网数据连接器 (api.landchina.com)
统一获取所有城市的土地数据
"""
import requests
import json
from typing import Any, Dict, List, Optional


BASE_URL = "https://api.landchina.com"
SOURCE = "全国土地市场网"


class ChinaLandAPIConnector:
    """全国土地市场网 API 连接器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.landchina.com/',
        })
    
    def get_cities(self) -> List[Dict[str, Any]]:
        """
        获取主要城市列表
        API: /bptFieldEnum/keyCity
        """
        url = f"{BASE_URL}/bptFieldEnum/keyCity"
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') == 200 or data.get('msg') == '操作成功':
                return data.get('data', [])
            else:
                print(f"⚠️  获取城市列表失败: {data.get('msg')}")
                return []
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return []
    
    def get_land_data(
        self,
        city_code: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        获取土地数据
        API: /epstBulletin/index/bulletin
        
        Args:
            city_code: 城市代码（例如：'11' 代表北京，'31' 代表上海）
            page: 页码
            limit: 每页数量
        """
        url = f"{BASE_URL}/epstBulletin/index/bulletin"
        
        # 构建请求参数
        params = {
            'page': page,
            'limit': limit
        }
        
        if city_code:
            params['xzqDm'] = city_code  # 行政区划代码
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"❌ 获取土地数据失败: {e}")
            return {}
    
    def get_land_data_by_city(
        self,
        city_name: str,
        page: int = 1,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        根据城市名称获取土地数据
        
        Args:
            city_name: 城市名称（如 '北京', '上海'）
            page: 页码
            limit: 每页数量
            
        Returns:
            土地数据列表
        """
        # 先获取城市列表，找到对应的城市代码
        cities = self.get_cities()
        
        city_code = None
        for city in cities:
            if city_name in city.get('enumName', ''):
                city_code = city.get('enumValue')
                break
        
        if not city_code:
            print(f"⚠️  未找到城市: {city_name}")
            return []
        
        print(f"✅ 找到城市 {city_name} (代码: {city_code})")
        
        # 获取该城市的土地数据
        data = self.get_land_data(city_code, page, limit)
        
        if data.get('code') == 200:
            return data.get('data', {}).get('list', [])
        else:
            print(f"⚠️  获取数据失败: {data.get('msg')}")
            return []
    
    def normalize_land_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化土地数据格式
        """
        return {
            'category': 'land',
            'title': raw_data.get('title', ''),
            'content': raw_data.get('content', ''),
            'city': raw_data.get('xzqName', ''),
            'date': raw_data.get('createTime', ''),
            'source': SOURCE,
            'source_level': 'level_1',
            'verified': True,
            'raw': raw_data
        }


def test_china_land_api():
    """测试全国土地市场网 API"""
    print("🧪 测试全国土地市场网 API")
    print("=" * 60)
    
    connector = ChinaLandAPIConnector()
    
    # 测试1: 获取城市列表
    print("\n📍 测试1: 获取主要城市列表...")
    cities = connector.get_cities()
    print(f"   找到 {len(cities)} 个城市")
    
    if cities:
        print("\n   前 10 个城市:")
        for city in cities[:10]:
            print(f"   - {city['enumName']} (代码: {city['enumValue']})")
    
    # 测试2: 获取上海的土地数据
    print("\n📊 测试2: 获取上海土地数据...")
    shanghai_data = connector.get_land_data_by_city('上海', page=1, limit=5)
    print(f"   获取到 {len(shanghai_data)} 条数据")
    
    if shanghai_data:
        print("\n   前 3 条数据:")
        for i, item in enumerate(shanghai_data[:3], 1):
            print(f"\n   {i}. {item.get('title', 'N/A')}")
            print(f"      日期: {item.get('createTime', 'N/A')}")
            print(f"      地区: {item.get('xzqName', 'N/A')}")
    
    # 测试3: 获取北京的土地数据
    print("\n📊 测试3: 获取北京土地数据...")
    beijing_data = connector.get_land_data_by_city('北京', page=1, limit=5)
    print(f"   获取到 {len(beijing_data)} 条数据")
    
    return {
        'cities_count': len(cities),
        'shanghai_count': len(shanghai_data),
        'beijing_count': len(beijing_data)
    }


if __name__ == "__main__":
    result = test_china_land_api()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"   城市总数: {result['cities_count']}")
    print(f"   上海数据: {result['shanghai_count']} 条")
    print(f"   北京数据: {result['beijing_count']} 条")
