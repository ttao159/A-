<template>
  <div>
    <div class="card">
      <button class="btn block" :disabled="scanning" @click="startScan">
        {{ scanning ? '扫描中...' : '立即扫描' }}
      </button>
      <button class="btn ghost block" style="margin-top: 8px" :disabled="scanning" @click="loadReports">
        刷新扫描历史
      </button>
    </div>

    <div class="card">
      <div class="card-title">扫描统计</div>
      <div class="stat-grid">
        <div class="metric">
          <div class="muted">累计扫描</div>
          <div>{{ reports.stats.total_scans }}</div>
        </div>
        <div class="metric">
          <div class="muted">累计买入</div>
          <div class="up">{{ reports.stats.total_buys }}</div>
        </div>
        <div class="metric">
          <div class="muted">累计卖出</div>
          <div class="down">{{ reports.stats.total_sells }}</div>
        </div>
        <div class="metric">
          <div class="muted">风控拦截</div>
          <div>{{ reports.stats.total_rejects }}</div>
        </div>
      </div>
      <div v-if="reports.scan_schedule" class="muted status-line">
        策略引擎运行中 · 每交易日 {{ pad(reports.scan_schedule.hour) }}:{{ pad(reports.scan_schedule.minute) }} 自动扫描
        · {{ reports.scan_schedule.broker_type === 'live' ? '实盘' : '模拟盘' }}
      </div>
    </div>

    <div v-if="lastResult" class="card">
      <div class="card-title">最近扫描结果</div>
      <div class="row" style="gap: 8px">
        <span class="stat">买入 <b>{{ lastResult.buys.length }}</b></span>
        <span class="stat">卖出 <b>{{ lastResult.sells.length }}</b></span>
        <span class="stat">拒绝 <b>{{ lastResult.rejected.length }}</b></span>
        <span class="stat">策略 <b>{{ lastResult.strategy_count }}</b></span>
      </div>
      <div v-if="lastResult.rejected.length" class="muted" style="margin-top: 8px">
        拒绝：{{ lastResult.rejected.map((r) => (r as { code?: string }).code ?? '').join('、') }}
      </div>
    </div>

    <div class="card">
      <div class="card-title">扫描历史</div>
      <div v-if="!reports.items.length" class="empty">暂无记录</div>
      <div v-for="r in reports.items" :key="r.id" class="list-item">
        <div style="flex: 1">
          <div>第 {{ r.id }} 次扫描</div>
          <div class="muted">{{ (r.created_at ?? '').slice(0, 16) }}</div>
        </div>
        <div class="muted">买 {{ r.buy_count }} · 卖 {{ r.sell_count }} · 拒 {{ r.reject_count }}</div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">策略生成器</div>
      <div class="field">
        <label>风险偏好</label>
        <select v-model="genRisk">
          <option value="conservative">保守</option>
          <option value="balanced">均衡</option>
          <option value="aggressive">激进</option>
        </select>
      </div>
      <div class="field">
        <label>生成数量</label>
        <input v-model.number="genCount" type="number" min="1" max="10" />
      </div>
      <button class="btn block" :disabled="generating" @click="startGen">
        {{ generating ? '生成中...' : '生成策略' }}
      </button>
      <div v-if="genMsg" class="muted" style="margin-top: 8px">{{ genMsg }}</div>
    </div>

    <div v-if="scanning || generating" class="scan-mask">
      <div class="box">
        <div class="spinner"></div>
        <div style="font-size: 15px; margin-bottom: 4px">{{ progressMsg }}</div>
        <div class="progress-bar">
          <div class="fill" :style="{ width: pct + '%' }"></div>
        </div>
        <div class="muted">{{ progressDone }} / {{ progressTotal }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { generatorApi, scanApi } from '../api'
import type { GenerationRequest, ScanReports, ScanResult } from '../api/types'
import type { StreamEvent } from '../api/http'

const scanning = ref(false)
const generating = ref(false)
const lastResult = ref<ScanResult | null>(null)
const reports = reactive<ScanReports>({ scan_schedule: undefined, stats: { total_scans: 0, total_buys: 0, total_sells: 0, total_rejects: 0 }, items: [] })

const progressMsg = ref('')
const progressDone = ref(0)
const progressTotal = ref(0)
const pct = ref(0)

const genRisk = ref('balanced')
const genCount = ref(3)
const genMsg = ref('')

onMounted(loadReports)

async function loadReports() {
  try {
    const r = await scanApi.reports()
    reports.scan_schedule = r.scan_schedule
    reports.stats = r.stats
    reports.items = r.items
  } catch (e) {
    alert((e as Error).message)
  }
}

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function handleEvent(e: StreamEvent) {
  if (e.type === 'progress') {
    progressMsg.value = String(e.message ?? '')
    progressDone.value = Number(e.done ?? 0)
    progressTotal.value = Number(e.total ?? 0)
    pct.value = progressTotal.value ? Math.round((progressDone.value / progressTotal.value) * 100) : 0
  } else if (e.type === 'result') {
    const report = e.report as ScanResult
    if (report) lastResult.value = report
  } else if (e.type === 'error') {
    alert(String(e.detail ?? '扫描失败'))
  }
}

async function startScan() {
  scanning.value = true
  progressMsg.value = '扫描中...'
  progressDone.value = 0
  progressTotal.value = 0
  pct.value = 0
  try {
    await scanApi.stream(handleEvent)
    await loadReports()
  } catch (e) {
    alert((e as Error).message)
  } finally {
    scanning.value = false
  }
}

function yearRange() {
  const end = new Date()
  const start = new Date()
  start.setFullYear(start.getFullYear() - 1)
  return {
    start_date: start.toISOString().slice(0, 10),
    end_date: end.toISOString().slice(0, 10),
  }
}

async function startGen() {
  generating.value = true
  genMsg.value = ''
  progressMsg.value = '生成策略中...'
  try {
    const req: GenerationRequest = {
      targets: { scope: 'market', codes: [] },
      ...yearRange(),
      risk_profile: genRisk.value,
      count: genCount.value,
      target_annual_return: 0,
      analysis_depth: 'standard',
    }
    const result = await generatorApi.run(req)
    const rec = Number(result.recommended_index ?? -1)
    const n = Array.isArray(result.candidates) ? result.candidates.length : 0
    genMsg.value = `已生成 ${n} 个候选策略，推荐第 ${rec + 1} 个`
  } catch (e) {
    alert((e as Error).message)
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.stat b {
  color: var(--primary);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.metric {
  background: var(--bg);
  border-radius: 8px;
  padding: 10px 6px;
  text-align: center;
}

.metric div:last-child {
  font-size: 16px;
  font-weight: 600;
  margin-top: 2px;
}

.status-line {
  margin-top: 10px;
}
</style>
