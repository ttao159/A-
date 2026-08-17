<template>
  <div class="card security-card" :class="{ live: isLive }">
    <div class="sec-row">
      <span class="badge" :class="isLive ? 'live' : 'paper'">{{ isLive ? '实盘' : '模拟盘' }}</span>
      <span class="sec-title">{{ isLive ? '真实资金交易' : '本地模拟环境' }}</span>
    </div>
    <div class="sec-desc">
      <div class="sec-line">数据存储本机 · 单用户使用 · 无登录认证</div>
      <div v-if="isLive" class="sec-warn">接口无登录认证，请勿将服务端口暴露到公网</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ brokerType: string }>()

const isLive = computed(() => props.brokerType === 'live')
</script>

<style scoped>
.security-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sec-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sec-title {
  font-weight: 600;
  font-size: 14px;
}

.sec-desc {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sec-line {
  font-size: 12px;
  color: var(--text-2);
}

.sec-warn {
  font-size: 12px;
  color: var(--danger);
  background: var(--danger-bg);
  border-radius: 6px;
  padding: 6px 10px;
}

.security-card.live {
  border-color: var(--live);
}
</style>
