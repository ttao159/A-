<template>
  <div>
    <div class="card">
      <div class="card-title">回测配置</div>
      <div class="field">
        <label>选择策略</label>
        <select v-model="sid">
          <option v-for="s in strategyStore.strategies" :key="s.id" :value="s.id">
            {{ s.name }}
          </option>
        </select>
      </div>
      <div class="row date-row">
        <div class="field date-field">
          <label>开始日期</label>
          <input v-model="startDate" type="date" />
        </div>
        <div class="field date-field">
          <label>结束日期</label>
          <input v-model="endDate" type="date" />
        </div>
      </div>
      <div class="quick-ranges">
        <button
          v-for="r in QUICK_RANGES"
          :key="r.months"
          class="quick-btn"
          :class="{ active: quickMonths === r.months }"
          @click="setQuickRange(r.months)"
        >
          {{ r.label }}
        </button>
      </div>
      <button class="btn block" :disabled="loading" @click="run">
        {{ loading ? '回测中...' : '运行回测' }}
      </button>
    </div>

    <div v-if="result" class="card">
      <div class="card-title">回测结果</div>
      <BacktestResultDetail :result="result" />
    </div>

    <div v-if="viewingResult" class="scan-mask" @click.self="viewingResult = null">
      <div class="box backtest-detail">
        <div class="detail-head">
          <h3 style="margin: 0">历史回测结果</h3>
          <button class="btn ghost small" @click="viewingResult = null">关闭</button>
        </div>
        <div class="detail-body">
          <BacktestResultDetail :result="viewingResult" />
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">参数优化</div>
      <div class="opt-dims">
        <button
          v-for="d in OPTIMIZE_DIMS"
          :key="d.key"
          class="opt-dim"
          :class="{ active: selectedDims.includes(d.key) }"
          @click="toggleDim(d.key)"
        >
          <span class="opt-dim-name">{{ d.label }}</span>
          <span class="opt-dim-vals">{{ d.values.join(' / ') }}</span>
        </button>
      </div>
      <button
        class="btn block"
        :disabled="optimizing || !selectedDims.length"
        @click="runOptimize"
      >
        {{ optimizing ? `优化中 ${optimizeProgress}/${optimizeTotal}...` : `开始优化${selectedDims.length ? `（${selectedDims.length} 项）` : ''}` }}
      </button>
      <div v-if="optimizeError" class="empty">{{ optimizeError }}</div>
    </div>

    <div v-if="optimizeResults.length" class="card">
      <div class="card-title">优化结果（按累计收益降序）</div>
      <div v-if="optimizeSample" class="muted" style="font-size: 12px; margin-bottom: 6px">{{ optimizeSample }}</div>
      <div v-for="(r, i) in optimizeResults" :key="i" class="opt-row">
        <div class="opt-rank">{{ i + 1 }}</div>
        <div class="opt-params">
          <div v-for="(v, k) in r.params" :key="k" class="opt-param">{{ dimLabel(k) }}={{ v }}</div>
        </div>
        <div class="opt-metrics">
          <span :class="(r.metrics.total_return_pct ?? 0) >= 0 ? 'up' : 'down'">
            {{ fmtPct(r.metrics.total_return_pct) }}
          </span>
          <span class="muted">回撤 {{ fmtPct(r.metrics.max_drawdown_pct) }}</span>
          <span class="muted">胜率 {{ fmtPct(r.metrics.win_rate_pct) }}</span>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="hist-head">
        <span class="card-title" style="margin: 0">历史回测</span>
        <select v-model="histSort" class="sort-select">
          <option value="time">最新优先</option>
          <option value="return">收益优先</option>
          <option value="winrate">胜率优先</option>
          <option value="drawdown">回撤最小</option>
        </select>
      </div>
      <div v-if="history.length" class="hist-filters">
        <button
          v-for="f in histFilters"
          :key="f.key"
          class="filter-btn"
          :class="{ active: histFilter === f.key }"
          @click="histFilter = f.key"
        >
          {{ f.label }}
        </button>
      </div>
      <div v-if="history.length" class="hist-adv-filters">
        <div class="field hist-date">
          <input v-model="histDateStart" type="date" aria-label="开始日期" />
        </div>
        <div class="field hist-date">
          <input v-model="histDateEnd" type="date" aria-label="结束日期" />
        </div>
        <div class="field hist-name">
          <input v-model="histStrategyName" type="text" placeholder="策略名称筛选" />
        </div>
      </div>
      <div v-if="!sortedHistory.length" class="empty">暂无历史回测</div>
      <div v-for="h in sortedHistory" :key="h.id" class="hist-row">
        <div style="flex: 1">
          <div class="muted" style="font-size: 12px">
            <span v-if="h.strategy_name" class="hist-sname">{{ h.strategy_name }}</span>
            {{ h.start_date }} ~ {{ h.end_date }}
          </div>
          <div style="font-size: 13px; margin-top: 2px">
            收益 <span :class="(h.metrics.total_return_pct ?? 0) >= 0 ? 'up' : 'down'">{{ fmtPct(h.metrics.total_return_pct) }}</span>
            · 胜率 {{ fmtPct(h.metrics.win_rate_pct) }}
            · 回撤 {{ fmtPct(h.metrics.max_drawdown_pct) }}
          </div>
        </div>
        <button class="btn ghost small" :disabled="viewingId === h.id" @click="viewHistory(h)">
          {{ viewingId === h.id ? '加载中...' : '查看' }}
        </button>
        <button class="btn ghost small del" @click="removeBacktest(h)">删除</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import BacktestResultDetail from '../components/BacktestResultDetail.vue'
