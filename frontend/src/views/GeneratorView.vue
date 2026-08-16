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
      <div v-for="r in visibleReports" :key="r.id" class="scan-item">
        <div class="scan-item-top">
          <span class="scan-time">{{ fmtScanTime(r.created_at) }}</span>
          <span class="muted">
            买 <b class="up">{{ r.buy_count }}</b> · 卖 <b class="down">{{ r.sell_count }}</b> · 拒 <b>{{ r.reject_count }}</b>
          </span>
        </div>
        <div class="scan-item-sub">启用策略 {{ r.strategy_count }} 个 · {{ r.source === 'auto' ? '自动扫描' : '手动扫描' }}</div>
      </div>
      <button
        v-if="reports.items.length > SCAN_VISIBLE"
        class="btn ghost block"
        style="margin-top: 8px"
        @click="scanExpanded = !scanExpanded"
      >
        {{ scanExpanded ? '收起' : `展开全部 ${reports.items.length} 条记录` }}
      </button>
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
      <div class="field">
        <label>目标年化（%）</label>
        <input v-model.number="genTarget" type="number" min="0" step="1" />
      </div>
      <button class="btn block" :disabled="generating" @click="startGen">
        {{ generating ? '生成中...' : '生成策略' }}
      </button>
      <div v-if="genMsg" class="muted" style="margin-top: 8px">{{ genMsg }}</div>
    </div>

    <div v-if="genResult" class="card">
      <div class="card-title">生成结果对比</div>
      <div class="muted" style="font-size: 12px; margin-bottom: 8px">{{ genRequestText }}</div>

      <div v-if="recStrategy" class="gen-recommend">
        <div class="gen-recommend-title">推荐策略 #{{ recStrategy.index + 1 }}</div>
        <div class="muted">{{ sigNames(recStrategy.signals) }}</div>
        <div class="gen-recommend-metrics">
          <span>年化 <b :class="cls(recStrategy.metrics.annual_return_pct)">{{ recStrategy.metrics.annual_return_pct ?? '—' }}%</b></span>
          <span>回撤 <b>{{ recStrategy.metrics.max_drawdown_pct ?? '—' }}%</b></span>
          <span>胜率 <b>{{ recStrategy.metrics.win_rate_pct ?? '—' }}%</b></span>
        </div>
        <div v-if="recStrategy.decision" class="muted" style="margin-top: 6px">
          {{ recStrategy.decision.rating }} · {{ recStrategy.decision.risk_level }} · {{ recStrategy.decision.action }}
        </div>
        <button class="btn block" style="margin-top: 10px" @click="saveGenStrategy(recStrategy)">保存为策略</button>
      </div>

      <div class="card-title" style="font-size: 13px; margin-top: 12px">策略对比</div>
      <div v-for="s in sortedStrategies" :key="s.index" class="cmp-row">
        <div style="flex: 1">
          <div style="font-weight: 500">
            #{{ s.index + 1 }}{{ s.index === genResult.recommended_index ? ' ★推荐' : '' }}
          </div>
          <div class="muted" style="font-size: 12px">{{ sigNames(s.signals) }}</div>
          <div class="muted" style="font-size: 12px">
            {{ (s.decision && s.decision.rating) || '—' }} · 年化 {{ s.metrics.annual_return_pct ?? '-' }}% · 回撤 {{ s.metrics.max_drawdown_pct ?? '-' }}%
          </div>
        </div>
        <button class="btn ghost" @click="saveGenStrategy(s)">保存</button>
      </div>
    </div>

    <div class="card">
      <div class="card-title">生成历史</div>
      <div v-if="!genHistory.length" class="empty">暂无记录</div>
      <div v-for="g in genHistory" :key="g.id" class="scan-item">
        <div class="scan-item-top">
          <span class="scan-time">{{ fmtScanTime(g.created_at) }}</span>
          <button class="btn ghost small" @click="viewReport(g.id)">查看</button>
        </div>
        <div class="scan-item-sub">
          推荐第 {{ g.recommended_index + 1 }} 个 · {{ genHistoryText(g.request) }}
        </div>
      </div>
    </div>

    <div v-if="scanning || generating" class="scan-mask">
      <div class="box">
        <div class="spinner"></div>
        <div style="font-size: 15px; margin-bottom: 4px">{{ progressMsg }}</div>
        <div class="progress-bar">
          <div class="fill" :style="{ width: pct + '%' }"></div>
        </div>
        <div class="muted">{{ progressDone }} / {{ progressTotal }} · 已用时 {{ elapsed }} 秒</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { generatorApi, scanApi } from '../api'
import type {
  GenerationReport,
  GenerationReportItem,
  GenerationRequest,
  GenStrategy,
  ScanReports,
  ScanResult,
  StrategyConfig,
} from '../api/types'
import type { StreamEvent } from '../api/http'
import { useStrategyStore } from '../stores/strategy'
import { sigNames } from '../utils/signals'

const strategyStore = useStrategyStore()

const scanning = ref(false)
const generating = ref(false)
const lastResult = ref<ScanResult | null>(null)
const reports = reactive<ScanReports>({ scan_schedule: undefined, stats: { total_scans: 0, total_buys: 0, total_sells: 0, total_rejects: 0 }, items: [] })

const SCAN_VISIBLE = 5
const scanExpanded = ref(false)
const visibleReports = computed(() =>
  scanExpanded.value ? reports.items : reports.items.slice(0, SCAN_VISIBLE),
)

const progressMsg = ref('')
const progressDone = ref(0)
const progressTotal = ref(0)
const pct = ref(0)
const elapsed = ref(0)

