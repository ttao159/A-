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

    <FoldCard title="账户说明" icon="wallet" default-open persist-key="about-account">
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
    </FoldCard>

    <FoldCard title="交易费用（A 股规则）" icon="receipt" default-open persist-key="about-fee">
      <div class="info-row"><span>佣金</span><b>万 2.5（最低 5 元）</b></div>
      <div class="info-row"><span>印花税</span><b>0.05%（仅卖出）</b></div>
      <div class="info-row"><span>过户费</span><b>0.001%</b></div>
    </FoldCard>

    <FoldCard title="扫描范围" icon="activity" default-open persist-key="about-scope">
      <div class="note note-static">
        沪深 A 股主板，剔除创业板（300/301）与科创板（688/689），规避高波动与涨跌幅限制差异。
      </div>
    </FoldCard>

    <FoldCard title="数据来源" icon="database" default-open persist-key="about-source">
      <div class="info-row"><span>股票列表</span><b>新浪财经公开接口</b></div>
      <div class="info-row"><span>日线 / 分时 / 实时</span><b>腾讯行情公开接口</b></div>
      <div class="info-row"><span>全市场快照</span><b>新浪行情公开接口</b></div>
      <div class="info-row"><span>策略生成</span><b>内置智能体推理</b></div>
      <div class="note note-warning">
        行情存在延迟，非交易所原生实时行情，仅使用真实公开行情，不做合成数据。
      </div>
    </FoldCard>

    <FoldCard title="操作指南" icon="book" default-open persist-key="about-guide">
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
          <div class="guide-desc">手动下单（输入代码/名称自动联想，仅支持沪深主板），查看成交与委托记录，支持分页加载、状态筛选与搜索。</div>
        </div>
      </div>
      <div id="guide-center" class="guide-item">
        <Icon name="target" :size="16" class="guide-icon" />
        <div class="guide-body">
          <div class="guide-name">策略中心</div>
          <div class="guide-desc">底部「策略中心」进入，内含 4 个二级页签：策略、回测、选股、扫描。新建策略使用右下角悬浮按钮；策略卡片支持启停开关与「更多」菜单（详情/编辑/回测），删除按钮带二次确认；收益为零且空仓的策略自动收进「未启用策略」区。</div>
        </div>
      </div>
      <div id="guide-about" class="guide-item">
        <Icon name="info" :size="16" class="guide-icon" />
        <div class="guide-body">
          <div class="guide-name">说明</div>
          <div class="guide-desc">本页查看账户说明、数据来源、交易费用、风控与版本更新记录。</div>
        </div>
      </div>
    </FoldCard>

    <FoldCard title="风控说明" icon="shield" default-open persist-key="about-risk">
      <div class="info-row"><span>单笔委托上限</span><b>50 万元</b></div>
      <div class="info-row"><span>单日委托上限</span><b>200 万元</b></div>
      <div class="info-row"><span>生效条件</span><b>仅实盘模式</b></div>
    </FoldCard>

    <FoldCard title="策略参数说明" icon="target" :default-open="false" persist-key="about-params">
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
    </FoldCard>

    <FoldCard title="版本信息" icon="info" :default-open="false" persist-key="about-version">
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

    <div class="card">
      <div class="note note-danger">
        本系统仅供学习与技术演示，模拟盘不构成任何投资建议。实盘交易存在风险，接入前请谨慎评估并核实每笔委托。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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

const guides = [
  { id: 'guide-account', label: '账户', icon: 'wallet' },
  { id: 'guide-trade', label: '交易', icon: 'swap' },
  { id: 'guide-center', label: '策略中心', icon: 'target' },
  { id: 'guide-about', label: '说明', icon: 'info' },
]

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

.note-danger {
  border: 1px solid var(--danger);
  background: var(--danger-bg);
  color: var(--danger);
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
