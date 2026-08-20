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
      <div class="row" style="gap: 6px; margin-top: 8px">
        <button
          v-for="t in drawTools"
          :key="t.key"
          class="draw-btn"
          :class="{ active: drawTool === t.key }"
          @click="drawTool = drawTool === t.key ? 'none' : (t.key as DrawTool)"
        >
          {{ t.label }}
        </button>
        <button
          v-if="drawnLines.length"
          class="draw-btn"
          @click="clearDrawnLines()"
        >清除</button>
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
          @pointerdown.prevent="onPointerDown"
          @pointermove.prevent="onPointerMove"
          @pointerup="onPointerEnd"
          @pointercancel="onPointerEnd"
          @pointerleave="onPointerEnd"
        ></canvas>
        <div v-if="!netStatus.online" class="net-offline-hint">网络中断，恢复后自动补全行情</div>
      <div v-else-if="catchingUp" class="net-offline-hint">数据补全中...</div>
      <div class="legend">
          <span v-if="mode === 'minute'">{{ minuteInfo }}</span>
          <span v-else>{{ legendText }}</span>
          <label v-if="mode !== 'minute'" class="ma-toggle">
            <input type="checkbox" v-model="showPatterns" />
            形态
          </label>
          <label v-if="mode !== 'minute'" class="ma-toggle">
            <input type="checkbox" v-model="showMA" />
            均线
          </label>
        </div>
      </div>
    </div>

    <StockDiagnosis :code="code" />

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
import StockDiagnosis from '../components/StockDiagnosis.vue'
import { fmtPrice } from '../utils/format'
import { isTradingTime } from '../utils/date'
import { chartColors } from '../utils/theme'
import { useThemeRedraw } from '../composables/useThemeRedraw'
import { netStatus } from '../composables/netStatus'
import { hiDPIContext } from '../utils/canvas'
import { type PatternResult, type SupportResistance, findSupportResistance, detectPatterns } from '../utils/patterns'

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
const showMA = ref(true)
const scrollOffset = ref(0)
const showPatterns = ref(true)

const maxScrollOffset = computed(() => Math.max(0, bars.value.length - visibleCount.value))

function visibleBars() {
  const start = Math.max(0, bars.value.length - visibleCount.value - scrollOffset.value)
  return bars.value.slice(start, bars.value.length - scrollOffset.value)
}

type DrawTool = 'none' | 'trendline' | 'horizontal' | 'erase'
const drawTool = ref<DrawTool>('none')

interface DrawnLine {
  type: 'trendline' | 'horizontal'
  id: number
  x1: number
  y1: number
  x2: number
  y2: number
  color: string
  dash: boolean
}
const drawnLines = ref<DrawnLine[]>([])
const drawStart = ref<{ x: number; y: number } | null>(null)
let drawIdSeq = 0

const detectedPatterns = ref<PatternResult[]>([])
const detectedSR = ref<SupportResistance[]>([])

const drawTools = [
  { key: 'trendline', label: '趋势线' },
  { key: 'horizontal', label: '水平线' },
  { key: 'erase', label: '擦除' },
]

function lsKey() {
  return `drawnLines_${code.value}`
}

function saveDrawnLines() {
  localStorage.setItem(lsKey(), JSON.stringify(drawnLines.value))
}

function loadDrawnLines() {
  try {
    const raw = localStorage.getItem(lsKey())
    if (raw) drawnLines.value = JSON.parse(raw)
  } catch { /* ignore */ }
}

function detectPatternsOnData() {
  if (mode.value === 'minute') {
    detectedSR.value = []
    detectedPatterns.value = []
    return
  }
  try {
    if (bars.value.length < 5) {
      detectedSR.value = []
      detectedPatterns.value = []
      return
    }
    detectedSR.value = findSupportResistance(bars.value)
    detectedPatterns.value = detectPatterns(bars.value)
  } catch {
    detectedSR.value = []
    detectedPatterns.value = []
  }
}

function clearDrawnLines() {
  drawnLines.value = []
  saveDrawnLines()
  draw()
}

watch(drawTool, () => {
  if (drawTool.value !== 'none') crossIndex.value = null
  draw()
})

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

const catchingUp = ref(false)
watch(() => netStatus.online, (on) => {
  if (!on) return
  catchingUp.value = true
  load(true).finally(() => {
    catchingUp.value = false
  })
})

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
    loadDrawnLines()
    detectPatternsOnData()
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
  scrollOffset.value = 0
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
  scrollOffset.value = 0
}

