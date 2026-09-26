# 从真实材料到报道正文

## 为什么此前失败

选题发现依赖固定关键词，漏掉现房销售、封顶预售、主办银行和开发贷款；三条真实材料因此全部漏检。旧 deep_report_drafter 则直接返回写作指导和占位符，不调用模型，final_editorial_engine 只把这些模板拼接起来。旧测试检查的是接口字段，不是有来源的完整正文。

## 现在的执行方式

统一接口 `mode: report` 接受 `sources`。每条来源提供 `title`、`url`、`content`，可选 `source_type`。内容已经给定的 sources 会自动路由到报道流程；仅有链接的输入仍保留原有抓取路由。显式 report 不偷偷抓取链接，缺少正文时返回阻断状态。

- `writer: extractive`（默认）：离线来源摘编，生成有来源归属的正文及逐段对应表，不添加虚构采访或行业结论。它是简讯/资料稿能力，不等同于深度报道的独立采写。
- `writer: model`：调用已配置的 OpenAI Responses API 进行写作。请求使用结构化输出、`store: false`、55秒超时和输出上限。拒绝错误来源id、非原文摘录、证据中不存在的数字、重复段落、模板占位符及未完成响应。请求失败明确报错，不悄悄降级冒充模型稿。
- 原 `deep_report_drafter` 默认走正文路径；仅显式传 `target_length="outline"` 时保留旧规划模式。无来源不再制造提纲当成正文。
- `final_edit` 编辑已有原稿时保留原文事实，不附加提纲。提供来源时走完整正文路径。
- `newsroom_orchestrator` 已增加 article 输出；sources-only 输入也能发现选题。

模型配置仅从服务端环境读取 `OPENAI_API_KEY` 和 `CODEX_WRITER_MODEL`，请求JSON不接受密钥、模型覆盖或自定义地址。密钥不要写入输入文件、仓库或日志。必须通过安全配置方式提供。使用模型模式会发生API调用，默认摘编模式不发出模型请求。

## 运行

```bash
PYTHONPATH=src python -m codex.cli report --input examples/policy_828.json --output /tmp/policy-828.md
PYTHONPATH=src python -m codex.server
```

网页选择“从来源生成报道”，粘贴包含 sources 的JSON，选择来源摘编或已配置的模型写作。网页呈现正文、审核状态、来源和段落对应，不再只输出原始JSON。

在模型已安全配置后：

```bash
PYTHONPATH=src python -m codex.cli report --input examples/policy_828.json --writer model --output /tmp/policy-828-model.md
```

CLI输出完整JSON用于保留来源映射，`--output`只保存正文。来源输入不能被输出覆盖。API同样支持 `POST /api/interact`，发送 `mode: report`。

## 828案例复验（2026-09-26）

`examples/policy_828.json`保留上一轮人工检索后整理的3条材料摘要及其URL，而非完整文件抓取结果。不要将这个夹具当作实时政策数据库。

相同材料修正前选题为0，修正后得到6个规则候选方向（不是6个独立新闻事件），3份来源、9段来源摘编，标题和正文合计433字符。材料只有摘要，因此不扩写成数千字深度报道。每段可找到对应的来源原文片段，数字35.61亿元完整保留，无“待补”占位符。

108项unittest测试全部通过，包括15项新增的真实案例、来源和模型接口回归测试。CLI实际导出成功；真实本地HTTP服务的网页、report API输出与CLI一致。模型接口使用模拟HTTP响应验证了请求结构和异常分支，未进行真实模型调用，因为运行环境没有API密钥与模型配置。

## 不应混淆的状态

`source_excerpt_only`只表示来自输入资料，不代表已核验；`draft_for_editor_review`只表示有正文待审核。即使来源和数字检查通过，程序也不会自动置为publishable。来源真假、时效、政策适用条件、推断是否成立、报道是否达到发表标准仍需人工判断。当前校验不能全面识别同数字不同主体、语义反转或伪造的输入来源。

官方接口依据：https://developers.openai.com/api/docs/guides/structured-outputs
