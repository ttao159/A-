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

    <div class="section">
      <div class="section-title">买入信号</div>
      <div v-for="s in BUY_SIGNALS" :key="s.key" class="signal-row">
        <label class="signal-name">
          <input v-model="form.buyEnabled[s.key]" type="checkbox" />
          {{ s.label }}
        </label>
        <div v-if="form.buyEnabled[s.key] && s.params.length" class="params">
          <div v-for="p in s.params" :key="p.key" class="param">
            <span>{{ p.label }}</span>
            <input v-model.number="form.buyParams[s.key][p.key]" type="number" />
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">卖出信号</div>
      <div v-for="s in SELL_SIGNALS" :key="s.key" class="signal-row">
        <label class="signal-name">
          <input v-model="form.sellEnabled[s.key]" type="checkbox" />
          {{ s.label }}
        </label>
        <div v-if="form.sellEnabled[s.key] && s.params.length" class="params">
          <div v-for="p in s.params" :key="p.key" class="param">
            <span>{{ p.label }}</span>
            <input v-model.number="form.sellParams[s.key][p.key]" type="number" />
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">风控参数</div>
      <div v-for="r in RISK_ITEMS" :key="r.key" class="param">
        <span>{{ r.label }}</span>
        <input v-model.number="form.risk[r.key]" type="number" />
      </div>
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

interface ParamDef {
  key: string
  label: string
  value: number
}

interface SignalDef {
  key: string
  label: string
  params: ParamDef[]
  defaultEnabled?: boolean
}

const BUY_SIGNALS: SignalDef[] = [
  { key: 'breakHigh', label: '突破新高', defaultEnabled: true, params: [{ key: 'days', label: '天数', value: 20 }] },
  { key: 'maCross', label: '均线金叉', params: [{ key: 'shortPeriod', label: '短周期', value: 5 }, { key: 'longPeriod', label: '长周期', value: 20 }] },
  { key: 'macdCross', label: 'MACD金叉', params: [{ key: 'fast', label: '快线', value: 12 }, { key: 'slow', label: '慢线', value: 26 }, { key: 'signal', label: '信号线', value: 9 }] },
  { key: 'volumeBreak', label: '放量突破', params: [{ key: 'multiple', label: '倍数', value: 1.5 }, { key: 'avgDays', label: '均量天数', value: 5 }] },
  { key: 'hammer', label: '锤子线', params: [] },
  { key: 'bullishEngulfing', label: '看涨吞没', params: [] },
  { key: 'morningStar', label: '早晨之星', params: [] },
  { key: 'threeWhiteSoldiers', label: '红三兵', params: [] },
  { key: 'doubleBottom', label: '双底', params: [] },
  { key: 'rsiOversold', label: 'RSI超卖', params: [{ key: 'period', label: '周期', value: 14 }, { key: 'threshold', label: '阈值', value: 30 }] },
  { key: 'kdjGoldenCross', label: 'KDJ低位金叉', params: [{ key: 'n', label: 'N周期', value: 9 }, { key: 'lowZone', label: '低位区', value: 50 }] },
  { key: 'bollLowerRebound', label: '布林下轨反弹', params: [{ key: 'period', label: '周期', value: 20 }, { key: 'numStd', label: '标准差倍数', value: 2 }] },
]

const SELL_SIGNALS: SignalDef[] = [
  { key: 'takeProfit', label: '固定止盈', defaultEnabled: true, params: [{ key: 'percent', label: '百分比%', value: 10 }] },
  { key: 'stopLoss', label: '固定止损', defaultEnabled: true, params: [{ key: 'percent', label: '百分比%', value: 5 }] },
  { key: 'trailingStop', label: '移动止盈', params: [{ key: 'drawdown', label: '回撤%', value: 8 }] },
  { key: 'maDeathCross', label: '均线死叉', params: [{ key: 'shortPeriod', label: '短周期', value: 5 }, { key: 'longPeriod', label: '长周期', value: 20 }] },
  { key: 'macdDeathCross', label: 'MACD死叉', params: [] },
  { key: 'belowMA', label: '跌破均线', params: [{ key: 'period', label: '周期', value: 20 }] },
  { key: 'maxHoldDays', label: '持有天数到期', params: [{ key: 'days', label: '天数', value: 20 }] },
  { key: 'hangingMan', label: '上吊线', params: [] },
  { key: 'bearishEngulfing', label: '看跌吞没', params: [] },
  { key: 'eveningStar', label: '黄昏之星', params: [] },
  { key: 'threeBlackCrows', label: '三只乌鸦', params: [] },
  { key: 'doubleTop', label: '双顶', params: [] },
  { key: 'rsiOverbought', label: 'RSI超买', params: [{ key: 'period', label: '周期', value: 14 }, { key: 'threshold', label: '阈值', value: 70 }] },
  { key: 'kdjDeathCross', label: 'KDJ高位死叉', params: [{ key: 'n', label: 'N周期', value: 9 }, { key: 'highZone', label: '高位区', value: 50 }] },
  { key: 'bollBelowMid', label: '跌破布林中轨', params: [{ key: 'period', label: '周期', value: 20 }, { key: 'numStd', label: '标准差倍数', value: 2 }] },
]

