<template>
  <div>
    <div class="nav-card">
      <div class="nav-pills">
        <button
          v-for="g in guides"
          :key="g.id"
          class="nav-pill"
          @click="scrollTo(g.id)"
        >
          <Icon :name="g.icon" :size="14" />
          <span>{{ g.label }}</span>
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-title"><Icon name="wallet" :size="16" /><span>账户说明</span></div>
      <div class="info-row"><span>账户模式</span><b>{{ accountStore.isLive ? '实盘' : '模拟盘' }}</b></div>
      <div class="info-row"><span>安全模式</span><b>{{ accountStore.isLive ? '真实资金·注意风险' : '本地模拟·无真实资金' }}</b></div>
      <div class="info-row"><span>数据存储</span><b>本机 · 无登录认证</b></div>
      <div class="info-row"><span>初始资金</span><b>{{ fmtMoney(accountStore.account?.initial_capital ?? 0) }}</b></div>
      <div class="info-row">
        <span class="with-icon"><Icon name="trending-up" :size="14" />资金曲线</span>
        <b>按日记录总资产</b>
      </div>
      <div class="info-row">
        <span class="with-icon"><Icon name="calendar" :size="14" />扫描时间</span>
        <b>{{ schedule }}</b>
      </div>
    </div>

    <div class="card">
      <div class="card-title"><Icon name="book" :size="16" /><span>操作指南</span></div>
      <div id="guide-account" class="guide-item">
        <Icon name="wallet" :size="16" class="guide-icon" />
        <div class="guide-body">
          <div class="guide-name">账户</div>
          <div class="guide-desc">查看总资产、资金曲线、持仓概览与预警提醒，下拉可刷新；支持 AI 账户健康度诊断与今日盈亏归因。</div>
        </div>
      </div>
      <div id="guide-trade" class="guide-item">
        <Icon name="swap" :size="16" class="guide-icon" />
        <div class="guide-body">
          <div class="guide-name">交易</div>
          <div class="guide-desc">手动下单，查看成交与委托记录，支持分页加载、状态筛选与搜索。</div>
        </div>
      </div>
      <div id="guide-center" class="guide-item">
        <Icon name="target" :size="16" class="guide-icon" />
        <div class="guide-body">
          <div class="guide-name">策略中心</div>
          <div class="guide-desc">底部「策略中心」进入，内含 4 个二级页签：策略、回测、选股、扫描。新建策略使用右下角悬浮按钮；策略卡片支持启停开关与「更多」菜单（详情/编辑/回测），删除按钮带二次确认；收益为零且空仓的策略自动收进「未启用策略」区，建议检查条件设置或运行回测。</div>
        </div>
      </div>
      <div id="guide-about" class="guide-item">
        <Icon name="info" :size="16" class="guide-icon" />
        <div class="guide-body">
          <div class="guide-name">说明</div>
          <div class="guide-desc">本页查看账户说明、数据来源、交易费用、风控与版本更新记录。</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title"><Icon name="database" :size="16" /><span>数据来源</span></div>
      <div class="info-row"><span>股票列表</span><b>新浪财经公开接口</b></div>
      <div class="info-row"><span>日线 / 分时 / 实时</span><b>腾讯行情公开接口</b></div>
      <div class="info-row"><span>全市场快照</span><b>新浪行情公开接口</b></div>
      <div class="info-row"><span>策略生成</span><b>内置智能体推理</b></div>
      <div class="muted data-note">仅使用真实公开行情，不做合成数据。</div>
    </div>

    <div class="card">
      <div class="card-title"><Icon name="activity" :size="16" /><span>扫描范围</span></div>
      <div class="muted data-note">
        沪深 A 股主板，剔除创业板（300/301）与科创板（688/689），规避高波动与涨跌幅限制差异。
      </div>
    </div>

    <div class="card">
      <div class="card-title"><Icon name="receipt" :size="16" /><span>交易费用（A 股规则）</span></div>
      <div class="info-row"><span>佣金</span><b>万 2.5（最低 5 元）</b></div>
      <div class="info-row"><span>印花税</span><b>0.05%（仅卖出）</b></div>
      <div class="info-row"><span>过户费</span><b>0.001%</b></div>
    </div>

    <div class="card">
      <div class="card-title"><Icon name="shield" :size="16" /><span>风控说明</span></div>
      <div class="info-row"><span>单笔委托上限</span><b>50 万元</b></div>
      <div class="info-row"><span>单日委托上限</span><b>200 万元</b></div>
      <div class="info-row"><span>生效条件</span><b>仅实盘模式</b></div>
    </div>

    <div class="card">
      <div class="card-title"><Icon name="target" :size="16" /><span>策略参数说明</span></div>
      <div class="guide-item no-icon">
        <div class="guide-body">
          <div class="guide-name">买入信号</div>
          <div class="guide-desc">均线金叉、MACD 金叉、突破新高、放量突破、RSI 超卖、KDJ 金叉、布林下轨反弹等，可多选组合。</div>
        </div>
      </div>
      <div class="guide-item no-icon">
        <div class="guide-body">
          <div class="guide-name">卖出信号</div>
          <div class="guide-desc">止盈、止损、移动止盈、均线死叉、MACD 死叉、跌破均线、最大持有天数等。</div>
        </div>
      </div>
      <div class="guide-item no-icon">
        <div class="guide-body">
          <div class="guide-name">风控参数</div>
          <div class="guide-desc">单只最大仓位、最大持仓数、单只最大亏损、组合整体止损、最大回撤，触发即强制生效。</div>
        </div>
      </div>
    </div>

    <div class="card">
      <button class="card-title title-btn" @click="expanded = !expanded">
        <Icon name="info" :size="16" /><span>版本信息</span>
        <span class="version-tag">v{{ version }}</span>
        <Icon :name="expanded ? 'chevron-up' : 'chevron-down'" :size="18" class="chev" />
      </button>
      <Transition name="collapse">
        <div v-show="expanded" class="changelog">
          <div class="changelog-item"><span class="changelog-tag">优化</span>账户页卡片式分区：账户概览/资金曲线/收益日历/持仓明细/预警/系统状态可折叠，状态本地记忆</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>今日盈亏归因改横向条形图，直观展示各持仓贡献度</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>资金曲线：Y 轴刻度、悬停显示数值、近7天/近30天/近3月切换</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>收益日历红绿底色块显示盈亏，金额加粗放大</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>市场概览移至顶部横幅，系统状态信息下沉至底部折叠</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>底部导航精简为 4 项（账户/交易/策略中心/说明），策略中心内含策略/回测/选股/扫描二级页签</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>策略卡片操作：详情/编辑/回测收进「更多」菜单，删除独立置右并带二次确认</div>
          <div class="changelog-item"><span class="changelog-tag">新增</span>未启用策略区：零收益零仓位策略自动折叠并提示检查条件设置</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>新建策略改为右下角悬浮按钮；头部增加模拟盘/实盘切换下拉（实盘未接入）</div>
          <div class="changelog-item"><span class="changelog-tag">新增</span>条件选股：价格/涨跌幅/换手率/市值/成交额多条件筛选</div>
          <div class="changelog-item"><span class="changelog-tag">新增</span>AI 个股诊断：多空观点/目标价/止损/支撑阻力，未配置 LLM 时启发式降级</div>
          <div class="changelog-item"><span class="changelog-tag">新增</span>今日盈亏归因：板块/个股级当日盈亏贡献标签</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>网络断线自动重连、指数退避重试与恢复后数据补全</div>
          <div class="changelog-item"><span class="changelog-tag">新增</span>AI 账户诊断：健康评分、亮点/风险/建议，未配置 LLM 时启发式降级</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>下拉刷新：加载动画、箭头旋转指示与刷新成功提示</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>全局按压反馈：按钮与底部导航按压缩放过渡</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>资产卡信息层级：现金/市值资产分布条、核心数据聚合</div>
          <div class="changelog-item"><span class="changelog-tag">新增</span>账户安全标识：本地模式与实盘风险提示</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>账户页：今日盈亏、指数涨跌点数与闪烁、策略收益率高亮、盘前倒计时</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>实时收益高亮：总盈亏大号强调、实时角标、刷新闪烁</div>
          <div class="changelog-item"><span class="changelog-tag">修复</span>持仓收益实时显示：现价改用实时行情接口，盘中随行情更新</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>历史回测查看改为弹窗展示，关闭后停留列表原位</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>回测页排版：快捷日期区间、核心指标突出、参数优化触控选择</div>
          <div class="changelog-item"><span class="changelog-tag">新增</span>回测历史查看与删除、生成历史分类筛选与删除</div>
          <div class="changelog-item"><span class="changelog-tag">新增</span>扫描历史详情、实盘扫描确认与下次扫描倒计时</div>
          <div class="changelog-item"><span class="changelog-tag">新增</span>K线双指缩放、十字光标与均线显示开关</div>
          <div class="changelog-item"><span class="changelog-tag">新增</span>委托与成交分页加载、下单数字键盘</div>
          <div class="changelog-item"><span class="changelog-tag">优化</span>全站暗色适配、图表高清与触控体验</div>
          <div class="changelog-item"><span class="changelog-tag">新增</span>AI 策略生成与智能体多观点分析</div>
        </div>
      </Transition>
    </div>

    <div class="card">
      <div class="disclaimer">
        本系统仅供学习与技术演示，模拟盘不构成任何投资建议。实盘交易存在风险，接入前请谨慎评估并核实每笔委托。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAccountStore } from '../stores/account'
