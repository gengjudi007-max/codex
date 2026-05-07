# codex 工程规范

## 测试原则

项目属于财经新闻工作流工具。

测试目标不仅是“代码是否运行”，还包括：

- 是否会错误生成新闻结论
- 是否会误导记者
- 是否会遗漏核验步骤
- 是否会把低置信度内容包装成确定事实
- 是否会因为脏数据导致流程中断

因此测试分为：

1. 单元测试
2. 路由测试
3. 规则回归测试
4. 脏数据测试
5. 新闻语义测试

---

## 当前测试覆盖

当前已覆盖：

- topic pipeline
- annual report routing
- signal monitor
- store search
- source dedupe
- robustness
- malformed payload handling

后续建议新增：

- 政策语义变化测试
- 房企财报异常识别测试
- 土地市场异常测试
- 宣传稿识别测试
- 新闻标题风险测试

---

## 推荐本地开发流程

安装开发依赖：

```bash
pip install -e .[dev]
```

运行 unittest：

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

运行 pytest：

```bash
pytest
```

生成覆盖率：

```bash
pytest --cov=src/codex --cov-report=term-missing
```

运行 Ruff：

```bash
ruff check .
```

---

## 架构建议

当前 interaction.py 已逐渐成为中心调度层。

后续建议拆分：

```text
interaction/
├── router.py
├── validators.py
├── pipelines/
├── response_builder.py
└── error_handler.py
```

避免所有模式持续堆叠在单文件中。

---

## 新闻规则引擎方向

项目未来核心价值不只是 NLP。

真正壁垒包括：

- 房地产行业规则
- 财报异常逻辑
- 土地财政逻辑
- 城投托底逻辑
- 政策语义变化
- 财经媒体表达规范
- 宣传稿识别
- 新闻可信度边界

这些规则应逐渐结构化，而不是散落在关键词判断中。
