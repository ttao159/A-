export type NoticeLevel = 'static' | 'warning' | 'danger'

export interface Notice {
  level: NoticeLevel
  title: string
  content: string
  date: string
}

export type ChangelogTag = '新增' | '优化' | '修复' | '安全'

export interface ChangelogEntry {
  version: string
  date: string
  tag: ChangelogTag
  content: string
}

export const NOTICES: Notice[] = [
  {
    level: 'warning',
    title: '行情延迟说明',
    content: '本系统行情来自公开接口，存在一定延迟，非交易所原生实时行情，请以券商终端为准。',
    date: '2026-08',
  },
  {
    level: 'static',
    title: '系统状态',
    content: '模拟盘正常服务，实盘模式暂未接入券商通道。',
    date: '2026-08',
  },
  {
    level: 'danger',
    title: '风险提示',
    content: '本系统仅供学习与技术演示，不构成任何投资建议，实盘交易前请谨慎评估。',
    date: '2026-08',
  },
]

export const CHANGELOG: ChangelogEntry[] = [
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '形态识别升级：9 种形态、成交量确认、趋势上下文集过滤、置信度评分、支撑阻力自动画线' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: 'K线画线工具：趋势线、水平线绘制、擦除与 localStorage 持久化' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: 'K线形态智能识别：双顶/双底/头肩顶/上升三角自动检测与标注' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '策略模板扩充：MACD趋势/趋势跟随/强势追涨/零轴反弹/K线形态/均线多头排列/KDJ底背离' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '全局 UI 美化：统色方案、卡片层次、空态/加载/Toast 动画、暗色模式优化' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '用户登录与注册：bcrypt 密码哈希、JWT 认证、路由守卫' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '策略分组管理：默认分组、新建分组、批量归类/启停/删除' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '回测风险提示与历史时间/策略名筛选' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '参数实时校验：负数/百分比范围/非整数周期等非法值即时标红' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '卖出锁定最大可卖数量，仓位快捷下单（1成/3成/半仓/满仓）' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '全局回到顶部悬浮按钮' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '下单股票联想：输入代码或名称自动补全，过滤创业板/科创板并提示' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '选股结果信号列与指标快照、股价/市值区间过滤、导出 CSV、空态引导' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '说明页折叠面板重构、静态/警告/提示三色规范、行情延迟说明' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '版本日志分层归档、检测新版本、维护公告专区' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: 'AI 策略生成推理过程、参数可编辑、套用短线/波段模板' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '资金曲线加载动画占位，数据返回后再渲染' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: 'API 统一错误提示：4xx/5xx 自动 Toast（节流防刷屏），网络异常重试提示' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '本地数据持久化：持仓/账户/资金曲线刷新不丢失' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '首屏加载动画，避免白屏' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '构建分包：vue 运行时独立缓存，入口体积 57.8KB→16.3KB' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '预生成 Gzip/Brotli 压缩资源，传输体积减少约 60-70%' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '账户页卡片式分区：账户概览/资金曲线/收益日历/持仓明细/预警/系统状态可折叠' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '今日盈亏归因改横向条形图，直观展示各持仓贡献度' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '资金曲线：Y 轴刻度、悬停显示数值、近7天/近30天/近3月切换' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '收益日历红绿底色块显示盈亏，金额加粗放大' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '市场概览移至顶部横幅，系统状态信息下沉至底部折叠' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '底部导航精简为 4 项，策略中心内含策略/回测/选股/扫描二级页签' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '策略卡片操作：详情/编辑/回测收进「更多」菜单，删除独立置右并带二次确认' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '未启用策略区：零收益零仓位策略自动折叠并提示检查条件设置' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '新建策略改为右下角悬浮按钮；头部增加模拟盘/实盘切换下拉' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '条件选股：价格/涨跌幅/换手率/市值/成交额多条件筛选' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: 'AI 个股诊断：多空观点/目标价/止损/支撑阻力，未配置 LLM 时启发式降级' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '今日盈亏归因：板块/个股级当日盈亏贡献标签' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '网络断线自动重连、指数退避重试与恢复后数据补全' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: 'AI 账户诊断：健康评分、亮点/风险/建议，未配置 LLM 时启发式降级' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '下拉刷新：加载动画、箭头旋转指示与刷新成功提示' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '全局按压反馈：按钮与底部导航按压缩放过渡' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '资产卡信息层级：现金/市值资产分布条、核心数据聚合' },
  { version: '0.1.0', date: '2026-08', tag: '安全', content: '账户安全标识：本地模式与实盘风险提示' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '账户页：今日盈亏、指数涨跌点数与闪烁、策略收益率高亮、盘前倒计时' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '实时收益高亮：总盈亏大号强调、实时角标、刷新闪烁' },
  { version: '0.1.0', date: '2026-08', tag: '修复', content: '持仓收益实时显示：现价改用实时行情接口，盘中随行情更新' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '历史回测查看改为弹窗展示，关闭后停留列表原位' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '回测页排版：快捷日期区间、核心指标突出、参数优化触控选择' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '回测历史查看与删除、生成历史分类筛选与删除' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '扫描历史详情、实盘扫描确认与下次扫描倒计时' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: 'K线双指缩放、十字光标与均线显示开关' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: '委托与成交分页加载、下单数字键盘' },
  { version: '0.1.0', date: '2026-08', tag: '优化', content: '全站暗色适配、图表高清与触控体验' },
  { version: '0.1.0', date: '2026-08', tag: '新增', content: 'AI 策略生成与智能体多观点分析' },
]
