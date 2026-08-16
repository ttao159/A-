<template>
  <div class="card">
    <div class="card-title">持仓</div>
    <div v-if="!positions.length" class="empty">暂无持仓</div>
    <div v-for="p in positions" :key="p.code" class="list-item">
      <div class="pos-main">
        <div class="pos-name">
          {{ p.name }} <span class="muted">{{ p.code }}</span>
        </div>
        <div class="muted">{{ p.qty }} 股 · 成本 {{ fmtPrice(p.avg_cost) }} · 现价 {{ fmtPrice(p.price) }}</div>
      </div>
      <div class="pos-side">
        <div :class="p.pnl >= 0 ? 'up' : 'down'">{{ fmtMoney(p.pnl) }}</div>
        <div class="muted" :class="p.pnl_pct >= 0 ? 'up' : 'down'">{{ fmtPct(p.pnl_pct) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Position } from '../api/types'
import { fmtMoney, fmtPct, fmtPrice } from '../utils/format'

defineProps<{ positions: Position[] }>()
</script>

<style scoped>
.pos-main {
  flex: 1;
}

.pos-name {
  font-weight: 500;
}

.pos-side {
  text-align: right;
}
</style>
