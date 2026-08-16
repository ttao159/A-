<template>
  <div>
    <div class="card">
      <button class="btn block" @click="startCreate">新建策略</button>
    </div>

    <div v-if="strategyStore.loading && !strategyStore.strategies.length" class="empty">加载中...</div>
    <div v-else-if="!strategyStore.strategies.length" class="empty">暂无策略，点击上方新建</div>

    <div v-for="s in strategyStore.strategies" :key="s.id" class="card">
      <div class="row">
        <div>
          <div style="font-weight: 500">{{ s.name }}</div>
          <div class="muted">
            分配 {{ fmtMoney(s.initial_capital) }} · 可用 {{ fmtMoney(s.available_cash) }}
          </div>
        </div>
        <input type="checkbox" :checked="s.enabled" @change="toggle(s)" />
      </div>
      <div class="row" style="margin-top: 10px; gap: 8px">
        <button class="btn ghost" style="flex: 1" @click="startEdit(s)">编辑</button>
        <button class="btn ghost" style="flex: 1" @click="goBacktest(s)">回测</button>
        <button class="btn danger" style="flex: 1" @click="remove(s)">删除</button>
      </div>
    </div>

    <div v-if="editing" class="scan-mask" @click.self="editing = false">
      <div class="box" style="max-height: 82%; overflow-y: auto; text-align: left; width: 92%">
        <h3 style="margin: 0 0 12px">{{ current ? '编辑策略' : '新建策略' }}</h3>
        <StrategyEditor :strategy="current" @save="save" @cancel="editing = false" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import StrategyEditor from '../components/StrategyEditor.vue'
import { useStrategyStore } from '../stores/strategy'
import { usePullRefresh } from '../composables/pullRefresh'
import type { Strategy, StrategyInput } from '../api/types'
import { fmtMoney } from '../utils/format'

const strategyStore = useStrategyStore()
const router = useRouter()

const editing = ref(false)
const current = ref<Strategy | null>(null)

onMounted(() => strategyStore.fetch())
usePullRefresh(() => strategyStore.fetch())

function startCreate() {
  current.value = null
  editing.value = true
}

function startEdit(s: Strategy) {
  current.value = s
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
  if (!window.confirm(`确认删除策略「${s.name}」？`)) return
  await strategyStore.remove(s.id)
}

function goBacktest(s: Strategy) {
  router.push({ path: '/backtest', query: { sid: String(s.id) } })
}
</script>
