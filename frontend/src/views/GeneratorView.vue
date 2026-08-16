<template>
  <div>
    <div class="card seg-wrap">
      <div class="seg-tabs">
        <button class="seg-tab" :class="{ active: activeTab === 'scan' }" @click="activeTab = 'scan'">扫描</button>
        <button class="seg-tab" :class="{ active: activeTab === 'gen' }" @click="activeTab = 'gen'">生成</button>
      </div>
    </div>

    <template v-if="activeTab === 'scan'">
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
      <Skeleton v-if="reportsLoading" :rows="2" />
      <div v-else-if="reportsError" class="error-box">
        {{ reportsError }}<br /><button class="retry-btn" @click="loadReports">重试</button>
      </div>
      <template v-else>
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
          · {{ reports.scan_schedule.broker_type === 'live' ? '实盘' : '模拟盘' }} · {{ countdownText }}
        </div>
      </template>
    </div>

    <div v-if="lastResult" class="card">
      <div class="card-title">最近扫描结果</div>
      <div class="row" style="gap: 8px">
        <span class="stat">买入 <b>{{ lastResult.buys.length }}</b></span>
        <span class="stat">卖出 <b>{{ lastResult.sells.length }}</b></span>
        <span class="stat">拒绝 <b>{{ lastResult.rejected.length }}</b></span>
        <span class="stat">策略 <b>{{ lastResult.strategy_count }}</b></span>
      </div>
      <div v-if="lastResult.buys.length" class="scan-detail-block">
        <div class="scan-detail-title">买入</div>
        <div v-for="(b, i) in lastResult.buys" :key="i" class="scan-detail-item up">{{ tradeLabel(b) }}</div>
      </div>
      <div v-if="lastResult.sells.length" class="scan-detail-block">
        <div class="scan-detail-title">卖出</div>
        <div v-for="(s, i) in lastResult.sells" :key="i" class="scan-detail-item down">{{ tradeLabel(s) }}</div>
      </div>
      <div v-if="lastResult.rejected.length" class="scan-detail-block">
        <div class="scan-detail-title">拒绝</div>
        <div v-for="(r, i) in lastResult.rejected" :key="i" class="scan-detail-item muted">{{ rejectedLabel(r) }}</div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">扫描历史</div>
      <div v-if="reportsError" class="error-box">
        {{ reportsError }}<br /><button class="retry-btn" @click="loadReports">重试</button>
      </div>
      <div v-else-if="!reports.items.length" class="empty">暂无记录</div>
      <div v-for="r in visibleReports" :key="r.id" class="scan-item">
        <div class="scan-item-top">
          <div class="scan-item-left">
            <div class="scan-time">{{ fmtDateTime(r.created_at) }}</div>
            <div class="scan-item-sub">{{ r.source === 'auto' ? '自动扫描' : '手动扫描' }} · {{ r.strategy_count }} 策略</div>
          </div>
          <div class="scan-item-right">
            <span class="scan-counts">
              买 <b class="up">{{ r.buy_count }}</b> · 卖 <b class="down">{{ r.sell_count }}</b> · 拒 <b>{{ r.reject_count }}</b>
            </span>
            <button class="btn ghost small" @click="viewScanDetail(r.id)">查看</button>
          </div>
        </div>
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
    </template>

    <template v-else>
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
      <div v-if="genError" class="gen-error">{{ genError }}</div>
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
          <span>年化 <b :class="pnlClass(recStrategy.metrics.annual_return_pct)">{{ recStrategy.metrics.annual_return_pct ?? '—' }}%</b></span>
          <span>回撤 <b>{{ recStrategy.metrics.max_drawdown_pct ?? '—' }}%</b></span>
          <span>胜率 <b>{{ recStrategy.metrics.win_rate_pct ?? '—' }}%</b></span>
        </div>
        <div v-if="recStrategy.decision" class="gen-decision">
          <div class="gen-decision-top">
            <span class="gen-decision-rating">{{ recStrategy.decision.rating }}</span>
            <span class="gen-decision-action" :class="actionClass(recStrategy.decision.action)">
              {{ recStrategy.decision.action }}
            </span>
            <span class="muted">风险 {{ recStrategy.decision.risk_level }}</span>
            <span class="muted">置信 {{ recStrategy.decision.confidence }}%</span>
          </div>
          <div class="gen-decision-summary">{{ recStrategy.decision.summary }}</div>
        </div>

        <div v-if="genResult.agent_analysis" class="gen-agents">
          <template v-if="genResult.agent_analysis.available && genResult.agent_analysis.opinions">
            <div v-for="(v, k) in genResult.agent_analysis.opinions" :key="k" class="gen-agent">
              <b>{{ k }}</b>{{ v }}
            </div>
            <div
              v-if="genResult.agent_analysis.bull_case || genResult.agent_analysis.bear_case"
              class="gen-debate"
            >
              <div class="gen-debate-bull"><b>看涨</b>{{ genResult.agent_analysis.bull_case || '—' }}</div>
              <div class="gen-debate-bear"><b>看跌</b>{{ genResult.agent_analysis.bear_case || '—' }}</div>
            </div>
            <div
              v-if="genResult.agent_analysis.target_price || genResult.agent_analysis.stop_loss || genResult.agent_analysis.position_suggestion"
              class="gen-trade"
            >
              <span v-if="genResult.agent_analysis.target_price">目标价 ¥{{ genResult.agent_analysis.target_price }}</span>
              <span v-if="genResult.agent_analysis.stop_loss">止损价 ¥{{ genResult.agent_analysis.stop_loss }}</span>
              <span v-if="genResult.agent_analysis.position_suggestion">仓位 {{ genResult.agent_analysis.position_suggestion }}</span>
            </div>
            <div class="gen-agent-verdict">
              综合结论：{{ genResult.agent_analysis.verdict || '—' }} · 建议 {{ genResult.agent_analysis.action || '—' }} · 置信 {{ genResult.agent_analysis.confidence ?? '—' }}%
            </div>
          </template>
          <div v-else class="gen-agents-fallback">
            {{ genResult.agent_analysis.verdict || '使用启发式分析结论' }}
          </div>
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
        <button
          class="btn ghost"
          :class="{ saved: savedIndexes.includes(s.index) }"
          :disabled="savedIndexes.includes(s.index)"
          @click="saveGenStrategy(s)"
        >
          {{ savedIndexes.includes(s.index) ? '已保存' : '保存' }}
        </button>
      </div>
    </div>

    <div class="card">
      <div class="card-title">生成历史</div>
      <div v-if="genHistoryError" class="error-box">
        {{ genHistoryError }}<br /><button class="retry-btn" @click="loadGenHistory">重试</button>
      </div>
      <div v-else-if="!genHistory.length" class="empty">暂无记录</div>
      <div v-for="g in genHistory" :key="g.id" class="scan-item">
        <div class="scan-item-top">
          <span class="scan-time">{{ fmtDateTime(g.created_at) }}</span>
          <button class="btn ghost small" @click="viewReport(g.id)">查看</button>
        </div>
        <div class="scan-item-sub">
          推荐第 {{ g.recommended_index + 1 }} 个 · {{ genHistoryText(g.request) }}
        </div>
      </div>
    </div>
    </template>

    <div v-if="detailReport || detailLoading || detailError" class="scan-mask" @click.self="closeDetail">
      <div class="box scan-detail-box">
        <h3 style="margin: 0 0 10px">扫描详情</h3>
        <div v-if="detailLoading" class="empty">加载中...</div>
        <div v-else-if="detailError" class="error-box">
          {{ detailError }}<br /><button class="retry-btn" @click="viewScanDetail(detailId ?? 0)">重试</button>
        </div>
        <template v-else-if="detailReport">
          <div class="scan-detail-block">
            <div class="scan-detail-title">买入（{{ detailReport.buys.length }}）</div>
            <div v-if="!detailReport.buys.length" class="muted">无</div>
            <div v-for="(b, i) in detailReport.buys" :key="i" class="scan-detail-item up">{{ tradeLabel(b) }}</div>
          </div>
          <div class="scan-detail-block">
            <div class="scan-detail-title">卖出（{{ detailReport.sells.length }}）</div>
            <div v-if="!detailReport.sells.length" class="muted">无</div>
            <div v-for="(s, i) in detailReport.sells" :key="i" class="scan-detail-item down">{{ tradeLabel(s) }}</div>
          </div>
          <div class="scan-detail-block">
            <div class="scan-detail-title">拒绝（{{ detailReport.rejected.length }}）</div>
            <div v-if="!detailReport.rejected.length" class="muted">无</div>
            <div v-for="(r, i) in detailReport.rejected" :key="i" class="scan-detail-item muted">{{ rejectedLabel(r) }}</div>
          </div>
        </template>
        <button class="btn block" style="margin-top: 12px" @click="closeDetail">关闭</button>
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
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
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
import { useAccountStore } from '../stores/account'
import { sigNames } from '../utils/signals'
import { toast } from '../utils/toast'
import { confirmDialog } from '../utils/confirm'
import { fmtDateTime, pnlClass } from '../utils/format'
import { defaultDateRange } from '../utils/date'
import Skeleton from '../components/Skeleton.vue'