import { backtestApi, optimizeApi } from '../api'
import type { BacktestListItem, BacktestResult, OptimizeResultItem } from '../api/types'
import { useStrategyStore } from '../stores/strategy'
import { fmtPct } from '../utils/format'
import { todayStr, yearAgoStr, monthsAgoStr } from '../utils/date'
import { toast } from '../utils/toast'
import { confirmDialog } from '../utils/confirm'

const strategyStore = useStrategyStore()
const route = useRoute()

const sid = ref<number | string>('')
const startDate = ref(yearAgoStr())
const endDate = ref(todayStr())
const loading = ref(false)
const result = ref<BacktestResult | null>(null)
const viewingResult = ref<BacktestResult | null>(null)
const history = ref<BacktestListItem[]>([])
const viewingId = ref<number | null>(null)

const histFilter = ref<'all' | 'profit' | 'loss'>('all')
const histSort = ref<'time' | 'return' | 'winrate' | 'drawdown'>('time')
const histDateStart = ref('')
const histDateEnd = ref('')
const histStrategyName = ref('')

const histFilters = [
  { key: 'all', label: '全部' },
  { key: 'profit', label: '盈利' },
  { key: 'loss', label: '亏损' },
] as const

const sortedHistory = computed(() => {
  const nameQ = histStrategyName.value.trim()
  let list = history.value.filter((h) => {
    const ret = h.metrics.total_return_pct ?? 0
    if (histFilter.value === 'profit') return ret >= 0
    if (histFilter.value === 'loss') return ret < 0
    return true
  })
  if (histDateStart.value) {
    list = list.filter((h) => h.start_date >= histDateStart.value)
  }
  if (histDateEnd.value) {
    list = list.filter((h) => h.end_date <= histDateEnd.value)
  }
  if (nameQ) {
    list = list.filter((h) => (h.strategy_name ?? '').includes(nameQ))
  }
  const arr = [...list]
  switch (histSort.value) {
    case 'return':
      arr.sort((a, b) => (b.metrics.total_return_pct ?? 0) - (a.metrics.total_return_pct ?? 0))
      break
    case 'winrate':
      arr.sort((a, b) => (b.metrics.win_rate_pct ?? 0) - (a.metrics.win_rate_pct ?? 0))
      break
    case 'drawdown':
      arr.sort((a, b) => (a.metrics.max_drawdown_pct ?? 0) - (b.metrics.max_drawdown_pct ?? 0))
      break
    case 'time':
    default:
      arr.sort((a, b) => b.id - a.id)
      break
  }
  return arr
})

