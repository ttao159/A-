<template>
  <div>
    <div class="risk-alert">
      <Icon name="alert-triangle" :size="18" class="risk-alert-icon" />
      <div class="risk-alert-body">
        <div class="risk-alert-title">风险提示</div>
        <div class="risk-alert-text">本系统仅供学习与技术演示，模拟盘不构成任何投资建议。实盘交易存在风险，接入前请谨慎评估并核实每笔委托。</div>
      </div>
    </div>

    <div class="nav-card">
      <div class="nav-pills">
        <button
          v-for="g in sections"
          :key="g.id"
          class="nav-pill"
          :class="{ active: activeSection === g.id }"
          @click="activeSection = g.id"
        >
          <Icon :name="g.icon" :size="14" />
          <span>{{ g.label }}</span>
        </button>
      </div>
    </div>

    <section v-if="activeSection === 'account'">
      <FoldCard title="账户说明" icon="wallet" default-open>
        <div class="info-row"><span>账户模式</span><b>{{ accountStore.isLive ? '实盘' : '模拟盘' }}</b></div>
        <div class="info-row"><span>安全模式</span><b>{{ accountStore.isLive ? '真实资金·注意风险' : '本地模拟·无真实资金' }}</b></div>
        <div class="info-row"><span>数据存储</span><b>本机 · 用户名密码登录</b></div>
        <div class="info-row"><span>初始资金</span><b>{{ fmtMoney(accountStore.account?.initial_capital ?? 0) }}</b></div>
        <div class="info-row">
          <span class="with-icon"><Icon name="trending-up" :size="14" />资金曲线</span>
          <b>按日记录总资产</b>
        </div>
        <div class="info-row">
          <span class="with-icon"><Icon name="calendar" :size="14" />扫描时间</span>
          <b>{{ schedule }}</b>
        </div>
      </FoldCard>
    </section>

    <section v-else-if="activeSection === 'fee'">
      <FoldCard title="交易费用（A 股规则）" icon="receipt" default-open>
        <div class="info-row"><span>佣金</span><b>万 2.5（最低 5 元）</b></div>
        <div class="info-row"><span>印花税</span><b>0.05%（仅卖出）</b></div>
        <div class="info-row"><span>过户费</span><b>0.001%</b></div>
      </FoldCard>
    </section>

    <section v-else-if="activeSection === 'data'">
      <FoldCard title="扫描范围" icon="activity" default-open>
        <div class="note note-static">
          沪深 A 股主板，剔除创业板（300/301）与科创板（688/689），规避高波动与涨跌幅限制差异。
        </div>
      </FoldCard>
      <FoldCard title="数据来源" icon="database" default-open>
        <div class="info-row"><span>股票列表</span><b>新浪财经公开接口</b></div>
        <div class="info-row"><span>日线 / 分时 / 实时</span><b>腾讯行情公开接口</b></div>
        <div class="info-row"><span>全市场快照</span><b>新浪行情公开接口</b></div>
        <div class="info-row"><span>策略生成</span><b>内置智能体推理</b></div>
        <div class="note note-warning">
          行情存在延迟，非交易所原生实时行情，仅使用真实公开行情，不做合成数据。
        </div>
      </FoldCard>
    </section>

    <section v-else-if="activeSection === 'guide'">
      <FoldCard title="操作指南" icon="book" default-open>
        <div v-for="g in guideSteps" :key="g.id" class="guide-step">
          <span class="guide-step-no">{{ g.no }}</span>
          <div class="guide-step-body">
            <div class="guide-step-name">
              <Icon :name="g.icon" :size="15" class="guide-step-icon" />
              {{ g.name }}
            </div>
            <ul class="guide-step-list">
              <li v-for="(s, i) in g.steps" :key="i">{{ s }}</li>
            </ul>
          </div>
        </div>
      </FoldCard>
    </section>

    <section v-else-if="activeSection === 'risk'">
      <FoldCard title="风控说明" icon="shield" default-open>
        <div class="info-row"><span>单笔委托上限</span><b>50 万元</b></div>
        <div class="info-row"><span>单日委托上限</span><b>200 万元</b></div>
        <div class="info-row"><span>生效条件</span><b>仅实盘模式</b></div>
      </FoldCard>
      <FoldCard title="策略参数说明" icon="target" :default-open="false">
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
        <div class="guide-item no-icon">
          <div class="guide-body">
            <div class="guide-name">参数校验</div>
            <div class="guide-desc">所有信号与风控参数实时校验：负数、超出百分比范围、非整数周期等非法值即时标红并阻止保存；仅校验已启用的信号。</div>
          </div>
        </div>
      </FoldCard>
    </section>

    <section v-else-if="activeSection === 'faq'">
      <div v-for="f in faqs" :key="f.q" class="card fold-card">
        <button class="faq-head" @click="toggleFaq(f.q)">
          <Icon name="help-circle" :size="16" class="faq-q-icon" />
          <span class="faq-q">{{ f.q }}</span>
          <Icon :name="openFaq.has(f.q) ? 'chevron-up' : 'chevron-down'" :size="18" class="faq-chev" />
        </button>
        <Transition name="fold">
          <div v-show="openFaq.has(f.q)" class="faq-body">
            {{ f.a }}
          </div>
        </Transition>
      </div>
    </section>

    <section v-else-if="activeSection === 'about'">
      <FoldCard title="版本信息" icon="info" default-open>
        <div class="version-head">
          <span class="version-tag">v{{ version }}</span>
          <button class="btn ghost small" :disabled="checking" @click="checkUpdate">
            {{ checking ? '检查中...' : '检测新版本' }}
          </button>
        </div>

        <div class="sub-title">维护公告</div>
        <div v-for="(n, i) in NOTICES" :key="'n' + i" class="notice-item" :class="`notice-${n.level}`">
          <div class="notice-head">
            <span class="notice-title">{{ n.title }}</span>
            <span class="muted">{{ n.date }}</span>
          </div>
          <div class="notice-content">{{ n.content }}</div>
        </div>

        <div class="sub-title">版本日志</div>
        <div class="changelog-filter">
          <button
            v-for="t in TAG_FILTERS"
            :key="t"
            class="changelog-tab"
            :class="{ active: tagFilter === t }"
            @click="tagFilter = t"
          >
            {{ t }}
          </button>
        </div>
        <div v-for="g in groupedChangelog" :key="g.version" class="version-group">
          <button
            class="version-group-head"
            :class="{ archived: g.version !== version }"
            @click="g.version === version ? null : toggleArchive(g.version)"
          >
            <span>v{{ g.version }}{{ g.version === version ? '（当前）' : '（归档）' }}</span>
            <span class="muted">{{ g.entries.length }} 条</span>
            <Icon
              v-if="g.version !== version"
              :name="archivedOpen.includes(g.version) ? 'chevron-up' : 'chevron-down'"
              :size="16"
            />
          </button>
          <div v-if="g.version === version || archivedOpen.includes(g.version)">
            <div v-for="e in g.entries" :key="e.content" class="changelog-item">
              <span class="changelog-tag" :class="tagClass(e.tag)">{{ e.tag }}</span>
              <span>{{ e.content }}</span>
            </div>
          </div>
        </div>
        <div v-if="!groupedChangelog.length" class="muted">暂无版本记录</div>
      </FoldCard>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useAccountStore } from '../stores/account'
