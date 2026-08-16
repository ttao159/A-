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

    <div v-if="result" ref="resultCard" class="card">
      <div class="card-title">回测结果</div>
      <div class="hero-grid">
        <div class="hero-metric">
          <div class="muted">累计收益</div>
          <div class="hero-value" :class="pnlClass(result.metrics.total_return_pct)">
            {{ fmtPct(result.metrics.total_return_pct) }}
          </div>
        </div>
        <div class="hero-metric">
          <div class="muted">年化收益</div>
          <div class="hero-value" :class="pnlClass(result.metrics.annual_return_pct)">
            {{ fmtPct(result.metrics.annual_return_pct) }}
          </div>
        </div>
        <div class="hero-metric">
          <div class="muted">最大回撤</div>
          <div class="hero-value">{{ fmtPct(result.metrics.max_drawdown_pct) }}</div>
        </div>
        <div class="hero-metric">
          <div class="muted">胜率</div>
          <div class="hero-value">{{ fmtPct(result.metrics.win_rate_pct) }}</div>
        </div>
      </div>
      <div class="sub-grid">
        <div class="sub-metric">
          <span class="muted">盈亏比</span>
          <b>{{ result.metrics.profit_loss_ratio?.toFixed(2) ?? '--' }}</b>
        </div>
        <div class="sub-metric">
          <span class="muted">交易笔数</span>
          <b>{{ result.metrics.trade_count }}</b>
        </div>
        <div class="sub-metric">
          <span class="muted">夏普比率</span>
          <b :class="pnlClass(result.metrics.sharpe_ratio)">{{ result.metrics.sharpe_ratio?.toFixed(2) ?? '--' }}</b>
        </div>
        <div class="sub-metric">
          <span class="muted">卡玛比率</span>
          <b :class="pnlClass(result.metrics.calmar_ratio)">{{ result.metrics.calmar_ratio?.toFixed(2) ?? '--' }}</b>
        </div>
        <div class="sub-metric">
          <span class="muted">索提诺比率</span>
          <b :class="pnlClass(result.metrics.sortino_ratio)">{{ result.metrics.sortino_ratio?.toFixed(2) ?? '--' }}</b>
        </div>
        <div class="sub-metric">
          <span class="muted">年化波动率</span>
          <b>{{ result.metrics.annual_volatility_pct != null ? fmtPct(result.metrics.annual_volatility_pct) : '--' }}</b>
        </div>
        <div class="sub-metric">
          <span class="muted">最长回撤天数</span>
          <b>{{ result.metrics.max_drawdown_days ?? '--' }}</b>
        </div>
      </div>
      <div class="metrics-help">
        <button class="help-toggle" @click="showHelp = !showHelp">
          指标说明 {{ showHelp ? '▴' : '▾' }}
        </button>
        <div v-if="showHelp" class="help-list">
          <div v-for="h in METRIC_HELP" :key="h.k" class="help-item">
            <b>{{ h.k }}</b><span>{{ h.v }}</span>
          </div>
        </div>
      </div>
      <div v-if="signalStats" class="sub-box">
        <div class="sub-box-title">信号统计</div>
        <div class="signal-buy">
          <span>买入信号触发</span>
          <b class="up">{{ signalStats.buy }} 次</b>
        </div>
        <div class="sub-box-sub">卖出信号触发</div>
        <div v-if="!sellStatRows.length" class="muted">暂无卖出信号</div>
        <div v-for="r in sellStatRows" :key="r.key" class="signal-row">
          <span>{{ r.label }}</span>
          <b class="down">{{ r.count }} 次</b>
        </div>
      </div>
      <div v-if="result.equity_curve?.length" class="section">
        <div class="card-title">权益曲线</div>
        <EquityChart
          :data="result.equity_curve"
          :baseline="result.metrics.initial_capital"
          :trades="tradeMarks"
        />
      </div>
      <div v-if="tradeStocks.length" class="section">
        <div class="card-title">个股买卖点</div>
        <select v-model="selectedCode" class="stock-select">
          <option v-for="s in tradeStocks" :key="s.code" :value="s.code">
            {{ s.name }}（{{ s.code }}）
          </option>
        </select>
        <div v-if="tradeKlineLoading" class="empty">K线加载中...</div>
        <TradeMarkKline v-else :bars="tradeKlineBars" :marks="selectedMarks" />
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
      <div class="card-title">历史回测</div>
      <div v-if="!history.length" class="empty">暂无历史回测</div>
      <div v-for="h in history" :key="h.id" class="hist-row">
        <div style="flex: 1">
          <div class="muted" style="font-size: 12px">{{ h.start_date }} ~ {{ h.end_date }}</div>
          <div style="font-size: 13px; margin-top: 2px">
            收益 <span :class="(h.metrics.total_return_pct ?? 0) >= 0 ? 'up' : 'down'">{{ fmtPct(h.metrics.total_return_pct) }}</span>
            · 胜率 {{ fmtPct(h.metrics.win_rate_pct) }}
          </div>
        </div>
        <button class="btn ghost small" :disabled="viewingId === h.id" @click="viewHistory(h.id)">
          {{ viewingId === h.id ? '加载中...' : '查看' }}
        </button>
        <button class="btn ghost small del" @click="removeBacktest(h)">删除</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import EquityChart from '../components/EquityChart.vue'