import Icon from '../components/Icon.vue'
import { scanApi } from '../api'
import { fmtMoney } from '../utils/format'
import { version } from '../../package.json'

const accountStore = useAccountStore()

const guides = [
  { id: 'guide-account', label: '账户', icon: 'wallet' },
  { id: 'guide-trade', label: '交易', icon: 'swap' },
  { id: 'guide-center', label: '策略中心', icon: 'target' },
  { id: 'guide-about', label: '说明', icon: 'info' },
]

const expanded = ref(false)

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

const schedule = ref('交易日 15:05 收盘后')
onMounted(async () => {
  try {
    const r = await scanApi.reports()
    const s = r.scan_schedule
    if (s) {
      const h = String(s.hour).padStart(2, '0')
      const m = String(s.minute).padStart(2, '0')
      schedule.value = `每交易日 ${h}:${m} 自动扫描`
    }
  } catch {
    // 调度信息加载失败时保留默认文案
  }
})
</script>

<style scoped>
.nav-card {
  position: sticky;
  top: 0;
  z-index: 5;
  margin-bottom: 10px;
  padding: 8px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.nav-pills {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
}

.nav-pills::-webkit-scrollbar {
  display: none;
}

.nav-pill {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 4px;
  height: 32px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--card);
  color: var(--text-2);
  font-size: 13px;
  cursor: pointer;
  transition: transform 0.12s ease, color 0.2s ease, border-color 0.2s ease;
}

