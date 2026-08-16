# backend/app

后端核心模块，包含 FastAPI 路由、账户与撮合、扫描交易、回测、策略生成、行情服务等全部业务逻辑。

## 结构

```
backend/app/
├── main.py            # FastAPI 入口与 REST/NDJSON 路由
├── config.py          # 全局配置（费用、排除板块、扫描时间）
├── database.py        # 数据库连接与轻量迁移
├── models.py          # ORM 模型
├── schemas.py         # Pydantic 模型与默认策略配置
├── indicators.py      # 技术指标计算
├── patterns.py        # K 线技术形态识别
├── public_data.py     # 公开数据服务（真实行情）
├── market.py          # 行情服务（TTL/磁盘缓存 + 并发预取）
├── strategy_engine.py # 买卖信号判定
├── matching.py        # 撮合与费用计算
├── account.py         # 组合逻辑与账户服务
├── backtest.py        # 回测引擎
├── optimizer.py       # 参数优化（网格搜索）
├── scanner.py         # 自动扫描交易
├── scheduler.py       # 定时调度
├── broker.py          # 券商适配层抽象基类
├── generator.py       # 策略生成引擎
└── agents.py          # 多智能体 LLM 分析框架
```

## 关键文件

| 文件 | 目的 |
|------|------|
| `main.py` | API 入口，全部路由与流式端点 |
| `account.py` | Portfolio（回测用）与 AccountService（DB 持久化，含每策略独立本金） |
| `scanner.py` | 全市场扫描交易，`scan_lock` 保证单实例运行 |
| `market.py` | 行情缓存与并发预取，全市场扫描约 2~3 分钟 |
| `backtest.py` | 回测引擎，历史行情重放与指标统计 |
| `optimizer.py` | 参数优化，网格搜索多组参数并回测对比 |
| `broker.py` | 券商适配层抽象基类，屏蔽模拟盘与实盘差异 |

## 依赖

**本模块依赖**:
- `config.py` - 全局配置
- `models.py` - ORM 模型
- `public_data.py` - 腾讯/新浪公开行情

**依赖本模块的**:
- `tests/` - 单元测试
- `frontend/` - 通过 `/api` 访问
- `main.py` - 编排各服务

## 规范

### 文件命名

- 一个文件一个职责（`account.py`、`scanner.py`）
- 服务类 PascalCase（`AccountService`、`MarketDataService`）

### 错误处理

- 行情不可用抛 `DataUnavailableError`（路由层转 502）
- 撮合失败返回 `order.status = "rejected"` 并附 `reason`

### 测试

- 测试位于 `backend/tests/`，命名 `test_<module>.py`
- 运行 `python3 -m pytest -q`（当前 127 passed）

## 添加新文件

### 添加新服务模块

1. 按职责命名创建 `app/<name>.py`
2. 实现服务类与方法
3. 在 `main.py` 中导入并接入路由
4. 在 `tests/test_<name>.py` 中添加测试

**检查清单**:
- [ ] 遵循命名约定
- [ ] 有对应测试
- [ ] 异常处理完整（DataUnavailableError / ValueError / HTTPException）
- [ ] 未泄露密钥
