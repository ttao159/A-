# A股自动交易助手 文档

本文档覆盖系统架构、公开接口、开发工作流与核心领域概念，面向希望理解或贡献本项目的开发者。

**快速链接**: [架构](./ARCHITECTURE.md) | [接口](./INTERFACES.md) | [开发者指南](./DEVELOPER_GUIDE.md)

---

## 核心文档

### [架构](./ARCHITECTURE.md)
系统设计、技术栈、组件结构与数据流程。从这里开始了解系统如何运作。

### [接口](./INTERFACES.md)
REST 与 NDJSON 流式接口、请求/响应格式。集成或使用本系统的参考。

### [开发者指南](./DEVELOPER_GUIDE.md)
环境搭建、开发工作流、编码规范和常见任务。贡献者必读。

---

## 模块

| 模块 | 描述 | README |
|------|------|--------|
| `backend/app/` | 后端核心业务（路由、账户、扫描、回测、生成引擎） | [README](./模块/backend-app.md) |
| `frontend/` | 新前端（Vue 3 + Vite + TypeScript） | [README](./模块/frontend.md) |

---

## 核心概念

理解这些领域概念有助于导航代码库：

| 概念 | 描述 |
|------|------|
| [Strategy](./专有概念/Strategy.md) | 策略，独立本金与买卖信号的交易规则 |
| [Matching](./专有概念/Matching.md) | 撮合与费用，次日开盘价成交与 A 股计费 |
| [Backtest](./专有概念/Backtest.md) | 回测，历史重放与统计指标 |
| [BrokerAdapter](./专有概念/BrokerAdapter.md) | 券商适配层，屏蔽模拟盘与实盘差异 |

---

## 入门指南

### 项目新人？

按此路径学习：
1. **[架构](./ARCHITECTURE.md)** - 了解全局
2. **[核心概念](#核心概念)** - 学习领域术语
3. **[开发者指南](./DEVELOPER_GUIDE.md)** - 搭建环境
4. **[接口](./INTERFACES.md)** - 探索公开 API

### 需要集成？

1. **[接口](./INTERFACES.md)** - API 契约
2. **[架构](./ARCHITECTURE.md)** - 系统边界和数据流

### 首次贡献？

1. **[开发者指南](./DEVELOPER_GUIDE.md)** - 搭建和工作流
2. **[常见任务](./DEVELOPER_GUIDE.md#常见任务)** - 分步指南

---

## 快速参考

### 命令

```bash
# 后端
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001
python3 -m pytest -q

# 前端
cd frontend
npm install
npm run dev
```

### 重要文件

| 文件 | 目的 |
|------|------|
| `backend/app/main.py` | 后端入口与全部路由 |
| `backend/app/config.py` | 全局配置 |
| `backend/.env.example` | 环境变量模板 |
| `frontend/vite.config.ts` | 前端代理与开发服务器配置 |
