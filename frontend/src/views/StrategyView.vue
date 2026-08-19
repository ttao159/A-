<template>
  <div>
    <StrategyCompare />

    <div class="group-tabs">
      <button class="group-tab" :class="{ active: activeGroup === '' }" @click="activeGroup = ''">全部</button>
      <button
        v-for="g in groups"
        :key="g"
        class="group-tab"
        :class="{ active: activeGroup === g }"
        @click="activeGroup = g"
      >
        {{ g }}
      </button>
      <button class="group-add" aria-label="新建分组" @click="showGroupAdd = true">＋</button>
    </div>

    <div class="batch-bar">
      <button class="btn ghost small" @click="toggleBatch">{{ batchMode ? '退出批量' : '批量管理' }}</button>
      <span v-if="batchMode" class="muted" style="font-size: 12px">已选 {{ selectedIds.length }} 项</span>
    </div>

    <Skeleton v-if="strategyStore.loading && !strategyStore.strategies.length" :rows="2" />
    <div v-else-if="!strategyStore.strategies.length" class="empty">暂无策略，点击右下角 + 新建</div>

    <template v-for="s in activeStrategies" :key="s.id">
      <div class="card" :class="{ highlighted: s.id === highlightId, selected: selectedIds.includes(s.id) }" @click="onCardClick(s)">
        <div class="row">
          <label v-if="batchMode" class="check" @click.stop>
            <input v-model="selectedIds" type="checkbox" :value="s.id" />
          </label>
          <div style="flex: 1">
            <div style="font-weight: 500">
              {{ s.name }}
              <span v-if="s.group_name" class="group-tag">{{ s.group_name }}</span>
            </div>
            <div class="muted">
              分配 {{ fmtMoneyCompact(s.initial_capital) }} · 可用 {{ fmtMoneyCompact(s.available_cash) }}
            </div>
          </div>
          <button
            v-if="!batchMode"
            class="switch"
            :class="{ on: s.enabled }"
            role="switch"
            :aria-checked="s.enabled"
            :aria-label="`${s.enabled ? '停用' : '启用'}策略 ${s.name}`"
            @click.stop="toggle(s)"
          >
            <span class="knob"></span>
          </button>
        </div>
        <div v-if="!batchMode" class="ops-row">
          <div class="more-wrap">
            <button class="btn ghost" @click.stop="toggleMore(s.id)">
              <Icon name="more-h" :size="16" />
              <span>更多</span>
            </button>
            <Transition name="menu">
              <div v-if="moreOpenId === s.id" class="more-menu">
                <button class="menu-item" @click="openPreview(s)">详情</button>
                <button class="menu-item" @click="startEdit(s)">编辑</button>
                <button class="menu-item" @click="goBacktest(s)">回测</button>
              </div>
            </Transition>
          </div>
          <button class="btn danger" style="margin-left: auto" @click="remove(s)">删除</button>
        </div>
      </div>
    </template>

    <div v-if="idleStrategies.length" class="card">
      <button class="idle-toggle" @click="idleOpen = !idleOpen">
        <span>未启用策略（{{ idleStrategies.length }}）</span>
        <Icon :name="idleOpen ? 'chevron-up' : 'chevron-down'" :size="16" />
      </button>
      <div v-if="idleOpen" class="idle-hint">
        该策略尚未触发任何信号，建议检查条件设置或运行回测。
      </div>
      <template v-if="idleOpen">
        <div
          v-for="s in idleStrategies"
          :key="s.id"
          class="card idle-card"
          :class="{ highlighted: s.id === highlightId, selected: selectedIds.includes(s.id) }"
          @click="onCardClick(s)"
        >
          <div class="row">
            <label v-if="batchMode" class="check" @click.stop>
              <input v-model="selectedIds" type="checkbox" :value="s.id" />
            </label>
            <div style="flex: 1">
              <div style="font-weight: 500">
                {{ s.name }}
                <span v-if="!s.enabled" class="muted">（停用）</span>
                <span v-if="s.group_name" class="group-tag">{{ s.group_name }}</span>
              </div>
              <div class="muted">
                分配 {{ fmtMoneyCompact(s.initial_capital) }} · 可用 {{ fmtMoneyCompact(s.available_cash) }}
              </div>
            </div>
            <button
              v-if="!batchMode"
              class="switch"
              :class="{ on: s.enabled }"
              role="switch"
              :aria-checked="s.enabled"
              :aria-label="`${s.enabled ? '停用' : '启用'}策略 ${s.name}`"
              @click.stop="toggle(s)"
            >
              <span class="knob"></span>
            </button>
          </div>
          <div v-if="!batchMode" class="ops-row">
            <div class="more-wrap">
              <button class="btn ghost" @click.stop="toggleMore(s.id)">
                <Icon name="more-h" :size="16" />
                <span>更多</span>
              </button>
              <Transition name="menu">
                <div v-if="moreOpenId === s.id" class="more-menu">
                  <button class="menu-item" @click="openPreview(s)">详情</button>
                  <button class="menu-item" @click="startEdit(s)">编辑</button>
                  <button class="menu-item" @click="goBacktest(s)">回测</button>
                </div>
              </Transition>
            </div>
            <button class="btn danger" style="margin-left: auto" @click="remove(s)">删除</button>
          </div>
        </div>
      </template>
    </div>

    <div v-if="batchMode && selectedIds.length" class="batch-actions">
      <button class="batch-btn" @click="showGroupPick = true">归类</button>
      <button class="batch-btn" @click="batchToggle(true)">批量启用</button>
      <button class="batch-btn" @click="batchToggle(false)">批量停用</button>
      <button class="batch-btn danger" @click="batchDelete">批量删除</button>
    </div>

    <button v-if="!batchMode" class="fab" aria-label="新建策略" @click="showTemplatePicker = true">
      <Icon name="plus" :size="26" />
    </button>

    <div v-if="previewing" class="scan-mask" @click.self="previewing = null">
      <div class="box" style="max-height: 82%; overflow-y: auto; text-align: left; width: 92%">
        <h3 style="margin: 0 0 12px">策略详情</h3>
        <StrategyPreview v-if="previewing" :strategy="previewing" :positions="positionsOf(previewing.id)" />
        <button class="btn block" style="margin-top: 14px" @click="previewing = null">关闭</button>
      </div>
    </div>

    <div v-if="editing" class="scan-mask" @click.self="editing = false">
      <div class="box" style="max-height: 82%; overflow-y: auto; text-align: left; width: 92%">
        <h3 style="margin: 0 0 12px">{{ current ? '编辑策略' : '新建策略' }}</h3>
        <StrategyEditor :strategy="current" :template="template" @save="save" @cancel="editing = false" />
      </div>
    </div>

    <div v-if="showTemplatePicker" class="scan-mask" @click.self="showTemplatePicker = false">
      <div class="box" style="max-height: 82%; overflow-y: auto; text-align: left; width: 92%">
        <h3 style="margin: 0 0 12px">选择策略模板</h3>
        <div class="tpl-item" @click="pickTemplate(null)">
          <div class="tpl-name">空白策略</div>
          <div class="tpl-desc muted">从零开始配置买卖信号与风控参数</div>
        </div>
        <div v-for="t in templates" :key="t.key" class="tpl-item" @click="pickTemplate(t)">
          <div class="tpl-name">{{ t.name }}</div>
          <div class="tpl-desc muted">{{ t.description }}</div>
        </div>
        <button class="btn ghost block" style="margin-top: 12px" @click="showTemplatePicker = false">取消</button>
      </div>
    </div>

    <div v-if="showGroupAdd" class="scan-mask" @click.self="showGroupAdd = false">
      <div class="box" style="text-align: left; width: 88%">
        <h3 style="margin: 0 0 12px">新建分组</h3>
        <div class="field">
          <input v-model="newGroupName" placeholder="输入分组名称" @keyup.enter="addGroup" />
        </div>
        <div class="row" style="gap: 12px; margin-top: 12px">
          <button class="btn block" @click="addGroup">创建</button>
          <button class="btn ghost block" @click="showGroupAdd = false">取消</button>
        </div>
      </div>
    </div>

    <div v-if="showGroupPick" class="scan-mask" @click.self="showGroupPick = false">
      <div class="box" style="text-align: left; width: 88%">
        <h3 style="margin: 0 0 12px">归类到分组</h3>
        <button class="group-pick-item" @click="batchGroup('')">
          <span>未分组</span>
        </button>
        <button v-for="g in groups" :key="g" class="group-pick-item" @click="batchGroup(g)">
          <span>{{ g }}</span>
        </button>
        <button class="btn ghost block" style="margin-top: 12px" @click="showGroupPick = false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StrategyEditor from '../components/StrategyEditor.vue'
