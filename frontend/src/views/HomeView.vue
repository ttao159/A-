<template>
  <div>
    <Skeleton v-if="accountStore.loading && !accountStore.account" :rows="2" />
    <div v-else-if="accountStore.error" class="empty">{{ accountStore.error }}</div>
    <template v-else>
      <div class="card clock-card">
        <div class="clock-left">
          <div class="clock-time">{{ clockTime }}</div>
          <div class="muted">{{ clockDate }}</div>
        </div>
        <div class="clock-right">
          <div class="clock-status" :class="{ trading: status.trading }">{{ status.label }}</div>
          <div v-if="status.trading" class="muted">距收盘 {{ countdown }}</div>
        </div>
      </div>

      <AssetCard v-if="accountStore.account" :account="accountStore.account" />

      <div v-if="indices.length" class="card index-bar">
        <div v-for="idx in indices" :key="idx.code" class="index-item">
          <div class="index-name">{{ idx.name }}</div>
          <div class="index-price">{{ idx.price.toFixed(2) }}</div>
          <div class="pill index-change" :class="idx.change >= 0 ? 'up' : 'down'">
            {{ idx.change >= 0 ? '+' : '' }}{{ idx.change_pct.toFixed(2) }}%
          </div>
        </div>
      </div>
      <div v-else-if="indicesError" class="card index-bar index-err">
        <span>{{ indicesError }}</span>
        <button class="retry-btn" @click="fetchIndices">重试</button>
      </div>

      <div v-if="lastUpdated" class="updated-hint">最后更新 {{ lastUpdated }}</div>

      <EquityCurve
        :points="accountStore.equity"
        :baseline="accountStore.account?.initial_capital"
      />

      <DailyPnlCalendar />

      <div v-if="strategyStore.enabled.length" class="card" style="padding: 12px 16px">
        <div class="strategy-tabs">
          <button class="strat-tab" :class="{ active: activeId === 'all' }" @click="activeId = 'all'">
            全部
          </button>
          <button
            v-for="s in strategyStore.enabled"
            :key="s.id"
            class="strat-tab"
            :class="{ active: activeId === s.id }"
            @click="activeId = s.id"
          >
            {{ s.name }}
          </button>
        </div>
        <div v-if="activeStrategy" class="strat-summary">
          <span>可用现金 {{ fmtMoneyCompact(activeStrategy.available_cash) }}</span>
          <span>市值 {{ fmtMoneyCompact(activeStrategy.mv) }}</span>
          <span :class="activeStrategy.retPct >= 0 ? 'up' : 'down'">
            收益率 {{ fmtPct(activeStrategy.retPct) }}
          </span>
        </div>
      </div>

      <div class="card">
        <div class="card-title">持仓概览</div>
        <div class="stat-row">
          <span>盈利 {{ profitCount }} 只</span>
          <span>亏损 {{ lossCount }} 只</span>
          <span class="float-pnl" :class="[floatPnl >= 0 ? 'up' : 'down', { flash: floatFlashing }]">
            浮动盈亏 {{ fmtMoney(floatPnl) }}
            <span class="realtime-tag">实时</span>
          </span>
        </div>
      </div>

      <div class="card">
        <div class="card-title">预警提醒</div>
        <div v-if="alertsError" class="error-box">
          {{ alertsError }}<br /><button class="retry-btn" @click="fetchAlerts">重试</button>
        </div>
        <div v-else-if="!alerts.length" class="empty">暂无预警记录</div>
        <template v-else>
          <div v-for="a in visibleAlerts" :key="a.id" class="alert-item">
            <span class="alert-tag" :class="isProfitAlert(a.type) ? 'up' : 'down'">{{ alertTypeLabel(a.type) }}</span>
            <span class="alert-msg">{{ a.message }}</span>
            <span class="muted">{{ fmtDateTime(a.created_at) }}</span>
          </div>
          <button
            v-if="alerts.length > ALERT_VISIBLE"
            class="btn ghost block"
            style="margin-top: 8px"
            @click="goAlerts"
          >
            查看全部 {{ alerts.length }} 条
          </button>
        </template>
      </div>

      <PositionList
        :positions="filteredPositions"
        :strategies="strategyStore.strategies"
        @open-strategy="openStrategy"
        @open-stock="openStock"
      />

      <div class="card">
        <button class="btn ghost block" @click="onReset">重置模拟账户</button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AssetCard from '../components/AssetCard.vue'