import Icon from '../components/Icon.vue'
import FoldCard from '../components/FoldCard.vue'
import { scanApi } from '../api'
import { fmtMoney } from '../utils/format'
import { toast } from '../utils/toast'
import { NOTICES, CHANGELOG } from '../utils/changelog'
import { compareVersions } from '../utils/version'
import { version } from '../../package.json'

const accountStore = useAccountStore()

const sections = [
  { id: 'account', label: '账户说明', icon: 'wallet' },
  { id: 'fee', label: '交易费用', icon: 'receipt' },
  { id: 'data', label: '数据来源', icon: 'database' },
  { id: 'guide', label: '操作指南', icon: 'book' },
  { id: 'risk', label: '风控说明', icon: 'shield' },
  { id: 'faq', label: '常见问题', icon: 'help-circle' },
  { id: 'about', label: '关于', icon: 'info' },
]

const activeSection = ref('account')

const guideSteps = [
  {
    id: 'account',
    no: '1',
    icon: 'wallet',
    name: '账户',
    steps: ['查看总资产、资金曲线、持仓概览与预警提醒', '下拉可刷新行情与持仓', '支持 AI 账户健康度诊断与今日盈亏归因'],
  },
  {
    id: 'trade',
    no: '2',
    icon: 'swap',
    name: '交易',
    steps: ['输入代码/名称自动联想，仅支持沪深主板', '卖出自动锁定最大可卖数量、禁止超卖', '买入支持 1成/3成/半仓/满仓快捷下单', '查看成交与委托记录，支持分页、筛选与搜索'],
  },
  {
    id: 'center',
    no: '3',
    icon: 'target',
    name: '策略中心',
    steps: ['底部「策略中心」进入，内含策略/回测/选股/扫描 4 个二级页签', '新建策略使用右下角悬浮按钮', '策略支持分组管理、批量归类/启停/删除，删除带二次确认', '参数实时校验，非法值即时标红', '回测前有风险提示，历史记录支持时间与策略名筛选'],
  },
]