import StrategyPreview from '../components/StrategyPreview.vue'
import StrategyCompare from '../components/StrategyCompare.vue'
import Skeleton from '../components/Skeleton.vue'
import Icon from '../components/Icon.vue'
import { useStrategyStore } from '../stores/strategy'
import { usePositionStore } from '../stores/position'
import { usePullRefresh } from '../composables/pullRefresh'
import { strategyApi } from '../api'
import type { Strategy, StrategyInput } from '../api/types'
import type { StrategyCompareItem } from '../api/types'
import type { StrategyTemplate } from '../utils/strategyTemplates'
import { STRATEGY_TEMPLATES } from '../utils/strategyTemplates'
import { fmtMoneyCompact } from '../utils/format'
import { confirmDialog } from '../utils/confirm'
import { toast } from '../utils/toast'
import { loadLS, saveLS } from '../utils/storage'

const strategyStore = useStrategyStore()
const positionStore = usePositionStore()
const router = useRouter()
const route = useRoute()

const editing = ref(false)
const current = ref<Strategy | null>(null)
const previewing = ref<Strategy | null>(null)
const highlightId = ref<number | null>(null)
const showTemplatePicker = ref(false)
const template = ref<StrategyTemplate | null>(null)
const templates = STRATEGY_TEMPLATES

