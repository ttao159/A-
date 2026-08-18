<template>
  <div class="card">
    <div class="cal-head">
      <button class="nav" @click="shiftMonth(-1)">‹</button>
      <div class="cal-title">{{ year }} 年 {{ month }} 月</div>
      <button class="nav" :disabled="!canNext" @click="shiftMonth(1)">›</button>
    </div>

    <div v-if="error" class="error-box">
      {{ error }}<br /><button class="retry-btn" @click="load">重试</button>
    </div>
    <template v-else>
      <div class="cal-summary">
        <span>月盈亏</span>
        <span :class="monthPnl >= 0 ? 'up' : 'down'">{{ fmtMoney(monthPnl) }}</span>
      </div>

      <div class="cal-grid">
        <div v-for="w in ['一', '二', '三', '四', '五', '六', '日']" :key="w" class="cal-weekday">{{ w }}</div>
        <div v-for="cell in cells" :key="cell.key" class="cal-cell" :class="{ blank: !cell.day, has: cell.day && cell.pnl !== null, pos: cell.pnl !== null && cell.pnl >= 0, neg: cell.pnl !== null && cell.pnl < 0 }">
          <template v-if="cell.day">
            <div class="cal-day" :class="{ today: cell.isToday }">{{ cell.day }}</div>
            <div v-if="cell.pnl !== null" class="cal-pnl">
              {{ cell.pnl > 0 ? '+' : '' }}{{ cell.pnl.toFixed(0) }}
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { accountApi } from '../api'
import type { DailyPnlPoint } from '../api'
import { fmtMoney } from '../utils/format'

const points = ref<DailyPnlPoint[]>([])
const error = ref('')

const today = new Date()
const year = ref(today.getFullYear())
const month = ref(today.getMonth() + 1)

const byDate = computed(() => {
  const map = new Map<string, number>()
  for (const p of points.value) map.set(p.date, p.pnl)
  return map
})

const cells = computed(() => {
  const first = new Date(year.value, month.value - 1, 1)
  const daysInMonth = new Date(year.value, month.value, 0).getDate()
  // 周一为第 0 列
  const lead = (first.getDay() + 6) % 7
  const result: { key: string; day: number | null; pnl: number | null; isToday: boolean }[] = []
  for (let i = 0; i < lead; i++) {
    result.push({ key: `lead-${i}`, day: null, pnl: null, isToday: false })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year.value}-${String(month.value).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const pnl = byDate.value.get(dateStr)
    const isToday = dateStr === today.toISOString().slice(0, 10)
    result.push({ key: dateStr, day: d, pnl: pnl ?? null, isToday })
  }
  return result
})

const monthPnl = computed(() => {
  const prefix = `${year.value}-${String(month.value).padStart(2, '0')}`
  return points.value
    .filter((p) => p.date.startsWith(prefix))
    .reduce((sum, p) => sum + p.pnl, 0)
})

const canNext = computed(() => {
  const cur = today.getFullYear() * 12 + (today.getMonth() + 1)
  const sel = year.value * 12 + month.value
  return sel < cur
})

function shiftMonth(delta: number) {
  if (delta > 0 && !canNext.value) return
  const d = new Date(year.value, month.value - 1 + delta, 1)
  year.value = d.getFullYear()
  month.value = d.getMonth() + 1
}

async function load() {
  error.value = ''
  try {
    points.value = await accountApi.dailyPnl()
  } catch (e) {
    error.value = '收益日历加载失败'
  }
}

onMounted(load)
</script>

<style scoped>
.cal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.cal-title {
  font-size: 15px;
  font-weight: 700;
}

.nav {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text);
  font-size: 18px;
  line-height: 1;
}

.nav:active:not(:disabled) {
  opacity: 0.6;
}

.nav:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.cal-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--text-2);
  margin-bottom: 8px;
}

.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.cal-weekday {
  text-align: center;
  font-size: 11px;
  color: var(--text-2);
  padding: 4px 0;
}

.cal-cell {
  min-height: 44px;
  border-radius: 8px;
  background: var(--bg);
  padding: 4px 2px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.cal-cell.blank {
  background: transparent;
}

.cal-cell.pos {
  background: var(--up-bg);
}

.cal-cell.neg {
  background: var(--down-bg);
}

.cal-day {
  font-size: 13px;
  color: var(--text);
}

.cal-cell.has .cal-day {
  opacity: 0.75;
}

.cal-day.today {
  color: #fff;
  background: var(--primary);
  border-radius: 50%;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 1;
}

.cal-pnl {
  font-size: 13px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  margin-top: 1px;
}

.cal-cell.pos .cal-pnl {
  color: var(--up);
}

.cal-cell.neg .cal-pnl {
  color: var(--down);
}
</style>
