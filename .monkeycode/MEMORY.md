# User Instruction Memory

This file records user instructions, preferences, and teachings for reference in future interactions.

## Format

### User Instruction Entry
User instruction entries should follow this format:

[User Instruction Summary]
- Date: [YYYY-MM-DD]
- Context: [Mentioned scenario or time]
- Instructions:
  - [Content of user teaching or instruction, described line by line]

### Project Knowledge Entry
Entries discovered by the Agent during task execution should follow this format:

[Project Knowledge Summary]
- Date: [YYYY-MM-DD]
- Context: Discovered by Agent while performing [specific task description]
- Category: [Operations & Deployment|Build Methods|Testing Methods|Troubleshooting & Debugging|Workflow & Collaboration|Environment Configuration]
- Instructions:
  - [Specific knowledge points, described line by line]

## Deduplication Strategy
- Before adding a new entry, check for similar or identical instructions.
- If a duplicate is found, skip the new entry or merge it with the existing one.
- When merging, update the context or date information.
- This helps avoid redundant entries and keeps the memory file tidy.

## Entries

[A股自动交易助手 后端启动与预览]
- Date: 2026-08-14
- Context: Discovered by Agent while building the A-share auto-trading backend and preview
- Category: Operations & Deployment
- Instructions:
  - 后端服务启动命令：`cd /workspace/backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001`
  - 前端页面由 FastAPI 静态托管，直接访问后端 8001 端口即可，无需单独启动 http.server
  - 服务启动必须使用 background terminal 工具管理（background_terminal_create / list / kill），不得用 `&` 后台挂起
  - 依赖安装命令：`pip3 install --break-system-packages -r backend/requirements.txt`

[A股自动交易助手 测试运行]
- Date: 2026-08-14
- Context: Discovered by Agent while writing unit tests
- Category: Testing Methods
- Instructions:
  - 测试框架为 pytest，运行命令：`cd /workspace/backend && python3 -m pytest tests/ -v`
  - 测试目录为 `backend/tests/`，conftest.py 负责将 backend 目录加入 sys.path

[A股自动交易助手 用户决策约定]
- Date: 2026-08-14
- Context: User repeatedly said "你决定" when asked to choose next steps
- Category: Workflow & Collaboration
- Instructions:
  - 用户说「你决定」「你看着办」时，由 agent 自行决策并推进，不再反复询问
  - 用户默认用中文交流

[A股自动交易助手 公开行情API可用性]
- Date: 2026-08-14
- Context: Discovered by Agent while implementing strategy generation engine (public_data.py)
- Category: Troubleshooting & Debugging
- Instructions:
  - 当前预览环境可用的公开行情接口：腾讯 K 线 `web.ifzq.gtimg.cn/appstock/app/fqkline/get`（前复权日线）、腾讯实时 `qt.gtimg.cn/q=`（GBK 编码）、新浪股票列表 `vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?node=hs_a`
  - 不可用接口：东方财富 push2 系列（返回空）、腾讯 stock.gtimg.cn 榜单接口（返回空）、akshare（内部东财接口被限制）
  - 全系统行情数据已统一为公开 API 真实数据（MarketDataService 继承 PublicDataService），禁用合成数据；日线带 10 分钟 TTL 缓存、股票列表 1 小时缓存、并发预取（16 线程）
  - 腾讯 K 线复权参数：qfq 前复权（最新价=真实价，但极早期历史价可能为负，如茅台 2001 年）；hfq 后复权（恒为正，长期趋势/收益计算更可靠）。年K 等长周期显示默认用 hfq 避免负价
  - 回测必须用前复权 qfq 价（量级接近真实价才能正确计算成交手数），后复权 hfq 价放大数倍会导致无法满 100 股成手；两者仅差一个常数因子，信号等价
  - 前复权回测对分红送股天然精确：qfq 价把送股倍数折入价格，恒定股数下的收益率/盈亏金额/股数都与真实（含送股）完全一致，无需做除权股数调整；现金分红被隐式再投资进价格，总资产口径精确（仅现金余额明细有细微差异，策略不涉及分红现金逻辑时可忽略）

[回复建议呈现方式]
- Date: 2026-08-16
- Context: User instructed on how recommendations/suggestions should be presented
- Instructions:
  - 以后每一个建议都以对话选择方式呈现：需要给出建议、推荐或方案选择时，用 question 工具提供选项让用户选择，而不是直接输出建议文字