const strategyStore = useStrategyStore()
const accountStore = useAccountStore()

const activeTab = ref<'scan' | 'gen'>('scan')
const scanning = ref(false)
const generating = ref(false)
const lastResult = ref<ScanResult | null>(null)
const reports = reactive<ScanReports>({ scan_schedule: undefined, stats: { total_scans: 0, total_buys: 0, total_sells: 0, total_rejects: 0 }, items: [] })

const SCAN_VISIBLE = 5
const scanExpanded = ref(false)
const reportsLoading = ref(true)
const reportsError = ref('')
const genHistoryError = ref('')
const savedIndexes = ref<number[]>([])
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
const genError = ref('')
const genResult = ref<GenerationReport | null>(null)
const genHistory = ref<GenerationReportItem[]>([])

const detailReport = ref<ScanResult | null>(null)
const detailId = ref<number | null>(null)
const detailLoading = ref(false)
const detailError = ref('')
const countdownText = ref('')
let countdownTimer: number | undefined

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
  countdownTimer = window.setInterval(computeCountdown, 1000)
})

onUnmounted(() => {
  if (countdownTimer) window.clearInterval(countdownTimer)
})

async function loadReports() {
  reportsLoading.value = true
  reportsError.value = ''
  try {
    const r = await scanApi.reports()
    reports.scan_schedule = r.scan_schedule
    reports.stats = r.stats
    reports.items = r.items
    computeCountdown()
  } catch (e) {
    if (!reports.items.length) reportsError.value = '扫描数据加载失败'
  } finally {
    reportsLoading.value = false
  }
}

