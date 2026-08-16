<template>
  <div class="card">
    <div class="card-title">持仓</div>
    <div v-if="!positions.length" class="empty">暂无持仓</div>
    <div v-for="p in positions" :key="p.code" class="list-item" @click="toggle(p.code)">
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

      <div v-if="expanded === p.code" class="pos-detail" @click.stop>
        <div class="detail-row">
          <span>持有天数</span><b>{{ p.hold_days }} 天</b>
        </div>
        <div class="detail-row">
          <span>持仓市值</span><b>{{ fmtMoney(p.qty * p.price) }}</b>
        </div>
        <div class="detail-row">
          <span>浮动盈亏</span><b :class="p.pnl >= 0 ? 'up' : 'down'">{{ fmtMoney(p.pnl) }}</b>
        </div>
        <div class="detail-row">
          <span>所属策略</span><b>{{ p.strategy_name ?? '未分配' }}</b>
        </div>
        <button
          v-if="p.strategy_id"
          class="btn ghost block"
          style="margin-top: 10px"
          @click="$emit('openStrategy', p.strategy_id)"
        >
          查看所属策略
        </button>
        <button class="btn ghost block" style="margin-top: 8px" @click="$emit('openStock', p)">
          查看走势
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Position } from '../api/types'
import { fmtMoney, fmtPct, fmtPrice } from '../utils/format'

defineProps<{ positions: Position[] }>()
defineEmits<{ openStrategy: [id: number]; openStock: [p: Position] }>()

const expanded = ref<string | null>(null)

function toggle(code: string) {
  expanded.value = expanded.value === code ? null : code
}
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

.list-item {
  flex-wrap: wrap;
}

.pos-detail {
  flex-basis: 100%;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--border);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  padding: 4px 0;
  color: var(--text-2, #606266);
}

.detail-row b {
  color: var(--text, #303133);
  font-weight: 600;
}
</style>