function draw() {
  const el = canvas.value
  if (!el) return
  const ctx = hiDPIContext(el, W, H)
  if (!ctx) return
  ctx.clearRect(0, 0, W, H)
  if (mode.value === 'minute') drawMinute(ctx)
  else drawKline(ctx)
  drawDrawnLines(ctx)
  drawSupportResistance(ctx)
  drawPatterns(ctx)
  if (drawStart.value) drawPreviewLine(ctx)
  if (drawTool.value !== 'none') drawCanvasHint(ctx)
}

function drawKline(ctx: CanvasRenderingContext2D) {
  const c = chartColors()
  const all = bars.value
  if (!all.length) return
  const data = visibleBars()
  if (!data.length) return
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
    { n: 5, color: c.ma1 },
    { n: 10, color: c.ma2 },
    { n: 20, color: c.ma3 },
  ]
  const offset = Math.max(0, all.length - visibleCount.value - scrollOffset.value)
  if (showMA.value) {
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
  ctx.strokeStyle = c.ma1
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

  ctx.strokeStyle = c.ma2
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

function currentPlotData() {
  if (mode.value === 'minute') return (minuteData.value?.bars ?? []).slice(-visibleCount.value)
  return visibleBars()
}

function currentPlotStep(padded = false) {
  const data = currentPlotData()
  const n = data.length
  const plotW = padded ? W - PAD_L - PAD_R : W
  if (mode.value === 'minute') {
    return plotW / Math.max(1, n - 1)
  }
  return plotW / n
}

function drawDrawnLines(ctx: CanvasRenderingContext2D) {
  if (!drawnLines.value.length) return
  const data = currentPlotData()
  if (!data.length) return

  for (const line of drawnLines.value) {
    ctx.save()
    if (line.dash) ctx.setLineDash([6, 4])
    ctx.strokeStyle = line.color
    ctx.lineWidth = 1.8
    ctx.beginPath()
    ctx.moveTo(line.x1, line.y1)
    ctx.lineTo(line.x2, line.y2)
    ctx.stroke()
    if (drawTool.value === 'erase') {
      ctx.fillStyle = 'rgba(255,255,255,0.6)'
      ctx.fillRect(line.x1 - 6, line.y1 - 6, 12, 12)
      ctx.fillRect(line.x2 - 6, line.y2 - 6, 12, 12)
    }
    ctx.restore()
  }
}

function drawSupportResistance(ctx: CanvasRenderingContext2D) {
  if (mode.value === 'minute' || !detectedSR.value.length) return
  const data = visibleBars()
  if (!data.length) return

  let min = Infinity
  let max = -Infinity
  for (const b of data) {
    if (b.high > max) max = b.high
    if (b.low < min) min = b.low
  }
  const range = max - min || 1
  const volTop = H * VOL_TOP
  const priceH = volTop - PAD_T
  const y = (v: number) => PAD_T + ((max - v) / range) * priceH

  for (const sr of detectedSR.value) {
    const py = y(sr.price)
    if (py < PAD_T || py > volTop) continue
    const c = chartColors()
    ctx.save()
    ctx.strokeStyle = sr.type === 'resistance' ? c.up : c.down
    ctx.lineWidth = 1
    ctx.setLineDash([4, 4])
    ctx.beginPath()
    ctx.moveTo(PAD_L, py)
    ctx.lineTo(W - PAD_R, py)
    ctx.stroke()
    ctx.setLineDash([])

    ctx.font = '9px sans-serif'
    ctx.fillStyle = sr.type === 'resistance' ? c.up : c.down
    ctx.textBaseline = 'bottom'
    ctx.fillText(`${sr.type === 'resistance' ? 'R' : 'S'} ${sr.price.toFixed(2)}`, W - PAD_R, py - 1)
    ctx.restore()
  }
}

function drawPatterns(ctx: CanvasRenderingContext2D) {
  if (mode.value === 'minute' || !showPatterns.value) return
  const all = bars.value
  if (!all.length) return

  const visibleStart = Math.max(0, all.length - visibleCount.value - scrollOffset.value)
  const visibleEnd = all.length - scrollOffset.value
  const data = visibleBars()
  if (!data.length) return
  const step = currentPlotStep(true)

  let drawn = 0
  for (const p of detectedPatterns.value) {
    if (drawn >= 3) break
    const startIdx = p.startIdx
    const endIdx = p.endIdx ?? p.startIdx
    if (endIdx < visibleStart || startIdx >= visibleEnd) continue

    const relStart = startIdx - visibleStart
    const relEnd = endIdx - visibleStart
    const clampedStart = Math.max(0, relStart)
    const clampedEnd = Math.min(data.length - 1, relEnd)
    const x1 = PAD_L + step * clampedStart + step / 2
    const x2 = PAD_L + step * clampedEnd + step / 2
    const bx = Math.min(x1, x2) - 6
    const bw = Math.abs(x2 - x1) + 12
    const by = PAD_T + 2
    const bh = (H * VOL_TOP) - PAD_T - 4

    const bullish = p.direction === 'bullish'
    const baseColor = bullish ? chartColors().down : chartColors().up
    const alpha = Math.min(1, p.score * 0.5 + 0.3)

    ctx.save()
    ctx.globalAlpha = alpha * 0.25
    ctx.fillStyle = baseColor
    ctx.fillRect(bx, by, bw, bh)
    ctx.globalAlpha = alpha
    ctx.strokeStyle = baseColor
    ctx.lineWidth = 1.4
    ctx.setLineDash([5, 3])
    ctx.strokeRect(bx, by, bw, bh)
    ctx.setLineDash([])

    const label = `${p.label} ${Math.round(p.score * 100)}%`
    ctx.font = '11px sans-serif'
    const tw = ctx.measureText(label).width + 10
    ctx.globalAlpha = alpha * 0.4
    ctx.fillStyle = baseColor
    ctx.fillRect(bx, by, tw, 20)
    ctx.globalAlpha = alpha
    ctx.fillStyle = bullish ? chartColors().down : chartColors().up
    ctx.textBaseline = 'middle'
    ctx.fillText(label, bx + 5, by + 10)
    ctx.restore()
    drawn++
  }
}

function drawPreviewLine(ctx: CanvasRenderingContext2D) {
  const start = drawStart.value
  if (!start) return
  const c = chartColors()
  const ptr = [...pointers.values()]?.[0]
  if (!ptr) return

  ctx.save()
  if (drawTool.value === 'horizontal') {
    ctx.strokeStyle = c.line
    ctx.lineWidth = 1.4
    ctx.setLineDash([5, 3])
    ctx.beginPath()
    ctx.moveTo(PAD_L, start.y)
    ctx.lineTo(W - PAD_R, start.y)
    ctx.stroke()
  } else if (drawTool.value === 'trendline') {
    ctx.strokeStyle = c.line
    ctx.lineWidth = 1.4
    ctx.setLineDash([5, 3])
    ctx.beginPath()
    ctx.moveTo(start.x, start.y)
    ctx.lineTo(ptr.x, ptr.y)
    ctx.stroke()
  }
  ctx.setLineDash([])
  ctx.restore()
}

function drawCanvasHint(ctx: CanvasRenderingContext2D) {
  ctx.save()
  ctx.font = '12px sans-serif'
  ctx.fillStyle = chartColors().text2
  ctx.textAlign = 'center'
  const msg =
    drawTool.value === 'trendline'
      ? '点击起点拖至终点画趋势线'
      : drawTool.value === 'horizontal'
        ? '点击位置画水平线'
        : drawTool.value === 'erase'
          ? '点击线条以擦除'
          : ''
  ctx.fillText(msg, W / 2, H - 4)
  ctx.textAlign = 'start'
  ctx.restore()
}

function deleteLineAt(px: number, py: number) {
  const threshold = 12
  let idx = -1
  for (let i = drawnLines.value.length - 1; i >= 0; i--) {
    const l = drawnLines.value[i]
    if (distanceToSegment(px, py, l.x1, l.y1, l.x2, l.y2) < threshold) {
      idx = i
      break
    }
  }
  if (idx >= 0) {
    drawnLines.value.splice(idx, 1)
    saveDrawnLines()
    draw()
  }
}

function distanceToSegment(
  px: number,
  py: number,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
) {
  const dx = x2 - x1
  const dy = y2 - y1
  const len2 = dx * dx + dy * dy
  if (len2 === 0) return Math.hypot(px - x1, py - y1)
  let t = ((px - x1) * dx + (py - y1) * dy) / len2
  t = Math.max(0, Math.min(1, t))
  return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))
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
let dragState: 'none' | 'crosshair' | 'pan' = 'none'
let dragStartX = 0
let dragStartOffset = 0

