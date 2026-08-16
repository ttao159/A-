<template>
  <div class="preview">
    <div class="pv-head">
      <div class="pv-name">{{ strategy.name }}</div>
      <div class="muted">{{ strategy.enabled ? '已启用' : '已停用' }} · 累计收益
        <span :class="retPct >= 0 ? 'up' : 'down'">{{ retPct >= 0 ? '+' : '' }}{{ retPct.toFixed(2) }}%</span>
      </div>
    </div>

    <div class="pv-stats">
      <div class="pv-stat"><span>本金</span><b>{{ fmtMoneyCompact(strategy.initial_capital) }}</b></div>
      <div class="pv-stat"><span>现金</span><b>{{ fmtMoneyCompact(strategy.available_cash) }}</b></div>
      <div class="pv-stat"><span>市值</span><b>{{ fmtMoneyCompact(mv) }}</b></div>
    </div>

    <div class="pv-section">买入信号</div>
    <div v-if="!buySignals.length" class="pv-empty">未启用买入信号</div>
    <div v-for="s in buySignals" :key="s.key" class="pv-signal">
      <span class="pv-signal-name">{{ s.label }}</span>
      <span v-if="s.params" class="pv-signal-desc">{{ s.params }}</span>
    </div>

    <div class="pv-section">卖出信号</div>
    <div v-if="!sellSignals.length" class="pv-empty">未启用卖出信号</div>
    <div v-for="s in sellSignals" :key="s.key" class="pv-signal">
      <span class="pv-signal-name">{{ s.label }}</span>
      <span v-if="s.params" class="pv-signal-desc">{{ s.params }}</span>
    </div>

    <div class="pv-section">风控参数</div>
    <div v-for="r in riskItems" :key="r.key" class="pv-risk">
      <span>{{ r.label }}</span><b>{{ r.value }}</b>
    </div>

    <div class="pv-section">持仓 ({{ positions.length }})</div>
    <div v-if="!positions.length" class="pv-empty">暂无持仓</div>
    <div v-for="p in positions" :key="p.code" class="pv-pos">
      <span class="pv-pos-name">{{ p.name }}</span>
      <span class="pv-pos-code">{{ p.code }}</span>
      <span class="pv-pos-pnl" :class="p.pnl_pct >= 0 ? 'up' : 'down'">
        {{ p.pnl_pct >= 0 ? '+' : '' }}{{ p.pnl_pct }}%
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Position, Strategy } from '../api/types'
import { fmtMoneyCompact } from '../utils/format'
import { RISK_LABELS, signalName, signalParamText } from '../utils/signals'

const props = defineProps<{ strategy: Strategy; positions?: Position[] }>()

const positions = computed(() => props.positions ?? [])

const mv = computed(() => positions.value.reduce((s, p) => s + p.qty * p.price, 0))

const retPct = computed(() => {
  const capital = props.strategy.initial_capital || 0
  if (!capital) return 0
  return ((props.strategy.available_cash + mv.value - capital) / capital) * 100
})

const buySignals = computed(() => {
  const cfg = props.strategy.config.buy ?? {}
  return Object.keys(cfg)
    .filter((k) => Boolean(cfg[k].enabled))
    .map((k) => ({ key: k, label: signalName(k), params: signalParamText(cfg[k]) }))
})

const sellSignals = computed(() => {
  const cfg = props.strategy.config.sell ?? {}
  return Object.keys(cfg)
    .filter((k) => Boolean(cfg[k].enabled))
    .map((k) => ({ key: k, label: signalName(k), params: signalParamText(cfg[k]) }))
})

const riskItems = computed(() =>
  Object.keys(props.strategy.config.risk ?? {}).map((k) => ({
    key: k,
    label: RISK_LABELS[k] ?? k,
    value: props.strategy.config.risk[k],
  })),
)
</script>

<style scoped>
.preview {
  font-size: 14px;
}

.pv-head {
  margin-bottom: 12px;
}

.pv-name {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 2px;
}

.pv-stats {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}

.pv-stat {
  flex: 1;
  background: var(--bg);
  border-radius: 8px;
  padding: 10px 6px;
  text-align: center;
}

.pv-stat span {
  display: block;
  font-size: 12px;
  color: var(--text-2);
}

.pv-stat b {
  font-size: 14px;
  font-weight: 600;
}

.pv-section {
  margin-top: 14px;
  font-weight: 600;
  font-size: 13px;
  color: var(--text-2);
  border-bottom: 1px solid var(--border);
  padding-bottom: 4px;
}

.pv-signal {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px dashed var(--border);
}

.pv-signal-name {
  font-weight: 500;
}

.pv-signal-desc {
  font-size: 12px;
  color: var(--text-2);
  text-align: right;
}

.pv-risk {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px dashed var(--border);
}

.pv-pos {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 0;
  border-bottom: 1px dashed var(--border);
}

.pv-pos-name {
  flex: 1;
  font-weight: 500;
}

.pv-pos-code {
  color: var(--text-2);
  font-size: 12px;
}

.pv-pos-pnl {
  font-weight: 600;
  font-size: 13px;
}

.pv-empty {
  color: var(--text-2);
  font-size: 13px;
  padding: 8px 0;
}
</style>
