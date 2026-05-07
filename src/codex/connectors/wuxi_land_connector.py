#!/usr/bin/env python3
"""
无锡土地市场连接器
使用中国土地市场网作为数据源
"""
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from codex.connectors.simple_city_land_connector import SimpleCityLandConnector


class WuxiLandConnector:
    """
    无锡土地市场连接器
    使用中国土地市场网，通过城市名过滤数据
    """
    
    def __init__(self, max_pages: int = 20):
        """
        初始化连接器
        
        Args:
            max_pages: 每个分类最多翻几页（默认 20 页）
        """
        # 尝试多种可能的城市名称变体
        self.connector = SimpleCityLandConnector(
            city_name=['无锡', '无锡市', '江苏无锡'], 
            max_pages=max_pages
        )
    
    def fetch_land_data(self, max_per_category: int = 20) -> list:
        """
        获取无锡土地数据
        
        Args:
            max_per_category: 每个分类最多获取多少条（默认 20 条）
        
        Returns:
            list: 土地数据列表
        """
        return self.connector.fetch_data(max_per_category=max_per_category)
    
    def normalize_land_data(self, raw_data: dict) -> dict:
        """
        标准化土地数据格式
        
        Args:
            raw_data: 原始数据
        
        Returns:
            dict: 标准化后的数据
        """
        return self.connector.normalize_land_data(raw_data)


def test_wuxi_connector():
    """测试无锡连接器"""
    print("🧪 测试无锡土地市场连接器")
    print("=" * 60)
    
    connector = WuxiLandConnector(max_pages=5)
    data = connector.fetch_land_data(max_per_category=5)
    
    if data:
        print(f"\n✅ 成功获取 {len(data)} 条数据")
        print(f"\n前 3 条数据:")
        for i, item in enumerate(data[:3], 1):
            normalized = connector.normalize_land_data(item)
            print(f"{i}. {normalized['title']}")
            print(f"   日期: {normalized['date']}")
            print(f"   URL: {normalized['url']}")
    else:
        print("\n⚠️  未获取到数据")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")


if __name__ == '__main__':
    test_wuxi_connector()