const moreOpenId = ref<number | null>(null)
const idleOpen = ref(false)
const idleMap = ref<Record<number, StrategyCompareItem>>({})
const idleReady = ref(false)

const DEFAULT_GROUPS = ['测试中策略', '实盘运行策略', '废弃策略']
const groups = ref<string[]>(loadLS<string[]>('groups') ?? [...DEFAULT_GROUPS])
const activeGroup = ref('')
const batchMode = ref(false)
const selectedIds = ref<number[]>([])
const showGroupAdd = ref(false)
const showGroupPick = ref(false)
const newGroupName = ref('')

onMounted(() => {
  if (route.query.sid) highlightId.value = Number(route.query.sid)
  strategyStore.fetch()
  positionStore.fetch()
  loadCompare()
  document.addEventListener('click', onDocClick)
})
onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
})
usePullRefresh(() => {
  strategyStore.fetch()
  positionStore.fetch()
  loadCompare()
})

function isIdle(s: Strategy) {
  const it = idleMap.value[s.id]
  if (!idleReady.value || !it) return false
  return it.market_value === 0 && it.pnl === 0
}

function matchesGroup(s: Strategy) {
  return !activeGroup.value || s.group_name === activeGroup.value
}

const activeStrategies = computed(() => strategyStore.strategies.filter((s) => !isIdle(s) && matchesGroup(s)))
const idleStrategies = computed(() => strategyStore.strategies.filter((s) => isIdle(s) && matchesGroup(s)))

async function loadCompare() {
  try {
    const items = await strategyApi.compare()
    const m: Record<number, StrategyCompareItem> = {}
    for (const it of items) m[it.id] = it
    idleMap.value = m
    idleReady.value = true
  } catch {
    idleReady.value = false
  }
}

function toggleMore(id: number) {
  moreOpenId.value = moreOpenId.value === id ? null : id
}

function onDocClick() {
  moreOpenId.value = null
}

function positionsOf(id: number) {
  return positionStore.positions.filter((p) => p.strategy_id === id)
}

function openPreview(s: Strategy) {
  moreOpenId.value = null
  previewing.value = s
}

function pickTemplate(t: StrategyTemplate | null) {
  showTemplatePicker.value = false
  current.value = null
  template.value = t
  editing.value = true
}

function startEdit(s: Strategy) {
  moreOpenId.value = null
  current.value = s
  template.value = null
  editing.value = true
}

async function save(payload: StrategyInput) {
  if (current.value) {
    await strategyStore.update(current.value.id, payload)
  } else {
    await strategyStore.create(payload)
  }
  editing.value = false
}

async function toggle(s: Strategy) {
  await strategyStore.update(s.id, { enabled: !s.enabled })
}

