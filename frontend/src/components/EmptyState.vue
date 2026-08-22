<template>
  <div class="empty-state">
    <div class="empty-state-icon">
      <Icon :name="icon" :size="26" />
    </div>
    <div class="empty-state-title">{{ title }}</div>
    <div v-if="desc" class="empty-state-desc">{{ desc }}</div>
    <slot />
  </div>
</template>

<script setup lang="ts">
import Icon from './Icon.vue'

withDefaults(defineProps<{ icon?: string; title: string; desc?: string }>(), {
  icon: 'info',
})
</script>

<style scoped>
.empty-state {
  text-align: center;
  color: var(--text-2);
  padding: 40px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.empty-state-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-3);
  margin-bottom: 4px;
}

.empty-state-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.empty-state-desc {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-2);
  max-width: 260px;
}
</style>
