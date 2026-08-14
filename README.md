# A股自动交易助手

面向 A 股交易者的辅助交易系统：配置策略后，系统自动扫描全市场、模拟撮合成交、监控账户与持仓，并提供策略回测。

## 功能特性

- **策略配置**：9 个买入信号（均线金叉、MACD 金叉、突破 N 日最高价、放量突破 + K 线形态锤子线、看涨吞没、早晨之星、红三兵、双底）+ 12 个卖出信号（固定止盈、固定止损、移动止盈、均线死叉、MACD 死叉、跌破均线、持有天数到期 + K 线形态上吊线、看跌吞没、黄昏之星、三只乌鸦、双顶），全部可独立启停并配置参数。
- **全市场扫描**：沪深主板，自动排除创业板（300/301）与科创板（688/689）。
- **模拟撮合**：次日开盘价成交，处理涨跌停、停牌，按 A 股规则收取佣金/印花税/过户费。
- **完整风控**：单只仓位、最大持仓数、单只止损、组合止损线、最大回撤，均可配置。
- **策略回测**：历史行情重放，输出累计收益率、年化收益率、最大回撤、胜率、盈亏比、权益曲线。
- **自动交易**：每个交易日 15:05（北京时间）自动扫描交易，也支持手动触发。
- **手机预览界面**：模拟安卓手机的 Web 界面，实时增删改策略、查看账户与持仓、一键扫描、查看回测。

## 技术栈

- 后端：Python 3.11 + FastAPI + SQLAlchemy + pandas + APScheduler + akshare
- 前端：原生 HTML/CSS/JS（安卓风格手机预览），由后端静态托管
- 存储：SQLite

## 目录结构

```
.
├── index.html / style.css / app.js   # 前端手机预览界面
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py          # FastAPI 入口与 REST 路由
│   │   ├── config.py        # 全局配置（费用、排除板块、扫描时间）
│   │   ├── database.py      # 数据库连接与迁移
│   │   ├── models.py        # ORM 模型
│   │   ├── schemas.py       # Pydantic 模型与默认策略
│   │   ├── indicators.py    # 技术指标计算
│   │   ├── patterns.py      # K 线技术形态识别
│   │   ├── market.py        # 行情服务（akshare + 合成数据降级）
│   │   ├── strategy_engine.py  # 买卖信号判定
│   │   ├── matching.py      # 撮合与费用
│   │   ├── account.py       # 组合逻辑与账户服务
│   │   ├── backtest.py      # 回测引擎
│   │   ├── scanner.py       # 自动扫描交易
│   │   └── scheduler.py     # 定时调度
│   └── tests/               # 单元测试
└── .monkeycode/specs/a-share-auto-trading/  # 需求与技术设计文档
```

## 本地部署

```bash
# 安装依赖（需 Python 3.11+）
pip install -r backend/requirements.txt

# 启动后端（默认 8001 端口，同时托管前端页面）
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

启动后浏览器访问 `http://localhost:8001` 即可看到手机预览界面。

## 运行测试

```bash
cd backend
python3 -m pytest tests/ -v
```

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/strategies` | 策略列表 / 新建 |
| PUT/DELETE | `/api/strategies/{id}` | 更新 / 删除策略 |
| POST | `/api/strategies/{id}/backtest` | 运行回测 |
| GET | `/api/strategies/{id}/backtests/{bid}` | 回测结果 |
| POST | `/api/scan` | 手动触发全市场扫描交易 |
| POST | `/api/account/reset` | 重置模拟账户 |
| GET | `/api/account` | 账户总览 |
| GET | `/api/positions` | 持仓（含现价盈亏） |
| GET | `/api/trades` | 交易记录 |
| GET | `/api/stocks` | 标的池股票列表 |
| GET | `/api/stocks/{code}/bars?days=90` | 单只股票 K 线数据 |

## 说明

- 行情数据优先使用 akshare 真实数据；当网络不可用或接口失败时，自动降级为带趋势的合成数据（按股票代码生成、可复现，价格围绕样本股真实价位基准波动），保证功能完整可演示。
- 本系统为模拟交易，成交使用下一交易日开盘价，遵循 A 股 T+1 制度（买入当日不可卖出），不接入真实券商、不涉及真实资金。
- 风控支持单只最大亏损 `maxSingleLoss`（配置 > 0 时强制生效）、单只仓位、最大持仓数、组合止损、最大回撤。
