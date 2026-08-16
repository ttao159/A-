<template>
  <canvas ref="canvas" :width="W" :height="H" style="width: 100%; height: auto"></canvas>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import type { EquityPoint } from '../api/types'
import { fmtMoney } from '../utils/format'

interface TradeMark {
  date: string
  direction: string
}

const props = defineProps<{ data: EquityPoint[]; baseline?: number; trades?: TradeMark[] }>()

const canvas = ref<HTMLCanvasElement | null>(null)
const W = 360
const H = 220

const UP = '#e0393e'
const DOWN = '#0aa869'
const LINE = '#1a73e8'

onMounted(draw)
watch(() => props.data, draw)
watch(() => props.trades, draw)

function draw() {
  const el = canvas.value
  if (!el) return
  const ctx = el.getContext('2d')
  if (!ctx) return
  ctx.clearRect(0, 0, W, H)

  const data = props.data
  if (!data || data.length < 2) return

  const mainTop = 10
  const mainBottom = 138
  const ddTop = 158
  const ddBottom = 208
  const padL = 8
  const padR = 56

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
  const mainH = mainBottom - mainTop
  const x = (i: number) => padL + (i / (data.length - 1)) * plotW
  const y = (v: number) => mainTop + (1 - (v - min) / range) * mainH

  const dateIndex = new Map<string, number>()
  data.forEach((p, i) => dateIndex.set(p.date, i))

  // 净值曲线
  ctx.strokeStyle = LINE
  ctx.lineWidth = 1.6
  ctx.beginPath()
  data.forEach((p, i) => {
    if (i === 0) ctx.moveTo(x(i), y(p.equity))
    else ctx.lineTo(x(i), y(p.equity))
  })
  ctx.stroke()

  // 本金基准线
  if (base > 0) {
    const by = y(base)
    ctx.strokeStyle = '#c0c4cc'
    ctx.setLineDash([4, 4])
    ctx.beginPath()
    ctx.moveTo(padL, by)
    ctx.lineTo(W - padR, by)
    ctx.stroke()
    ctx.setLineDash([])
  }

  // 买卖点标记
  if (props.trades) {
    for (const t of props.trades) {
      const idx = dateIndex.get(t.date)
      if (idx === undefined) continue
      const px = x(idx)
      const py = y(data[idx].equity)
      if (t.direction === 'buy') {
        ctx.fillStyle = UP
        ctx.beginPath()
        ctx.moveTo(px, py - 8)
        ctx.lineTo(px - 4, py - 2)
        ctx.lineTo(px + 4, py - 2)
        ctx.closePath()
        ctx.fill()
      } else if (t.direction === 'sell') {
        ctx.fillStyle = DOWN
        ctx.beginPath()
        ctx.moveTo(px, py + 8)
        ctx.lineTo(px - 4, py + 2)
        ctx.lineTo(px + 4, py + 2)
        ctx.closePath()
        ctx.fill()
      }
    }
  }

  // 涨跌幅标注
  const first = data[0]
  const last = data[data.length - 1]
  const chg = first.equity ? ((last.equity - first.equity) / first.equity) * 100 : 0
  ctx.font = '10px sans-serif'
  ctx.fillStyle = chg >= 0 ? UP : DOWN
  ctx.textAlign = 'right'
  ctx.fillText(`${chg >= 0 ? '+' : ''}${chg.toFixed(2)}%`, W - padR, mainTop + 10)
  ctx.fillStyle = '#909399'
  ctx.fillText(fmtMoney(max), padL, mainTop + 8)
  ctx.fillText(fmtMoney(min), padL, mainBottom - 2)
  ctx.textAlign = 'left'
  ctx.fillText(first.date.slice(5), padL, mainBottom + 10)
  ctx.textAlign = 'right'
  ctx.fillText(last.date.slice(5), W - padR, mainBottom + 10)

  // 回撤子图
  let peak = values[0]
  const drawdowns = values.map((v) => {
    peak = Math.max(peak, v)
    return ((v - peak) / peak) * 100
  })
  const ddMin = Math.min(...drawdowns, 0)
  const ddMax = 0
  const ddRange = ddMax - ddMin || 1
  const ddH = ddBottom - ddTop
  const ydd = (v: number) => ddTop + ((ddMax - v) / ddRange) * ddH

  ctx.strokeStyle = '#c0c4cc'
  ctx.beginPath()
  ctx.moveTo(padL, ydd(0))
  ctx.lineTo(W - padR, ydd(0))
  ctx.stroke()

  ctx.fillStyle = 'rgba(224, 57, 62, 0.15)'
  ctx.strokeStyle = DOWN
  ctx.lineWidth = 1.2
  ctx.beginPath()
  data.forEach((_p, i) => {
    const px = x(i)
    const py = ydd(drawdowns[i])
    if (i === 0) ctx.moveTo(px, py)
    else ctx.lineTo(px, py)
  })
  ctx.lineTo(x(data.length - 1), ydd(0))
  ctx.lineTo(x(0), ydd(0))
  ctx.closePath()
  ctx.fill()
  ctx.stroke()

  ctx.fillStyle = '#909399'
  ctx.font = '9px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText(`最大回撤 ${ddMin.toFixed(2)}%`, padL, ddBottom + 8)
}
</script>