async function loadGenHistory() {
  genHistoryError.value = ''
  try {
    genHistory.value = await generatorApi.reports()
  } catch (e) {
    if (!genHistory.value.length) genHistoryError.value = '生成历史加载失败'
  }
}

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function computeCountdown() {
  const s = reports.scan_schedule
  if (!s) {
    countdownText.value = ''
    return
  }
  const now = new Date()
  const next = new Date(now)
  next.setHours(s.hour, s.minute, 0, 0)
  if (next.getTime() <= now.getTime()) next.setDate(next.getDate() + 1)
  while (next.getDay() === 0 || next.getDay() === 6) {
    next.setDate(next.getDate() + 1)
  }
  const diff = next.getTime() - now.getTime()
  const h = Math.floor(diff / 3600000)
  const m = Math.floor((diff % 3600000) / 60000)
  const sec = Math.floor((diff % 60000) / 1000)
  countdownText.value = `距下次扫描 ${pad(h)}:${pad(m)}:${pad(sec)}`
}

async function viewScanDetail(id: number) {
  detailId.value = id
  detailLoading.value = true
  detailError.value = ''
  detailReport.value = null
  try {
    detailReport.value = await scanApi.report(id)
  } catch (e) {
    detailError.value = '详情加载失败'
  } finally {
    detailLoading.value = false
  }
}