import TradeMarkKline from '../components/TradeMarkKline.vue'
import { backtestApi, optimizeApi, stockApi } from '../api'
import type { Bar } from '../api'
import type { BacktestListItem, BacktestResult, OptimizeResultItem } from '../api/types'
import { useStrategyStore } from '../stores/strategy'
import { fmtPct, pnlClass } from '../utils/format'
import { todayStr, yearAgoStr, monthsAgoStr } from '../utils/date'
import { toast } from '../utils/toast'
import { confirmDialog } from '../utils/confirm'
import { SELL_LABELS } from '../utils/signals'

const strategyStore = useStrategyStore()
const route = useRoute()

const sid = ref<number | string>('')
const startDate = ref(yearAgoStr())
const endDate = ref(todayStr())
const loading = ref(false)
const result = ref<BacktestResult | null>(null)
const history = ref<BacktestListItem[]>([])
const viewingId = ref<number | null>(null)
const resultCard = ref<HTMLElement | null>(null)

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

const showHelp = ref(false)
const METRIC_HELP = [
  { k: '累计收益', v: '期末权益相对期初本金的收益百分比' },
  { k: '年化收益', v: '按交易日折算的年化收益率' },
  { k: '最大回撤', v: '权益曲线从峰值到谷底的最大跌幅' },
  { k: '胜率', v: '盈利卖出笔数占卖出总笔数的比例' },
  { k: '盈亏比', v: '平均单笔盈利与平均单笔亏损之比' },
  { k: '交易笔数', v: '回测期间成交总笔数' },
  { k: '夏普比率', v: '超额收益与波动率之比，衡量风险调整后收益' },
  { k: '卡玛比率', v: '年化收益与最大回撤之比' },
  { k: '索提诺比率', v: '仅用下行波动率计算的风险调整后收益' },
  { k: '年化波动率', v: '日收益的年化标准差，衡量收益波动' },
  { k: '最长回撤天数', v: '权益从峰值到再创新高的最长连续交易日数' },
]

onMounted(async () => {
  await strategyStore.fetch()
  if (route.query.sid) sid.value = Number(route.query.sid)
  else if (strategyStore.strategies.length) sid.value = strategyStore.strategies[0].id
  loadHistory()
})

watch(sid, () => loadHistory())

const signalStats = computed(() => {
  const ss = result.value?.signal_stats as { buy?: number; sell?: Record<string, number> } | undefined
  if (!ss) return null
  return { buy: ss.buy ?? 0, sell: ss.sell ?? {} }
})

const sellStatRows = computed(() => {
  const sell = signalStats.value?.sell ?? {}
  return Object.keys(sell).map((key) => ({ key, label: SELL_LABELS[key] ?? key, count: sell[key] }))
})

const tradeMarks = computed(() =>
  (result.value?.trades ?? []).map((t) => ({
    date: String(t.date ?? ''),
    direction: String(t.direction ?? ''),
  })),
)

