# Newsroom OS 运维与运行指南

## 1. 安装

```bash
pip install -e .[dev]
```

## 2. 初始化配置

```bash
cp config/watchlist.example.json config/watchlist.json
```

将示例 URL 替换为真实数据源。

---

## 3. 健康检查（必须先跑）

```bash
python -m codex.cli health
```

或：

```bash
codex health
```

若存在 failed 项，不建议进入持续运行。

---

## 4. 单次运行

```bash
python -m codex.cli run-once
```

作用：

- ingest sources
- 写入 source store
- 写入 memory
- signal monitor
- topic pipeline
- risk chain
- alerts

---

## 5. newsroom desk

```bash
python -m codex.cli newsroom-desk
```

输出：

- 晨会简报
- 选题池
- 派单建议
- 发稿门
- 编辑动作

---

## 6. 持续运行

```bash
python -m codex.cli run-loop --interval 3600 --max-runs 24
```

说明：

- interval 单位为秒
- max-runs 为最大运行次数

---

## 7. 常见问题

### 无法解析 PDF

安装：

```bash
pip install pypdf
```

### watchlist.json 不存在

复制：

```bash
cp config/watchlist.example.json config/watchlist.json
```

### source store 无法写入

检查：

- data/
- data/run_logs/

是否具备写权限。

---

## 8. 当前系统定位

当前系统已经具备：

- newsroom ingest
- monitoring
- signal detection
- topic generation
- reasoning
- fact check
- draft generation
- editorial gate
- newsroom desk

但：

当前仍属于：

- local newsroom OS
- single-machine deployment
- experimental editorial infrastructure

尚未完成：

- distributed queue
- async workers
- postgres
- vector db
- real-time websocket
- production observability
- multi-user newsroom collaboration
