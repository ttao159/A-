<template>
  <div>
    <div class="card">
      <div class="row" style="align-items: center">
        <button class="back-btn" @click="$router.back()">‹</button>
        <div style="flex: 1">
          <div style="font-weight: 600">{{ name }} <span class="muted">{{ code }}</span></div>
          <div class="muted">{{ stockMeta }}</div>
        </div>
      </div>
      <div class="row" style="gap: 8px; margin-top: 12px">
        <button
          v-for="m in modes"
          :key="m.key"
          class="mode-btn"
          :class="{ active: mode === m.key }"
          @click="switchMode(m.key)"
        >
          {{ m.label }}
        </button>
      </div>
    </div>

    <div class="card">
      <div v-if="loading" class="empty">加载中...</div>
      <div v-else-if="error" class="empty">{{ error }}</div>
      <div v-else>
        <canvas ref="canvas" :width="W" :height="H" style="width: 100%; height: auto"></canvas>
        <div class="legend">
          <span v-if="mode === 'minute'">分时走势（昨收 {{ fmtPrice(minuteData?.prev_close ?? 0) }}）</span>
          <span v-else>{{ legendText }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { stockApi } from '../api'
import type { Bar, MinuteData } from '../api'
import { fmtPrice } from '../utils/format'

const route = useRoute()
const code = String(route.params.code ?? '')
const name = String(route.query.name ?? '')

const modes = [
  { key: 'minute', label: '分时' },
  { key: 'day', label: '日K' },
  { key: 'week', label: '周K' },
  { key: 'month', label: '月K' },
] as const
type Mode = (typeof modes)[number]['key']

const mode = ref<Mode>('day')
const loading = ref(false)
const error = ref('')
const bars = ref<Bar[]>([])
const minuteData = ref<MinuteData | null>(null)

const canvas = ref<HTMLCanvasElement | null>(null)
const W = 360
const H = 320

const UP = '#e0393e'
const DOWN = '#0aa869'

const stockMeta = computed(() => (mode.value === 'minute' ? '当日分时' : `${bars.value.length} 根K线`))
const legendText = computed(() => {
  const last = bars.value[bars.value.length - 1]
  if (!last) return ''
  const prev = bars.value[bars.value.length - 2]
  const chg = prev ? ((last.close - prev.close) / prev.close) * 100 : 0
  const ma = (p: number) => {
    if (bars.value.length < p) return '—'
    const s = bars.value.slice(-p).reduce((a, b) => a + b.close, 0)
    return (s / p).toFixed(2)
  }
  return `最新 ${fmtPrice(last.close)}（${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%） · MA5 ${ma(5)} · MA10 ${ma(10)} · MA20 ${ma(20)}`
})

onMounted(() => load())

async function load() {
  loading.value = true
  error.value = ''
  try {
    if (mode.value === 'minute') {
      minuteData.value = await stockApi.minute(code)
    } else {
      bars.value = await stockApi.bars(code, mode.value === 'day' ? 120 : 120, mode.value)
    }
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
    draw()
  }
}

function switchMode(m: Mode) {
  if (mode.value === m) return
  mode.value = m
  load()
}

watch(mode, () => load())

function draw() {
  const el = canvas.value
  if (!el) return
  const ctx = el.getContext('2d')
  if (!ctx) return
  ctx.clearRect(0, 0, W, H)
  if (mode.value === 'minute') drawMinute(ctx)
  else drawKline(ctx)
}

function drawKline(ctx: CanvasRenderingContext2D) {
  const data = bars.value
  if (!data.length) return
  const padL = 8
  const padR = 44
  const padT = 10
  const padB = 18
  const volTop = H * 0.72
  const priceH = volTop - padT
  const volH = H - padB - volTop

  let min = Infinity
  let max = -Infinity
  let maxVol = 0
  for (const b of data) {
    if (b.low < min) min = b.low
    if (b.high > max) max = b.high
    if (b.volume > maxVol) maxVol = b.volume
  }
  const range = max - min || 1
  const n = data.length
  const step = (W - padL - padR) / n
  const bodyW = Math.max(1, step * 0.6)
  const y = (v: number) => padT + ((max - v) / range) * priceH
  const volY = (v: number) => H - padB - (v / maxVol) * volH

  for (let i = 0; i < n; i++) {
    const b = data[i]
    const x = padL + step * i + step / 2
    const up = b.close >= b.open
    ctx.strokeStyle = up ? UP : DOWN
    ctx.fillStyle = up ? UP : DOWN
    ctx.beginPath()
    ctx.moveTo(x, y(b.high))
    ctx.lineTo(x, y(b.low))
    ctx.stroke()
    const top = y(Math.max(b.open, b.close))
    const bottom = y(Math.min(b.open, b.close))
    const bh = Math.max(1, bottom - top)
    ctx.fillRect(x - bodyW / 2, top, bodyW, bh)
    ctx.fillRect(x - bodyW / 2, volY(b.volume), bodyW, H - padB - volY(b.volume))
  }

  const maPeriods = [
    { n: 5, color: '#f5a623' },
    { n: 10, color: '#409eff' },
    { n: 20, color: '#9254de' },
  ]
  for (const { n: period, color } of maPeriods) {
    if (n < period) continue
    ctx.strokeStyle = color
    ctx.lineWidth = 1.1
    ctx.beginPath()
    let started = false
    let sum = 0
    for (let i = 0; i < n; i++) {
      sum += data[i].close
      if (i >= period - 1) {
        const ma = sum / period
        const px = padL + step * i + step / 2
        const py = y(ma)
        if (!started) {
          ctx.moveTo(px, py)
          started = true
        } else {
          ctx.lineTo(px, py)
        }
        sum -= data[i - period + 1].close
      }
    }
    ctx.stroke()
  }

  ctx.fillStyle = '#909399'
  ctx.font = '10px sans-serif'
  ctx.fillText(String(max.toFixed(2)), padL, padT + 8)
  ctx.fillText(String(min.toFixed(2)), padL, padT + priceH)
}

function drawMinute(ctx: CanvasRenderingContext2D) {
  const data = minuteData.value?.bars ?? []
  if (!data.length) return
  const prev = minuteData.value?.prev_close ?? 0
  const padL = 8
  const padR = 44
  const padT = 10
  const padB = 18
  const volTop = H * 0.72
  const priceH = volTop - padT
  const volH = H - padB - volTop

  const prices = data.map((b) => b.price)
  if (prev > 0) prices.push(prev)
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  const maxVol = Math.max(...data.map((b) => b.volume), 1)

  const n = data.length
  const step = (W - padL - padR) / Math.max(1, n - 1)
  const x = (i: number) => padL + step * i
  const y = (v: number) => padT + ((max - v) / range) * priceH
  const volY = (v: number) => H - padB - (v / maxVol) * volH

  let avg = 0
  let sum = 0
  ctx.strokeStyle = '#f5a623'
  ctx.lineWidth = 1.4
  ctx.beginPath()
  data.forEach((b, i) => {
    sum += b.price
    avg = sum / (i + 1)
    const px = x(i)
    const py = y(avg)
    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py)
  })
  ctx.stroke()

  ctx.strokeStyle = '#409eff'
  ctx.lineWidth = 1.2
  ctx.beginPath()
  data.forEach((b, i) => {
    const px = x(i)
    const py = y(b.price)
    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py)
  })
  ctx.stroke()

  if (prev > 0) {
    ctx.strokeStyle = '#bbb'
    ctx.setLineDash([4, 4])
    ctx.beginPath()
    ctx.moveTo(padL, y(prev))
    ctx.lineTo(W - padR, y(prev))
    ctx.stroke()
    ctx.setLineDash([])
  }

  ctx.fillStyle = '#409eff'
  for (let i = 0; i < n; i++) {
    const b = data[i]
    ctx.fillRect(x(i) - 1, volY(b.volume), 2, H - padB - volY(b.volume))
  }

  ctx.fillStyle = '#909399'
  ctx.font = '10px sans-serif'
  ctx.fillText(String(max.toFixed(2)), padL, padT + 8)
  ctx.fillText(String(min.toFixed(2)), padL, padT + priceH)
}
</script>

<style scoped>
.back-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: #fff;
  font-size: 20px;
  line-height: 1;
  margin-right: 8px;
}

.mode-btn {
  flex: 1;
  height: 34px;
  border-radius: 17px;
  border: 1px solid var(--border);
  background: #fff;
  color: var(--text);
  font-size: 13px;
}

.mode-btn.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.legend {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-2, #909399);
}
</style>
