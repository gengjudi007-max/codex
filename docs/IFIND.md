# 同花顺 iFinD 接入

本项目通过可选适配器接入 iFinD。仓库不会保存账号密码，也不会把同花顺专有 SDK 写入公开依赖。

## 本机准备

1. 安装并确认同花顺 iFinD Python SDK 可用。
2. 确认 Python 中可以执行：

```python
import iFinDPy
```

3. 设置环境变量：

```bash
export IFIND_USER="你的账号"
export IFIND_PASSWORD="你的密码"
```

## 查询入口

统一交互层支持：

```json
{
  "mode": "ifind_query",
  "function": "edb",
  "codes": "指标代码",
  "params": "",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31"
}
```

已预留函数：

- `hq`: 行情类 `THS_HQ`
- `ds`: 序列类 `THS_DS`
- `edb`: 宏观/经济数据库类 `THS_EDB`
- `bd`: 基础数据类 `THS_BD`

## 输出流向

iFinD 返回结果会被标准化为：

- `ifind`: 原始标准化结果
- `items`: 系统统一输入项
- `topic_pipeline`: 选题流水线
- `signal_monitor`: 信号监测

## 使用原则

- 不绕过终端授权、登录限制或数据使用协议。
- 对外发布报道时，仍需标注 iFinD 数据口径、指标代码和查询时间。
- iFinD 结果默认进入证据链，但涉及公开报道时仍建议回到原始公告或官方来源交叉核验。
