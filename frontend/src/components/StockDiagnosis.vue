<template>
  <div class="card stock-diag-card">
    <div class="row">
      <span class="card-title">AI 个股诊断</span>
      <span v-if="result" class="diag-tag" :class="result.available ? 'llm' : 'heuristic'">
        {{ result.available ? 'LLM' : '启发式' }}
      </span>
    </div>

    <button v-if="!result && !loading && !error" class="btn block" @click="run">
      AI 个股诊断
    </button>

    <div v-if="loading" class="diag-loading">
      <span class="diag-spinner"></span>
      <span>诊断中...</span>
    </div>

    <div v-else-if="error" class="error-box">
      {{ error }}
      <button class="retry-btn" @click="run">重试</button>
    </div>

    <template v-else-if="result">
      <div class="verdict-row">
        <span class="action-badge" :class="actionClass">{{ actionLabel }}</span>
        <span class="verdict">{{ result.verdict }}</span>
      </div>
      <div class="conf-row muted">
        信心 {{ result.confidence }}%
      </div>
      <div class="levels">
        <div class="level-cell"><span>目标</span><b>{{ fmtPrice(result.target_price) }}</b></div>
        <div class="level-cell"><span>支撑</span><b>{{ fmtPrice(result.support) }}</b></div>
        <div class="level-cell"><span>阻力</span><b>{{ fmtPrice(result.resistance) }}</b></div>
        <div class="level-cell"><span>止损</span><b class="down">{{ fmtPrice(result.stop_loss) }}</b></div>
      </div>
      <div class="case-row bull">
        <span class="case-label">看多</span>{{ result.bull_case }}
      </div>
      <div class="case-row bear">
        <span class="case-label">看空</span>{{ result.bear_case }}
      </div>
      <button class="btn ghost block" style="margin-top: 10px" @click="run" :disabled="loading">
        {{ loading ? '诊断中...' : '重新诊断' }}
      </button>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { stockApi, type StockDiagnosis } from '../api'
import { fmtPrice } from '../utils/format'

const props = defineProps<{ code: string }>()

const loading = ref(false)
const error = ref('')
const result = ref<StockDiagnosis | null>(null)

const actionClass = computed(() => {
  const a = result.value?.action ?? ''
  if (a === '看多') return 'up'
  if (a === '看空') return 'down'
  return 'mid'
})

const actionLabel = computed(() => {
  const a = result.value?.action ?? ''
  if (a === '看多') return '看多'
  if (a === '看空') return '看空'
  return '中性'
})

async function run() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    result.value = await stockApi.diagnose(props.code)
  } catch (e) {
    error.value = (e as Error).message || '诊断失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

watch(
  () => props.code,
  () => {
    result.value = null
    error.value = ''
  },
)
</script>

<style scoped>
.diag-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
}

.diag-tag.llm {
  color: var(--primary);
  background: var(--focus-ring);
}

.diag-tag.heuristic {
  color: var(--text-2);
  background: var(--bg);
}

.diag-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 18px 0;
  color: var(--text-2);
  font-size: 14px;
}

.diag-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: diag-spin 0.8s linear infinite;
}

@keyframes diag-spin {
  to {
    transform: rotate(360deg);
  }
}

.verdict-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.action-badge {
  flex: 0 0 auto;
  font-size: 13px;
  font-weight: 700;
  padding: 3px 12px;
  border-radius: 8px;
  color: #fff;
}

.action-badge.up {
  background: var(--up);
}

.action-badge.down {
  background: var(--down);
}

.action-badge.mid {
  background: var(--text-2);
}

.verdict {
  flex: 1;
  font-size: 13px;
  line-height: 1.5;
}

.conf-row {
  font-size: 12px;
  margin-bottom: 10px;
}

.levels {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}

.level-cell {
  flex: 1;
  background: var(--bg);
  border-radius: 8px;
  padding: 6px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  text-align: center;
}

.level-cell span {
  font-size: 11px;
  color: var(--text-2);
}

.level-cell b {
  font-size: 14px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.case-row {
  display: flex;
  gap: 8px;
  font-size: 13px;
  line-height: 1.5;
  padding: 8px 0;
  border-top: 1px dashed var(--border);
}

.case-label {
  flex: 0 0 auto;
  font-size: 12px;
  font-weight: 600;
}

.case-row.bull .case-label {
  color: var(--up);
}

.case-row.bear .case-label {
  color: var(--down);
}
</style>