const faqs = [
  {
    q: '为什么委托会被拒绝？',
    a: '常见原因包括：资金不足、持仓数量不足（超卖）、价格偏离当前行情、标的停牌或不在交易时间等。请核对委托条件后重试。',
  },
  {
    q: '模拟盘和实盘有什么区别？',
    a: '模拟盘使用本地模拟数据，无真实资金，仅供策略体验；实盘（Demo）使用随机/历史回放行情模拟，仍非真实券商通道，切换后策略将基于模拟数据决策。',
  },
  {
    q: '行情数据延迟多久？',
    a: '行情来自腾讯/新浪公开接口，存在一定延迟，非交易所原生实时行情，请以券商终端为准。',
  },
  {
    q: '策略收益显示 0.00% 是正常的吗？',
    a: '策略尚未运行或空仓时会显示 0.00%。可先运行回测查看历史效果，或检查策略条件是否合理。',
  },
  {
    q: '如何退出 Demo 只读模式？',
    a: 'Demo 模式免注册体验，只读限制下单与策略修改。使用用户名密码登录即可获得完整功能。',
  },
]

const openFaq = reactive(new Set<string>())

function toggleFaq(q: string) {
  if (openFaq.has(q)) openFaq.delete(q)
  else openFaq.add(q)
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

const TAG_FILTERS = ['全部', '新增', '优化', '修复', '安全'] as const
const tagFilter = ref<'全部' | '新增' | '优化' | '修复' | '安全'>('全部')
const archivedOpen = ref<string[]>([])
const checking = ref(false)

const filteredChangelog = computed(() => {
  if (tagFilter.value === '全部') return CHANGELOG
  return CHANGELOG.filter((e) => e.tag === tagFilter.value)
})

const groupedChangelog = computed(() => {
  const groups: { version: string; entries: typeof CHANGELOG }[] = []
  for (const e of filteredChangelog.value) {
    let g = groups.find((x) => x.version === e.version)
    if (!g) {
      g = { version: e.version, entries: [] }
      groups.push(g)
    }
    g.entries.push(e)
  }
  return groups
})

function tagClass(tag: string): string {
  if (tag === '新增') return 'tag-new'
  if (tag === '修复') return 'tag-fix'
  if (tag === '安全') return 'tag-safe'
  return 'tag-opt'
}

function toggleArchive(v: string) {
  archivedOpen.value = archivedOpen.value.includes(v)
    ? archivedOpen.value.filter((x) => x !== v)
    : [...archivedOpen.value, v]
}

async function checkUpdate() {
  checking.value = true
  try {
    const res = await fetch(`${import.meta.env.BASE_URL}versions.json`)
    if (!res.ok) throw new Error(String(res.status))
    const data = (await res.json()) as { latest?: string }
    const latest = data.latest || ''
    if (latest && compareVersions(latest, version) > 0) {
      toast(`发现新版本 v${latest}，请前往更新`)
    } else {
      toast('当前已是最新版本')
    }
  } catch {
    toast('检查更新失败，请稍后重试')
  } finally {
    checking.value = false
  }
}
</script>

<style scoped>
.risk-alert {
  display: flex;
  gap: 10px;
  margin: 12px 16px 0;
  padding: 12px 14px;
  border: 1px solid var(--warning);
  border-radius: var(--radius);
  background: var(--warning-bg);
}

.risk-alert-icon {
  flex: 0 0 auto;
  color: var(--warning);
  margin-top: 1px;
}

.risk-alert-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--warning);
  margin-bottom: 2px;
}