.nav-pill:active {
  transform: scale(0.95);
}

.nav-pill:first-child {
  color: var(--primary);
  border-color: var(--primary);
  background: var(--focus-ring);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-title svg {
  color: var(--primary);
}

.title-btn {
  width: 100%;
  text-align: left;
  cursor: pointer;
  background: none;
  border: none;
  padding: 0;
  color: inherit;
}

.title-btn .chev {
  margin-left: auto;
  color: var(--text-2);
}

.version-tag {
  margin-left: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--primary);
  background: var(--focus-ring);
  padding: 1px 6px;
  border-radius: 4px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px dashed var(--border);
  font-size: 14px;
}

.info-row b {
  font-weight: 600;
}

.with-icon {
  display: flex;
  align-items: center;
  gap: 5px;
}

.with-icon svg {
  color: var(--text-2);
}

.guide-item {
  display: flex;
  gap: 10px;
  padding: 9px 0;
  border-bottom: 1px dashed var(--border);
}

.guide-item:last-child {
  border-bottom: none;
}

.guide-icon {
  flex: 0 0 auto;
  margin-top: 2px;
  color: var(--primary);
}

.guide-body {
  min-width: 0;
}

.guide-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 2px;
}

.guide-desc {
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-2);
}

.data-note {
  font-size: 13px;
  line-height: 1.6;
  margin-top: 8px;
}

.changelog {
  margin-top: 8px;
}

.changelog-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 0;
  font-size: 13px;
  color: var(--text-2);
}

.changelog-tag {
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 600;
  color: var(--primary);
  background: var(--focus-ring);
  padding: 1px 6px;
  border-radius: 4px;
}

.collapse-enter-active,
.collapse-leave-active {
  transition: opacity 0.2s ease;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
}

.disclaimer {
  background: var(--warning-bg);
  border: 1px solid var(--warning);
  color: var(--warning);
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 13px;
  line-height: 1.6;
}
</style>