function closeDetail() {
  detailReport.value = null
  detailError.value = ''
  detailId.value = null
}

function tradeLabel(t: Record<string, unknown>) {
  const name = String(t.name || t.code || '')
  const code = String(t.code || '')
  const price = t.price != null ? ` @${Number(t.price).toFixed(2)}` : ''
  const qty = t.qty != null ? ` ×${t.qty}` : ''
  const reason = t.reason ? ` · ${t.reason}` : ''
  return `${name}(${code})${price}${qty}${reason}`
}

function rejectedLabel(r: Record<string, unknown>) {
  const name = String(r.name || r.code || '')
  const code = String(r.code || '')
  const reason = r.reason ? ` · ${r.reason}` : ''
  return `${name}(${code})${reason}`
}

function actionClass(a: string) {
  if (a === '采用') return 'gen-action-use'
  if (a === '弃用') return 'gen-action-drop'
  return 'gen-action-watch'
}

function genHistoryText(req: Record<string, unknown>) {
  const targets = (req.targets ?? {}) as Record<string, unknown>
  const scope = targets.scope
  const risk = RISK_LABELS[String(req.risk_profile ?? 'balanced')] ?? req.risk_profile
  return `${scope === 'market' ? '全市场' : '指定标的'} · ${risk}`
}

function applyProgress(e: StreamEvent) {
  progressMsg.value = String(e.message ?? '')
  progressDone.value = Number(e.done ?? 0)
  progressTotal.value = Number(e.total ?? 0)
  pct.value = progressTotal.value ? Math.round((progressDone.value / progressTotal.value) * 100) : 0
}

function beginElapsed(): number {
  elapsed.value = 0
  const start = Date.now()
  return window.setInterval(() => {
    elapsed.value = Math.round((Date.now() - start) / 1000)
  }, 1000)
}

function handleEvent(e: StreamEvent) {
  if (e.type === 'progress') {
    applyProgress(e)
  } else if (e.type === 'result') {
    const report = e.report as ScanResult
    if (report) lastResult.value = report
  } else if (e.type === 'error') {
    toast(String(e.detail ?? '扫描失败'))
  }
}

function handleGenEvent(e: StreamEvent) {
  if (e.type === 'progress') {
    applyProgress(e)
  } else if (e.type === 'result') {
    const report = e.report as GenerationReport
    if (report) {
      genResult.value = report
      genMsg.value = `已生成 ${report.strategies.length} 个候选策略，推荐第 ${(report.recommended_index ?? 0) + 1} 个`
    }
  } else if (e.type === 'error') {
    toast(String(e.detail ?? '生成失败'))
  }
}

async function startScan() {
  const live = accountStore.isLive
  const ok = await confirmDialog({
    title: live ? '实盘扫描确认' : '开始扫描',
    message: live
      ? '将对全市场按策略信号执行扫描，命中即自动下达实盘委托。请确认已开启风控并核对策略。'
      : '将对全市场按策略信号执行扫描，命中即在模拟盘自动成交。',
    confirmText: live ? '确认扫描' : '开始',
    danger: live,
  })
  if (!ok) return
  scanning.value = true
  progressMsg.value = '扫描中...'
  progressDone.value = 0
  progressTotal.value = 0
  pct.value = 0
  const timer = beginElapsed()
  try {
    await scanApi.stream(handleEvent)
    await loadReports()
  } catch (e) {
    toast((e as Error).message)
  } finally {
    window.clearInterval(timer)
    scanning.value = false
  }
}

