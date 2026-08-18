<template>
  <div class="card fold-card">
    <button class="fold-head" @click="toggle">
      <Icon v-if="icon" :name="icon" :size="16" class="fold-icon" />
      <span class="fold-title">{{ title }}</span>
      <span v-if="count !== undefined && count !== null" class="fold-count">{{ count }}</span>
      <Icon :name="open ? 'chevron-up' : 'chevron-down'" :size="18" class="fold-chev" />
    </button>
    <Transition name="fold">
      <div v-show="open" class="fold-body">
        <slot />
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import Icon from './Icon.vue'

const props = withDefaults(
  defineProps<{
    title: string
    icon?: string
    count?: string | number
    defaultOpen?: boolean
    persistKey?: string
  }>(),
  { defaultOpen: true },
)

const storageKey = props.persistKey ? `fold:${props.persistKey}` : null
const stored = storageKey ? localStorage.getItem(storageKey) : null
const open = ref(stored !== null ? stored === '1' : props.defaultOpen)

function toggle() {
  open.value = !open.value
  if (storageKey) localStorage.setItem(storageKey, open.value ? '1' : '0')
}
</script>

<style scoped>
.fold-card {
  padding: 0;
  overflow: hidden;
}

.fold-head {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  border: none;
  background: none;
  color: var(--text);
  font-size: 15px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.fold-head:active {
  opacity: 0.7;
}

.fold-icon {
  color: var(--primary);
}

.fold-count {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-2);
  background: var(--bg);
  padding: 1px 8px;
  border-radius: 10px;
}

.fold-chev {
  margin-left: auto;
  color: var(--text-2);
}

.fold-body {
  padding: 0 16px 14px;
}

.fold-body :deep(.card) {
  margin: 0 0 10px;
}

.fold-body :deep(.card:last-child) {
  margin-bottom: 0;
}

.fold-enter-active,
.fold-leave-active {
  transition: opacity 0.18s ease;
}

.fold-enter-from,
.fold-leave-to {
  opacity: 0;
}
</style>
