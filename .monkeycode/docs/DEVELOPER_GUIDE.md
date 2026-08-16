# 开发者指南

## 项目目的

A股自动交易助手是面向 A 股交易者的辅助交易系统。核心职责：

- 策略配置：9 个买入信号 + 12 个卖出信号 + 完整风控，可独立启停与调参
- 全市场扫描：沪深主板（排除创业板 300/301、科创板 688/689），信号触发自动模拟下单
- 模拟撮合：次日开盘价成交，处理涨跌停、停牌，按 A 股规则计费
- 策略回测：历史重放，输出收益、回撤、胜率、盈亏比与权益曲线
- 策略生成引擎：启发式生成候选策略并回测对比，可选多智能体 LLM 增强分析
- 自动交易：每个工作日 15:05（北京时间）自动扫描

相关系统：行情数据来自腾讯 K 线、新浪股票列表等公开接口；未来将通过券商适配层接入真实券商。

## 环境搭建

### 前置条件

- Python 3.11+
- Node.js 22+（仅新前端开发需要）

### 安装

```bash
# 克隆仓库
git clone <repo-url>
cd a-share-auto-trading

# 安装后端依赖
pip install --break-system-packages -r backend/requirements.txt

# 安装前端依赖（新前端）
cd frontend
npm install
```

### 环境变量

后端可选环境变量（复制 `backend/.env.example` 为 `backend/.env`）：

| 变量 | 必需 | 描述 | 示例 |
|------|------|------|------|
| `USER_LLM_API_KEY` | 否 | 用户自备的大模型 API Key | `sk-...` |
| `USER_LLM_BASE_URL` | 否 | OpenAI 兼容接口地址 | `https://api.openai.com/v1` |
| `USER_LLM_MODEL` | 否 | 模型名称 | `gpt-4o-mini` |

未配置时，策略生成的多智能体分析自动降级为启发式结论。绝不提交密钥，`.env` 已在 `.gitignore` 中。

### 运行

```bash
# 后端（默认 8001 端口，同时托管前端构建产物）
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# 前端开发服务器（5173 端口，/api 反向代理到 8001）
cd frontend
npm run dev
```

### 运行测试

```bash
# 后端
cd backend
python3 -m pytest -q

# 前端
cd frontend
npm test
```

## 开发工作流

### 代码质量工具

| 工具 | 命令 | 目的 |
|------|------|------|
| pytest | `python3 -m pytest -q` | 后端单元测试 |
| vue-tsc | `npm run build`（含类型检查） | 前端类型检查 |

### 提交前检查

1. 后端改动后运行 `python3 -m pytest -q`，确保既有测试通过
2. 前端改动后运行 `npm run build`，确保类型与构建通过
3. 检查未泄露密钥（`.env` 不提交，只提交 `.env.example`）

### 分支策略

- `main` - 生产就绪代码
- `YYMMDD-feat/fix/chore/...` - 按日期前缀的功能/修复分支

## 常见任务

### 添加新 API 端点

需修改的文件：
1. `backend/app/main.py` - 添加路由处理器
2. `backend/app/schemas.py` - 添加请求/响应模型（如需要）
3. `backend/tests/` - 添加测试

步骤：定义路由 → 实现逻辑 → 添加校验 → 编写测试 → 更新本接口文档。

### 添加新的买卖信号

需修改的文件：
1. `backend/app/schemas.py` - 在 `default_config()` 的 `buy`/`sell` 中登记信号及默认参数
2. `backend/app/strategy_engine.py` - 在 `evaluate_buy`/`evaluate_sell` 中加入判定（必要时在 `attach_indicators` 预计算指标）
3. `backend/app/patterns.py`（K 线形态信号）或 `backend/app/indicators.py`（指标信号）
4. `backend/tests/test_strategy_engine.py` - 添加测试

### 添加新的技术指标

1. 在 `backend/app/indicators.py` 中实现纯 pandas 指标函数
2. 在 `strategy_engine.attach_indicators` 中按需预计算列
3. 在 `test_indicators.py` 中补充测试

### 添加数据库字段

1. 在 `backend/app/models.py` 对应模型添加列
2. 在 `backend/app/database.py` 的 `migrate()` 中补充 `ALTER TABLE`（轻量迁移，供已存在的表）
3. 新表通过 `Base.metadata.create_all` 自动创建

### 修复 Bug

1. 编写复现 bug 的失败测试
2. 定位根因，用最小改动修复
3. 运行全量测试验证
4. 检查类似问题是否存在于其他位置

## 编码规范

### 文件组织

- 后端每个模块一个职责清晰的文件（`account.py`、`scanner.py` 等）
- 前端组件按 `views/`、`components/` 划分

### 命名

| 类型 | 约定 | 示例 |
|------|------|------|
| 后端模块 | snake_case | `strategy_engine.py` |
| 类 | PascalCase | `AccountService` |
| 函数/变量 | snake_case | `scan_and_trade` |
| 前端组件 | PascalCase | `HomeView.vue` |

### 错误处理

- 行情数据不可用抛 `DataUnavailableError`，由路由层转为 `502`
- 参数错误抛 `ValueError`，路由层转为 `400`
- 资源不存在抛 `HTTPException(404, ...)`

### 日志

- 调度器使用 `logging.getLogger("scheduler")`
- 扫描/交易关键路径记录买入、卖出、拒绝笔数

### 测试

- 测试文件位于 `backend/tests/`，命名 `test_<module>.py`
- 测试使用临时数据库与真实公开行情接口（必要时 mock）
