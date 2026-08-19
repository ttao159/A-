<template>
  <div class="card">
    <div class="ec-head">
      <div class="ec-range">
        <button
          v-for="r in RANGES"
          :key="r.key"
          class="ec-range-btn"
          :class="{ active: timeRange === r.key }"
          @click="timeRange = r.key"
        >
          {{ r.label }}
        </button>
      </div>
    </div>
    <div v-if="loading" class="ec-loading">
      <span class="ec-spinner"></span>
      <span>数据加载中...</span>
    </div>
    <canvas
      v-else-if="filtered.length >= 2"
      ref="canvas"
      :width="W"
      :height="H"
      style="width: 100%; height: auto; touch-action: none"
      @mousemove="onPointerMove"
      @mouseleave="onPointerLeave"
      @touchstart.passive="onTouchStart"
      @touchmove.passive="onTouchMove"
      @touchend="onPointerLeave"
    ></canvas>
    <div v-else class="empty">暂无历史数据，打开账户页后按日记录总资产</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { AccountEquityPoint } from '../api'
import { fmtMoney, fmtMoneyCompact } from '../utils/format'
import { chartColors } from '../utils/theme'
import { useThemeRedraw } from '../composables/useThemeRedraw'
import { hiDPIContext } from '../utils/canvas'

const props = defineProps<{ points: AccountEquityPoint[]; baseline?: number; loading?: boolean }>()

const RANGES = [
  { key: '7d', label: '近7天', days: 7 },
  { key: '30d', label: '近30天', days: 30 },
  { key: '3m', label: '近3月', days: 90 },
] as const

type RangeKey = (typeof RANGES)[number]['key']

const timeRange = ref<RangeKey>('30d')
const hover = ref<number | null>(null)

const canvas = ref<HTMLCanvasElement | null>(null)
const W = 360
const H = 190

const filtered = computed(() => {
  const days = RANGES.find((r) => r.key === timeRange.value)?.days ?? 30
  const cutoff = new Date()
  cutoff.setDate(cutoff.getDate() - days)
  const list = props.points.filter((p) => new Date(p.date) >= cutoff)
  return list.length >= 2 ? list : props.points
})

onMounted(draw)
watch(() => props.points, () => { hover.value = null; draw() })
watch(filtered, draw)
useThemeRedraw(() => draw())

function clampIndex(i: number, len: number) {
  return Math.max(0, Math.min(len - 1, i))
}

function pointerXToIndex(cx: number, len: number) {
  const padL = 46
  const padR = 62
  const plotW = W - padL - padR
  const i = Math.round(((cx - padL) / plotW) * (len - 1))
  return clampIndex(i, len)
}

function onPointerMove(e: MouseEvent) {
  const el = canvas.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  const px = (e.clientX - rect.left) * (W / rect.width)
  hover.value = pointerXToIndex(px, filtered.value.length)
  draw()
}

function onTouchStart(e: TouchEvent) {
  const el = canvas.value
  if (!el || !e.touches.length) return
  const rect = el.getBoundingClientRect()
  const px = (e.touches[0].clientX - rect.left) * (W / rect.width)
  hover.value = pointerXToIndex(px, filtered.value.length)
  draw()
}

function onTouchMove(e: TouchEvent) {
  const el = canvas.value
  if (!el || !e.touches.length) return
  const rect = el.getBoundingClientRect()
  const px = (e.touches[0].clientX - rect.left) * (W / rect.width)
  hover.value = pointerXToIndex(px, filtered.value.length)
  draw()
}

function onPointerLeave() {
  hover.value = null
  draw()
}

