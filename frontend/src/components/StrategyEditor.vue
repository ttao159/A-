<template>
  <div class="card editor">
    <div class="field">
      <label>策略名称</label>
      <input v-model="form.name" placeholder="输入策略名称" />
    </div>

    <div class="field">
      <label>分配本金（元）</label>
      <input v-model.number="form.initial_capital" type="number" min="0" step="10000" />
    </div>

    <div class="field row">
      <label style="margin: 0">启用策略</label>
      <input v-model="form.enabled" type="checkbox" />
    </div>

    <div class="field">
      <label>买入信号（可多选）</label>
      <div class="chips">
        <button
          v-for="s in buySignals"
          :key="s.key"
          class="chip"
          :class="{ active: form.buyKeys.includes(s.key) }"
          @click="toggleBuy(s.key)"
        >
          {{ s.label }}
        </button>
      </div>
    </div>

    <div class="field">
      <label>止盈（%）</label>
      <input v-model.number="form.takeProfit" type="number" min="1" />
    </div>

    <div class="field">
      <label>止损（%）</label>
      <input v-model.number="form.stopLoss" type="number" min="1" />
    </div>

    <div class="field">
      <label>单只最大仓位（%）</label>
      <input v-model.number="form.maxPositionPercent" type="number" min="1" max="100" />
    </div>

    <div class="field">
      <label>最大持仓数</label>
      <input v-model.number="form.maxHoldings" type="number" min="1" max="50" />
    </div>

    <div class="row" style="gap: 12px">
      <button class="btn block" @click="$emit('save', buildPayload())">保存</button>
      <button class="btn ghost block" @click="$emit('cancel')">取消</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import type { Strategy, StrategyInput } from '../api/types'

const buySignals = [
  { key: 'breakHigh', label: '突破新高' },
  { key: 'maCross', label: '均线金叉' },
  { key: 'macdCross', label: 'MACD金叉' },
  { key: 'volumeBreak', label: '放量突破' },
  { key: 'hammer', label: '锤子线' },
  { key: 'bullishEngulfing', label: '看涨吞没' },
  { key: 'morningStar', label: '早晨之星' },
  { key: 'threeWhiteSoldiers', label: '红三兵' },
  { key: 'doubleBottom', label: '双底' },
] as const

const props = defineProps<{ strategy?: Strategy | null }>()

defineEmits<{ save: [payload: StrategyInput]; cancel: [] }>()

const buyParams: Record<string, Record<string, unknown>> = {
  breakHigh: { days: 20 },
  maCross: { shortPeriod: 5, longPeriod: 20 },
  macdCross: { fast: 12, slow: 26, signal: 9 },
  volumeBreak: { multiple: 1.5, avgDays: 5 },
  hammer: {},
  bullishEngulfing: {},
  morningStar: {},
  threeWhiteSoldiers: {},
  doubleBottom: {},
}

const form = reactive({
  name: props.strategy?.name ?? '',
  enabled: props.strategy?.enabled ?? true,
  initial_capital: props.strategy?.initial_capital ?? 1000000,
  takeProfit: 10,
  stopLoss: 5,
  maxPositionPercent: 20,
  maxHoldings: 10,
  buyKeys: [] as string[],
})

if (props.strategy?.config) {
  const cfg = props.strategy.config
  for (const s of buySignals) {
    if (cfg.buy?.[s.key]?.enabled) form.buyKeys.push(s.key)
  }
  form.takeProfit = Number(cfg.sell?.takeProfit?.percent ?? 10)
  form.stopLoss = Number(cfg.sell?.stopLoss?.percent ?? 5)
  form.maxPositionPercent = Number(cfg.risk?.maxPositionPercent ?? 20)
  form.maxHoldings = Number(cfg.risk?.maxHoldings ?? 10)
}

function toggleBuy(key: string) {
  const idx = form.buyKeys.indexOf(key)
  if (idx >= 0) form.buyKeys.splice(idx, 1)
  else form.buyKeys.push(key)
}

function buildPayload(): StrategyInput {
  const buy: Record<string, Record<string, unknown>> = {}
  for (const key of buySignals.map((s) => s.key)) {
    buy[key] = { enabled: form.buyKeys.includes(key), ...buyParams[key] }
  }
  const sell: Record<string, Record<string, unknown>> = {
    takeProfit: { enabled: true, percent: form.takeProfit },
    stopLoss: { enabled: true, percent: form.stopLoss },
  }
  return {
    name: form.name,
    enabled: form.enabled,
    initial_capital: form.initial_capital,
    config: {
      buy,
      sell,
      risk: {
        maxPositionPercent: form.maxPositionPercent,
        maxHoldings: form.maxHoldings,
        maxSingleLoss: 15,
        totalStopLoss: 20,
        maxDrawdown: 25,
      },
    },
  }
}
</script>

<style scoped>
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  min-height: 36px;
  padding: 0 14px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--text);
  font-size: 14px;
}

.chip.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}
</style>
