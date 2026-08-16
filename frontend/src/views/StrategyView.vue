<template>
  <div>
    <StrategyCompare />

    <div class="card">
      <button class="btn block" @click="showTemplatePicker = true">新建策略</button>
    </div>

    <Skeleton v-if="strategyStore.loading && !strategyStore.strategies.length" :rows="2" />
    <div v-else-if="!strategyStore.strategies.length" class="empty">暂无策略，点击上方新建</div>

    <div v-for="s in strategyStore.strategies" :key="s.id" class="card" :class="{ highlighted: s.id === highlightId }">
      <div class="row">
        <div>
          <div style="font-weight: 500">{{ s.name }}</div>
          <div class="muted">
            分配 {{ fmtMoney(s.initial_capital) }} · 可用 {{ fmtMoney(s.available_cash) }}
          </div>
        </div>
        <button
          class="switch"
          :class="{ on: s.enabled }"
          role="switch"
          :aria-checked="s.enabled"
          :aria-label="`${s.enabled ? '停用' : '启用'}策略 ${s.name}`"
          @click="toggle(s)"
        >
          <span class="knob"></span>
        </button>
      </div>
      <div class="row" style="margin-top: 10px; gap: 8px">
        <button class="btn ghost" style="flex: 1" @click="openPreview(s)">详情</button>
        <button class="btn ghost" style="flex: 1" @click="startEdit(s)">编辑</button>
        <button class="btn ghost" style="flex: 1" @click="goBacktest(s)">回测</button>
        <button class="btn danger" style="flex: 1" @click="remove(s)">删除</button>
      </div>
    </div>

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
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StrategyEditor from '../components/StrategyEditor.vue'
import StrategyPreview from '../components/StrategyPreview.vue'
import StrategyCompare from '../components/StrategyCompare.vue'
import Skeleton from '../components/Skeleton.vue'
import { useStrategyStore } from '../stores/strategy'
import { usePositionStore } from '../stores/position'
import { usePullRefresh } from '../composables/pullRefresh'
import type { Strategy, StrategyInput } from '../api/types'
import type { StrategyTemplate } from '../utils/strategyTemplates'
import { STRATEGY_TEMPLATES } from '../utils/strategyTemplates'
import { fmtMoney } from '../utils/format'
import { confirmDialog } from '../utils/confirm'

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

onMounted(() => {
  if (route.query.sid) highlightId.value = Number(route.query.sid)
  strategyStore.fetch()
  positionStore.fetch()
})
usePullRefresh(() => {
  strategyStore.fetch()
  positionStore.fetch()
})

function positionsOf(id: number) {
  return positionStore.positions.filter((p) => p.strategy_id === id)
}

function openPreview(s: Strategy) {
  previewing.value = s
}

function pickTemplate(t: StrategyTemplate | null) {
  showTemplatePicker.value = false
  current.value = null
  template.value = t
  editing.value = true
}

function startEdit(s: Strategy) {
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
  router.push({ path: '/backtest', query: { sid: String(s.id) } })
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
</style>