const pointers = new Map<number, { x: number; y: number }>()

function canvasPoint(e: PointerEvent) {
  const el = canvas.value
  if (!el) return { x: 0, y: 0 }
  const rect = el.getBoundingClientRect()
  return {
    x: rect.width ? ((e.clientX - rect.left) / rect.width) * W : 0,
    y: rect.height ? ((e.clientY - rect.top) / rect.height) * H : 0,
  }
}

function twoFingerDist(): number {
  const pts = [...pointers.values()]
  if (pts.length < 2) return 0
  return Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y)
}

function updateCrossAt(px: number, toggle = false) {
  const data =
    mode.value === 'minute'
      ? (minuteData.value?.bars ?? []).slice(-visibleCount.value)
      : visibleBars()
  if (!data.length) return
  if (px < PAD_L || px > W - PAD_R) {
    crossIndex.value = null
    draw()
    return
  }
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
  const clamped = Math.max(0, Math.min(n - 1, idx))
  if (toggle && crossIndex.value === clamped) {
    crossIndex.value = null
  } else {
    crossIndex.value = clamped
  }
  draw()
}

function onPointerDown(e: PointerEvent) {
  e.preventDefault()
  try {
    canvas.value?.setPointerCapture?.(e.pointerId)
  } catch {
    // 忽略指针捕获失败
  }
  pointers.set(e.pointerId, canvasPoint(e))
  if (drawTool.value !== 'none') {
    const pt = canvasPoint(e)
    if (drawTool.value === 'erase') {
      deleteLineAt(pt.x, pt.y)
      return
    }
    drawStart.value = { x: pt.x, y: pt.y }
    return
  }
  if (pointers.size === 1) {
    const px = canvasPoint(e).x
    dragState = 'crosshair'
    dragStartX = px
    dragStartOffset = scrollOffset.value
    updateCrossAt(px, true)
  } else if (pointers.size === 2) {
    dragState = 'none'
    pinchStartDist = twoFingerDist()
    pinchStartCount = visibleCount.value
    crossIndex.value = null
    draw()
  }
}