.risk-alert-text {
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-2);
}

.nav-card {
  position: sticky;
  top: 0;
  z-index: 5;
  margin: 12px 16px 10px;
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
  transition: transform 0.12s ease, color 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.nav-pill:active {
  transform: scale(0.95);
}

.nav-pill.active {
  color: #fff;
  border-color: var(--primary);
  background: var(--primary);
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

.guide-step {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--border);
}

.guide-step:last-child {
  border-bottom: none;
}

.guide-step-no {
  flex: 0 0 auto;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--focus-ring);
  color: var(--primary);
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 1px;
}

.guide-step-body {
  min-width: 0;
  flex: 1;
}

.guide-step-name {
  display: flex;
  align-items: center;
  gap: 5px;
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.guide-step-icon {
  color: var(--primary);
}

.guide-step-list {
  margin: 0;
  padding-left: 16px;
  font-size: 13px;
  line-height: 1.7;
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

.note {
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
}

.note-static {
  border: 1px solid var(--primary);
  background: var(--focus-ring);
  color: var(--primary);
}

.note-warning {
  border: 1px solid var(--warning);
  background: var(--warning-bg);
  color: var(--warning);
}

.faq-head {
  width: 100%;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 14px 0;
  border: none;
  background: none;
  color: var(--text);
  text-align: left;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.faq-head:active {
  opacity: 0.7;
}

.faq-q-icon {
  flex: 0 0 auto;
  color: var(--primary);
  margin-top: 2px;
}

.faq-q {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
}

.faq-chev {
  flex: 0 0 auto;
  color: var(--text-2);
}

.faq-body {
  padding: 0 0 14px 24px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-2);
}

.fold-enter-active,
.fold-leave-active {
  transition: opacity 0.18s ease;
}

.fold-enter-from,
.fold-leave-to {
  opacity: 0;
}

.version-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.version-tag {
  font-size: 12px;
  font-weight: 600;
  color: var(--primary);
  background: var(--focus-ring);
  padding: 2px 8px;
  border-radius: 4px;
}

.btn.small {
  height: 30px;
  padding: 0 12px;
  font-size: 12px;
}

.sub-title {
  margin: 12px 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.notice-item {
  margin-bottom: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
}

.notice-static {
  border: 1px solid var(--primary);
  background: var(--focus-ring);
}

.notice-warning {
  border: 1px solid var(--warning);
  background: var(--warning-bg);
}

.notice-danger {
  border: 1px solid var(--danger);
  background: var(--danger-bg);
}

.notice-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.notice-title {
  font-weight: 600;
}

.notice-content {
  line-height: 1.6;
  color: var(--text-2);
}

.changelog-filter {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.changelog-tab {
  flex: 0 0 auto;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 15px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text-2);
  font-size: 12px;
  cursor: pointer;
}

.changelog-tab.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.version-group {
  margin-top: 6px;
}

.version-group-head {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border: none;
  background: none;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  cursor: default;
}

.version-group-head.archived {
  cursor: pointer;
}

.version-group-head svg {
  margin-left: auto;
  color: var(--text-2);
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
  padding: 1px 6px;
  border-radius: 4px;
}

.tag-new {
  color: var(--primary);
  background: var(--focus-ring);
}

.tag-opt {
  color: var(--text-2);
  background: var(--bg);
}

.tag-fix {
  color: var(--warning);
  background: var(--warning-bg);
}

.tag-safe {
  color: var(--danger);
  background: var(--danger-bg);
}
</style>
