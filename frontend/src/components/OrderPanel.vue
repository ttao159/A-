<template>
  <div v-if="visible" class="scan-mask" @click.self="close">
    <div class="box" style="width: 92%; text-align: left">
      <h3 style="margin: 0 0 12px">手动下单</h3>

      <template v-if="step === 'form'">
        <div class="field suggest-field">
          <label>股票代码</label>
          <input
            v-model="form.code"
            placeholder="输入代码或名称搜索"
            @focus="showSuggest = true"
            @blur="onCodeBlur"
          />
          <div v-if="blockedTip" class="board-tip">{{ blockedTip }}</div>
          <div v-else-if="showSuggest && suggestions.length" class="suggest-list">
            <div
              v-for="s in suggestions"
              :key="s.code"
              class="suggest-item"
              @mousedown.prevent="pick(s)"
            >
              <span class="s-name">{{ s.name }}</span>
              <span class="s-code">{{ s.code }}</span>
            </div>
          </div>
        </div>
        <div class="field">
          <label>方向</label>
          <div class="row" style="gap: 8px">
            <button class="btn" :class="form.direction === 'buy' ? '' : 'ghost'" style="flex: 1" @click="form.direction = 'buy'">
              买入
            </button>
            <button class="btn" :class="form.direction === 'sell' ? '' : 'ghost'" style="flex: 1" @click="form.direction = 'sell'">
              卖出
            </button>
          </div>
        </div>
        <div class="field">
          <label>价格（元）</label>
          <input v-model="form.price" type="text" inputmode="decimal" placeholder="0.00" @input="onPriceInput" />
        </div>
        <div class="field">
          <label>数量（100 股整数倍）</label>
          <input v-model="form.qty" type="text" inputmode="numeric" placeholder="100 的整数倍" @input="onQtyInput" />
        </div>
        <div class="field">
          <label>所属策略（可选）</label>
          <select v-model="form.strategy_id">
            <option :value="null">不指定</option>
            <option v-for="s in strategyStore.strategies" :key="s.id" :value="s.id">
              {{ s.name }}
            </option>
          </select>
        </div>
        <div class="row" style="gap: 12px">
          <button class="btn block" :disabled="submitting" @click="prepare">
            {{ submitting ? '提交中...' : '提交' }}
          </button>
          <button class="btn ghost block" @click="close">取消</button>
        </div>
      </template>

      <template v-else-if="step === 'confirm'">
        <div class="confirm-box">
          <div class="row"><span class="muted">代码</span><span>{{ order.code }}</span></div>
          <div class="row"><span class="muted">方向</span><span>{{ order.direction === 'buy' ? '买入' : '卖出' }}</span></div>
          <div class="row"><span class="muted">价格</span><span>{{ fmtPrice(order.price) }}</span></div>
          <div class="row"><span class="muted">数量</span><span>{{ order.qty }} 股</span></div>
          <div class="row"><span class="muted">金额</span><span>{{ fmtMoney(order.price * order.qty) }}</span></div>
        </div>
        <div v-if="accountStore.isLive" class="risk-tip">
          实盘交易存在风险，请确认委托信息无误后下发。
        </div>
        <div class="row" style="gap: 12px; margin-top: 12px">
          <button class="btn block" :disabled="submitting" @click="confirm">
            {{ submitting ? '下发中...' : '确认下单' }}
          </button>
          <button class="btn ghost block" @click="step = 'form'">返回修改</button>
        </div>
      </template>

      <template v-else>
        <div class="result-box">
          <div :class="resultOk ? 'text-primary' : 'text-danger'" style="font-size: 16px; font-weight: 600; margin-bottom: 8px">
            {{ resultOk ? '下单成功' : '下单被拒绝' }}
          </div>
          <div class="muted">{{ resultMsg }}</div>
        </div>
        <button class="btn block" style="margin-top: 12px" @click="close">完成</button>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { orderApi, stockApi } from '../api'
import type { Stock } from '../api'
import type { OrderPrepareInput } from '../api/types'
import { useAccountStore } from '../stores/account'
import { useStrategyStore } from '../stores/strategy'
import { isBlockedBoard } from '../utils/board'
import { fmtMoney, fmtPrice } from '../utils/format'
import { toast } from '../utils/toast'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ close: []; done: [] }>()

const accountStore = useAccountStore()
const strategyStore = useStrategyStore()

const step = ref<'form' | 'confirm' | 'result'>('form')
const submitting = ref(false)
const resultOk = ref(false)
const resultMsg = ref('')
const requestId = ref('')

const form = reactive({
  code: '',
  direction: 'buy',
  price: '',
  qty: '100',
  strategy_id: null as number | null,
})

const stockList = ref<Stock[]>([])
const showSuggest = ref(false)
const blockedTip = ref('')

