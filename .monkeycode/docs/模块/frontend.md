# frontend

新的前端工程，采用 Vue 3 + Vite + TypeScript，移动端优先，重构旧的安卓风格手机预览界面。

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
    ├── App.vue          # 根组件
    ├── env.d.ts         # Vite 类型声明
    ├── router/index.ts  # 路由配置
    └── views/HomeView.vue  # 首页视图（占位）
```

## 关键文件

| 文件 | 目的 |
|------|------|
| `vite.config.ts` | 开发服务器配置，`/api` 反向代理到 `http://localhost:8001` |
| `src/main.ts` | 应用入口，挂载 Pinia 与 Vue Router |

## 依赖

**本模块依赖**:
- `vue`、`pinia`、`vue-router`
- `vite`、`@vitejs/plugin-vue`、`typescript`、`vue-tsc`（开发依赖）
- 后端 `/api` 接口

**依赖本模块的**:
- 无（前端顶层）

## 规范

### 文件命名

- 视图组件 PascalCase（`HomeView.vue`）
- 类型声明 `env.d.ts`

### 目录约定

- `views/` - 页面级视图
- `components/` - 可复用组件（待建）
- `stores/` - Pinia 状态（待建）
- `api/` - REST 与 NDJSON 封装（待建）

### 测试

前端测试将在后续任务补充（当前仅骨架）。

## 添加新文件

### 添加新视图

1. 在 `src/views/` 创建 `XxxView.vue`
2. 在 `src/router/index.ts` 注册路由
3. 运行 `npm run build` 验证类型

**检查清单**:
- [ ] 遵循命名约定
- [ ] 路由已注册
- [ ] 类型检查通过
