# Requirements Document

## Introduction

A股自动交易助手新增「策略生成引擎」：用户输入标的范围、回测区间、风险偏好、生成数量与收益目标，系统基于启发式规则自动生成多个候选交易策略，使用公开数据 API 获取真实日线行情（禁用合成数据），对全部候选策略执行回测，输出多策略对比与回测报告，辅助交易者挑选最优策略。

## Glossary

- **系统**：A股自动交易助手及其策略生成引擎
- **候选策略**：一套可被现有回测引擎直接执行的 `buy`/`sell`/`risk` 配置
- **风险偏好**：用户选择的策略风格，取值 `conservative`（保守）、`balanced`（稳健）、`aggressive`（激进）
- **标的范围**：回测与策略生成所针对的股票范围，支持单只股票、自定义股票池、全市场三类
- **公开数据 API**：无需密钥的公开 HTTP 行情接口（腾讯 K线接口、新浪股票列表接口）
- **合成数据**：系统自行生成的模拟行情，本功能中禁用
- **回测报告**：包含输入参数、候选策略配置、指标对比、排名与权益曲线的结构化输出

## Requirements

### Requirement 1: 参数输入

**User Story:** 作为交易者，我想提交策略生成参数，以便系统按照我的约束生成候选策略。

#### Acceptance Criteria

1. WHEN 用户提交策略生成请求，系统 SHALL 接受以下参数：`targets`（标的范围）、`start_date`（开始日期）、`end_date`（结束日期）、`risk_profile`（风险偏好）、`count`（生成数量）、`target_annual_return`（目标年化收益率）
2. WHEN `count` 超出 1 到 10 的范围，系统 SHALL 拒绝请求并返回明确错误信息
3. WHEN `end_date` 早于 `start_date`，系统 SHALL 拒绝请求并返回明确错误信息
4. WHEN 回测区间内可用的交易日少于 60 个，系统 SHALL 拒绝请求并返回明确错误信息
5. WHEN `targets` 为空或包含无效股票代码，系统 SHALL 拒绝请求并返回明确错误信息
6. WHEN `risk_profile` 不是 `conservative`、`balanced`、`aggressive` 之一，系统 SHALL 拒绝请求并返回明确错误信息

### Requirement 2: 策略生成

**User Story:** 作为交易者，我想让系统根据参数自动生成多个候选策略，以便对比挑选。

#### Acceptance Criteria

1. WHEN 请求参数有效，系统 SHALL 生成数量等于 `count` 的候选策略配置
2. WHERE `risk_profile=conservative`，系统 SHALL 使用保守参数集，包含较低的单只仓位上限、较小的单只止损与较低的最大回撤上限
3. WHERE `risk_profile=aggressive`，系统 SHALL 使用进取参数集，包含较高的单只仓位上限与较大的单只止损
4. WHERE `risk_profile=balanced`，系统 SHALL 使用介于保守与进取之间的默认参数集
5. WHEN 生成候选策略，系统 SHALL 确保任意两个候选策略在买入信号或卖出信号或参数取值上存在差异
6. WHEN 生成候选策略，系统 SHALL 保证每个候选策略包含至少一个启用的买入信号与一个启用的卖出信号

### Requirement 3: 公开数据源

**User Story:** 作为交易者，我想让系统只使用真实行情数据，以便回测结果可信。

#### Acceptance Criteria

1. WHEN 需要某只股票的日线数据，系统 SHALL 通过腾讯 K线公开接口获取真实日线行情
2. WHEN 需要全市场股票列表，系统 SHALL 通过新浪股票列表公开接口获取真实股票代码与名称
3. WHEN 需要日线行情，系统 SHALL 使用前复权价格数据
4. IF 任一公开数据接口请求失败或返回空数据，系统 SHALL 返回数据源错误，系统 SHALL NOT 使用合成数据替代
5. WHEN 标的范围为单只股票或自定义股票池，系统 SHALL 仅请求该范围内的股票行情

### Requirement 4: 多策略回测与对比

**User Story:** 作为交易者，我想对比多个候选策略的回测表现，以便选择最优策略。

#### Acceptance Criteria

1. WHEN 候选策略生成完成，系统 SHALL 对每个候选策略在相同的 `start_date` 至 `end_date` 区间内执行回测
2. WHEN 每个候选策略回测完成，系统 SHALL 计算指标：累计收益率、年化收益率、最大回撤、胜率、盈亏比、交易次数
3. WHEN 全部候选策略回测完成，系统 SHALL 依据综合评分对候选策略从优到劣排序
4. WHEN 计算综合评分，系统 SHALL 综合考量年化收益率、最大回撤与胜率
5. WHEN 用户提供了 `target_annual_return`，系统 SHALL 将年化收益率与目标值的接近程度纳入评分

### Requirement 5: 回测报告

**User Story:** 作为交易者，我想获得结构化的回测报告，以便理解生成结果。

#### Acceptance Criteria

1. WHEN 生成任务完成，系统 SHALL 返回包含输入参数的回测报告
2. WHEN 生成任务完成，系统 SHALL 返回每个候选策略的配置、回测指标与排名
3. WHEN 生成任务完成，系统 SHALL 返回每个候选策略的逐日权益曲线
4. WHEN 生成任务完成，系统 SHALL 标记综合评分最高的策略为推荐策略

### Requirement 6: 前端交互

**User Story:** 作为交易者，我想在手机界面操作策略生成，以便查看对比结果。

#### Acceptance Criteria

1. WHEN 用户打开策略生成页面，系统 SHALL 提供参数输入表单，包含标的范围、回测区间、风险偏好、生成数量与收益目标
2. WHEN 用户提交生成请求，系统 SHALL 展示候选策略的对比表格
3. WHEN 生成结果包含权益曲线，系统 SHALL 在同一坐标系内叠加展示各候选策略的权益曲线
4. IF 生成失败，系统 SHALL 展示错误信息并保留用户已填写的参数

## Out of Scope

- 接入外部 LLM API 生成策略（本版本采用启发式生成）
- 策略生成结果的持久化存储与历史批次管理
- 对生成策略进行参数寻优的遗传算法或网格搜索
