<template>
  <div class="card asset-card">
    <div class="row">
      <span class="card-title">总资产</span>
      <span class="badge" :class="account.broker_type === 'live' ? 'live' : 'paper'">
        {{ account.broker_type === 'live' ? '实盘' : '模拟盘' }}
      </span>
    </div>
    <div class="asset-total">{{ fmtMoney(account.total_asset) }}</div>
    <div class="asset-pnl">
      <span class="pill" :class="account.total_pnl >= 0 ? 'up' : 'down'">
        {{ pnlText }}
      </span>
    </div>
    <div class="asset-grid">
      <div class="asset-cell">
        <div class="muted">可用现金</div>
        <div class="val">{{ fmtMoney(account.available_cash) }}</div>
      </div>
      <div class="asset-cell">
        <div class="muted">持仓市值</div>
        <div class="val">{{ fmtMoney(account.market_value) }}</div>
      </div>
      <div class="asset-cell">
        <div class="muted">初始本金</div>
        <div class="val">{{ fmtMoney(account.initial_capital) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Account } from '../api/types'
import { fmtMoney, fmtPct } from '../utils/format'

const props = defineProps<{ account: Account }>()

const pnlText = computed(() => {
  const pct = props.account.initial_capital
    ? (props.account.total_pnl / props.account.initial_capital) * 100
    : 0
  return `${fmtMoney(props.account.total_pnl)} (${fmtPct(pct)})`
})
</script>

<style scoped>
.asset-total {
  font-size: 28px;
  font-weight: 600;
  margin: 4px 0;
}

.asset-pnl {
  font-size: 14px;
  margin-bottom: 12px;
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
