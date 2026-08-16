<template>
  <div>
    <div class="card">
      <div class="field">
        <label>选择策略</label>
        <select v-model="sid">
          <option v-for="s in strategyStore.strategies" :key="s.id" :value="s.id">
            {{ s.name }}
          </option>
        </select>
      </div>
      <div class="row" style="gap: 8px">
        <div class="field" style="flex: 1; margin: 0">
          <label>开始日期</label>
          <input v-model="startDate" type="date" />
        </div>
        <div class="field" style="flex: 1; margin: 0">
          <label>结束日期</label>
          <input v-model="endDate" type="date" />
        </div>
      </div>
      <button class="btn block" style="margin-top: 12px" :disabled="loading" @click="run">
        {{ loading ? '回测中...' : '运行回测' }}
      </button>
    </div>

    <div v-if="result" class="card">
      <div class="card-title">回测结果</div>
      <div class="metric-grid">
        <div class="metric">
          <div class="muted">累计收益</div>
          <div :class="pnlClass(result.metrics.total_return_pct)">
            {{ fmtPct(result.metrics.total_return_pct) }}
          </div>
        </div>
        <div class="metric">
          <div class="muted">年化收益</div>
          <div :class="pnlClass(result.metrics.annual_return_pct)">
            {{ fmtPct(result.metrics.annual_return_pct) }}
          </div>
        </div>
        <div class="metric">
          <div class="muted">最大回撤</div>
          <div>{{ fmtPct(result.metrics.max_drawdown_pct) }}</div>
        </div>
        <div class="metric">
          <div class="muted">胜率</div>
          <div>{{ fmtPct(result.metrics.win_rate_pct) }}</div>
        </div>
        <div class="metric">
          <div class="muted">盈亏比</div>
          <div>{{ result.metrics.profit_loss_ratio?.toFixed(2) }}</div>
        </div>
        <div class="metric">
          <div class="muted">交易笔数</div>
          <div>{{ result.metrics.trade_count }}</div>
        </div>
        <div class="metric">
          <div class="muted">夏普比率</div>
          <div :class="pnlClass(result.metrics.sharpe_ratio)">{{ result.metrics.sharpe_ratio?.toFixed(2) ?? '--' }}</div>
        </div>
        <div class="metric">
          <div class="muted">卡玛比率</div>
          <div :class="pnlClass(result.metrics.calmar_ratio)">{{ result.metrics.calmar_ratio?.toFixed(2) ?? '--' }}</div>
        </div>
        <div class="metric">
          <div class="muted">索提诺比率</div>
          <div :class="pnlClass(result.metrics.sortino_ratio)">{{ result.metrics.sortino_ratio?.toFixed(2) ?? '--' }}</div>
        </div>
        <div class="metric">
          <div class="muted">年化波动率</div>
          <div>{{ result.metrics.annual_volatility_pct != null ? fmtPct(result.metrics.annual_volatility_pct) : '--' }}</div>
        </div>
        <div class="metric">
          <div class="muted">最长回撤天数</div>
          <div>{{ result.metrics.max_drawdown_days ?? '--' }}</div>
        </div>
      </div>
      <div v-if="signalStats" class="card" style="margin-top: 0">
        <div class="card-title">信号统计</div>
        <div class="signal-buy">
          <span>买入信号触发</span>
          <b class="up">{{ signalStats.buy }} 次</b>
        </div>
        <div class="card-title" style="font-size: 13px">卖出信号触发</div>
        <div v-if="!sellStatRows.length" class="muted">暂无卖出信号</div>
        <div v-for="r in sellStatRows" :key="r.key" class="signal-row">
          <span>{{ r.label }}</span>
          <b class="down">{{ r.count }} 次</b>
        </div>
      </div>
      <div v-if="result.equity_curve?.length" style="margin-top: 12px">
        <div class="card-title">权益曲线</div>
        <EquityChart
          :data="result.equity_curve"
          :baseline="result.metrics.initial_capital"
          :trades="tradeMarks"
        />
      </div>
      <div v-if="tradeStocks.length" style="margin-top: 12px">
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
        <label v-for="d in OPTIMIZE_DIMS" :key="d.key" class="opt-dim">
          <input type="checkbox" :value="d.key" v-model="selectedDims" />
          <span>{{ d.label }}（{{ d.values.join('/') }}）</span>
        </label>
      </div>
      <button
        class="btn block"
        style="margin-top: 10px"
        :disabled="optimizing || !selectedDims.length"
        @click="runOptimize"
      >
        {{ optimizing ? `优化中 ${optimizeProgress}/${optimizeTotal}...` : '开始优化' }}
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
        <button class="btn ghost small" @click="viewHistory(h.id)">查看</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import EquityChart from '../components/EquityChart.vue'
import TradeMarkKline from '../components/TradeMarkKline.vue'
import { backtestApi, optimizeApi, stockApi } from '../api'
import type { Bar } from '../api'
import type { BacktestListItem, BacktestResult, OptimizeResultItem } from '../api/types'
import { useStrategyStore } from '../stores/strategy'
import { fmtPct, pnlClass } from '../utils/format'
import { todayStr, yearAgoStr } from '../utils/date'
import { toast } from '../utils/toast'
import { SELL_LABELS } from '../utils/signals'

const strategyStore = useStrategyStore()
const route = useRoute()

const sid = ref<number | string>('')
const startDate = ref(yearAgoStr())
const endDate = ref(todayStr())
const loading = ref(false)
const result = ref<BacktestResult | null>(null)
const history = ref<BacktestListItem[]>([])

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
  loading.value = true
  try {
    result.value = await backtestApi.get(Number(sid.value), bid)
  } catch (e) {
    toast((e as Error).message)
  } finally {
    loading.value = false
  }
}

function dimLabel(key: string) {
  return OPTIMIZE_DIMS.find((d) => d.key === key)?.label ?? key
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

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.opt-dims {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.opt-dim {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.opt-dim input {
  width: 16px;
  height: 16px;
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
