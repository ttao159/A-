<template>
  <div class="card asset-card">
    <div class="row">
      <span class="card-title">总资产</span>
      <span class="badge" :class="account.broker_type === 'live' ? 'live' : 'paper'">
        {{ account.broker_type === 'live' ? '实盘' : '模拟盘' }}
      </span>
    </div>
    <div class="asset-total">{{ fmtMoneyCompact(account.total_asset) }}</div>
    <div class="asset-pnl">
      <span class="pnl-big" :class="[pnlClass, { flash: flashing }]">{{ pnlText }}</span>
      <span class="realtime-tag">实时</span>
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
import { fmtMoneyCompact, fmtPct } from '../utils/format'
import { useFlashValue } from '../composables/useFlash'

const props = defineProps<{ account: Account }>()

const flashing = useFlashValue(() => props.account.total_pnl)

const pnlClass = computed(() => (props.account.total_pnl >= 0 ? 'up' : 'down'))

const pnlText = computed(() => {
  const pct = props.account.initial_capital
    ? (props.account.total_pnl / props.account.initial_capital) * 100
    : 0
  return `${fmtMoneyCompact(props.account.total_pnl)} (${fmtPct(pct)})`
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
  margin-bottom: 12px;
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
