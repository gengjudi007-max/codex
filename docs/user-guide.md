# Codex 用户使用指南

## 目录

1. [简介](#简介)
2. [安装方法](#安装方法)
3. [快速开始](#快速开始)
4. [核心连接器](#核心连接器)
5. [示例代码](#示例代码)
6. [高级用法](#高级用法)
7. [常见问题](#常见问题)

---

## 简介

Codex 是一个中国土地市场数据抓取工具，支持多个重点城市的土地交易数据获取，包括：

- **直辖市**：北京、上海
- **一线城市**：广州、深圳
- **新一线城市**：杭州、成都、西安、天津、南京、苏州、厦门等
- **其他重点城市**：青岛、宁波、无锡、佛山、东莞、昆明、合肥、福州、济南、沈阳、长春、哈尔滨、石家庄、太原、兰州、西宁、郑州

**数据来源**：
- 各市自然资源和规划局官网
- 中国土地市场网（landchina.mnr.gov.cn）

---

## 安装方法

### 方法一：从 PyPI 安装（推荐）

```bash
pip install codex
```

### 方法二：从源码安装

```bash
git clone https://github.com/gengjudi007-max/codex.git
cd codex
pip install -e .
```

### 方法三：从 GitHub Release 下载

1. 访问 [GitHub Releases](https://github.com/gengjudi007-max/codex/releases)
2. 下载最新的 `.whl` 或 `.tar.gz` 文件
3. 安装：

```bash
pip install codex-0.1.0-py3-none-any.whl
```

### 依赖要求

- Python 3.11+
- 标准库（无需额外依赖）
- 可选：Playwright（用于上海连接器）

---

## 快速开始

### 示例 1：获取北京土地数据

```python
from codex.connectors.beijing_land_connector import fetch_beijing_land_items

# 获取前3页数据，每页10条
items = fetch_beijing_land_items(max_pages=3, limit=10)

for item in items:
    print(f"标题: {item['title']}")
    print(f"日期: {item['date']}")
    print(f"城市: {item['city']}")
    print(f"来源: {item['source']}")
    print("-" * 80)
```

### 示例 2：获取上海土地数据

```python
from codex.connectors.shanghai_land_connector import fetch_shanghai_land_items

# 获取前3页数据
items = fetch_shanghai_land_items(max_pages=3)

for item in items:
    print(f"标题: {item['title']}")
    print(f"日期: {item['date']}")
    print("-" * 80)
```

### 示例 3：使用通用连接器获取多个城市数据

```python
from codex.connectors.simple_city_land_connector import SimpleCityLandConnector

# 获取广州的数据（翻20页）
connector = SimpleCityLandConnector(city_name='广州', max_pages=20)
items = connector.fetch_data()

for item in items:
    print(f"标题: {item['title']}")
    print(f"日期: {item['date']}")
    print(f"链接: {item['url']}")
    print("-" * 80)
```

---

## 核心连接器

### 1. 北京连接器 (`beijing_land_connector.py`)

**数据源**：北京市规划和自然资源委员会官网

**功能**：
- 通过 API 接口获取土地交易数据
- 支持翻页（每页 10 条）
- 自动提取日期、地块名称、区域、用途、交易状态等

**使用示例**：

```python
from codex.connectors.beijing_land_connector import fetch_beijing_land_items

# 获取5页数据
items = fetch_beijing_land_items(max_pages=5, limit=10)

print(f"总共获取 {len(items)} 条数据")
```

**返回字段**：
- `category`: 类别（固定为 "land"）
- `title`: 地块名称
- `content`: 详细内容
- `city`: 城市（固定为 "北京"）
- `date`: 发布日期
- `source`: 数据来源
- `source_level`: 来源级别（level_2）
- `url`: 详情页链接
- `verified`: 是否已验证（True）
- `metrics`: 指标数据（面积、价格等）
- `raw`: 原始数据

---

### 2. 上海连接器 (`shanghai_land_connector.py`)

**数据源**：上海市规划和自然资源局官网

**功能**：
- 使用 Playwright 绕过 SSL 证书验证
- 支持翻页
- 解析 JavaScript 渲染后的页面

**使用示例**：

```python
from codex.connectors.shanghai_land_connector import fetch_shanghai_land_items

# 获取3页数据
items = fetch_shanghai_land_items(max_pages=3)

print(f"总共获取 {len(items)} 条数据")
```

**注意**：需要安装 Playwright：

```bash
pip install playwright
playwright install
```

---

### 3. 广州/深圳/杭州连接器 (`guangzhou_land_connector.py`, `shenzhen_land_connector.py`, `hangzhou_land_connector.py`)

**数据源**：各市公共资源交易中心官网

**功能**：
- 使用 curl + 正则表达式解析 HTML
- 支持翻页
- 无需额外依赖（使用标准库）

**使用示例**：

```python
from codex.connectors.guangzhou_land_connector import fetch_guangzhou_land_items

# 获取5页数据
items = fetch_guangzhou_land_items(max_pages=5)

print(f"总共获取 {len(items)} 条数据")
```

---

### 4. 通用简化版连接器 (`simple_city_land_connector.py`)

**数据源**：中国土地市场网（landchina.mnr.gov.cn）

**功能**：
- 支持任意城市（通过城市名过滤）
- 支持翻页（默认 20 页，每页 25 条）
- 无需额外依赖（使用 curl 和标准库）
- 适合快速覆盖多个城市

**使用示例**：

```python
from codex.connectors.simple_city_land_connector import SimpleCityLandConnector

# 获取成都的数据
connector = SimpleCityLandConnector(city_name='成都', max_pages=20)
items = connector.fetch_data()

print(f"总共获取 {len(items)} 条数据")

# 标准化数据格式
for item in items:
    normalized = connector.normalize_land_data(item)
    print(f"标题: {normalized['title']}")
    print(f"日期: {normalized['date']}")
    print("-" * 80)
```

**支持的城市**：

已测试成功的城市（22个）：
- 北京、上海、广州、深圳、杭州、成都、西安、天津、武汉、重庆
- 南京、苏州、厦门、青岛、宁波、无锡、佛山、东莞、合肥、福州
- 济南、沈阳、长春、哈尔滨、石家庄、太原、兰州、西宁、郑州

---

## 示例代码

### 示例 1：批量获取多个城市的数据

```python
from codex.connectors.simple_city_land_connector import SimpleCityLandConnector

cities = ['北京', '上海', '广州', '深圳', '杭州', '成都']

all_data = {}

for city in cities:
    print(f"\n🔍 获取 {city} 的数据...")
    connector = SimpleCityLandConnector(city_name=city, max_pages=10)
    data = connector.fetch_data()
    all_data[city] = data
    print(f"   ✅ 获取 {len(data)} 条数据")

# 统计
print("\n📊 统计结果：")
for city, data in all_data.items():
    print(f"   {city}: {len(data)} 条")
```

### 示例 2：保存数据到 CSV 文件

```python
import csv
from codex.connectors.beijing_land_connector import fetch_beijing_land_items

# 获取数据
items = fetch_beijing_land_items(max_pages=5, limit=10)

# 保存到 CSV
with open('beijing_land_data.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['title', 'date', 'city', 'source', 'url'])
    writer.writeheader()
    for item in items:
        writer.writerow({
            'title': item['title'],
            'date': item['date'],
            'city': item['city'],
            'source': item['source'],
            'url': item['url']
        })

print(f"✅ 数据已保存到 beijing_land_data.csv")
```

### 示例 3：数据分析（土地成交面积统计）

```python
from codex.connectors.beijing_land_connector import fetch_beijing_land_items

# 获取数据
items = fetch_beijing_land_items(max_pages=10, limit=10)

# 统计
total_area = 0
count_with_area = 0

for item in items:
    metrics = item.get('metrics', {})
    if 'land_area' in metrics:
        total_area += metrics['land_area']
        count_with_area += 1

if count_with_area > 0:
    avg_area = total_area / count_with_area
    print(f"📊 统计数据：")
    print(f"   - 总数据条数：{len(items)}")
    print(f"   - 有面积数据：{count_with_area} 条")
    print(f"   - 总面积：{total_area:.2f} 平方米")
    print(f"   - 平均面积：{avg_area:.2f} 平方米")
```

---

## 高级用法

### 1. 自定义过滤器

```python
from codex.connectors.simple_city_land_connector import SimpleCityLandConnector

connector = SimpleCityLandConnector(city_name='北京', max_pages=20)
items = connector.fetch_data()

# 过滤：只保留包含"住宅"的数据
residential_items = [item for item in items if '住宅' in item['title']]

print(f"总共有 {len(items)} 条数据，其中住宅用地 {len(residential_items)} 条")
```

### 2. 定时任务（使用 crontab）

```bash
# 每天上午 9:00 自动获取数据
0 9 * * * cd /path/to/your/project && python3 fetch_daily_data.py
```

`fetch_daily_data.py` 示例：

```python
from codex.connectors.beijing_land_connector import fetch_beijing_land_items
from datetime import datetime

# 获取昨天的数据（根据实际需求调整）
items = fetch_beijing_land_items(max_pages=1, limit=10)

# 添加抓取时间
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(f"[{timestamp}] 获取 {len(items)} 条数据")

# 保存到数据库或文件
# ...
```

### 3. 集成到 Web 应用（FastAPI）

```python
from fastapi import FastAPI
from codex.connectors.beijing_land_connector import fetch_beijing_land_items

app = FastAPI()

@app.get("/api/land/beijing")
def get_beijing_land_data(max_pages: int = 3, limit: int = 10):
    items = fetch_beijing_land_items(max_pages=max_pages, limit=limit)
    return {
        "success": True,
        "count": len(items),
        "data": items
    }
```

运行：

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

访问：http://localhost:8000/api/land/beijing

---

## 常见问题

### Q1：为什么有些城市获取不到数据？

**A**：可能的原因：
1. 该城市在中国土地市场网上没有以"城市名"开头的标题
2. 数据分布在更深的页面（已超过 20 页）
3. 需要使用该城市的本地官网（类似广州/深圳/杭州模式）

**解决方案**：
- 增加 `max_pages` 参数（默认 20 页）
- 为该城市编写完整的连接器（参考 `guangzhou_land_connector.py`）

---

### Q2：如何添加新的城市连接器？

**A**：步骤如下：

1. 找到该城市的土地市场官网（通常是"XX市公共资源交易中心"或"XX市规划和自然资源委员会"）
2. 分析网站的 API 接口或 HTML 结构
3. 参考现有连接器（如 `guangzhou_land_connector.py`）编写新的连接器
4. 将新连接器保存到 `src/codex/connectors/` 目录
5. 测试并提交代码

---

### Q3：北京连接器的日期字段为什么是 None？

**A**：这个问题已经在 v0.1.1 中修复。如果你使用的是旧版本，请升级：

```bash
pip install --upgrade codex
```

修复内容：
- 在 `normalize_api_row()` 的日期别名列表中添加 `createDateTime`, `publishTime`, `executiondate`, `startdate`
- 将 `beijing_land_connector.py` 从 `requests` 改为使用标准库 `urllib`

---

### Q4：如何提高数据获取的成功率？

**A**：
1. 使用多个数据源（中国土地市场网 + 各市本地官网）
2. 增加翻页数量（`max_pages`）
3. 定期运行（每天或每周），避免错过数据
4. 保存原始数据（`raw` 字段），方便后续解析

---

### Q5：上海连接器报错"SSL Certificate Verify Failed"？

**A**：这个问题已经在 v0.1.0 中修复。如果你使用的是旧版本，请升级：

```bash
pip install --upgrade codex
```

修复内容：使用 Playwright 绕过 SSL 证书验证。

---

## 联系与贡献

- **GitHub 仓库**：https://github.com/gengjudi007-max/codex
- **Issue 追踪**：https://github.com/gengjudi007-max/codex/issues
- **贡献指南**：欢迎提交 Pull Request！

---

## 版本历史

- **v0.1.1** (2026-05-07)：修复北京连接器日期字段问题
- **v0.1.0** (2026-05-07)：首次发布，支持 22+ 个城市

---

**文档版本**：v1.0  
**最后更新**：2026-05-07  
**作者**：Codex Team
