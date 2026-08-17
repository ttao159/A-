<template>
  <div>
    <div class="card">
      <div class="card-title">条件选股</div>
      <div class="field-row">
        <div class="field">
          <span class="field-label">价格</span>
          <div class="range">
            <input v-model.number="f.price_min" type="number" placeholder="最低" />
            <span class="dash">~</span>
            <input v-model.number="f.price_max" type="number" placeholder="最高" />
          </div>
        </div>
        <div class="field">
          <span class="field-label">涨跌幅%</span>
          <div class="range">
            <input v-model.number="f.change_pct_min" type="number" placeholder="最低" />
            <span class="dash">~</span>
            <input v-model.number="f.change_pct_max" type="number" placeholder="最高" />
          </div>
        </div>
      </div>
      <div class="field-row">
        <div class="field">
          <span class="field-label">换手率%</span>
          <div class="range">
            <input v-model.number="f.turnover_min" type="number" placeholder="最低" />
            <span class="dash">~</span>
            <input v-model.number="f.turnover_max" type="number" placeholder="最高" />
          </div>
        </div>
        <div class="field">
          <span class="field-label">总市值(亿)</span>
          <div class="range">
            <input v-model.number="f.market_cap_min" type="number" placeholder="最低" />
            <span class="dash">~</span>
            <input v-model.number="f.market_cap_max" type="number" placeholder="最高" />
          </div>
        </div>
      </div>
      <div class="field-row">
        <div class="field">
          <span class="field-label">成交额(亿)</span>
          <div class="range">
            <input v-model.number="f.amount_min" type="number" placeholder="最低" />
            <span class="dash">~</span>
            <input v-model.number="f.amount_max" type="number" placeholder="最高" />
          </div>
        </div>
        <div class="field">
          <span class="field-label">排序</span>
          <div class="range">
            <select v-model="sortBy" class="sort-select">
              <option value="change_pct">涨跌幅</option>
              <option value="turnover">换手率</option>
              <option value="amount">成交额</option>
              <option value="market_cap">市值</option>
              <option value="price">价格</option>
            </select>
            <select v-model="sortDir" class="sort-select">
              <option value="desc">降序</option>
              <option value="asc">升序</option>
            </select>
          </div>
        </div>
      </div>
      <button class="btn block" @click="run" :disabled="loading">
        {{ loading ? '筛选中...' : '开始筛选' }}
      </button>
    </div>

    <div v-if="error" class="card">
      <div class="error-box">
        {{ error }}
        <button class="retry-btn" @click="run">重试</button>
      </div>
    </div>

    <div v-if="result" class="card">
      <div class="result-head">
        <span>匹配 {{ result.total }} 只</span>
        <span class="muted">更新 {{ result.updated_at }}</span>
      </div>
      <div class="screener-table">
        <div class="srow head">
          <span class="c-name">名称</span>
          <span class="c-num">现价</span>
          <span class="c-num">涨跌幅</span>
          <span class="c-num">换手</span>
          <span class="c-num">市值</span>
        </div>
        <div
          v-for="s in result.items"
          :key="s.code"
          class="srow"
          @click="openStock(s)"
        >
          <span class="c-name">
            <span class="stock-name">{{ s.name }}</span>
            <span class="muted stock-code">{{ s.code }}</span>
          </span>
          <span class="c-num">{{ s.price.toFixed(2) }}</span>
          <span class="c-num" :class="s.change_pct >= 0 ? 'up' : 'down'">
            {{ s.change_pct >= 0 ? '+' : '' }}{{ s.change_pct.toFixed(2) }}%
          </span>
          <span class="c-num">{{ s.turnover.toFixed(1) }}%</span>
          <span class="c-num">{{ s.market_cap.toFixed(0) }}亿</span>
        </div>
        <div v-if="!result.items.length" class="empty">无匹配结果，请放宽条件</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { screenerApi, type ScreenerRequest, type ScreenerResult } from '../api'

const router = useRouter()

const f = reactive<ScreenerRequest>({
  price_min: undefined,
  price_max: undefined,
  change_pct_min: undefined,
  change_pct_max: undefined,
  turnover_min: undefined,
  turnover_max: undefined,
  market_cap_min: undefined,
  market_cap_max: undefined,
  amount_min: undefined,
  amount_max: undefined,
})

const sortBy = ref('change_pct')
const sortDir = ref('desc')
const loading = ref(false)
const error = ref('')
const result = ref<ScreenerResult | null>(null)

function clean(req: ScreenerRequest): ScreenerRequest {
  const out: ScreenerRequest = { sort_by: sortBy.value, sort_dir: sortDir.value, limit: 50 }
  for (const [k, v] of Object.entries(req)) {
    if (v !== undefined && v !== null && v !== '') {
      ;(out as Record<string, unknown>)[k] = v
    }
  }
  return out
}

async function run() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    result.value = await screenerApi.run(clean({ ...f }))
  } catch (e) {
    error.value = '筛选失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function openStock(s: { code: string; name: string }) {
  router.push({ path: `/stock/${s.code}`, query: { name: s.name } })
}
</script>

<style scoped>
.field-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.field {
  flex: 1;
  min-width: 0;
}

.field-label {
  display: block;
  font-size: 12px;
  color: var(--text-2);
  margin-bottom: 4px;
}

.range {
  display: flex;
  align-items: center;
  gap: 4px;
}

.range input {
  flex: 1;
  min-width: 0;
  height: 38px;
  padding: 0 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  background: var(--card);
  color: var(--text);
  box-sizing: border-box;
}

.range input::placeholder {
  color: var(--text-2);
}

.dash {
  color: var(--text-2);
  font-size: 13px;
}

.sort-select {
  flex: 1;
  min-width: 0;
  height: 38px;
  padding: 0 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 13px;
  background: var(--card);
  color: var(--text);
}

.result-head {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 8px;
}

.screener-table {
  font-size: 13px;
}

.srow {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--border);
}

.srow:last-child {
  border-bottom: none;
}

.srow.head {
  font-size: 12px;
  color: var(--text-2);
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}

.c-name {
  flex: 2;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.srow:not(.head) .c-name {
  cursor: pointer;
}

.stock-name {
  font-weight: 600;
}

.stock-code {
  font-size: 11px;
}

.c-num {
  flex: 1;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.up {
  color: var(--up);
}

.down {
  color: var(--down);
}
</style>
