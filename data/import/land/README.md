# 土地数据导入说明

将土地成交Excel导出为CSV后放入本目录。

## 文件要求

文件名：land_data.csv

字段示例（无需完全一致，系统会自动识别）：

城市,区县,地块名称,规划用途,总用地面积(㎡),规划建筑面积(㎡),成交时间,竞得方,成交价(万元),成交楼面价(元/㎡),溢价率(%)

## 使用方式

1. 将CSV文件放入本目录
2. 运行：

```
python -m codex.jobs.import_land_data
```

3. 输出：

```
data/processed/land_items.json
```

4. 再运行日报系统：

```
python -m codex.daily_run --input data/processed/land_items.json
```
