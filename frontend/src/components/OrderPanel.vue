<template>
  <div v-if="visible" class="scan-mask" @click.self="close">
    <div class="box" style="width: 92%; text-align: left">
      <h3 style="margin: 0 0 12px">手动下单</h3>

      <template v-if="step === 'form'">
        <div class="field">
          <label>股票代码</label>
          <input v-model="form.code" placeholder="如 600000" />
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
          <input v-model.number="form.price" type="number" min="0.01" step="0.01" />
        </div>
        <div class="field">
          <label>数量（100 股整数倍）</label>
          <input v-model.number="form.qty" type="number" min="100" step="100" />
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
import { reactive, ref, watch } from 'vue'
import { orderApi } from '../api'
import type { OrderPrepareInput } from '../api/types'
import { useAccountStore } from '../stores/account'
import { useStrategyStore } from '../stores/strategy'
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
  price: 0,
  qty: 100,
  strategy_id: null as number | null,
})

const order = reactive<{ code: string; direction: string; price: number; qty: number }>({
  code: '',
  direction: 'buy',
  price: 0,
  qty: 100,
})

watch(
  () => props.visible,
  (v) => {
    if (v) {
      step.value = 'form'
      if (!strategyStore.strategies.length) strategyStore.fetch()
    }
  },
)

function buildInput(): OrderPrepareInput {
  return {
    code: form.code.trim(),
    direction: form.direction,
    price: form.price,
    qty: form.qty,
    strategy_id: form.strategy_id,
  }
}

function validate(): string {
  if (!form.code) return '请输入股票代码'
  if (!form.price || form.price <= 0) return '请输入有效价格'
  if (!form.qty || form.qty % 100 !== 0) return '数量需为 100 股整数倍'
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
    order.price = form.price
    order.qty = form.qty
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

.confirm-box .row {
  padding: 4px 0;
}

.risk-tip {
  margin-top: 12px;
  padding: 10px 12px;
  background: #fff3f3;
  color: var(--danger);
  border-radius: 8px;
  font-size: 13px;
}
</style>