const suggestions = computed(() => {
  const q = form.code.trim()
  if (!q) return []
  const num = /^\d+$/.test(q)
  return stockList.value
    .filter((s) => (num ? s.code.startsWith(q) : s.name.includes(q) || s.code.startsWith(q)))
    .slice(0, 8)
})

watch(
  () => props.visible,
  (v) => {
    if (v) {
      step.value = 'form'
      showSuggest.value = false
      if (!strategyStore.strategies.length) strategyStore.fetch()
      if (!stockList.value.length) {
        stockApi.list().then((list) => (stockList.value = list)).catch(() => {})
      }
    }
  },
)

watch(
  () => form.code,
  (code) => {
    const t = code.trim()
    blockedTip.value =
      /^(300|301|688|689)/.test(t) && t.length >= 3 ? '本系统不支持该板块（创业板/科创板）' : ''
  },
)

function pick(s: Stock) {
  form.code = s.code
  showSuggest.value = false
}

function onCodeBlur() {
  setTimeout(() => (showSuggest.value = false), 150)
}

const order = reactive<{ code: string; direction: string; price: number; qty: number }>({
  code: '',
  direction: 'buy',
  price: 0,
  qty: 100,
})

let priceTimer: ReturnType<typeof setTimeout> | undefined
watch(
  () => form.code,
  (code) => {
    if (priceTimer) clearTimeout(priceTimer)
    const trimmed = code.trim()
    if (!/^\d{6}$/.test(trimmed)) return
    priceTimer = setTimeout(async () => {
      try {
        const md = await stockApi.minute(trimmed)
        const last = md.bars[md.bars.length - 1]
        const px = last ? last.price : md.prev_close
        if (px > 0) {
          form.price = px.toFixed(2)
          toast(`已按现价 ${fmtPrice(px)} 填入`)
        }
      } catch {
        // 获取现价失败时保留手动输入
      }
    }, 400)
  },
)

function onPriceInput() {
  let s = form.price.replace(/[^\d.]/g, '')
  const firstDot = s.indexOf('.')
  if (firstDot >= 0) {
    s = s.slice(0, firstDot + 1) + s.slice(firstDot + 1).replace(/\./g, '')
    const [int, dec] = s.split('.')
    s = int + '.' + (dec || '').slice(0, 2)
  }
  if (s.startsWith('.')) s = '0' + s
  form.price = s
}

function onQtyInput() {
  form.qty = form.qty.replace(/\D/g, '').replace(/^0+(?=\d)/, '')
}

function buildInput(): OrderPrepareInput {
  return {
    code: form.code.trim(),
    direction: form.direction,
    price: Number(form.price),
    qty: Number(form.qty),
    strategy_id: form.strategy_id,
  }
}

function validate(): string {
  const price = Number(form.price)
  const qty = Number(form.qty)
  if (!form.code) return '请输入股票代码'
  if (isBlockedBoard(form.code.trim())) return '本系统不支持该板块（创业板/科创板）'
  if (!price || price <= 0) return '请输入有效价格'
  if (!qty || qty % 100 !== 0) return '数量需为 100 股整数倍'
  return ''
}

async function prepare() {
  const err = validate()
  if (err) {
    toast(err)
    return
  }
  submitting.value = true
  try {
    const res = await orderApi.prepare(buildInput())
    requestId.value = res.request_id
    order.code = form.code
    order.direction = form.direction
    order.price = Number(form.price)
    order.qty = Number(form.qty)
    step.value = 'confirm'
  } catch (e) {
    toast((e as Error).message)
  } finally {
    submitting.value = false
  }
}

async function confirm() {
  submitting.value = true
  try {
    const res = await orderApi.confirm(requestId.value)
    resultOk.value = res.status === 'filled'
    resultMsg.value = res.status === 'filled' ? `委托已成交，订单号 ${res.order_id}` : (res.reason || '已拒绝')
    step.value = 'result'
    emit('done')
  } catch (e) {
    toast((e as Error).message)
  } finally {
    submitting.value = false
  }
}

function close() {
  emit('close')
}
</script>

<style scoped>
.confirm-box {
  background: var(--bg);
  border-radius: 8px;
  padding: 12px;
}

.suggest-field {
  position: relative;
}

.suggest-list {
  position: absolute;
  left: 0;
  right: 0;
  top: 100%;
  z-index: 20;
  margin-top: 4px;
  max-height: 220px;
  overflow-y: auto;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.suggest-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
}

.suggest-item:active {
  background: var(--bg);
}

.s-name {
  font-size: 14px;
}

.s-code {
  font-size: 12px;
  color: var(--text-2);
}

.board-tip {
  margin-top: 6px;
  font-size: 12px;
  color: var(--danger);
}

.confirm-box .row {
  padding: 4px 0;
}

.risk-tip {
  margin-top: 12px;
  padding: 10px 12px;
  background: var(--danger-bg);
  color: var(--danger);
  border-radius: 8px;
  font-size: 13px;
}
</style>
