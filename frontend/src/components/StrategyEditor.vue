<template>
  <div class="card editor">
    <div class="field">
      <label>策略名称</label>
      <input v-model="form.name" placeholder="输入策略名称" />
    </div>

    <div class="field">
      <label>分配本金（元）</label>
      <input v-model.number="form.initial_capital" type="number" min="0" step="10000" @input="validateCapital" />
      <div v-if="capitalError" class="param-error">{{ capitalError }}</div>
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
            <div class="param-input-wrap">
              <input
                v-model.number="form.buyParams[s.key][p.key]"
                type="number"
                :min="p.min"
                :max="p.max"
                :class="{ error: errors.buy[s.key]?.[p.key] }"
                @input="validateBuyParam(s.key, p.key)"
              />
              <div v-if="errors.buy[s.key]?.[p.key]" class="param-error">{{ errors.buy[s.key][p.key] }}</div>
            </div>
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
            <div class="param-input-wrap">
              <input
                v-model.number="form.sellParams[s.key][p.key]"
                type="number"
                :min="p.min"
                :max="p.max"
                :class="{ error: errors.sell[s.key]?.[p.key] }"
                @input="validateSellParam(s.key, p.key)"
              />
              <div v-if="errors.sell[s.key]?.[p.key]" class="param-error">{{ errors.sell[s.key][p.key] }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">风控参数</div>
      <div v-for="r in RISK_ITEMS" :key="r.key" class="param">
        <span>{{ r.label }}</span>
        <div class="param-input-wrap">
          <input
            v-model.number="form.risk[r.key]"
            type="number"
            :min="r.min"
            :max="r.max"
            :class="{ error: errors.risk[r.key] }"
            @input="validateRiskParam(r.key)"
          />
          <div v-if="errors.risk[r.key]" class="param-error">{{ errors.risk[r.key] }}</div>
        </div>
      </div>
    </div>

    <div class="row" style="gap: 12px">
      <button class="btn block" @click="onSave">保存</button>
      <button class="btn ghost block" @click="$emit('cancel')">取消</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { Strategy, StrategyInput } from '../api/types'
import type { StrategyTemplate } from '../utils/strategyTemplates'
import { toast } from '../utils/toast'

interface ParamDef {
  key: string
  label: string
  value: number
  min?: number
  max?: number
  integer?: boolean
}

interface SignalDef {
  key: string
  label: string
  params: ParamDef[]
  defaultEnabled?: boolean
}

interface RiskDef {
  key: string
  label: string
  value: number
  min?: number
  max?: number
  integer?: boolean
}

const BUY_SIGNALS: SignalDef[] = [
  { key: 'breakHigh', label: '突破新高', defaultEnabled: true, params: [{ key: 'days', label: '天数', value: 20, min: 1, integer: true }] },
  { key: 'maCross', label: '均线金叉', params: [{ key: 'shortPeriod', label: '短周期', value: 5, min: 1, integer: true }, { key: 'longPeriod', label: '长周期', value: 20, min: 2, integer: true }] },
  { key: 'macdCross', label: 'MACD金叉', params: [{ key: 'fast', label: '快线', value: 12, min: 2, integer: true }, { key: 'slow', label: '慢线', value: 26, min: 2, integer: true }, { key: 'signal', label: '信号线', value: 9, min: 1, integer: true }] },
  { key: 'volumeBreak', label: '放量突破', params: [{ key: 'multiple', label: '倍数', value: 1.5, min: 0.1, max: 10 }, { key: 'avgDays', label: '均量天数', value: 5, min: 1, integer: true }] },
  { key: 'hammer', label: '锤子线', params: [] },
  { key: 'bullishEngulfing', label: '看涨吞没', params: [] },
  { key: 'morningStar', label: '早晨之星', params: [] },
  { key: 'threeWhiteSoldiers', label: '红三兵', params: [] },
  { key: 'doubleBottom', label: '双底', params: [] },
  { key: 'rsiOversold', label: 'RSI超卖', params: [{ key: 'period', label: '周期', value: 14, min: 2, integer: true }, { key: 'threshold', label: '阈值', value: 30, min: 0, max: 100 }] },
  { key: 'kdjGoldenCross', label: 'KDJ低位金叉', params: [{ key: 'n', label: 'N周期', value: 9, min: 1, integer: true }, { key: 'lowZone', label: '低位区', value: 50, min: 0, max: 100 }] },
  { key: 'bollLowerRebound', label: '布林下轨反弹', params: [{ key: 'period', label: '周期', value: 20, min: 2, integer: true }, { key: 'numStd', label: '标准差倍数', value: 2, min: 0.1, max: 10 }] },
]

const SELL_SIGNALS: SignalDef[] = [
  { key: 'takeProfit', label: '固定止盈', defaultEnabled: true, params: [{ key: 'percent', label: '百分比%', value: 10, min: 0, max: 100 }] },
  { key: 'stopLoss', label: '固定止损', defaultEnabled: true, params: [{ key: 'percent', label: '百分比%', value: 5, min: 0, max: 100 }] },
  { key: 'trailingStop', label: '移动止盈', params: [{ key: 'drawdown', label: '回撤%', value: 8, min: 0, max: 100 }] },
  { key: 'maDeathCross', label: '均线死叉', params: [{ key: 'shortPeriod', label: '短周期', value: 5, min: 1, integer: true }, { key: 'longPeriod', label: '长周期', value: 20, min: 2, integer: true }] },
  { key: 'macdDeathCross', label: 'MACD死叉', params: [] },
  { key: 'belowMA', label: '跌破均线', params: [{ key: 'period', label: '周期', value: 20, min: 1, integer: true }] },
  { key: 'maxHoldDays', label: '持有天数到期', params: [{ key: 'days', label: '天数', value: 20, min: 1, integer: true }] },
  { key: 'hangingMan', label: '上吊线', params: [] },
  { key: 'bearishEngulfing', label: '看跌吞没', params: [] },
  { key: 'eveningStar', label: '黄昏之星', params: [] },
  { key: 'threeBlackCrows', label: '三只乌鸦', params: [] },
  { key: 'doubleTop', label: '双顶', params: [] },
  { key: 'rsiOverbought', label: 'RSI超买', params: [{ key: 'period', label: '周期', value: 14, min: 2, integer: true }, { key: 'threshold', label: '阈值', value: 70, min: 0, max: 100 }] },
  { key: 'kdjDeathCross', label: 'KDJ高位死叉', params: [{ key: 'n', label: 'N周期', value: 9, min: 1, integer: true }, { key: 'highZone', label: '高位区', value: 50, min: 0, max: 100 }] },
  { key: 'bollBelowMid', label: '跌破布林中轨', params: [{ key: 'period', label: '周期', value: 20, min: 2, integer: true }, { key: 'numStd', label: '标准差倍数', value: 2, min: 0.1, max: 10 }] },
]

const RISK_ITEMS: RiskDef[] = [
  { key: 'maxPositionPercent', label: '单只最大仓位%', value: 20, min: 0, max: 100 },
  { key: 'maxHoldings', label: '最大持仓数', value: 10, min: 1, integer: true },
  { key: 'maxSingleLoss', label: '单只最大亏损%', value: 15, min: 0, max: 100 },
  { key: 'totalStopLoss', label: '组合整体止损%', value: 20, min: 0, max: 100 },
  { key: 'maxDrawdown', label: '最大回撤%', value: 25, min: 0, max: 100 },
]

const props = defineProps<{ strategy?: Strategy | null; template?: StrategyTemplate | null }>()

const emit = defineEmits<{ save: [payload: StrategyInput]; cancel: [] }>()

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

const errors = reactive({
  buy: {} as Record<string, Record<string, string>>,
  sell: {} as Record<string, Record<string, string>>,
  risk: {} as Record<string, string>,
})
const capitalError = ref('')

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
  form.risk[r.key] = r.value
}

