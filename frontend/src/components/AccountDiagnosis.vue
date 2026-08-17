<template>
  <div class="card diag-card">
    <div class="row">
      <span class="card-title">AI 账户诊断</span>
      <span v-if="result" class="diag-tag" :class="result.available ? 'llm' : 'heuristic'">
        {{ result.available ? 'LLM' : '启发式' }}
      </span>
    </div>

    <button v-if="!result && !loading && !error" class="btn block" @click="run">
      AI 账户诊断
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
      <div class="diag-head">
        <div class="diag-score" :class="scoreClass">{{ result.score }}</div>
        <div class="diag-summary">{{ result.summary }}</div>
      </div>

      <div v-if="result.highlights?.length" class="diag-sec">
        <div class="diag-label good">亮点</div>
        <div v-for="(h, i) in result.highlights" :key="'h' + i" class="diag-line">{{ h }}</div>
      </div>

      <div v-if="result.risks?.length" class="diag-sec">
        <div class="diag-label warn">风险</div>
        <div v-for="(r, i) in result.risks" :key="'r' + i" class="diag-line">{{ r }}</div>
      </div>

      <div v-if="result.suggestions?.length" class="diag-sec">
        <div class="diag-label">建议</div>
        <div v-for="(s, i) in result.suggestions" :key="'s' + i" class="diag-line">{{ s }}</div>
      </div>

      <button class="btn ghost block" style="margin-top: 10px" @click="run" :disabled="loading">
        {{ loading ? '诊断中...' : '重新诊断' }}
      </button>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { accountApi, type AccountDiagnosis } from '../api'

const loading = ref(false)
const error = ref('')
const result = ref<AccountDiagnosis | null>(null)

const scoreClass = computed(() => {
  const s = result.value?.score ?? 0
  if (s >= 75) return 'good'
  if (s >= 50) return 'mid'
  return 'bad'
})

async function run() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    result.value = await accountApi.diagnose()
  } catch (e) {
    error.value = '诊断失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
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

.diag-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 12px;
}

.diag-score {
  flex: 0 0 auto;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.diag-score.good {
  color: var(--down);
  background: var(--down-bg);
}

.diag-score.mid {
  color: var(--warning);
  background: var(--warning-bg);
}

.diag-score.bad {
  color: var(--danger);
  background: var(--danger-bg);
}

.diag-summary {
  flex: 1;
  font-size: 14px;
  color: var(--text);
  line-height: 1.5;
}

.diag-sec {
  padding: 8px 0;
  border-top: 1px dashed var(--border);
}

.diag-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-2);
  margin-bottom: 4px;
}

.diag-label.good {
  color: var(--down);
}

.diag-label.warn {
  color: var(--warning);
}

.diag-line {
  font-size: 13px;
  line-height: 1.5;
  padding: 3px 0;
  color: var(--text);
}
</style>
