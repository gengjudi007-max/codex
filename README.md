# codex

`codex` 是一个面向财经记者的房地产行业选题、资料搜集、采访策划与稿件优化助手。项目目标是帮助记者持续跟踪房地产行业及上下游领域的政策、市场、企业、土地、不动产金融、城市更新、住房制度、土地改革和房地产税改革等动态，从信息变化中识别有新闻价值、商业价值和公共议题价值的报道线索。

## 项目定位

`codex` 不是单纯的资料整理工具，而是一个围绕财经新闻生产流程设计的工作助手，重点服务以下场景：

- 从最新政策、上市公司公告、土地市场、金融市场和行业数据中发现新闻选题
- 为选题补充背景材料、关键数据、政策脉络和企业线索
- 提供选题操作方向、报道角度和问题意识
- 生成采访对象清单、采访提纲和核验问题
- 为初稿提供结构、逻辑、语言、事实表达和财经媒体风格层面的优化建议

## 重点覆盖领域

- 房地产市场：新房、二手房、库存、价格、成交、去化、区域分化
- 房地产行业：周期变化、商业模式、行业出清、企业转型
- 房地产企业：上市公司公告、年报、债务、融资、并购、重组、经营数据
- 土地市场：集中供地、城投拿地、民企拿地、土地流拍、底价成交、土地财政
- 不动产金融：REITs、CMBS、ABS、经营性物业贷、房企融资、化债工具
- 政策解读：中央和地方房地产政策、住房政策、土地政策、金融监管政策
- 住房问题：保障房、城中村改造、租赁住房、老旧小区改造、住房制度改革
- 城市更新：片区更新、旧改、低效用地再开发、城市运营
- 土地改革与房地产税改革：制度设计、试点进展、地方财政影响

## 核心工作流

```text
信息输入
  ├── 政策文件
  ├── 上市公司公告
  ├── 市场数据
  ├── 土地成交数据
  ├── 机构报告
  └── 公开报道
        ↓
线索识别
  ├── 异常变化
  ├── 趋势拐点
  ├── 企业动作
  ├── 政策语义变化
  └── 市场分化信号
        ↓
选题生成
  ├── 新闻价值判断
  ├── 商业价值判断
  ├── 公共议题价值判断
  └── 可操作性判断
        ↓
报道策划
  ├── 素材清单
  ├── 采访对象
  ├── 采访问题
  ├── 数据核验
  └── 稿件框架
        ↓
稿件优化
  ├── 事实核查
  ├── 结构调整
  ├── 逻辑强化
  ├── 表达精校
  └── 财经媒体风格收口
```

## 目录结构

```text
codex/
├── examples/                     # 示例输入和示例输出
├── src/
│   └── codex/
│       ├── __init__.py
│       ├── main.py               # 程序入口
│       ├── interaction.py        # 统一交互和自动路由
│       ├── interactive.py        # 命令行互动入口
│       ├── server.py             # 本地网页/API 服务
│       ├── config.py             # 环境变量配置
│       ├── services/
│       │   ├── evidence.py       # 证据链、置信度和核验状态
│       │   ├── topic_finder.py   # 选题发现
│       │   ├── topic_scoring.py  # 选题评分
│       │   ├── material_builder.py # 素材、数据和核验清单
│       │   ├── interview_planner.py # 分层采访方案
│       │   ├── photo_planner.py # 新闻现场摄影策划
│       │   ├── signal_monitor.py # 行业信息变化监测
│       │   ├── annual_report_parser.py # 年报指标解析
│       │   ├── company_comparator.py # 房企横向比较
│       │   ├── city_land_comparator.py # 城市土地市场比较
│       │   ├── city_investment_land_model.py # 城投兜底拿地专题模型
│       │   ├── draft_editor.py   # 稿件体检和编辑建议
│       │   ├── source_store.py   # JSONL 资料库存储、统计和流式检索
│       │   ├── bulk_importer.py  # 本地文件夹批量导入
│       │   └── text_utils.py     # 文本清洗和城市/公司识别
├── tests/                        # 测试代码
├── .gitignore
├── pyproject.toml
└── README.md
```

## 模块说明

### 1. 选题发现 `topic_finder`

用于从政策、公告、数据和市场变化中识别选题线索，重点判断：

- 是否出现政策语义变化
- 是否出现企业经营或融资异常
- 是否出现市场拐点或区域分化
- 是否具备新闻价值、商业价值和可操作性

所有进入选题流水线的输出都会补充：

- `evidence`: 原始输入、链接或必备材料线索
- `confidence`: 当前证据强度评分
- `verification_status`: `verified` / `needs_check` / `insufficient_source`
- `limitations`: 不能直接下结论的原因
- `claim_boundary`: 该输出可被使用的边界

### 2. 素材整理 `material_builder`

用于围绕一个选题生成资料清单，包括：

- 必备材料
- 关键数据点
- 来源渠道
- 核验步骤
- 缺失数据风险

### 3. 采访策划 `interview_planner`

用于生成采访对象和采访问题，包括：

- 事实核验问题
- 原因与机制问题
- 影响和后续跟踪问题
- 采访顺序
- 采访红线和匿名信源注意事项

