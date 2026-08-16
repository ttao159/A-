# 需求实施计划

- [x] 1. 搭建前端工程与后端券商适配层骨架
   - 创建 frontend/ 目录，初始化 Vue 3 + Vite + TypeScript 工程
   - 配置 vite.config.ts 将 /api 反向代理至后端 8001 端口
   - 创建 backend/app/broker.py，定义 BrokerAdapter 抽象基类与 broker_type
   - 安装前端依赖，确保开发服务器可启动

- [x] 2. 实现后端券商适配层
  - [x] 2.1 定义 BrokerAdapter 抽象基类接口
    - 声明 place_order / cancel_order / get_account / get_positions / get_orders / get_trades / reconcile 抽象方法
  - [x] 2.2 实现 PaperBroker 模拟券商
    - 复用 AccountService.place_order 完成模拟撮合与费用计算
    - 实现撤单、查账户、查持仓、查委托、查成交、对账
  - [x] 2.3 实现 LiveBroker 实盘券商占位
    - 各方法返回「实盘券商未接入」错误，broker_type="live"
  - [ ]* 2.4 为券商适配层编写单元测试
    - 覆盖 PaperBroker 下单/撤单/对账与资金守恒

- [x] 3. 检查点 - 确保所有测试通过
  - 运行后端 pytest，确保既有测试通过，如有疑问请询问用户

- [x] 4. 改造扫描与账户链路走券商适配器
  - [x] 4.1 修改 scanner.py 下单入口调用 BrokerAdapter
    - 将 accounts.place_order 替换为 PaperBroker 实例下单
  - [x] 4.2 扩展 models.py 与 database.py
    - 为 Order 增加 broker_type 与 external_order_id 字段并写入迁移
  - [x] 4.3 修改 main.py 账户与订单接口
    - /api/account 返回 broker_type 字段，订单接口返回外部委托号与券商类型
  - [x] 4.4 新增实盘下单二次确认接口
    - 提供下单请求与确认下发两阶段接口

- [x] 5. 检查点 - 确保后端链路完整
  - 运行 pytest 并手动触发扫描，验证模拟盘下单、账户与持仓刷新

- [x] 6. 实现前端 API 层与状态管理
  - [x] 6.1 实现 REST 与 NDJSON 流式 API 封装
    - 封装账户、策略、持仓、交易、扫描、回测、生成引擎接口
  - [x] 6.2 实现 Pinia 状态管理
    - 建立 account / strategy / position / trade store
  - [ ]* 6.3 为 API 层与 store 编写单元测试

- [x] 7. 实现前端视图与组件
  - [x] 7.1 实现移动优先布局与导航
    - 底部导航、单列布局、下拉刷新（滑动返回由安卓原生容器提供）
  - [x] 7.2 实现账户总览视图
    - 资产卡片、持仓概览组件
  - [x] 7.3 实现策略管理与编辑器视图
    - 策略列表、编辑器、分配金额输入
  - [x] 7.4 实现回测与交易记录视图
    - 回测指标与权益曲线、交易统计与明细
  - [x] 7.5 实现扫描与策略生成视图
    - 扫描流式进度遮罩、生成引擎运行

- [x] 8. 检查点 - 确保前端功能完整
  - 运行前端构建与类型检查，验证各视图可用

- [ ] 9. 实盘安全风控与状态标注
  - [ ] 9.1 实现实盘下单二次确认交互
    - 实盘模式下每笔订单下发前弹出确认
  - [ ] 9.2 实现下单金额限额与异常状态提示
    - 单笔与单日累计金额上限校验、异常订单标记与提示
  - [ ] 9.3 界面标注实盘/模拟盘状态与风险提示
    - 显著位置展示当前 broker_type 与实盘风险提示

- [ ] 10. 检查点 - 最终验证与收尾
  - 确保所有测试通过，前后端联调无误
