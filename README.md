# A股自动交易助手

面向 A 股交易者的辅助交易系统：配置策略后，系统自动扫描全市场、模拟撮合成交、监控账户与持仓，并提供策略回测、参数优化与策略生成。

## 功能特性

- **策略配置**：9 个买入信号（均线金叉、MACD 金叉、突破 N 日最高价、放量突破 + K 线形态锤子线、看涨吞没、早晨之星、红三兵、双底）+ 12 个卖出信号（固定止盈、固定止损、移动止盈、均线死叉、MACD 死叉、跌破均线、持有天数到期 + K 线形态上吊线、看跌吞没、黄昏之星、三只乌鸦、双顶），全部可独立启停并配置参数。
- **全市场扫描**：沪深主板，自动排除创业板（300/301）与科创板（688/689）；支持手动触发与每个交易日 15:05（北京时间）自动扫描，扫描报告可回看详情。
- **模拟撮合**：次日开盘价成交，处理涨跌停、停牌，按 A 股规则收取佣金/印花税/过户费；遵循 T+1 制度。
- **完整风控**：单只仓位、最大持仓数、单只止损、组合止损线、最大回撤，均可配置。
- **策略回测**：历史行情重放，输出累计收益率、年化收益率、最大回撤、胜率、盈亏比、权益曲线与信号统计；支持近 1 月/3 月/6 月/1 年快捷区间，历史回测按盈亏分类、按收益/胜率/回撤排序，可查看与删除。
- **参数优化**：对策略参数网格搜索，输出多组参数的指标对比，支持流式进度。
- **策略生成引擎**：输入标的范围、回测区间、风险偏好、生成数量与收益目标，启发式生成多个候选策略，使用公开 API 真实日线数据回测，输出多策略对比（指标表 + 叠加权益曲线）与推荐策略，支持一键保存；生成历史按风险分类筛选、可查看与删除。
- **预警中心**：汇总策略的止盈/止损、组合止损、回撤等触发预警。
- **手动下单**：两阶段 prepare/confirm，支持限价委托下单。
- **手机预览界面**：Vue 3 移动端优先界面，含首页、策略、回测、策略生成、交易、预警、个股详情与说明页，支持暗色模式、下拉刷新。

## 技术栈

- 后端：Python 3.11 + FastAPI + SQLAlchemy + pandas + APScheduler
- 前端：Vue 3 + Vite + TypeScript + Pinia + Vue Router（移动端优先，安卓风格）
- 存储：SQLite
- 行情数据：全系统统一使用公开 HTTP API（腾讯 K 线前复权日线 / 实时行情 / 分时 + 新浪股票列表 + 指数行情），禁用合成数据，带内存 TTL 缓存与并发预取

## 目录结构

```
.
├── frontend/                    # Vue 3 + Vite + TypeScript 前端
│   └── src/
│       ├── views/               # 页面视图（首页/策略/回测/生成/交易/预警/个股/说明）
│       ├── components/          # 可复用组件（权益曲线/买卖点K线/持仓列表等）
│       ├── stores/              # Pinia 状态（账户/持仓/策略/交易）
│       ├── api/                 # REST 与 NDJSON 封装
│       ├── composables/         # 组合式函数（下拉刷新/主题重绘）
│       └── utils/               # 工具函数（日期/格式化/信号/主题等）
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py             # FastAPI 入口与 REST 路由
│   │   ├── config.py           # 全局配置（费用、排除板块、扫描时间）
│   │   ├── database.py         # 数据库连接与迁移
│   │   ├── models.py           # ORM 模型
│   │   ├── schemas.py          # Pydantic 模型与默认策略
│   │   ├── public_data.py      # 公开行情数据源（腾讯/新浪）
│   │   ├── market.py           # 行情服务（TTL 缓存与并发预取）
│   │   ├── indicators.py       # 技术指标计算
│   │   ├── patterns.py         # K 线技术形态识别
│   │   ├── strategy_engine.py  # 买卖信号判定
│   │   ├── generator.py        # 策略生成引擎
│   │   ├── optimizer.py        # 参数优化（网格搜索）
│   │   ├── matching.py         # 撮合与费用
│   │   ├── account.py          # 组合逻辑与账户服务
│   │   ├── backtest.py         # 回测引擎
│   │   ├── scanner.py          # 自动扫描交易
│   │   ├── broker.py           # 券商适配层
│   │   └── scheduler.py        # 定时调度
│   └── tests/                  # 单元测试
├── .monkeycode/docs/           # 项目文档（架构/接口/开发者指南）
└── .monkeycode/specs/          # 需求与技术设计文档
```

