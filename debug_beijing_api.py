#!/usr/bin/env python3
"""
调试：查看北京 API 返回的字段，找到正确的日期字段名
"""
import urllib.request
import urllib.parse
import json
import time

BASE_URL = "https://yewu.ghzrzyw.beijing.gov.cn"
API_URL = f"{BASE_URL}/zkdncms/tdgltdsc/tdzpgxm/esSearchList"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": f"{BASE_URL}/gwxxfb/tdsc/tdzpgxm.html",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

print("🔍 调试：北京 API 返回字段")
print("=" * 80)

print("\n📡 调用 API...")
timestamp = int(time.time() * 1000)
params = {
    "t": timestamp,
    "page": 1,
    "limit": 3,  # 只取 3 条
    "landusetype1": "",
    "announcetype": "",
    "county": "",
    "gjz": "",
    "_": timestamp,
}

url = f"{API_URL}?{urllib.parse.urlencode(params)}"
req = urllib.request.Request(url, headers=HEADERS)

with urllib.request.urlopen(req, timeout=15) as response:
    payload = json.loads(response.read().decode('utf-8'))

print(f"✅ API 响应成功")
print(f"   Keys: {list(payload.keys())}")

# 提取 rows
rows = []
for key in ["data", "rows", "list", "result"]:
    value = payload.get(key)
    if isinstance(value, list):
        rows = value
        print(f"   找到数据列表：key='{key}', {len(rows)} 条")
        break

if not rows:
    print("❌ 未找到数据列表")
    exit(1)

# 打印第一条数据的所有字段
print(f"\n📊 第一条数据的所有字段：")
print("-" * 80)
row = rows[0]
for key, value in row.items():
    # 截断过长的值
    str_value = str(value)
    if len(str_value) > 60:
        str_value = str_value[:60] + "..."
    print(f"  {key}: {str_value}")

# 特别查找日期相关的字段
print(f"\n📅 日期相关字段：")
print("-" * 80)
date_aliases = ["date", "cjsj", "jzsj", "fbsj", "pubdate", "createTime", 
                "fbSj", "fbrq", "dateTime", "time", "timestamp", 
                "createDate", "updateTime", "publishDate"]

for alias in date_aliases:
    if alias in row:
        print(f"  ✅ 找到字段：{alias} = {row[alias]}")

print(f"\n💡 建议：将找到的字段名添加到 normalize_api_row() 的 date = pick(row, [...]) 中")
