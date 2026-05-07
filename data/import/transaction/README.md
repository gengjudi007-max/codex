# 成交数据导入说明

支持来自住建委、贝壳、中指、Wind等成交数据。

## 文件要求

文件名：transaction_data.csv

字段示例：

城市,日期,新房成交套数,新房成交面积,二手房成交套数,二手房成交面积

## 使用方式

1. 将CSV文件放入本目录
2. 运行：

```
python -m codex.jobs.import_transaction_data
```

3. 输出：

```
data/processed/transaction_items.json
```

4. 再运行：

```
python -m codex.daily_run --input data/processed/transaction_items.json
```
