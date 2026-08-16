<template>
  <div>
    <div class="card">
      <div class="row" style="align-items: center">
        <button class="back-btn" @click="$router.back()">‹</button>
        <div style="flex: 1">
          <div style="font-weight: 600">{{ name }} <span class="muted">{{ code }}</span></div>
          <div class="muted">{{ stockMeta }}</div>
        </div>
        <button class="search-btn" @click="openSearch">搜索</button>
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
        <canvas
          ref="canvas"
          :width="W"
          :height="H"
          class="chart-canvas"
          style="width: 100%; height: auto"
          @touchstart.prevent="onTouchStart"
          @touchmove.prevent="onTouchMove"
          @touchend="onTouchEnd"
        ></canvas>
        <div class="legend">
          <span v-if="mode === 'minute'">{{ minuteInfo }}</span>
          <span v-else>{{ legendText }}</span>
        </div>
      </div>
    </div>

    <div v-if="searching" class="scan-mask" @click.self="searching = false">
      <div class="box search-box">
        <input v-model="searchQuery" placeholder="输入代码或名称搜索" />
        <div class="search-results">
          <div v-if="!searchResults.length" class="empty">无匹配结果</div>
          <div v-for="s in searchResults" :key="s.code" class="search-item" @click="pickStock(s)">
            <span class="search-code">{{ s.code }}</span>
            <span class="search-name">{{ s.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { stockApi } from '../api'
import type { Bar, MinuteData, Stock } from '../api'
import { fmtPrice } from '../utils/format'
import { isTradingTime } from '../utils/date'
import { chartColors } from '../utils/theme'
import { useThemeRedraw } from '../composables/useThemeRedraw'

const route = useRoute()
const code = ref(String(route.params.code ?? ''))
const name = ref(String(route.query.name ?? ''))

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

const PAD_L = 8
const PAD_R = 44
const PAD_T = 10
const PAD_B = 18
const VOL_TOP = 0.72
const MIN_VISIBLE = 20
const MAX_VISIBLE = 240

const visibleCount = ref(120)
const crossIndex = ref<number | null>(null)

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
  const limitUp = prev ? prev.close * 1.1 : 0
  const limitDown = prev ? prev.close * 0.9 : 0
  return `最新 ${fmtPrice(last.close)}（${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%） · MA5 ${ma(5)} · MA10 ${ma(10)} · MA20 ${ma(20)} · 涨停 ${fmtPrice(limitUp)} · 跌停 ${fmtPrice(limitDown)}`
})

const minuteInfo = computed(() => {
  const md = minuteData.value
  if (!md || !md.bars.length) return '分时走势'
  const prev = md.prev_close || 0
  const last = md.bars[md.bars.length - 1]
  const avg = md.bars.reduce((s, b) => s + b.price, 0) / md.bars.length
  const chg = prev ? ((last.price - prev) / prev) * 100 : 0
  return `昨收 ${fmtPrice(prev)} · 现价 ${fmtPrice(last.price)}（${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%） · 均价 ${fmtPrice(avg)} · 涨停 ${fmtPrice(prev * 1.1)} · 跌停 ${fmtPrice(prev * 0.9)}`
})

onMounted(() => {
  load()
  startPolling()
})

onUnmounted(stopPolling)

useThemeRedraw(() => draw())

async function load(silent = false) {
  if (!silent) loading.value = true
  if (!silent) error.value = ''
  try {
    if (mode.value === 'minute') {
      minuteData.value = await stockApi.minute(code.value)
    } else {
      bars.value = await stockApi.bars(code.value, mode.value === 'day' ? 120 : 120, mode.value)
    }
  } catch (e) {
    if (!silent) error.value = (e as Error).message
  } finally {
    loading.value = false
    draw()
  }
}

let refreshTimer: number | undefined

function startPolling() {
  stopPolling()
  refreshTimer = window.setInterval(() => {
    if (isTradingTime() && !searching.value) load(true)
  }, 15000)
}

function stopPolling() {
  if (refreshTimer) window.clearInterval(refreshTimer)
  refreshTimer = undefined
}

const searching = ref(false)
const searchQuery = ref('')
const stockList = ref<Stock[]>([])
const stockLoaded = ref(false)

async function openSearch() {
  searching.value = true
  if (stockLoaded.value) return
  try {
    stockList.value = await stockApi.list()
    stockLoaded.value = true
  } catch (e) {
    error.value = (e as Error).message
  }
}

const searchResults = computed(() => {
  const q = searchQuery.value.trim()
  const list = stockList.value
  if (!q) return list.slice(0, 50)
  return list.filter((s) => s.code.includes(q) || s.name.includes(q)).slice(0, 50)
})

function pickStock(s: Stock) {
  code.value = s.code
  name.value = s.name
  searching.value = false
  searchQuery.value = ''
  load()
}

watch(
  () => route.params.code,
  () => {
    const c = String(route.params.code ?? '')
    if (c && c !== code.value) {
      code.value = c
      name.value = String(route.query.name ?? '')
      load()
    }
  },
)

