#!/usr/bin/env python3
"""
广州土地市场连接器
- 静态 HTML 页面
- 分页模式：index.html、index_2.html、index_3.html...
- 使用 curl 绕过 SSL 问题获取 HTML
- 正则表达式解析列表
"""
import subprocess
import re
import json
from typing import Any, Dict, List, Optional


class GuangzhouLandConnector:
    """
    广州土地市场连接器
    
    数据来源：广州市规划和自然资源局网站
    URL: https://ghzyj.gz.gov.cn/ywpd/tdgl/tdjysc/cjgs/
    
    分页模式：
    - 第1页：index.html
    - 第2页：index_2.html
    - 第N页：index_N.html
    """
    
    BASE_URL = "https://ghzyj.gz.gov.cn/ywpd/tdgl/tdjysc/cjgs"
    
    def __init__(self):
        pass
    
    def _fetch_html(self, url: str) -> Optional[str]:
        """使用 curl 获取 HTML（绕过 Python SSL 问题）"""
        try:
            result = subprocess.run(
                ['curl', '-s', '--insecure', url],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
            else:
                print(f"   ❌ curl 失败: {result.stderr}")
                return None
        except Exception as e:
            print(f"   ❌ 获取 HTML 失败: {e}")
            return None
    
    def _parse_list_page(self, html: str) -> List[Dict[str, Any]]:
        """解析列表页面，提取土地成交项目"""
        results = []
        
        # 正则模式：匹配 <li> 中的链接和日期
        # 格式：<li><a href="...">标题</a> <span>日期</span></li>
        pattern = r'<li[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>([^<]+(?:地块|公示)[^<]*)</a>\s*<span>([^<]+)</span>\s*</li>'
        
        matches = re.findall(pattern, html)
        
        for href, title, date in matches:
            # 处理相对 URL
            if href.startswith('http'):
                full_url = href
            else:
                full_url = self.BASE_URL + '/' + href.lstrip('/')
            
            results.append({
                'title': title.strip(),
                'url': full_url,
                'date': date.strip(),
                'city': '广州',
                'source': '广州市规划和自然资源局'
            })
        
        return results
    
    def fetch_land_data(
        self,
        page_num: int = 1,
        max_pages: int = 1
    ) -> List[Dict[str, Any]]:
        """
        获取广州土地数据
        
        Args:
            page_num: 起始页码
            max_pages: 最大页数（1=只获取当前页）
        
        Returns:
            土地数据列表
        """
        all_data = []
        
        for page in range(page_num, page_num + max_pages):
            # 构造 URL
            if page == 1:
                url = f"{self.BASE_URL}/index.html"
            else:
                url = f"{self.BASE_URL}/index_{page}.html"
            
            print(f"📊 获取第 {page} 页: {url}")
            
            # 获取 HTML
            html = self._fetch_html(url)
            if not html:
                print(f"   ❌ 获取失败，停止翻页")
                break
            
            # 解析列表
            page_data = self._parse_list_page(html)
            print(f"   ✅ 提取到 {len(page_data)} 条数据")
            
            if not page_data:
                print(f"   ⚠️  本页无数据，停止翻页")
                break
            
            all_data.extend(page_data)
            
            # 如果只获取一页，跳出循环
            if max_pages == 1:
                break
        
        return all_data
    
    def normalize_land_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化土地数据格式"""
        return {
            'category': 'land',
            'title': raw_data.get('title') or '广州土地成交项目',
            'content': f"地块：{raw_data.get('title', '')}，日期：{raw_data.get('date', '')}",
            'city': '广州',
            'date': raw_data.get('date') or '',
            'source': raw_data.get('source') or '广州市规划和自然资源局',
            'source_level': 'level_2',
            'verified': True,
            'url': raw_data.get('url'),
            'raw': raw_data
        }


async def test_guangzhou_land_connector():
    """测试广州土地市场连接器"""
    print("🧪 测试广州土地市场连接器")
    print("=" * 60)
    
    connector = GuangzhouLandConnector()
    
    # 测试：获取第 1 页
    print("\n📍 测试：获取第 1 页数据...")
    data = connector.fetch_land_data(page_num=1, max_pages=1)
    print(f"   获取到 {len(data)} 条数据")
    
    if data:
        print("\n   前 3 条数据:")
        for i, item in enumerate(data[:3], 1):
            normalized = connector.normalize_land_data(item)
            print(f"   {i}. {normalized['title']}")
            print(f"      日期: {normalized['date']}")
            print(f"      URL: {normalized['url'][:80]}")
    
    # 测试：获取多页
    print("\n📍 测试：获取前 3 页数据...")
    data_multi = connector.fetch_land_data(page_num=1, max_pages=3)
    print(f"   共获取到 {len(data_multi)} 条数据")
    
    return {
        'page_1_count': len(data),
        'multi_page_count': len(data_multi)
    }


if __name__ == '__main__':
    import asyncio
    result = asyncio.run(test_guangzhou_land_connector())
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"   第1页: {result['page_1_count']} 条")
    print(f"   前3页: {result['multi_page_count']} 条")