const QUICK_RANGES = [
  { label: '近1月', months: 1 },
  { label: '近3月', months: 3 },
  { label: '近6月', months: 6 },
  { label: '近1年', months: 12 },
]

const quickMonths = ref(12)

function setQuickRange(months: number) {
  quickMonths.value = months
  startDate.value = monthsAgoStr(months)
  endDate.value = todayStr()
}

const OPTIMIZE_DIMS = [
  { key: 'buy.maCross.shortPeriod', label: '均线短周期', values: [5, 10, 15] },
  { key: 'buy.maCross.longPeriod', label: '均线长周期', values: [20, 30, 60] },
  { key: 'buy.breakHigh.days', label: '突破天数', values: [10, 20, 30] },
  { key: 'sell.takeProfit.percent', label: '止盈百分比', values: [5, 10, 15, 20] },
  { key: 'sell.stopLoss.percent', label: '止损百分比', values: [3, 5, 8] },
  { key: 'sell.trailingStop.drawdown', label: '移动止盈回撤', values: [5, 8, 12] },
  { key: 'risk.maxPositionPercent', label: '单只最大仓位', values: [10, 15, 20, 25] },
] as const

const selectedDims = ref<string[]>([])
const optimizing = ref(false)
const optimizeProgress = ref(0)
const optimizeTotal = ref(0)
const optimizeError = ref('')
const optimizeResults = ref<OptimizeResultItem[]>([])
const optimizeSample = ref('')

onMounted(async () => {
  await strategyStore.fetch()
  if (route.query.sid) sid.value = Number(route.query.sid)
  else if (strategyStore.strategies.length) sid.value = strategyStore.strategies[0].id
  loadHistory()
})

async function run() {
  if (!sid.value) return
  toast('历史回测不代表未来行情效果，仅作学习参考')
  loading.value = true
  try {
    result.value = await backtestApi.run(Number(sid.value), startDate.value, endDate.value)
    loadHistory()
  } catch (e) {
    toast((e as Error).message)
  } finally {
    loading.value = false
  }
}

async function loadHistory() {
  try {
    history.value = await backtestApi.listAll()
  } catch (e) {
    // 历史加载失败不阻塞
  }
}

async function viewHistory(h: BacktestListItem) {
  viewingId.value = h.id
  try {
    viewingResult.value = await backtestApi.get(h.strategy_id, h.id)
  } catch (e) {
    toast((e as Error).message)
  } finally {
    viewingId.value = null
  }
}