import PositionList from '../components/PositionList.vue'
import EquityCurve from '../components/EquityCurve.vue'
import DailyPnlCalendar from '../components/DailyPnlCalendar.vue'
import Skeleton from '../components/Skeleton.vue'
import { useAccountStore } from '../stores/account'
import { usePositionStore } from '../stores/position'
import { useStrategyStore } from '../stores/strategy'
import { usePullRefresh } from '../composables/pullRefresh'
import { useFlashValue } from '../composables/useFlash'
import { alertApi, indexApi } from '../api'
import type { Alert, IndexQuote } from '../api'
import { fmtMoney, fmtMoneyCompact, fmtPct, fmtDateTime } from '../utils/format'
import { isTradingTime } from '../utils/date'
import { alertTypeLabel, isProfitAlert } from '../utils/alerts'
import { confirmDialog } from '../utils/confirm'

const accountStore = useAccountStore()
const positionStore = usePositionStore()
const strategyStore = useStrategyStore()
const router = useRouter()

const activeId = ref<number | 'all'>('all')
const alerts = ref<Alert[]>([])
const indices = ref<IndexQuote[]>([])
const indicesError = ref('')
const alertsError = ref('')
const lastUpdated = ref('')

const ALERT_VISIBLE = 5
const visibleAlerts = computed(() => alerts.value.slice(0, ALERT_VISIBLE))

const now = ref(new Date())
let clockTimer: number | undefined
let pollTimer: number | undefined
let quoteTimer: number | undefined

onMounted(() => {
  refresh()
  clockTimer = window.setInterval(() => {
    now.value = new Date()
  }, 1000)
  quoteTimer = window.setInterval(() => {
    if (isTradingTime() && document.visibilityState === 'visible') fetchQuotes()
  }, 15000)
  pollTimer = window.setInterval(() => {
    if (isTradingTime() && document.visibilityState === 'visible') refresh()
  }, 60000)
})

onUnmounted(() => {
  if (clockTimer) window.clearInterval(clockTimer)
  if (pollTimer) window.clearInterval(pollTimer)
  if (quoteTimer) window.clearInterval(quoteTimer)
})

const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六']

const clockTime = computed(() => {
  const d = now.value
  return [d.getHours(), d.getMinutes(), d.getSeconds()].map((x) => String(x).padStart(2, '0')).join(':')
})