async function startGen() {
  if (!Number.isInteger(genCount.value) || genCount.value < 1 || genCount.value > 10) {
    genError.value = '生成数量需为 1-10 的整数'
    return
  }
  if (!Number.isFinite(genTarget.value) || genTarget.value < 0 || genTarget.value > 200) {
    genError.value = '目标年化需在 0-200% 之间'
    return
  }
  genError.value = ''
  generating.value = true
  genMsg.value = ''
  genResult.value = null
  progressMsg.value = '生成策略中...'
  progressDone.value = 0
  progressTotal.value = 0
  pct.value = 0
  const timer = beginElapsed()
  try {
    const req: GenerationRequest = {
      targets: { scope: 'market', codes: [] },
      ...defaultDateRange(),
      risk_profile: genRisk.value,
      count: genCount.value,
      target_annual_return: genTarget.value,
      analysis_depth: 'standard',
    }
    await generatorApi.stream(req, handleGenEvent)
    await loadGenHistory()
  } catch (e) {
    toast((e as Error).message)
  } finally {
    window.clearInterval(timer)
    generating.value = false
  }
}

async function viewReport(gid: number) {
  try {
    genResult.value = await generatorApi.report(gid)
  } catch (e) {
    toast((e as Error).message)
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
    if (!savedIndexes.value.includes(s.index)) savedIndexes.value = [...savedIndexes.value, s.index]
  } catch (e) {
    toast((e as Error).message)
  }
}
</script>

<style scoped>
.seg-wrap {
  padding: 8px;
}

.gen-error {
  margin-top: 8px;
  font-size: 13px;
  color: var(--danger);
}

.seg-tabs {
  display: flex;
  background: var(--bg);
  border-radius: 10px;
  padding: 3px;
}

.seg-tab {
  flex: 1;
  min-height: 44px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-2);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.seg-tab:active {
  opacity: 0.7;
}

.seg-tab.active {
  background: var(--card);
  color: var(--primary);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.stat b {
  color: var(--primary);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
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

.scan-item-left {
  min-width: 0;
}

.scan-item-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scan-counts {
  color: var(--text-2);
  font-size: 12px;
  white-space: nowrap;
}

.scan-detail-box {
  max-height: 72vh;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  text-align: left;
}

.scan-detail-block {
  margin-top: 8px;
}

.scan-detail-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-2);
  margin-bottom: 4px;
}

.scan-detail-item {
  font-size: 13px;
  padding: 3px 0;
  line-height: 1.4;
  word-break: break-all;
}

.gen-recommend {
  background: var(--bg);
  border-radius: 10px;
  padding: 12px;
  border: 1px solid var(--primary);
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
  height: 44px;
  padding: 0 16px;
  font-size: 12px;
}

.btn.small:active {
  opacity: 0.7;
}

.btn.saved {
  background: var(--down);
  color: #fff;
  border-color: var(--down);
}

.gen-decision {
  margin-top: 10px;
  padding: 10px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.gen-decision-top {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 13px;
}

.gen-decision-rating {
  font-weight: 700;
  color: var(--primary);
  font-size: 15px;
}

.gen-decision-action {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.gen-action-use {
  background: var(--up-bg);
  color: var(--up);
}

.gen-action-drop {
  background: var(--down-bg);
  color: var(--down);
}

.gen-action-watch {
  background: var(--warning-bg);
  color: var(--warning);
}

.gen-decision-summary {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-2);
}

.gen-agents {
  margin-top: 10px;
  padding: 10px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
}

.gen-agent {
  padding: 4px 0;
  border-bottom: 1px dashed var(--border);
}

.gen-agent b {
  margin-right: 8px;
  color: var(--primary);
}

.gen-debate {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}

.gen-debate-bull,
.gen-debate-bear {
  padding: 8px;
  border-radius: 6px;
  background: var(--bg);
}

.gen-debate-bull b {
  color: var(--up);
  margin-right: 6px;
}

.gen-debate-bear b {
  color: var(--down);
  margin-right: 6px;
}

.gen-trade {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.gen-trade b {
  color: var(--text);
}

.gen-agent-verdict {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
  font-weight: 600;
}

.gen-agents-fallback {
  color: var(--text-2);
}
</style>
