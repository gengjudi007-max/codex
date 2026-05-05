# 数据导入目录（手动接入）

将以下来源数据导出后放入本目录：

## 支持格式
- CSV（Wind / 同花顺 / 东方财富）
- JSON（中指 / CRIC / 贝壳 / 政策）

## 示例文件

### wind_market.csv
```
date,city,metric,value
2026-05-05,北京,new_home_area_yoy,5.2
```

### policy.json
```
{
  "items": [
    {
      "city": "北京",
      "title": "房地产新政",
      "content": "优化公积金政策",
      "source": "北京市住建委"
    }
  ]
}
```

## 使用方式

1. 将文件放入本目录
2. 运行：

```
python -m codex.jobs.import_daily_data
```

3. 输出：

```
data/processed/daily_items.json
```

4. 再运行：

```
python -m codex.daily_run --input data/processed/daily_items.json
```
