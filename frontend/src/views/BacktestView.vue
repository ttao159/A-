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
          <div :class="val(result.metrics.total_return_pct)">
            {{ fmtPct(result.metrics.total_return_pct) }}
          </div>
        </div>
        <div class="metric">
          <div class="muted">年化收益</div>
          <div :class="val(result.metrics.annual_return_pct)">
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
import { backtestApi } from '../api'
import type { BacktestListItem, BacktestResult } from '../api/types'
import { useStrategyStore } from '../stores/strategy'
import { fmtPct } from '../utils/format'
import { SELL_LABELS } from '../utils/signals'

const strategyStore = useStrategyStore()
const route = useRoute()

const sid = ref<number | string>('')
const startDate = ref(defaultStart())
const endDate = ref(today())
const loading = ref(false)
const result = ref<BacktestResult | null>(null)
const history = ref<BacktestListItem[]>([])

onMounted(async () => {
  await strategyStore.fetch()
  if (route.query.sid) sid.value = Number(route.query.sid)
  else if (strategyStore.strategies.length) sid.value = strategyStore.strategies[0].id
  loadHistory()
})

watch(sid, () => loadHistory())

function today() {
  return new Date().toISOString().slice(0, 10)
}

function defaultStart() {
  const d = new Date()
  d.setFullYear(d.getFullYear() - 1)
  return d.toISOString().slice(0, 10)
}

function val(v: number | undefined) {
  return (v ?? 0) >= 0 ? 'up' : 'down'
}

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

async function run() {
  if (!sid.value) return
  loading.value = true
  try {
    result.value = await backtestApi.run(Number(sid.value), startDate.value, endDate.value)
    loadHistory()
  } catch (e) {
    alert((e as Error).message)
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
    alert((e as Error).message)
  } finally {
    loading.value = false
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

.metric {
  background: var(--bg);
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.metric div:last-child {
  font-size: 15px;
  font-weight: 600;
  margin-top: 2px;
}
</style>