if (props.strategy?.config) {
  applyConfig(props.strategy.config as any, false)
} else if (props.template) {
  form.name = props.template.name
  applyConfig(props.template.config as any, true)
}

function applyConfig(cfg: any, resetEnabled: boolean) {
  if (resetEnabled) {
    for (const s of BUY_SIGNALS) form.buyEnabled[s.key] = false
    for (const s of SELL_SIGNALS) form.sellEnabled[s.key] = false
  }
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

function checkValue(val: unknown, def: { min?: number; max?: number; integer?: boolean }): string {
  if (val === '' || val == null || Number.isNaN(Number(val))) return '请输入有效数字'
  const n = Number(val)
  if (def.min != null && n < def.min) return `需 ≥ ${def.min}`
  if (def.max != null && n > def.max) return `需 ≤ ${def.max}`
  if (def.integer && !Number.isInteger(n)) return '需为整数'
  return ''
}

function setMapError(map: Record<string, Record<string, string>>, a: string, b: string, msg: string) {
  if (!map[a]) map[a] = {}
  if (msg) map[a][b] = msg
  else delete map[a][b]
}

function validateBuyParam(sigKey: string, pKey: string) {
  const s = BUY_SIGNALS.find((x) => x.key === sigKey)
  const p = s?.params.find((x) => x.key === pKey)
  if (!p) return
  setMapError(errors.buy, sigKey, pKey, checkValue(form.buyParams[sigKey][pKey], p))
}

function validateSellParam(sigKey: string, pKey: string) {
  const s = SELL_SIGNALS.find((x) => x.key === sigKey)
  const p = s?.params.find((x) => x.key === pKey)
  if (!p) return
  setMapError(errors.sell, sigKey, pKey, checkValue(form.sellParams[sigKey][pKey], p))
}

function validateRiskParam(key: string) {
  const r = RISK_ITEMS.find((x) => x.key === key)
  if (!r) return
  const msg = checkValue(form.risk[key], r)
  if (msg) errors.risk[key] = msg
  else delete errors.risk[key]
}

function validateCapital() {
  const v = Number(form.initial_capital)
  if (!form.initial_capital || Number.isNaN(v)) {
    capitalError.value = ''
    return
  }
  capitalError.value = v < 0 ? '本金不能为负数' : ''
}

function validateAll(): boolean {
  let ok = true
  for (const s of BUY_SIGNALS) {
    if (!form.buyEnabled[s.key]) continue
    for (const p of s.params) {
      const msg = checkValue(form.buyParams[s.key][p.key], p)
      setMapError(errors.buy, s.key, p.key, msg)
      if (msg) ok = false
    }
  }
  for (const s of SELL_SIGNALS) {
    if (!form.sellEnabled[s.key]) continue
    for (const p of s.params) {
      const msg = checkValue(form.sellParams[s.key][p.key], p)
      setMapError(errors.sell, s.key, p.key, msg)
      if (msg) ok = false
    }
  }
  for (const r of RISK_ITEMS) {
    const msg = checkValue(form.risk[r.key], r)
    if (msg) errors.risk[r.key] = msg
    else delete errors.risk[r.key]
    if (msg) ok = false
  }
  return ok
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

function onSave() {
  if (!validateAll()) {
    toast('存在非法参数，请修正红色标记项')
    return
  }
  emit('save', buildPayload())
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
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
  color: var(--text-2);
}

.param > span {
  padding-top: 6px;
}

.param-input-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
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

.param input.error {
  border-color: var(--danger);
}

.param-error {
  font-size: 11px;
  color: var(--danger);
  text-align: right;
}
</style>