const RISK_ITEMS = [
  { key: 'maxPositionPercent', label: '单只最大仓位%' },
  { key: 'maxHoldings', label: '最大持仓数' },
  { key: 'maxSingleLoss', label: '单只最大亏损%' },
  { key: 'totalStopLoss', label: '组合整体止损%' },
  { key: 'maxDrawdown', label: '最大回撤%' },
]

const props = defineProps<{ strategy?: Strategy | null }>()

defineEmits<{ save: [payload: StrategyInput]; cancel: [] }>()

const form = reactive({
  name: props.strategy?.name ?? '',
  enabled: props.strategy?.enabled ?? true,
  initial_capital: props.strategy?.initial_capital ?? 1000000,
  buyEnabled: {} as Record<string, boolean>,
  buyParams: {} as Record<string, Record<string, number>>,
  sellEnabled: {} as Record<string, boolean>,
  sellParams: {} as Record<string, Record<string, number>>,
  risk: {} as Record<string, number>,
})

for (const s of BUY_SIGNALS) {
  form.buyEnabled[s.key] = s.defaultEnabled ?? false
  form.buyParams[s.key] = {}
  for (const p of s.params) form.buyParams[s.key][p.key] = p.value
}

for (const s of SELL_SIGNALS) {
  form.sellEnabled[s.key] = s.defaultEnabled ?? false
  form.sellParams[s.key] = {}
  for (const p of s.params) form.sellParams[s.key][p.key] = p.value
}

for (const r of RISK_ITEMS) {
  form.risk[r.key] = {
    maxPositionPercent: 20,
    maxHoldings: 10,
    maxSingleLoss: 15,
    totalStopLoss: 20,
    maxDrawdown: 25,
  }[r.key] as number
}

if (props.strategy?.config) {
  const cfg = props.strategy.config as any
  for (const s of BUY_SIGNALS) {
    const c = cfg.buy?.[s.key]
    if (c) {
      form.buyEnabled[s.key] = !!c.enabled
      for (const p of s.params) {
        if (c[p.key] != null) form.buyParams[s.key][p.key] = Number(c[p.key])
      }
    }
  }
  for (const s of SELL_SIGNALS) {
    const c = cfg.sell?.[s.key]
    if (c) {
      form.sellEnabled[s.key] = !!c.enabled
      for (const p of s.params) {
        if (c[p.key] != null) form.sellParams[s.key][p.key] = Number(c[p.key])
      }
    }
  }
  for (const r of RISK_ITEMS) {
    if (cfg.risk?.[r.key] != null) form.risk[r.key] = Number(cfg.risk[r.key])
  }
}

function buildPayload(): StrategyInput {
  const buy: Record<string, Record<string, unknown>> = {}
  for (const s of BUY_SIGNALS) {
    buy[s.key] = { enabled: form.buyEnabled[s.key], ...form.buyParams[s.key] }
  }
  const sell: Record<string, Record<string, unknown>> = {}
  for (const s of SELL_SIGNALS) {
    sell[s.key] = { enabled: form.sellEnabled[s.key], ...form.sellParams[s.key] }
  }
  return {
    name: form.name,
    enabled: form.enabled,
    initial_capital: form.initial_capital,
    config: { buy, sell, risk: { ...form.risk } },
  }
}
</script>

<style scoped>
.section {
  margin-top: 14px;
  border-top: 1px solid var(--border);
  padding-top: 10px;
}

.section-title {
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
  font-size: 14px;
}

.signal-row {
  padding: 6px 0;
  border-bottom: 1px dashed var(--border);
}

.signal-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.signal-name input {
  width: 16px;
  height: 16px;
}

.params {
  margin: 6px 0 2px 24px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.param {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  color: var(--text-secondary, #606266);
}

.param input {
  width: 90px;
  height: 30px;
  padding: 0 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  text-align: right;
}
</style>