function onPointerMove(e: PointerEvent) {
  if (!pointers.has(e.pointerId)) return
  pointers.set(e.pointerId, canvasPoint(e))
  if (drawTool.value !== 'none' && drawStart.value) {
    draw()
    return
  }
  if (pointers.size === 1) {
    const px = canvasPoint(e).x
    const dx = px - dragStartX
    if (dragState === 'crosshair' && Math.abs(dx) > 8) {
      dragState = 'pan'
      crossIndex.value = null
    }
    if (dragState === 'pan') {
      const data = currentPlotData()
      const n = data.length
      if (!n) return
      const step = (W - PAD_L - PAD_R) / n
      const barDelta = Math.round(-dx / step)
      const next = dragStartOffset + barDelta
      const clamped = Math.max(0, Math.min(maxScrollOffset.value, next))
      if (clamped !== scrollOffset.value) {
        scrollOffset.value = clamped
        draw()
      }
    } else {
      updateCrossAt(px)
    }
  } else if (pointers.size === 2) {
    const d = twoFingerDist()
    if (pinchStartDist > 0) {
      const ratio = d / pinchStartDist
      const next = Math.round(pinchStartCount / ratio)
      visibleCount.value = Math.max(MIN_VISIBLE, Math.min(MAX_VISIBLE, next))
      draw()
    }
  }
}

function onPointerEnd(e: PointerEvent) {
  pointers.delete(e.pointerId)
  dragState = 'none'
  scrollOffset.value = Math.max(0, Math.min(maxScrollOffset.value, scrollOffset.value))
  if (drawTool.value !== 'none' && drawStart.value) {
    const end = canvasPoint(e)
    const start = drawStart.value
    drawStart.value = null
    if (Math.hypot(end.x - start.x, end.y - start.y) < 4) return
    const line: DrawnLine = {
      type: drawTool.value as 'trendline' | 'horizontal',
      id: drawIdSeq++,
      x1: drawTool.value === 'horizontal' ? PAD_L : start.x,
      y1: drawTool.value === 'horizontal' ? start.y : start.y,
      x2: drawTool.value === 'horizontal' ? W - PAD_R : end.x,
      y2: drawTool.value === 'horizontal' ? start.y : end.y,
      color: chartColors().line,
      dash: false,
    }
    drawnLines.value.push(line)
    saveDrawnLines()
    draw()
    return
  }
  if (pointers.size < 2) pinchStartDist = 0
}

</script>

<style scoped>
.back-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--card);
  font-size: 20px;
  line-height: 1;
  margin-right: 8px;
}

.back-btn:active {
  opacity: 0.6;
}

.mode-btn {
  flex: 1;
  height: 44px;
  border-radius: 22px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text);
  font-size: 13px;
}

.mode-btn:active {
  opacity: 0.7;
}

.mode-btn.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.draw-btn {
  height: 32px;
  padding: 0 12px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text);
  font-size: 12px;
}

.draw-btn:active {
  opacity: 0.7;
}

.draw-btn.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.legend {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-2, #909399);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ma-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
  cursor: pointer;
}

.ma-toggle input {
  margin: 0;
}

.chart-canvas {
  touch-action: none;
}

.net-offline-hint {
  text-align: center;
  font-size: 12px;
  color: var(--warning);
  margin-bottom: 6px;
}

.search-btn {
  height: 44px;
  padding: 0 16px;
  border-radius: 22px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text);
  font-size: 13px;
}

.search-btn:active {
  opacity: 0.7;
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
