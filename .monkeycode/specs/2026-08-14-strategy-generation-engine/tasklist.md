# Task List: 策略生成引擎（2026-08-14-strategy-generation-engine）

## 后端

- [x] 1.1 公开数据服务 `public_data.py`：腾讯 K 线接口、新浪股票列表接口、`DataUnavailableError`、主板过滤、股票名称查询
- [x] 1.2 策略生成器 `generator.py`：风险偏好映射、信号模板库、参数校验、候选策略生成、综合评分、报告组装
- [x] 1.3 请求模型 `GeneratorRequest`（schemas.py）
- [x] 1.4 路由 `POST /api/generator/run`（main.py），含 400/502 错误映射

## 前端

- [x] 2.1 「策略生成」页面：参数表单、对比表格、叠加权益曲线、错误提示

## 测试与收尾

- [x] 3.1 单元测试：`test_public_data.py`、`test_generator.py`
- [x] 3.2 集成测试与全量测试通过
- [x] 3.3 更新 README 与接口文档，提交推送
