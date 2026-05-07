#!/usr/bin/env python3
"""
杭州土地市场连接器
- 静态 HTML 页面
- 分页模式待确认
- 使用 curl 绕过 SSL 问题获取 HTML
- 正则表达式解析列表
"""
import subprocess
import re
from typing import Any, Dict, List, Optional


class HangzhouLandConnector:
    """
    杭州土地市场连接器
    
    数据来源：杭州市人民政府门户网站
    URL: https://www.hangzhou.gov.cn/col/col1228974784/
    """
    
    BASE_URL = "https://www.hangzhou.gov.cn/col/col1228974784"
    
    def __init__(self):
        pass
    
    def _fetch_html(self, url: str) -> Optional[str]:
        """使用 curl 获取 HTML（绕过 Python SSL 问题）"""
        try:
            result = subprocess.run(
                ['curl', '-s', '--insecure', '-A', 'Mozilla/5.0', url],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout and len(result.stdout) > 500:
                return result.stdout
            else:
                print(f"   ❌ curl 失败或返回空页面 (长度: {len(result.stdout) if result.stdout else 0})")
                return None
        except Exception as e:
            print(f"   ❌ 获取 HTML 失败: {e}")
            return None
    
    def _parse_list_page(self, html: str) -> List[Dict[str, Any]]:
        """解析列表页面，提取土地成交项目"""
        results = []
        
        # 正则模式：匹配 <li class="clearfix">
        # 格式：<li class="clearfix"><a href="...">标题</a><span>日期</span></li>
        pattern = r'<li[^>]*clearfix[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>[^<]*([^<]+)[^<]*</a>\s*<span>([^<]+)</span>'
        
        # 更灵活的匹配
        pattern2 = r'<li[^>]*clearfix[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"[^>]*>([^<]*)</a>\s*<span>([^<]+)</span>'
        
        matches = re.findall(pattern2, html)
        
        for href, title_from_attr, title_from_text, date in matches:
            # 使用 title 属性或链接文本作为标题
            title = title_from_attr.strip() if title_from_attr.strip() else title_from_text.strip()
            
            # 跳过非土地相关链接
            if not any(keyword in title for keyword in ['地块', '出让', '成交', '挂牌']):
                continue
            
            # 处理相对 URL
            if href.startswith('http'):
                full_url = href
            else:
                full_url = 'https://www.hangzhou.gov.cn' + href
            
            results.append({
                'title': title,
                'url': full_url,
                'date': date.strip(),
                'city': '杭州',
                'source': '杭州市人民政府门户网站'
            })
        
        return results
    
    def fetch_land_data(
        self,
        page_num: int = 1,
        max_pages: int = 1
    ) -> List[Dict[str, Any]]:
        """
        获取杭州土地数据
        
        Args:
            page_num: 起始页码
            max_pages: 最大页数
        
        Returns:
            土地数据列表
        """
        all_data = []
        
        for page in range(page_num, page_num + max_pages):
            # 构造 URL（需要先确认分页模式）
            if page == 1:
                url = f"{self.BASE_URL}/index.html"
            else:
                # 待确认：可能是 index_2.html 或其他模式
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
            'title': raw_data.get('title') or '杭州土地交易公告',
            'content': f"公告：{raw_data.get('title', '')}，日期：{raw_data.get('date', '')}",
            'city': '杭州',
            'date': raw_data.get('date') or '',
            'source': raw_data.get('source') or '杭州市人民政府门户网站',
            'source_level': 'level_2',
            'verified': True,
            'url': raw_data.get('url'),
            'raw': raw_data
        }


def test_hangzhou_land_connector():
    """测试杭州土地市场连接器"""
    print("🧪 测试杭州土地市场连接器")
    print("=" * 60)
    
    connector = HangzhouLandConnector()
    
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
    
    return {
        'data_count': len(data)
    }


if __name__ == '__main__':
    result = test_hangzhou_land_connector()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print(f"   数据: {result['data_count']} 条")