function switchMode(m: Mode) {
  if (mode.value === m) return
  mode.value = m
}

watch(mode, () => {
  resetVisible()
  load()
})

function resetVisible() {
  visibleCount.value = mode.value === 'minute' ? 240 : 120
}

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
  const c = chartColors()
  const all = bars.value
  if (!all.length) return
  const data = all.slice(-visibleCount.value)
  const volTop = H * VOL_TOP
  const priceH = volTop - PAD_T
  const volH = H - PAD_B - volTop

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
  const step = (W - PAD_L - PAD_R) / n
  const bodyW = Math.max(1, step * 0.6)
  const y = (v: number) => PAD_T + ((max - v) / range) * priceH
  const volY = (v: number) => H - PAD_B - (v / maxVol) * volH

  for (let i = 0; i < n; i++) {
    const b = data[i]
    const x = PAD_L + step * i + step / 2
    const up = b.close >= b.open
    ctx.strokeStyle = up ? c.up : c.down
    ctx.fillStyle = up ? c.up : c.down
    ctx.beginPath()
    ctx.moveTo(x, y(b.high))
    ctx.lineTo(x, y(b.low))
    ctx.stroke()
    const top = y(Math.max(b.open, b.close))
    const bottom = y(Math.min(b.open, b.close))
    const bh = Math.max(1, bottom - top)
    ctx.fillRect(x - bodyW / 2, top, bodyW, bh)
    ctx.fillRect(x - bodyW / 2, volY(b.volume), bodyW, H - PAD_B - volY(b.volume))
  }

  const maPeriods = [
    { n: 5, color: '#f5a623' },
    { n: 10, color: '#409eff' },
    { n: 20, color: '#9254de' },
  ]
  const offset = all.length - data.length
  for (const { n: period, color } of maPeriods) {
    if (all.length < period) continue
    ctx.strokeStyle = color
    ctx.lineWidth = 1.1
    ctx.beginPath()
    let started = false
    let sum = 0
    for (let j = 0; j < all.length; j++) {
      sum += all[j].close
      if (j >= period - 1) {
        const ma = sum / period
        sum -= all[j - period + 1].close
        if (j < offset) continue
        const px = PAD_L + step * (j - offset) + step / 2
        const py = y(ma)
        if (!started) {
          ctx.moveTo(px, py)
          started = true
        } else {
          ctx.lineTo(px, py)
        }
      }
    }
    ctx.stroke()
  }
  ctx.lineWidth = 1

  ctx.fillStyle = c.text2
  ctx.font = '10px sans-serif'
  ctx.fillText(String(max.toFixed(2)), PAD_L, PAD_T + 8)
  ctx.fillText(String(min.toFixed(2)), PAD_L, PAD_T + priceH)

  if (crossIndex.value !== null) {
    const i = crossIndex.value
    const b = data[i]
    if (b) {
      const x = PAD_L + step * i + step / 2
      drawCrosshair(ctx, x, y(b.close))
      drawCrossLabel(ctx, b.date, `开${b.open.toFixed(2)} 高${b.high.toFixed(2)} 低${b.low.toFixed(2)} 收${b.close.toFixed(2)}`)
    }
  }
}

function drawMinute(ctx: CanvasRenderingContext2D) {
  const c = chartColors()
  const data = (minuteData.value?.bars ?? []).slice(-visibleCount.value)
  if (!data.length) return
  const prev = minuteData.value?.prev_close ?? 0
  const volTop = H * VOL_TOP
  const priceH = volTop - PAD_T
  const volH = H - PAD_B - volTop

  const prices = data.map((b) => b.price)
  if (prev > 0) prices.push(prev)
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  const maxVol = Math.max(...data.map((b) => b.volume), 1)

  const n = data.length
  const step = (W - PAD_L - PAD_R) / Math.max(1, n - 1)
  const x = (i: number) => PAD_L + step * i
  const y = (v: number) => PAD_T + ((max - v) / range) * priceH
  const volY = (v: number) => H - PAD_B - (v / maxVol) * volH

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
    ctx.strokeStyle = c.grid
    ctx.setLineDash([4, 4])
    ctx.beginPath()
    ctx.moveTo(PAD_L, y(prev))
    ctx.lineTo(W - PAD_R, y(prev))
    ctx.stroke()
    ctx.setLineDash([])

    const upLimit = prev * 1.1
    const downLimit = prev * 0.9
    ctx.setLineDash([3, 3])
    if (upLimit < max) {
      ctx.strokeStyle = c.up
      ctx.beginPath()
      ctx.moveTo(PAD_L, y(upLimit))
      ctx.lineTo(W - PAD_R, y(upLimit))
      ctx.stroke()
    }
    if (downLimit > min) {
      ctx.strokeStyle = c.down
      ctx.beginPath()
      ctx.moveTo(PAD_L, y(downLimit))
      ctx.lineTo(W - PAD_R, y(downLimit))
      ctx.stroke()
    }
    ctx.setLineDash([])
  }

  for (let i = 0; i < n; i++) {
    const b = data[i]
    ctx.fillStyle = prev > 0 && b.price >= prev ? c.up : c.down
    ctx.fillRect(x(i) - 1, volY(b.volume), 2, H - PAD_B - volY(b.volume))
  }

  ctx.fillStyle = c.text2
  ctx.font = '10px sans-serif'
  ctx.fillText(String(max.toFixed(2)), PAD_L, PAD_T + 8)
  ctx.fillText(String(min.toFixed(2)), PAD_L, PAD_T + priceH)

  if (crossIndex.value !== null) {
    const i = crossIndex.value
    const b = data[i]
    if (b) {
      drawCrosshair(ctx, x(i), y(b.price))
      drawCrossLabel(ctx, b.time, `价格 ${b.price.toFixed(2)}`)
    }
  }
}