## 本地部署

```bash
# 安装后端依赖（需 Python 3.11+）
pip install -r backend/requirements.txt

# 启动后端（默认 8001 端口）
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

启动后端后浏览器访问 `http://localhost:8001` 即可使用（后端托管前端构建产物）。

前端开发模式：

```bash
# 安装前端依赖
cd frontend
npm install

# 启动前端开发服务器（/api 反向代理到后端 8001）
npm run dev

# 构建前端产物
npm run build
```

## 运行测试

```bash
# 后端
cd backend
python3 -m pytest -q

# 前端
cd frontend
npm test
```

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/strategies` | 策略列表 / 新建 |
| GET | `/api/strategies/compare` | 多策略对比 |
| PUT/DELETE | `/api/strategies/{id}` | 更新 / 删除策略 |
| POST | `/api/strategies/{id}/backtest` | 运行回测 |
| GET | `/api/strategies/{id}/backtests` | 回测历史（最近 20 条） |
| GET/DELETE | `/api/strategies/{id}/backtests/{bid}` | 回测详情 / 删除 |
| POST | `/api/strategies/{id}/optimize` | 参数优化（网格搜索） |
| POST | `/api/strategies/{id}/optimize/stream` | 参数优化（NDJSON 流式） |
| POST | `/api/generator/run` | 策略生成：生成并对比多个候选策略 |
| POST | `/api/generator/run/stream` | 策略生成（NDJSON 流式） |
| GET | `/api/generator/reports` | 生成历史 |
| GET/DELETE | `/api/generator/reports/{gid}` | 生成报告详情 / 删除 |
| GET | `/api/account` | 账户总览 |
| GET | `/api/account/equity` | 账户权益曲线 |
| GET | `/api/account/daily-pnl` | 每日盈亏 |
| GET | `/api/alerts` | 预警列表 |
| GET | `/api/positions` | 持仓（含现价盈亏） |
| GET | `/api/trades` | 成交记录 |
| GET | `/api/orders` | 委托记录 |
| POST | `/api/orders/prepare` | 手动下单（预检） |
| POST | `/api/orders/confirm/{request_id}` | 手动下单（确认） |
| GET | `/api/indices` | 指数行情 |
| GET | `/api/stocks` | 标的池股票列表 |
| GET | `/api/stocks/{code}/bars?days=90` | 单只股票 K 线数据 |
| GET | `/api/stocks/{code}/minute` | 当日分时数据 |
| POST | `/api/scan` | 手动触发全市场扫描交易 |
| POST | `/api/scan/stream` | 扫描交易（NDJSON 流式） |
| GET | `/api/scan/reports` | 扫描统计与历史报告 |
| GET | `/api/scan/reports/{rid}` | 扫描报告详情 |
| POST | `/api/account/reset` | 重置模拟账户 |

## 说明

- 全系统行情数据统一来自公开 HTTP 接口（腾讯 K 线前复权日线、实时行情、分时，新浪股票列表，指数行情），真实行情、禁用合成数据；数据源不可用时接口返回明确错误。日线数据带内存缓存（10 分钟）与并发预取，全市场扫描约 2~3 分钟。
- 本系统为模拟交易，成交使用下一交易日开盘价，遵循 A 股 T+1 制度（买入当日不可卖出），不接入真实券商、不涉及真实资金。
- 风控支持单只最大亏损 `maxSingleLoss`（配置 > 0 时强制生效）、单只仓位、最大持仓数、组合止损、最大回撤。

## 风险提示与免责声明

本系统仅供技术学习、研究与模拟演练使用，不构成任何投资建议、收益承诺或买卖推荐。请务必知悉以下风险：

- **模拟盘与实盘存在差异**：模拟撮合按次日开盘价成交，未完全还原滑点、流动性、涨跌停无法成交、停牌等真实市场情况，模拟收益不代表真实收益。
- **历史回测不代表未来表现**：回测与参数优化基于历史行情，存在过拟合风险，历史最优参数在实盘中可能失效。
- **行情数据存在延迟与误差**：行情来自公开第三方接口，可能存在延迟、缺失或错误，系统对其准确性与完整性不作保证。
- **投资有风险，决策需谨慎**：股市存在本金损失风险，任何依据本系统作出的交易决策及其后果由使用者自行承担，与本项目及开发者无关。