### 4. 摄影策划 `photo_planner`

用于把选题转化为可执行的现场拍摄方案，包括：

- 视觉主张
- 必拍画面和备选画面
- 人物肖像、工地、售楼处、小区内部等拍摄授权提醒
- 图注核验清单
- 现场画面误读风险

### 5. 信息变化监测 `signal_monitor`

用于从连续输入的信息流中识别变化信号，包括：

- 政策、市场、企业、土地、金融和城市更新领域归类
- 异常变化、趋势拐点、风险暴露、政策边际变化和主体动作识别
- 优先级排序、跟踪清单和下一步核验动作

### 6. 稿件优化 `draft_editor`

用于对初稿进行基础体检，包括：

- 清洗段落和空白
- 识别模板化表达
- 标记过长段落
- 检查数字是否缺少来源
- 给出结构建议和标题方向

### 7. 结构化模型

项目还支持三类结构化分析：

- `annual_report_parser`: 将房企年报指标转化为选题线索
- `company_comparator`: 横向比较房企利润、销售、拿地、债务和现金流
- `city_land_comparator`: 比较城市城投依赖度、市场修复程度、消化风险和专项债闭环风险

## 快速开始

```bash
git clone https://github.com/gengjudi007-max/codex.git
cd codex
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m codex.main
```

Windows 环境：

```bash
.venv\Scripts\activate
python -m codex.main
```

## 互动连接方式

统一交互层会自动识别输入类型，把自然语言、选题线索 JSON、城市土地数据、房企指标数据、年报数据或稿件文本接入对应分析模块。

命令行互动：

```bash
PYTHONPATH=src python -m codex.interactive
```

本地网页/API：

```bash
PYTHONPATH=src python -m codex.server
```

可通过环境变量或参数调整端口：

```bash
CODEX_PORT=8766 PYTHONPATH=src python -m codex.server
PYTHONPATH=src python -m codex.server --port 8766
```

启动后打开：

```text
http://127.0.0.1:8765/
```

健康检查：

```bash
curl http://127.0.0.1:8765/health
```

接口调用示例：

```bash
curl -X POST http://127.0.0.1:8765/api/interact \
  -H "Content-Type: application/json" \
  -d '{"message":"武汉土拍城投占比超70%，多宗地块底价成交，地方平台托底土地市场。"}'
```

结构化 JSON 会自动路由：

- `items`: 进入选题发现、评分、素材和采访策划流程
- `companies`: 进入房企经营横向比较模型
- `cities`: 进入城市土地市场比较模型
- `yearly` / `disposal` / `special_bonds`: 进入城投兜底拿地专题模型
- `report` / `reports`: 进入年报解析，再进入选题流程
- `mode: "draft_edit"` + `text`: 进入稿件体检流程
- `mode: "signal_monitor"` + `items`: 进入行业信息变化监测
- `tracking: true` + `items`: 自动进入行业信息变化监测
- `sources`: 抓取公开 URL 后，同时进入选题流水线和信号监测
- `mode: "search_store"` + `path` + `query`: 流式检索本地资料库
- `mode: "store_summary"` + `path`: 统计资料库规模、文件类型和状态

年报示例：

```bash
PYTHONPATH=src python examples/annual_report_case.py
```

城投公司兜底拿地专题示例：

```bash
PYTHONPATH=src python examples/city_investment_land_case.py
```

本地资料库检索示例：

```json
{
  "mode": "search_store",
  "path": "data/local_workfile_library.jsonl",
  "query": "城投 土地",
  "limit": 10
}
```

资料库统计示例：

```json
{
  "mode": "store_summary",
  "path": "data/local_workfile_library_extra.jsonl"
}
```

更多说明见 `docs/LOCAL_LIBRARY.md`。

测试：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## 稳定性设计

- 坏输入返回明确错误，不直接抛出栈信息给调用方
- 自由文本会尝试识别城市和公司，降低手动填字段成本
- API 限制请求体大小，默认 `CODEX_MAX_BODY_BYTES=1000000`
- 本地 API 支持 CORS、`OPTIONS` 和 `/health`
- 单元测试覆盖交互路由、选题识别、材料清单、稿件体检和结构化模型
- CI 会在 GitHub Actions 中对 Python 3.9 和 3.12 运行单元测试
- 输出默认区分已核验事实、待核验线索和证据不足内容
- 大型本地资料库采用流式统计和检索，避免日常检索时整库加载到内存
- 当前系统是规则和指标模型，不会替代事实核查；输出应作为报道线索和采访计划使用

## 后续开发计划

- [x] 建立房地产报道选题评分规则
- [x] 建立上市房企年报指标解析模板
- [x] 建立土地市场异动识别模板
- [x] 增加稿件基础体检模块
- [x] 增加示例和单元测试
- [ ] 接入更多政策文件、公告、市场数据等信息源
- [ ] 增加 PDF/HTML 年报自动抽取
- [ ] 增加更细的城市、公司和关键词词库
- [ ] 增加持久化任务队列和用户会话
- [ ] 增加前端结构化输入表单

## License

MIT License