const clockDate = computed(() => {
  const d = now.value
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} 周${WEEKDAYS[d.getDay()]}`
})

const status = computed(() => {
  const d = now.value
  const day = d.getDay()
  if (day === 0 || day === 6) return { label: '周末休市', trading: false }
  const mins = d.getHours() * 60 + d.getMinutes()
  if (mins < 570) return { label: '开盘前', trading: false }
  if (mins < 690) return { label: '早盘交易中', trading: true }
  if (mins < 780) return { label: '午间休市', trading: false }
  if (mins < 900) return { label: '午后交易中', trading: true }
  return { label: '已收盘', trading: false }
})

const countdown = computed(() => {
  const d = now.value
  const close = new Date(d)
  close.setHours(15, 0, 0, 0)
  let diff = close.getTime() - d.getTime()
  if (diff < 0) diff = 0
  const h = Math.floor(diff / 3600000)
  const m = Math.floor((diff % 3600000) / 60000)
  const s = Math.floor((diff % 60000) / 1000)
  return [h, m, s].map((x) => String(x).padStart(2, '0')).join(':')
})

usePullRefresh(refresh)

async function refresh() {
  await Promise.all([
    accountStore.fetch(),
    accountStore.fetchEquity(),
    positionStore.fetch(),
    strategyStore.fetch(),
    fetchAlerts(),
    fetchIndices(),
  ])
  setLastUpdated()
}

async function fetchQuotes() {
  await Promise.all([positionStore.fetch(), fetchIndices()])
  setLastUpdated()
}

function setLastUpdated() {
  const d = new Date()
  lastUpdated.value = [d.getHours(), d.getMinutes(), d.getSeconds()]
    .map((x) => String(x).padStart(2, '0'))
    .join(':')
}

async function fetchIndices() {
  try {
    indices.value = await indexApi.list()
    indicesError.value = ''
  } catch (e) {
    indicesError.value = '指数行情加载失败'
  }
}

async function fetchAlerts() {
  try {
    alerts.value = await alertApi.list()
    alertsError.value = ''
  } catch (e) {
    alertsError.value = '预警列表加载失败'
  }
}

const filteredPositions = computed(() => {
  if (activeId.value === 'all') return positionStore.positions
  return positionStore.positions.filter((p) => p.strategy_id === activeId.value)
})

const activeStrategy = computed(() => {
  if (activeId.value === 'all') return null
  const s = strategyStore.byId(activeId.value)
  if (!s) return null
  const ps = positionStore.positions.filter((p) => p.strategy_id === s.id)
  const mv = ps.reduce((sum, p) => sum + p.qty * p.price, 0)
  const capital = s.initial_capital || 0
  const retPct = capital ? ((s.available_cash + mv - capital) / capital) * 100 : 0
  return { available_cash: s.available_cash, mv, retPct }
})

const profitCount = computed(() => filteredPositions.value.filter((p) => p.pnl > 0).length)
const lossCount = computed(() => filteredPositions.value.filter((p) => p.pnl < 0).length)
const floatPnl = computed(() => filteredPositions.value.reduce((s, p) => s + p.pnl, 0))

const floatFlashing = useFlashValue(() => floatPnl.value)

async function onReset() {
  const ok = await confirmDialog({
    title: '重置模拟账户',
    message: '将清空持仓与交易记录，各策略资金恢复本金。',
    confirmText: '重置',
    danger: true,
  })
  if (!ok) return
  await accountStore.reset()
  positionStore.fetch()
}

function openStrategy(id: number) {
  router.push({ path: '/strategy', query: { sid: String(id) } })
}

function openStock(p: { code: string; name: string }) {
  router.push({ path: `/stock/${p.code}`, query: { name: p.name } })
}

function goAlerts() {
  router.push({ path: '/alerts' })
}
</script>

<style scoped>
.clock-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.clock-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.clock-time {
  font-size: 26px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.clock-right {
  text-align: right;
}

.clock-status {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-2);
}

.clock-status.trading {
  color: var(--up);
}

.strategy-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 4px;
}

.strat-tab {
  flex: 0 0 auto;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 17px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text);
  font-size: 14px;
}

.strat-tab.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.strat-summary {
  display: flex;
  gap: 12px;
  margin-top: 10px;
  font-size: 13px;
  color: var(--text-2);
}

.stat-row {
  display: flex;
  gap: 16px;
  font-size: 14px;
}

.float-pnl {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 700;
  font-size: 15px;
  padding: 2px 8px;
  border-radius: 6px;
  font-variant-numeric: tabular-nums;
}

.float-pnl.up {
  background: var(--up-bg);
  color: var(--up);
}

.float-pnl.down {
  background: var(--down-bg);
  color: var(--down);
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px dashed var(--border);
  font-size: 13px;
}

.alert-item:last-child {
  border-bottom: none;
}

.alert-tag {
  flex: 0 0 auto;
  font-weight: 600;
  font-size: 12px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--bg);
}

.alert-msg {
  flex: 1;
}

.updated-hint {
  text-align: center;
  font-size: 12px;
  color: var(--text-2);
  margin: -4px 16px 0;
}

.index-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.index-err {
  justify-content: space-between;
  font-size: 13px;
  color: var(--text-2);
}

.index-err .retry-btn {
  margin-top: 0;
}

.index-item {
  flex: 1 0 0;
  min-width: 0;
  text-align: center;
}

.index-name {
  font-size: 12px;
  color: var(--text-2);
}

.index-price {
  font-size: 15px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.index-change {
  margin-top: 4px;
}
</style>