async function remove(s: Strategy) {
  const ok = await confirmDialog({
    title: '删除策略',
    message: `确认删除策略「${s.name}」？删除后不可恢复。`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return
  await strategyStore.remove(s.id)
}

function goBacktest(s: Strategy) {
  moreOpenId.value = null
  router.push({ path: '/strategy/backtest', query: { sid: String(s.id) } })
}

function toggleBatch() {
  batchMode.value = !batchMode.value
  selectedIds.value = []
}

function onCardClick(s: Strategy) {
  if (!batchMode.value) return
  const i = selectedIds.value.indexOf(s.id)
  if (i >= 0) selectedIds.value = selectedIds.value.filter((x) => x !== s.id)
  else selectedIds.value = [...selectedIds.value, s.id]
}

function addGroup() {
  const name = newGroupName.value.trim()
  if (!name) {
    toast('请输入分组名称')
    return
  }
  if (groups.value.includes(name)) {
    toast('分组已存在')
    return
  }
  groups.value = [...groups.value, name]
  saveLS('groups', groups.value)
  newGroupName.value = ''
  showGroupAdd.value = false
}

async function batchGroup(groupName: string) {
  try {
    await strategyApi.batchGroup(selectedIds.value, groupName)
    showGroupPick.value = false
    toast(`已归类 ${selectedIds.value.length} 个策略`)
    await strategyStore.fetch()
  } catch (e) {
    toast((e as Error).message)
  }
}

async function batchToggle(enabled: boolean) {
  try {
    await strategyApi.batchToggle(selectedIds.value, enabled)
    toast(enabled ? `已启用 ${selectedIds.value.length} 个策略` : `已停用 ${selectedIds.value.length} 个策略`)
    await strategyStore.fetch()
  } catch (e) {
    toast((e as Error).message)
  }
}

async function batchDelete() {
  const ok = await confirmDialog({
    title: '批量删除策略',
    message: `确认删除选中的 ${selectedIds.value.length} 个策略？删除后不可恢复。`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return
  try {
    await strategyApi.batchDelete(selectedIds.value)
    toast('已删除')
    selectedIds.value = []
    await strategyStore.fetch()
  } catch (e) {
    toast((e as Error).message)
  }
}
</script>

<style scoped>
.switch {
  position: relative;
  flex: 0 0 auto;
  width: 46px;
  height: 26px;
  border-radius: 26px;
  background: var(--border);
  border: none;
  padding: 0;
  cursor: pointer;
  transition: background 0.2s;
}

.switch .knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.2s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.switch.on {
  background: var(--primary);
}

.switch.on .knob {
  transform: translateX(20px);
}

.highlighted {
  outline: 2px solid var(--primary);
  outline-offset: -2px;
}

.ops-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.more-wrap {
  position: relative;
}

.more-wrap > .btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.more-menu {
  position: absolute;
  left: 0;
  top: calc(100% + 6px);
  z-index: 30;
  min-width: 128px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 4px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
}

.menu-item {
  padding: 10px 12px;
  border: none;
  background: none;
  color: var(--text);
  font-size: 14px;
  text-align: left;
  border-radius: 7px;
  cursor: pointer;
}

.menu-item:active {
  background: var(--focus-ring);
}

.menu-enter-active,
.menu-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.menu-enter-from,
.menu-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.idle-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
  border: none;
  background: none;
  color: var(--text-2);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.idle-hint {
  margin-top: 8px;
  padding: 10px 12px;
  background: var(--warning-bg);
  border: 1px dashed var(--warning);
  color: var(--warning);
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.5;
}

.idle-card {
  margin: 12px 0 0;
  background: var(--bg);
}

.fab {
  position: fixed;
  right: max(16px, calc(50% - 244px));
  bottom: calc(80px + env(safe-area-inset-bottom));
  z-index: 25;
  width: 54px;
  height: 54px;
  border-radius: 50%;
  border: none;
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
  cursor: pointer;
  transition: transform 0.12s ease;
  -webkit-tap-highlight-color: transparent;
}

.fab:active {
  transform: scale(0.92);
}

.tpl-item {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 10px;
  cursor: pointer;
  background: var(--bg);
}

.tpl-item:active {
  background: var(--border);
}

.tpl-name {
  font-weight: 600;
  font-size: 14px;
}

.tpl-desc {
  font-size: 12px;
  margin-top: 4px;
}

.group-tabs {
  display: flex;
  gap: 6px;
  padding: 2px 0 8px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.group-tab {
  flex: 0 0 auto;
  min-height: 32px;
  padding: 0 14px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text-2);
  font-size: 13px;
  cursor: pointer;
}

.group-tab.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
  font-weight: 600;
}

.group-add {
  flex: 0 0 auto;
  width: 32px;
  min-height: 32px;
  border-radius: 16px;
  border: 1px dashed var(--border);
  background: none;
  color: var(--text-2);
  font-size: 16px;
  cursor: pointer;
}

.group-tag {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--focus-ring);
  color: var(--primary);
  font-size: 11px;
  vertical-align: middle;
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.check {
  display: flex;
  align-items: center;
  margin-right: 4px;
}

.check input {
  width: 18px;
  height: 18px;
}

.card.selected {
  outline: 2px solid var(--primary);
  outline-offset: -2px;
}

.batch-actions {
  position: fixed;
  left: 0;
  right: 0;
  bottom: calc(56px + env(safe-area-inset-bottom));
  z-index: 26;
  display: flex;
  gap: 8px;
  padding: 10px 16px;
  background: var(--card);
  border-top: 1px solid var(--border);
}

.batch-btn {
  flex: 1;
  min-height: 40px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  cursor: pointer;
}

.batch-btn.danger {
  color: var(--danger);
  border-color: var(--danger);
}

.group-pick-item {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 8px;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  text-align: left;
  cursor: pointer;
}

.group-pick-item:active {
  background: var(--border);
}
</style>
