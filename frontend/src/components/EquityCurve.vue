<template>
  <div class="card">
    <div class="card-title">资金曲线</div>
    <canvas
      v-if="points.length >= 2"
      ref="canvas"
      :width="W"
      :height="H"
      style="width: 100%; height: auto"
    ></canvas>
    <div v-else class="empty">暂无历史数据，打开账户页后按日记录总资产</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import type { AccountEquityPoint } from '../api'
import { fmtMoney } from '../utils/format'
import { chartColors } from '../utils/theme'
import { useThemeRedraw } from '../composables/useThemeRedraw'
import { hiDPIContext } from '../utils/canvas'

const props = defineProps<{ points: AccountEquityPoint[]; baseline?: number }>()

const canvas = ref<HTMLCanvasElement | null>(null)
const W = 360
const H = 180

onMounted(draw)
watch(() => props.points, draw)
useThemeRedraw(() => draw())

function draw() {
  const c = chartColors()
  const el = canvas.value
  if (!el) return
  const ctx = hiDPIContext(el, W, H)
  if (!ctx) return
  ctx.clearRect(0, 0, W, H)

  const data = props.points
  if (data.length < 2) return

  const padL = 8
  const padR = 60
  const padT = 12
  const padB = 22
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

  ctx.font = '10px sans-serif'
  ctx.fillStyle = c.text2
  ctx.textAlign = 'left'
  ctx.fillText(fmtMoney(max), padL, padT - 2)
  ctx.fillText(fmtMoney(min), padL, H - padB + 12)

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
  ctx.fillText(`${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%`, W - padR, padT + 10)
  ctx.fillStyle = c.text2
  ctx.fillText(last.date.slice(5), W - padR, H - padB + 12)
}
</script>