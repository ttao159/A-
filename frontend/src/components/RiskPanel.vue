<template>
  <div class="card">
    <div class="card-title">风控面板</div>
    <div class="risk-mode">
      <span>账户模式</span>
      <span class="badge" :class="isLive ? 'live' : 'paper'">{{ isLive ? '实盘' : '模拟盘' }}</span>
    </div>
    <div v-if="!strategies.length" class="empty">暂无策略</div>
    <div v-for="s in strategies" :key="s.id" class="risk-strategy">
      <div class="risk-name">{{ s.name }} <span v-if="!s.enabled" class="muted">(已停用)</span></div>
      <div class="risk-params">
        <span v-for="r in riskRows(s)" :key="r.key" class="risk-pill">
          {{ r.label }} <b>{{ r.value }}</b>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Strategy } from '../api/types'
import { RISK_LABELS } from '../utils/signals'

const props = defineProps<{ strategies: Strategy[]; isLive: boolean }>()

const ORDER = ['maxPositionPercent', 'maxHoldings', 'maxSingleLoss', 'totalStopLoss', 'maxDrawdown']

function riskRows(s: Strategy) {
  const risk = s.config.risk ?? {}
  return ORDER.filter((k) => risk[k] !== undefined).map((k) => ({
    key: k,
    label: RISK_LABELS[k] ?? k,
    value: risk[k],
  }))
}
</script>

<style scoped>
.risk-mode {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px dashed var(--border);
  font-size: 14px;
}

.risk-strategy {
  padding: 10px 0;
  border-bottom: 1px dashed var(--border);
}

.risk-strategy:last-child {
  border-bottom: none;
}

.risk-name {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 6px;
}

.risk-params {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.risk-pill {
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 12px;
  background: var(--bg);
  color: var(--text-2);
}

.risk-pill b {
  color: var(--text);
  font-weight: 600;
}
</style>
