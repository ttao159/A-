<template>
  <div>
    <canvas ref="canvas" :width="W" :height="H" style="width: 100%; height: auto"></canvas>
    <div class="legend">红三角=买入 · 绿三角=卖出</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import type { Bar } from '../api'
import { chartColors } from '../utils/theme'
import { useThemeRedraw } from '../composables/useThemeRedraw'
import { hiDPIContext } from '../utils/canvas'

const props = defineProps<{
  bars: Bar[]
  marks: { date: string; direction: string; price: number }[]
}>()

const canvas = ref<HTMLCanvasElement | null>(null)
const W = 360
const H = 300

function draw() {
  const c = chartColors()
  const el = canvas.value
  if (!el) return
  const ctx = hiDPIContext(el, W, H)
  if (!ctx) return
  ctx.clearRect(0, 0, W, H)
  const data = props.bars
  if (!data.length) return

  const padL = 8
  const padR = 44
  const padT = 14
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
    ctx.fillRect(x - bodyW / 2, volY(b.volume), bodyW, H - padB - volY(b.volume))
  }

  const dateIndex = new Map<string, number>()
  data.forEach((b, i) => dateIndex.set(String(b.date).slice(0, 10), i))

  for (const m of props.marks) {
    const i = dateIndex.get(String(m.date).slice(0, 10))
    if (i === undefined) continue
    const x = padL + step * i + step / 2
    if (m.direction === 'buy') {
      const ty = y(data[i].low) + 10
      ctx.fillStyle = c.up
      ctx.beginPath()
      ctx.moveTo(x, ty)
      ctx.lineTo(x - 4, ty + 8)
      ctx.lineTo(x + 4, ty + 8)
      ctx.closePath()
      ctx.fill()
    } else {
      const ty = y(data[i].high) - 10
      ctx.fillStyle = c.down
      ctx.beginPath()
      ctx.moveTo(x, ty)
      ctx.lineTo(x - 4, ty - 8)
      ctx.lineTo(x + 4, ty - 8)
      ctx.closePath()
      ctx.fill()
    }
  }

  ctx.fillStyle = c.text2
  ctx.font = '10px sans-serif'
  ctx.fillText(String(max.toFixed(2)), padL, padT + 8)
  ctx.fillText(String(min.toFixed(2)), padL, padT + priceH)
}

watch(() => [props.bars, props.marks], draw, { deep: true })
onMounted(draw)
useThemeRedraw(() => draw())
</script>

<style scoped>
.legend {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-2, #909399);
}
</style>