const tradeStocks = computed(() => {
  const map = new Map<string, string>()
  for (const t of result.value?.trades ?? []) {
    const code = String(t.code ?? '')
    const name = String(t.name ?? '')
    if (code && !map.has(code)) map.set(code, name)
  }
  return Array.from(map.entries()).map(([code, name]) => ({ code, name }))
})

const selectedCode = ref('')
const tradeKlineBars = ref<Bar[]>([])
const tradeKlineLoading = ref(false)

const selectedMarks = computed(() =>
  (result.value?.trades ?? [])
    .filter((t) => String(t.code ?? '') === selectedCode.value)
    .map((t) => ({
      date: String(t.date ?? ''),
      direction: String(t.direction ?? ''),
      price: Number(t.price ?? 0),
    })),
)

watch(result, () => {
  selectedCode.value = tradeStocks.value[0]?.code ?? ''
})

watch(selectedCode, async (code) => {
  if (!code) return
  tradeKlineLoading.value = true
  try {
    tradeKlineBars.value = await stockApi.bars(code, 250, 'day')
  } catch (e) {
    tradeKlineBars.value = []
  } finally {
    tradeKlineLoading.value = false
  }
})

async function run() {
  if (!sid.value) return
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
  if (!sid.value) return
  try {
    history.value = await backtestApi.list(Number(sid.value))
  } catch (e) {
    // 历史加载失败不阻塞
  }
}

async function viewHistory(bid: number) {
  if (!sid.value) return
  viewingId.value = bid
  try {
    result.value = await backtestApi.get(Number(sid.value), bid)
    await nextTick()
    resultCard.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } catch (e) {
    toast((e as Error).message)
  } finally {
    viewingId.value = null
  }
}

async function removeBacktest(h: BacktestListItem) {
  if (!sid.value) return
  const ok = await confirmDialog({
    title: '删除回测',
    message: `确定删除 ${h.start_date} ~ ${h.end_date} 的回测记录吗？此操作不可恢复。`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return
  try {
    await backtestApi.remove(Number(sid.value), h.id)
    history.value = history.value.filter((x) => x.id !== h.id)
    if (result.value?.id === h.id) result.value = null
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

.signal-buy {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 14px;
}

.signal-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px dashed var(--border);
  font-size: 14px;
}

.hero-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.hero-metric {
  background: var(--bg);
  border-radius: 10px;
  padding: 12px;
  text-align: center;
}

.hero-value {
  font-size: 22px;
  font-weight: 700;
  margin-top: 4px;
  font-variant-numeric: tabular-nums;
}

.sub-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0 16px;
  margin-top: 10px;
  padding: 4px 2px;
}

.sub-metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px dashed var(--border);
  font-size: 13px;
}

.sub-metric b {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.sub-box {
  margin-top: 14px;
  padding: 12px;
  background: var(--bg);
  border-radius: 10px;
}

.sub-box-title {
  font-size: 13px;
  color: var(--text-2);
  margin-bottom: 6px;
}

.sub-box-sub {
  font-size: 12px;
  color: var(--text-2);
  margin-top: 8px;
}

.section {
  margin-top: 14px;
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

.metrics-help {
  margin-top: 10px;
}

.help-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: none;
  background: transparent;
  color: var(--text-2);
  font-size: 13px;
  padding: 4px 0;
  min-height: 44px;
  cursor: pointer;
}

.help-toggle:active {
  opacity: 0.6;
}

.help-list {
  margin-top: 6px;
  padding: 10px 12px;
  background: var(--bg);
  border-radius: 8px;
}

.help-item {
  display: flex;
  gap: 8px;
  padding: 5px 0;
  border-bottom: 1px dashed var(--border);
  font-size: 12px;
  line-height: 1.5;
}

.help-item:last-child {
  border-bottom: none;
}

.help-item b {
  flex: 0 0 72px;
  font-weight: 600;
  color: var(--text);
}

.help-item span {
  color: var(--text-2);
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

.stock-select {
  width: 100%;
  height: 36px;
  padding: 0 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--card);
  color: var(--text);
  font-size: 14px;
  margin-bottom: 10px;
  box-sizing: border-box;
}
</style>