function drawCrosshair(ctx: CanvasRenderingContext2D, px: number, py: number) {
  const c = chartColors()
  ctx.save()
  ctx.strokeStyle = c.text2
  ctx.setLineDash([3, 3])
  ctx.beginPath()
  ctx.moveTo(px, PAD_T)
  ctx.lineTo(px, H - PAD_B)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(PAD_L, py)
  ctx.lineTo(W - PAD_R, py)
  ctx.stroke()
  ctx.restore()
}

function drawCrossLabel(ctx: CanvasRenderingContext2D, time: string, detail: string) {
  const text = `${time}  ${detail}`
  ctx.save()
  ctx.font = '11px sans-serif'
  const tw = ctx.measureText(text).width
  const bw = tw + 14
  const bh = 20
  const bx = Math.max(PAD_L, Math.min(W - PAD_R - bw, W / 2 - bw / 2))
  ctx.fillStyle = 'rgba(0, 0, 0, 0.62)'
  ctx.fillRect(bx, PAD_T, bw, bh)
  ctx.fillStyle = '#ffffff'
  ctx.textBaseline = 'middle'
  ctx.fillText(text, bx + 7, PAD_T + bh / 2)
  ctx.restore()
}

let pinchStartDist = 0
let pinchStartCount = 120

function updateCross(touch: Touch) {
  const el = canvas.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  if (!rect.width) return
  const px = ((touch.clientX - rect.left) / rect.width) * W
  const data =
    mode.value === 'minute'
      ? (minuteData.value?.bars ?? []).slice(-visibleCount.value)
      : bars.value.slice(-visibleCount.value)
  if (!data.length) return
  const n = data.length
  const plotW = W - PAD_L - PAD_R
  let idx: number
  if (mode.value === 'minute') {
    const step = plotW / Math.max(1, n - 1)
    idx = Math.round((px - PAD_L) / step)
  } else {
    const step = plotW / n
    idx = Math.floor((px - PAD_L) / step)
  }
  crossIndex.value = Math.max(0, Math.min(n - 1, idx))
  draw()
}

function twoFingerDist(e: TouchEvent): number {
  const a = e.touches[0]
  const b = e.touches[1]
  return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY)
}

function onTouchStart(e: TouchEvent) {
  if (e.touches.length === 1) {
    updateCross(e.touches[0])
  } else if (e.touches.length === 2) {
    pinchStartDist = twoFingerDist(e)
    pinchStartCount = visibleCount.value
    crossIndex.value = null
    draw()
  }
}

function onTouchMove(e: TouchEvent) {
  if (e.touches.length === 1) {
    updateCross(e.touches[0])
  } else if (e.touches.length === 2) {
    const d = twoFingerDist(e)
    if (pinchStartDist > 0) {
      const ratio = d / pinchStartDist
      const next = Math.round(pinchStartCount / ratio)
      visibleCount.value = Math.max(MIN_VISIBLE, Math.min(MAX_VISIBLE, next))
      draw()
    }
  }
}

function onTouchEnd(e: TouchEvent) {
  if (e.touches.length === 0) {
    crossIndex.value = null
    pinchStartDist = 0
    draw()
  }
}
</script>

<style scoped>
.back-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--card);
  font-size: 20px;
  line-height: 1;
  margin-right: 8px;
}

.mode-btn {
  flex: 1;
  height: 34px;
  border-radius: 17px;
  border: 1px solid var(--border);
  background: var(--card);
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

.chart-canvas {
  touch-action: none;
}

.search-btn {
  height: 32px;
  padding: 0 14px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text);
  font-size: 13px;
}

.search-box {
  max-height: 70%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  width: 92%;
}

.search-box input {
  width: 100%;
  height: 38px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
  margin-bottom: 10px;
}

.search-results {
  flex: 1;
  overflow-y: auto;
}

.search-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 4px;
  border-bottom: 1px dashed var(--border);
  cursor: pointer;
}

.search-item:active {
  background: var(--bg);
}

.search-code {
  font-weight: 600;
  font-size: 14px;
  min-width: 64px;
}

.search-name {
  color: var(--text);
  font-size: 14px;
}
</style>