function draw() {
  const c = chartColors()
  const el = canvas.value
  if (!el) return
  const ctx = hiDPIContext(el, W, H)
  if (!ctx) return
  ctx.clearRect(0, 0, W, H)

  const data = filtered.value
  if (data.length < 2) return

  const padL = 46
  const padR = 62
  const padT = 16
  const padB = 24
  const values = data.map((p) => p.equity)
  let min = Math.min(...values)
  let max = Math.max(...values)
  const base = props.baseline ?? 0
  if (base > 0) {
    min = Math.min(min, base)
    max = Math.max(max, base)
  }
  if (max === min) max = min + 1
  const range = max - min
  const plotW = W - padL - padR
  const plotH = H - padT - padB
  const x = (i: number) => padL + (i / (data.length - 1)) * plotW
  const y = (v: number) => padT + (1 - (v - min) / range) * plotH

  ctx.font = '9px sans-serif'
  ctx.fillStyle = c.text2
  ctx.textAlign = 'right'
  const TICKS = 4
  for (let i = 0; i <= TICKS; i++) {
    const v = min + (range * i) / TICKS
    const ty = y(v)
    ctx.fillText(fmtMoneyCompact(v), padL - 5, ty + 3)
    ctx.strokeStyle = c.grid
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(padL, ty)
    ctx.lineTo(W - padR, ty)
    ctx.stroke()
  }

  if (base > 0) {
    const by = y(base)
    ctx.strokeStyle = c.grid
    ctx.setLineDash([4, 4])
    ctx.beginPath()
    ctx.moveTo(padL, by)
    ctx.lineTo(W - padR, by)
    ctx.stroke()
    ctx.setLineDash([])
  }

  ctx.strokeStyle = c.line
  ctx.lineWidth = 1.6
  ctx.beginPath()
  data.forEach((p, i) => {
    if (i === 0) ctx.moveTo(x(i), y(p.equity))
    else ctx.lineTo(x(i), y(p.equity))
  })
  ctx.stroke()

  const last = data[data.length - 1]
  const first = data[0]
  const chg = first.equity ? ((last.equity - first.equity) / first.equity) * 100 : 0
  ctx.fillStyle = chg >= 0 ? c.up : c.down
  ctx.textAlign = 'right'
  ctx.fillText(`${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%`, W - padR, padT)
  ctx.fillStyle = c.text2
  ctx.textAlign = 'center'
  ctx.fillText(first.date.slice(5), padL, H - 4)
  ctx.fillText(last.date.slice(5), W - padR, H - 4)

  if (hover.value !== null) {
    const i = clampIndex(hover.value, data.length)
    const p = data[i]
    const hx = x(i)
    const hy = y(p.equity)
    ctx.strokeStyle = c.text2
    ctx.lineWidth = 1
    ctx.setLineDash([3, 3])
    ctx.beginPath()
    ctx.moveTo(hx, padT)
    ctx.lineTo(hx, H - padB)
    ctx.stroke()
    ctx.setLineDash([])

    ctx.beginPath()
    ctx.arc(hx, hy, 3, 0, Math.PI * 2)
    ctx.fillStyle = c.line
    ctx.fill()

    const tw = 92
    const th = 30
    let tx = hx + 10
    if (tx + tw > W - padR) tx = hx - tw - 10
    if (tx < padL) tx = padL
    const ty = Math.max(padT, hy - th - 6)
    ctx.fillStyle = c.bg
    ctx.strokeStyle = c.border
    ctx.beginPath()
    ctx.roundRect(tx, ty, tw, th, 4)
    ctx.fill()
    ctx.stroke()
    ctx.fillStyle = c.text2
    ctx.textAlign = 'left'
    ctx.font = '9px sans-serif'
    ctx.fillText(p.date, tx + 6, ty + 11)
    ctx.fillStyle = c.text
    ctx.font = 'bold 10px sans-serif'
    ctx.fillText(fmtMoney(p.equity), tx + 6, ty + 23)
  }
}
</script>

<style scoped>
.ec-head {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.ec-range {
  display: flex;
  gap: 6px;
}

.ec-range-btn {
  height: 28px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--card);
  color: var(--text-2);
  font-size: 12px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
}

.ec-range-btn.active {
  color: var(--primary);
  border-color: var(--primary);
  background: var(--focus-ring);
  font-weight: 600;
}

.ec-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 150px;
  color: var(--text-2);
  font-size: 13px;
}

.ec-spinner {
  width: 26px;
  height: 26px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: ec-spin 0.8s linear infinite;
}

@keyframes ec-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