async function removeBacktest(h: BacktestListItem) {
  const ok = await confirmDialog({
    title: '删除回测',
    message: `确定删除 ${h.start_date} ~ ${h.end_date} 的回测记录吗？此操作不可恢复。`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return
  try {
    await backtestApi.remove(h.strategy_id, h.id)
    history.value = history.value.filter((x) => x.id !== h.id)
    if (result.value?.id === h.id) result.value = null
    if (viewingResult.value?.id === h.id) viewingResult.value = null
    toast('已删除')
  } catch (e) {
    toast((e as Error).message)
  }
}

function dimLabel(key: string) {
  return OPTIMIZE_DIMS.find((d) => d.key === key)?.label ?? key
}

function toggleDim(key: string) {
  const i = selectedDims.value.indexOf(key)
  if (i >= 0) selectedDims.value.splice(i, 1)
  else selectedDims.value.push(key)
}

async function runOptimize() {
  if (!sid.value || !selectedDims.value.length) return
  toast('历史回测不代表未来行情效果，仅作学习参考')
  optimizing.value = true
  optimizeError.value = ''
  optimizeResults.value = []
  optimizeProgress.value = 0
  optimizeTotal.value = 0
  const grid: Record<string, unknown[]> = {}
  for (const d of OPTIMIZE_DIMS) {
    if (selectedDims.value.includes(d.key)) grid[d.key] = [...d.values]
  }
  try {
    await optimizeApi.stream(Number(sid.value), startDate.value, endDate.value, grid, (e) => {
      if (e.type === 'progress') {
        optimizeProgress.value = Number(e.done ?? 0)
        optimizeTotal.value = Number(e.total ?? 0)
      } else if (e.type === 'result') {
        optimizeResults.value = (e.results as OptimizeResultItem[]) ?? []
        const sample = e.sample as { sampled_stocks?: number; total_stocks?: number } | undefined
        if (sample && sample.total_stocks) {
          optimizeSample.value = `基于 ${sample.sampled_stocks}/${sample.total_stocks} 只股票抽样`
        }
      } else if (e.type === 'error') {
        optimizeError.value = String(e.detail ?? '优化失败')
      }
    })
  } catch (err) {
    optimizeError.value = (err as Error).message
  } finally {
    optimizing.value = false
  }
}
</script>

<style scoped>
.hist-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.sort-select {
  width: auto;
  min-height: 32px;
  height: 32px;
  padding: 0 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--card);
  color: var(--text-2);
  font-size: 13px;
}

.hist-filters {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.filter-btn {
  flex: 1;
  min-height: 36px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
}

.filter-btn:active {
  opacity: 0.7;
}

.filter-btn.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.hist-adv-filters {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.hist-adv-filters .field {
  margin: 0;
}

.hist-date {
  flex: 1;
  min-width: 0;
}

.hist-name {
  flex: 1.4;
  min-width: 0;
}

.hist-adv-filters input {
  width: 100%;
  height: 34px;
  padding: 0 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--card);
  color: var(--text);
  font-size: 13px;
  box-sizing: border-box;
}

.hist-sname {
  display: inline-block;
  margin-right: 6px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--focus-ring);
  color: var(--primary);
  font-size: 11px;
}

.hist-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--border);
}

.btn.small {
  height: 28px;
  padding: 0 12px;
  font-size: 12px;
}

.btn.small.del {
  color: var(--danger);
  border-color: var(--danger);
}

.date-row {
  gap: 8px;
}

.date-field {
  flex: 1;
  margin: 0;
}

.quick-ranges {
  display: flex;
  gap: 6px;
  margin: 2px 0 12px;
}

.quick-btn {
  flex: 1;
  min-height: 36px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text-2);
  font-size: 13px;
  cursor: pointer;
}

.quick-btn:active {
  opacity: 0.7;
}

.quick-btn.active {
  background: var(--focus-ring);
  color: var(--primary);
  border-color: var(--primary);
  font-weight: 600;
}

.opt-dims {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.opt-dim {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--card);
  color: var(--text);
  font-size: 14px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.opt-dim:active {
  opacity: 0.8;
}

.opt-dim-name {
  font-weight: 500;
}

.opt-dim-vals {
  font-size: 12px;
  color: var(--text-2);
  font-variant-numeric: tabular-nums;
}

.opt-dim.active {
  border-color: var(--primary);
  background: var(--focus-ring);
}

.opt-dim.active .opt-dim-name {
  color: var(--primary);
  font-weight: 600;
}

.opt-dim.active .opt-dim-vals {
  color: var(--primary);
}

.opt-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--border);
}

.opt-row:last-child {
  border-bottom: none;
}

.opt-rank {
  flex: 0 0 auto;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--bg);
  color: var(--text-2);
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.opt-params {
  flex: 1;
  min-width: 0;
}

.opt-param {
  font-size: 12px;
  color: var(--text-2);
}

.opt-metrics {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  font-size: 12px;
}

.scan-mask .backtest-detail {
  width: 92%;
  max-width: 480px;
  max-height: 85%;
  overflow-y: auto;
  text-align: left;
  padding: 16px;
  box-sizing: border-box;
}

.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}
</style>
