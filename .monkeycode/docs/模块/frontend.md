# frontend

新的前端工程，采用 Vue 3 + Vite + TypeScript + Pinia + Vue Router，移动端优先，重构旧的安卓风格手机预览界面，支持暗色模式与下拉刷新。

## 结构

```
frontend/
├── index.html           # 入口 HTML
├── vite.config.ts       # Vite 配置（/api 反向代理到后端 8001）
├── tsconfig.json        # TypeScript 配置
├── tsconfig.node.json   # Vite 配置的类型检查
├── package.json         # 依赖与脚本
└── src/
    ├── main.ts          # 应用入口（注册 Pinia 与 Router）
    ├── App.vue          # 根组件（底部导航 + 主题）
    ├── env.d.ts         # Vite 类型声明
    ├── style.css        # 全局样式（暗色主题变量）
    ├── router/index.ts  # 路由配置
    ├── views/           # 页面级视图
    │   ├── HomeView.vue       # 首页（账户总览、权益曲线、每日盈亏）
    │   ├── StrategyView.vue   # 策略管理
    │   ├── BacktestView.vue   # 回测与参数优化
    │   ├── GeneratorView.vue  # 策略生成引擎
    │   ├── TradeView.vue      # 交易（委托/持仓）
    │   ├── AlertsView.vue     # 预警中心
    │   ├── StockDetail.vue    # 个股详情
    │   └── AboutView.vue      # 说明页
    ├── components/      # 可复用组件
    │   ├── EquityChart.vue        # 权益曲线图
    │   ├── EquityCurve.vue        # 多策略叠加权益曲线
    │   ├── BacktestResultDetail.vue # 回测结果详情（内联与弹窗共用）
    │   ├── TradeMarkKline.vue     # 个股买卖点 K 线
    │   ├── PositionList.vue       # 持仓列表
    │   ├── OrderPanel.vue         # 下单面板
    │   ├── StrategyEditor.vue     # 策略编辑器
    │   ├── StrategyCompare.vue    # 策略对比
    │   └── ...                    # 其余卡片/图标/骨架屏等
    ├── stores/          # Pinia 状态（account/position/strategy/trade）
    ├── api/             # REST 与 NDJSON 封装（http/index/types）
    ├── composables/     # 组合式函数（pullRefresh/useThemeRedraw）
    └── utils/           # 工具函数（date/format/signals/theme/alerts/canvas 等）
```

## 关键文件

| 文件 | 目的 |
|------|------|
| `vite.config.ts` | 开发服务器配置，`/api` 反向代理到 `http://localhost:8001` |
| `src/main.ts` | 应用入口，挂载 Pinia 与 Vue Router |
| `src/api/index.ts` | 全部后端接口封装（策略/回测/优化/生成/扫描/账户/预警/下单） |
| `src/api/types.ts` | 与后端 Pydantic 模型对应的 TypeScript 类型 |
| `src/stores/*` | Pinia 状态管理，跨视图共享数据与加载态 |

## 依赖

**本模块依赖**:
- `vue`、`pinia`、`vue-router`
- `vite`、`@vitejs/plugin-vue`、`typescript`、`vue-tsc`、`vitest`（开发依赖）
- 后端 `/api` 接口

**依赖本模块的**:
- 无（前端顶层）

## 规范

### 文件命名

- 视图组件 PascalCase（`HomeView.vue`）
- 通用组件 PascalCase（`EquityChart.vue`）
- 工具/组合式函数 camelCase（`date.ts`、`useThemeRedraw.ts`）
- 类型声明 `env.d.ts`

### 目录约定

- `views/` - 页面级视图，对应路由
- `components/` - 可复用组件
- `stores/` - Pinia 状态
- `api/` - REST 与 NDJSON 封装
- `composables/` - 组合式函数
- `utils/` - 纯函数工具

### 测试

- 使用 `vitest`，测试文件位于 `src/utils/__tests__/`
- 运行 `npm test`（静默模式）或 `npx vitest run` 执行全部测试

## 添加新文件

### 添加新视图

1. 在 `src/views/` 创建 `XxxView.vue`
2. 在 `src/router/index.ts` 注册路由
3. 运行 `npm run build` 验证类型

### 添加新接口封装

1. 在 `src/api/types.ts` 定义请求/响应类型
2. 在 `src/api/index.ts` 添加对应方法
3. 运行 `npm run build` 验证类型

**检查清单**:
- [ ] 遵循命名约定
- [ ] 路由已注册
- [ ] 类型检查通过
- [ ] 相关测试通过
