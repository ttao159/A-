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
      <div v-if="result.equity_curve?.length" style="margin-top: 12px">
        <div class="card-title">权益曲线</div>
        <EquityChart :data="result.equity_curve" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import EquityChart from '../components/EquityChart.vue'
import { backtestApi } from '../api'
import type { BacktestResult } from '../api/types'
import { useStrategyStore } from '../stores/strategy'
import { fmtPct } from '../utils/format'

const strategyStore = useStrategyStore()
const route = useRoute()

const sid = ref<number | string>('')
const startDate = ref(defaultStart())
const endDate = ref(today())
const loading = ref(false)
const result = ref<BacktestResult | null>(null)

onMounted(async () => {
  await strategyStore.fetch()
  if (route.query.sid) sid.value = Number(route.query.sid)
  else if (strategyStore.strategies.length) sid.value = strategyStore.strategies[0].id
})

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

async function run() {
  if (!sid.value) return
  loading.value = true
  try {
    result.value = await backtestApi.run(Number(sid.value), startDate.value, endDate.value)
  } catch (e) {
    alert((e as Error).message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
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
