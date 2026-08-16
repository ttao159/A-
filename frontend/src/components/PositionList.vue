<template>
  <div class="card">
    <div class="card-title">持仓</div>
    <div v-if="!positions.length" class="empty">暂无持仓</div>
    <div v-for="p in positions" :key="p.code" class="pos-item">
      <div class="pos-row" @click="$emit('openStock', p)">
        <div class="pos-main">
          <div class="pos-name">
            {{ p.name }} <span class="muted">{{ p.code }}</span>
            <span v-if="warnOf(p)" class="tag" :class="warnOf(p)!.type === 'tp' ? 'tag-tp' : 'tag-sl'">
              {{ warnOf(p)!.label }}
            </span>
            <span v-if="p.hold_days === 0" class="tag tag-lock">T+1 锁定</span>
          </div>
          <div class="muted">{{ p.qty }} 股 · 成本 {{ fmtPrice(p.avg_cost) }} · 现价 {{ fmtPrice(p.price) }}</div>
        </div>
        <div class="pos-side">
          <div :class="p.pnl >= 0 ? 'up' : 'down'">{{ fmtMoney(p.pnl) }}</div>
          <span class="pill" :class="p.pnl_pct >= 0 ? 'up' : 'down'">{{ fmtPct(p.pnl_pct) }}</span>
        </div>
        <button class="expand-btn" @click.stop="toggle(p.code)">{{ expanded === p.code ? '▴' : '▾' }}</button>
      </div>

      <div v-if="expanded === p.code" class="pos-detail">
        <div class="detail-row">
          <span>持有天数</span><b>{{ p.hold_days }} 天</b>
        </div>
        <div class="detail-row">
          <span>持仓市值</span><b>{{ fmtMoneyCompact(p.qty * p.price) }}</b>
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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Position, Strategy } from '../api/types'
import { fmtMoney, fmtMoneyCompact, fmtPct, fmtPrice } from '../utils/format'

const props = defineProps<{ positions: Position[]; strategies?: Strategy[] }>()
defineEmits<{ openStrategy: [id: number]; openStock: [p: Position] }>()

const expanded = ref<string | null>(null)

function toggle(code: string) {
  expanded.value = expanded.value === code ? null : code
}

function warnOf(p: Position): { type: 'tp' | 'sl'; label: string } | null {
  const s = props.strategies?.find((x) => x.id === p.strategy_id)
  if (!s) return null
  const cfg = s.config as { sell?: Record<string, { enabled?: boolean; percent?: number }> }
  const tp = cfg.sell?.takeProfit
  const sl = cfg.sell?.stopLoss
  const tpPct = tp?.enabled ? Number(tp.percent ?? 0) : 0
  const slPct = sl?.enabled ? Number(sl.percent ?? 0) : 0
  if (tpPct > 0 && p.pnl_pct >= tpPct) return { type: 'tp', label: `止盈 ${tpPct}%` }
  if (slPct > 0 && p.pnl_pct <= -slPct) return { type: 'sl', label: `止损 ${slPct}%` }
  return null
}
</script>

<style scoped>
.pos-item {
  border-bottom: 1px solid var(--border);
}

.pos-item:last-child {
  border-bottom: none;
}

.pos-row {
  display: flex;
  align-items: center;
  padding: 12px 0;
}

.pos-main {
  flex: 1;
  min-width: 0;
}

.pos-name {
  font-weight: 500;
}

.tag {
  display: inline-block;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: 6px;
  vertical-align: middle;
}

.tag-lock {
  background: var(--warning-bg);
  color: var(--warning);
}

.tag-tp {
  background: var(--up-bg);
  color: var(--up);
}

.tag-sl {
  background: var(--down-bg);
  color: var(--down);
}

.pos-side {
  text-align: right;
  margin-left: 8px;
}

.expand-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: var(--text-2);
  font-size: 14px;
  margin-left: 4px;
}

.pos-detail {
  padding: 8px 0 12px;
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