const genRisk = ref('balanced')
const genCount = ref(3)
const genTarget = ref(15)
const genMsg = ref('')
const genResult = ref<GenerationReport | null>(null)
const genHistory = ref<GenerationReportItem[]>([])

const RISK_LABELS: Record<string, string> = { conservative: '保守', balanced: '均衡', aggressive: '激进' }

const sortedStrategies = computed(() =>
  (genResult.value?.strategies ?? []).slice().sort((a, b) => a.index - b.index),
)

const recStrategy = computed(() => {
  const rec = genResult.value?.recommended_index
  if (rec == null) return null
  return genResult.value?.strategies.find((s) => s.index === rec) ?? null
})

const genRequestText = computed(() => {
  const req = genResult.value?.request as Record<string, unknown> | undefined
  if (!req) return ''
  const targets = (req.targets ?? {}) as Record<string, unknown>
  const scope = targets.scope
  const codes = Array.isArray(targets.codes) ? (targets.codes as string[]).join(',') : ''
  const scopeText = scope === 'market' ? '全市场' : scope === 'single' ? `单只 ${codes}` : `自定义 ${codes}`
  const risk = RISK_LABELS[String(req.risk_profile ?? 'balanced')] ?? req.risk_profile
  return `${scopeText} · ${req.start_date} ~ ${req.end_date} · ${risk} · 目标年化 ${req.target_annual_return ?? 0}%`
})

onMounted(() => {
  loadReports()
  loadGenHistory()
})

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

async function loadGenHistory() {
  try {
    genHistory.value = await generatorApi.reports()
  } catch (e) {
    // 历史加载失败不阻塞
  }
}

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function fmtScanTime(s: string | null) {
  return (s ?? '').slice(5, 16).replace('T', ' ')
}

function cls(v: number | undefined) {
  return (v ?? 0) >= 0 ? 'up' : 'down'
}

function genHistoryText(req: Record<string, unknown>) {
  const targets = (req.targets ?? {}) as Record<string, unknown>
  const scope = targets.scope
  const risk = RISK_LABELS[String(req.risk_profile ?? 'balanced')] ?? req.risk_profile
  return `${scope === 'market' ? '全市场' : '指定标的'} · ${risk}`
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

function handleGenEvent(e: StreamEvent) {
  if (e.type === 'progress') {
    progressMsg.value = String(e.message ?? '')
    progressDone.value = Number(e.done ?? 0)
    progressTotal.value = Number(e.total ?? 0)
    pct.value = progressTotal.value ? Math.round((progressDone.value / progressTotal.value) * 100) : 0
  } else if (e.type === 'result') {
    const report = e.report as GenerationReport
    if (report) {
      genResult.value = report
      genMsg.value = `已生成 ${report.strategies.length} 个候选策略，推荐第 ${(report.recommended_index ?? 0) + 1} 个`
    }
  } else if (e.type === 'error') {
    alert(String(e.detail ?? '生成失败'))
  }
}

async function startScan() {
  scanning.value = true
  progressMsg.value = '扫描中...'
  progressDone.value = 0
  progressTotal.value = 0
  pct.value = 0
  elapsed.value = 0
  const start = Date.now()
  const timer = window.setInterval(() => {
    elapsed.value = Math.round((Date.now() - start) / 1000)
  }, 1000)
  try {
    await scanApi.stream(handleEvent)
    await loadReports()
  } catch (e) {
    alert((e as Error).message)
  } finally {
    window.clearInterval(timer)
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
  genResult.value = null
  progressMsg.value = '生成策略中...'
  progressDone.value = 0
  progressTotal.value = 0
  pct.value = 0
  elapsed.value = 0
  const start = Date.now()
  const timer = window.setInterval(() => {
    elapsed.value = Math.round((Date.now() - start) / 1000)
  }, 1000)
  try {
    const req: GenerationRequest = {
      targets: { scope: 'market', codes: [] },
      ...yearRange(),
      risk_profile: genRisk.value,
      count: genCount.value,
      target_annual_return: genTarget.value,
      analysis_depth: 'standard',
    }
    await generatorApi.stream(req, handleGenEvent)
    await loadGenHistory()
  } catch (e) {
    alert((e as Error).message)
  } finally {
    window.clearInterval(timer)
    generating.value = false
  }
}

async function viewReport(gid: number) {
  try {
    genResult.value = await generatorApi.report(gid)
  } catch (e) {
    alert((e as Error).message)
  }
}

async function saveGenStrategy(s: GenStrategy) {
  try {
    await strategyStore.create({
      name: `AI生成策略 #${s.index + 1} ${sigNames(s.signals).split(' / ')[0]}`,
      enabled: true,
      initial_capital: 1000000,
      config: s.config as unknown as StrategyConfig,
    })
    genMsg.value = '已保存到策略列表'
  } catch (e) {
    alert((e as Error).message)
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

.scan-item {
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
}

.scan-item:last-child {
  border-bottom: none;
}

.scan-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.scan-time {
  font-weight: 500;
  font-size: 14px;
}

.scan-item-sub {
  margin-top: 2px;
  color: var(--text-2);
  font-size: 12px;
}

.gen-recommend {
  background: var(--bg);
  border-radius: 10px;
  padding: 12px;
}

.gen-recommend-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.gen-recommend-metrics {
  display: flex;
  gap: 12px;
  margin-top: 6px;
  font-size: 14px;
}

.cmp-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--border);
}

.btn.small {
  height: 28px;
  padding: 0 12px;
  font-size: 12px;
}
</style>
