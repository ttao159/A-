<template>
  <div>
    <div class="card">
      <div class="card-title">全部预警</div>
      <Skeleton v-if="loading && !alerts.length" :rows="2" />
      <div v-else-if="error" class="error-box">
        {{ error }}<br /><button class="retry-btn" @click="load">重试</button>
      </div>
      <EmptyState v-else-if="!alerts.length" icon="bell" title="暂无预警记录" desc="预警触发后会在这里展示，去策略中心配置提醒条件" />
      <template v-else>
        <div v-for="a in alerts" :key="a.id" class="alert-item">
          <span class="alert-tag" :class="isProfitAlert(a.type) ? 'up' : 'down'">{{ alertTypeLabel(a.type) }}</span>
          <div class="alert-body">
            <div class="alert-msg">{{ a.message }}</div>
            <div class="muted">{{ a.name }} · {{ fmtDateTime(a.created_at) }}</div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { alertApi, type Alert } from '../api'
import { usePullRefresh } from '../composables/pullRefresh'
import Skeleton from '../components/Skeleton.vue'
import EmptyState from '../components/EmptyState.vue'
import { fmtDateTime } from '../utils/format'
import { alertTypeLabel, isProfitAlert } from '../utils/alerts'

const alerts = ref<Alert[]>([])
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    alerts.value = await alertApi.list(500)
  } catch (e) {
    if (!alerts.value.length) error.value = '预警列表加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
usePullRefresh(load)
</script>

<style scoped>
.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--border);
  font-size: 13px;
}

.alert-item:last-child {
  border-bottom: none;
}

.alert-tag {
  flex: 0 0 auto;
  font-weight: 600;
  font-size: 12px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--bg);
}

.alert-body {
  flex: 1;
  min-width: 0;
}

.alert-msg {
  line-height: 1.5;
}
</style>
