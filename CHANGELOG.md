# Changelog

## 0.3.0

- ✅ 打通东方财富公告数据接口（使用真实 API）
- ✅ 添加 `fetch_announcements()` 方法到 `EastmoneyConnector`
- ✅ 使用 API：`https://np-anotice-stock.eastmoney.com/api/security/ann`
- ✅ 可获取公告：标题、时间、类别、URL、股票代码、股票名称
- ✅ 支持按股票代码过滤，或获取最新全部公告
- ✅ 现在 `EastmoneyConnector` 可获取：财务数据 + 公告数据
- ✅ 测试通过：成功获取万科A的公告数据

## 0.2.0

- 打通东方财富财务数据接口（使用真实 API）
- 添加交易所数据连接器框架（上交所、深交所、港交所）
- 修复类型错误，添加安全类型转换函数 `to_num()`
- 完成端到端集成测试（单个+批量获取财务数据）
- 系统功能完善，为后续开发打下基础

## 0.1.0

- Established the real estate reporting assistant workflow.
- Added topic discovery, scoring, material planning, interview planning, draft editing, signal monitoring, and photography planning modules.
- Added local CLI, HTTP API, examples, and unit tests.
