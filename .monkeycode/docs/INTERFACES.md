# 接口文档

本系统为 REST API 服务，后端默认监听 8001 端口，所有接口以 `/api` 为前缀，另有 `/health` 健康检查接口。扫描与策略生成同时提供流式 NDJSON 端点。

前端（旧静态页面与新的 Vue 前端）通过 `/api` 访问这些接口；新前端的 Vite 开发服务器将 `/api` 反向代理到后端 8001 端口。

## 认证

当前接口无认证，面向本地单用户使用。未来接入实盘券商时将在券商适配层增加凭据管理。

## 通用约定

- 响应均为 JSON（流式接口为 `application/x-ndjson`）
- 行情数据不可用时返回 `502`，资源不存在返回 `404`，参数错误返回 `400`，扫描并发冲突返回 `409`

## 策略

### GET `/api/strategies`
策略列表。返回所有策略（含启用与停用）。

### POST `/api/strategies`
新建策略。

请求体（`StrategyCreate`）：
```json
{
  "name": "均线金叉策略",
  "enabled": true,
  "config": { "buy": {}, "sell": {}, "risk": {} },
  "initial_capital": 1000000
}
```
`initial_capital` 可选，缺省为默认 100 万。`config` 缺省为系统默认配置。

### PUT `/api/strategies/{sid}`
更新策略名称、启用状态、配置或分配本金（`initial_capital`）。调整本金时校验不低于当前持仓成本。

### DELETE `/api/strategies/{sid}`
删除策略。

## 回测

### POST `/api/strategies/{sid}/backtest`
运行回测。请求体（`BacktestRequest`）：
```json
{ "start_date": "2024-01-01", "end_date": "2025-01-01" }
```
返回指标、权益曲线、交易明细与信号统计。

### GET `/api/strategies/{sid}/backtests`
最近 20 条回测记录（不含权益曲线）。

### GET `/api/strategies/{sid}/backtests/{bid}`
单次回测详情，含权益曲线。

## 策略生成引擎

### POST `/api/generator/run`
同步生成多个候选策略并回测对比。请求体（`GeneratorRequest`）：
```json
{
  "targets": { "scope": "market", "codes": [] },
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "risk_profile": "balanced",
  "count": 5,
  "target_annual_return": 15,
  "analysis_depth": "standard"
}
```
`risk_profile` 为 `conservative` / `balanced` / `aggressive`；`analysis_depth` 为 `quick` / `standard` / `deep`。

### POST `/api/generator/run/stream`
同上，NDJSON 流式输出进度事件，末行输出完整报告。

### GET `/api/generator/reports`
策略生成历史（最近 20 条，不含完整报告）。

### GET `/api/generator/reports/{gid}`
某次生成的完整报告。

## 账户与持仓

### GET `/api/account`
账户总览。按全部策略聚合，返回：
```json
{
  "initial_capital": 2000000,
  "available_cash": 2000000,
  "market_value": 0,
  "total_asset": 2000000,
  "total_pnl": 0
}
```

### GET `/api/positions`
持仓列表，含现价、盈亏、盈亏比例、持有天数与所属策略。

### GET `/api/trades`
最近 50 条成交记录。

### POST `/api/account/reset`
重置模拟账户：清空持仓、订单与成交，各策略资金恢复其分配本金。

## 行情

### GET `/api/stocks`
标的池股票列表（沪深主板，排除创业板/科创板）。

### GET `/api/stocks/{code}/bars?days=90&period=day&adjust=qfq`
单只股票 K 线数据。`period` 支持 `day` / `week` / `month` / `year`，`adjust` 支持 `qfq` / `hfq`。

### GET `/api/stocks/{code}/minute`
当日分时数据。

## 扫描交易

### POST `/api/scan`
手动触发一次全市场扫描交易，返回扫描报告（买入/卖出/拒绝明细）。并发时返回 409。

### POST `/api/scan/stream`
同上，NDJSON 流式输出扫描进度事件，末行输出完整报告。

### GET `/api/scan/reports`
扫描统计（全量累计）与历史报告（最近 20 条明细）。

## 健康检查

### GET `/health`
返回 `{"status": "ok"}`。
