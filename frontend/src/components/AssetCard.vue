<template>
  <div class="card asset-card">
    <div class="row">
      <span class="card-title">总资产</span>
      <span class="badge" :class="account.broker_type === 'live' ? 'live' : 'paper'">
        {{ account.broker_type === 'live' ? '实盘' : '模拟盘' }}
      </span>
    </div>
    <div class="asset-total">{{ fmtMoneyCompact(displayTotal) }}</div>
    <div class="asset-pnl">
      <span class="pnl-big" :class="[pnlClass, { flash: flashing }]">{{ pnlText }}</span>
      <span class="realtime-tag">实时</span>
    </div>
    <div class="today-row">
      <span class="muted">今日盈亏</span>
      <span class="today-pnl" :class="[todayClass, { flash: todayFlashing }]">{{ todayText }}</span>
    </div>
    <div class="asset-bar">
      <div class="bar-track">
        <div class="bar-cash" :style="{ width: cashPct + '%' }"></div>
        <div class="bar-mv" :style="{ width: mvPct + '%' }"></div>
      </div>
      <div class="bar-legend">
        <span class="legend-item"><i class="dot-cash"></i>现金 {{ cashPct.toFixed(0) }}%</span>
        <span class="legend-item"><i class="dot-mv"></i>市值 {{ mvPct.toFixed(0) }}%</span>
      </div>
    </div>
    <div class="asset-grid">
      <div class="asset-cell">
        <div class="muted">可用现金</div>
        <div class="val">{{ fmtMoneyCompact(account.available_cash) }}</div>
      </div>
      <div class="asset-cell">
        <div class="muted">持仓市值</div>
        <div class="val">{{ fmtMoneyCompact(account.market_value) }}</div>
      </div>
      <div class="asset-cell">
        <div class="muted">初始本金</div>
        <div class="val">{{ fmtMoneyCompact(account.initial_capital) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Account } from '../api/types'
import { fmtMoneyCompact, fmtPct, pnlClass as pnlColor } from '../utils/format'
import { useFlashValue } from '../composables/useFlash'
import { useCountUp } from '../composables/useCountUp'

const props = defineProps<{ account: Account }>()

const displayTotal = useCountUp(() => props.account.total_asset)

const flashing = useFlashValue(() => props.account.total_pnl)
const todayFlashing = useFlashValue(() => props.account.today_pnl)

const pnlClass = computed(() => pnlColor(props.account.total_pnl))

const todayClass = computed(() => pnlColor(props.account.today_pnl))

const todayText = computed(() => {
  const v = props.account.today_pnl
  const sign = v > 0 ? '+' : ''
  return `${sign}${fmtMoneyCompact(v)}`
})

const pnlText = computed(() => {
  const pct = props.account.initial_capital
    ? (props.account.total_pnl / props.account.initial_capital) * 100
    : 0
  return `${fmtMoneyCompact(props.account.total_pnl)} (${fmtPct(pct)})`
})

const cashPct = computed(() => {
  const t = props.account.total_asset
  if (t <= 0) return 0
  return Math.min(100, Math.max(0, (props.account.available_cash / t) * 100))
})

const mvPct = computed(() => {
  const t = props.account.total_asset
  if (t <= 0) return 0
  return Math.min(100, Math.max(0, (props.account.market_value / t) * 100))
})
</script>

<style scoped>
.asset-total {
  font-size: 28px;
  font-weight: 600;
  margin: 4px 0;
}

.asset-pnl {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pnl-big {
  display: inline-block;
  font-size: 16px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 8px;
  font-variant-numeric: tabular-nums;
  line-height: 1.4;
}

.pnl-big.up {
  background: var(--up-bg);
  color: var(--up);
}

.pnl-big.down {
  background: var(--down-bg);
  color: var(--down);
}

.today-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  margin: 8px 0 10px;
}

.today-pnl {
  font-weight: 700;
  font-size: 14px;
  padding: 1px 8px;
  border-radius: 6px;
  font-variant-numeric: tabular-nums;
}

.today-pnl.up {
  background: var(--up-bg);
  color: var(--up);
}

.today-pnl.down {
  background: var(--down-bg);
  color: var(--down);
}

.asset-bar {
  margin-bottom: 12px;
}

.bar-track {
  display: flex;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--bg);
  gap: 2px;
}

.bar-cash {
  background: var(--primary);
  border-radius: 4px 0 0 4px;
  transition: width 0.3s ease;
}

.bar-mv {
  background: var(--up);
  border-radius: 0 4px 4px 0;
  transition: width 0.3s ease;
}

.bar-legend {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-2);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.dot-cash,
.dot-mv {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}

.dot-cash {
  background: var(--primary);
}

.dot-mv {
  background: var(--up);
}

.asset-grid {
  display: flex;
  gap: 8px;
}

.asset-cell {
  flex: 1;
  background: var(--bg);
  border-radius: 8px;
  padding: 8px 10px;
}

.asset-cell .val {
  font-size: 14px;
  font-weight: 500;
  margin-top: 2px;
}
</style>
