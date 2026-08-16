<template>
  <div class="bt-result">
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
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import EquityChart from './EquityChart.vue'
import TradeMarkKline from './TradeMarkKline.vue'
import { stockApi } from '../api'
import type { Bar } from '../api'
import type { BacktestResult } from '../api/types'
import { fmtPct, pnlClass } from '../utils/format'
import { SELL_LABELS } from '../utils/signals'

const props = defineProps<{ result: BacktestResult }>()

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

const signalStats = computed(() => {
  const ss = props.result.signal_stats as { buy?: number; sell?: Record<string, number> } | undefined
  if (!ss) return null
  return { buy: ss.buy ?? 0, sell: ss.sell ?? {} }
})

const sellStatRows = computed(() => {
  const sell = signalStats.value?.sell ?? {}
  return Object.keys(sell).map((key) => ({ key, label: SELL_LABELS[key] ?? key, count: sell[key] }))
})

const tradeMarks = computed(() =>
  (props.result.trades ?? []).map((t) => ({
    date: String(t.date ?? ''),
    direction: String(t.direction ?? ''),
  })),
)

const tradeStocks = computed(() => {
  const map = new Map<string, string>()
  for (const t of props.result.trades ?? []) {
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
  (props.result.trades ?? [])
    .filter((t) => String(t.code ?? '') === selectedCode.value)
    .map((t) => ({
      date: String(t.date ?? ''),
      direction: String(t.direction ?? ''),
      price: Number(t.price ?? 0),
    })),
)

watch(
  () => props.result,
  () => {
    selectedCode.value = tradeStocks.value[0]?.code ?? ''
  },
  { immediate: true },
)

watch(selectedCode, async (code) => {
  if (!code) return
  tradeKlineLoading.value = true
  try {
    tradeKlineBars.value = await stockApi.bars(code, 250, 'day')
  } catch {
    tradeKlineBars.value = []
  } finally {
    tradeKlineLoading.value = false
  }
})
</script>

<style scoped>
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

.section {
  margin-top: 14px;
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
