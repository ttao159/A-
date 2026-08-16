<template>
  <svg :viewBox="`0 0 ${width} ${height}`" class="equity-chart">
    <polyline :points="points" fill="none" stroke="var(--primary)" stroke-width="2" />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EquityPoint } from '../api/types'

const props = defineProps<{ data: EquityPoint[] }>()

const width = 300
const height = 120

const points = computed(() => {
  if (!props.data || props.data.length < 2) return ''
  const values = props.data.map((p) => p.equity)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  return props.data
    .map((p, i) => {
      const x = (i / (props.data.length - 1)) * width
      const y = height - ((p.equity - min) / range) * height
      return `${x},${y}`
    })
    .join(' ')
})
</script>

<style scoped>
.equity-chart {
  width: 100%;
  height: 120px;
  display: block;
}
</style>
