<template>
  <div class="notif-wrap">
    <button
      class="bell-btn"
      aria-label="消息通知"
      :class="{ active: open }"
      @click="toggle"
    >
      <Icon name="bell" :size="18" />
      <span v-if="store.unreadCount > 0" class="badge">{{ store.unreadCount > 99 ? '99+' : store.unreadCount }}</span>
    </button>

    <Transition name="notif-drop">
      <div v-if="open" class="notif-panel">
        <div class="notif-head">
          <span class="notif-title">消息通知</span>
          <button v-if="store.unreadCount > 0" class="mark-read" @click="store.markAllRead()">全部已读</button>
        </div>
        <div v-if="store.loading && store.notifications.length === 0" class="notif-empty">加载中...</div>
        <div v-else-if="store.notifications.length === 0" class="notif-empty">
          <Icon name="bell" :size="28" />
          <p>暂无通知</p>
        </div>
        <ul v-else class="notif-list">
          <li
            v-for="n in store.notifications"
            :key="n.id"
            class="notif-item"
            :class="{ unread: !n.read }"
            @click="store.markRead(n.id)"
          >
            <span class="notif-dot" :class="n.category"></span>
            <div class="notif-body">
              <div class="notif-row">
                <span class="notif-tag">{{ n.category }}</span>
                <span class="notif-time">{{ formatTime(n.time) }}</span>
              </div>
              <div class="notif-title-text">{{ n.title }}</div>
              <div class="notif-content">{{ n.content }}</div>
            </div>
          </li>
        </ul>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useNotificationStore } from '../stores/notification'
import Icon from './Icon.vue'

const store = useNotificationStore()
const open = ref(false)

function toggle() {
  open.value = !open.value
  if (open.value) store.sync()
}

function close() {
  open.value = false
}

function formatTime(t: string) {
  if (!t) return ''
  const d = new Date(t)
  if (Number.isNaN(d.getTime())) return t
  const now = new Date()
  const sameDay = d.toDateString() === now.toDateString()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return sameDay ? `${hh}:${mm}` : `${d.getMonth() + 1}/${d.getDate()} ${hh}:${mm}`
}

onMounted(() => {
  store.sync()
  document.addEventListener('click', onDocClick)
})

function onDocClick(e: MouseEvent) {
  const wrap = (e.target as HTMLElement).closest('.notif-wrap')
  if (!wrap) close()
}
</script>

<style scoped>
.notif-wrap {
  position: relative;
}

.bell-btn {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text-2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.bell-btn:active,
.bell-btn.active {
  color: var(--primary);
  border-color: var(--primary);
  transform: scale(0.92);
}

.badge {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  background: var(--danger);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
}

.notif-panel {
  position: absolute;
  top: 52px;
  right: -60px;
  width: 300px;
  max-height: 420px;
  overflow: hidden;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.16);
  z-index: 60;
  display: flex;
  flex-direction: column;
}

.notif-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.notif-title {
  font-size: 14px;
  font-weight: 700;
}

.mark-read {
  border: none;
  background: none;
  color: var(--primary);
  font-size: 12px;
  cursor: pointer;
  padding: 4px;
}

.notif-empty {
  padding: 28px 16px;
  text-align: center;
  color: var(--text-3);
  font-size: 13px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.notif-list {
  list-style: none;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  max-height: 340px;
}

.notif-item {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  cursor: pointer;
  transition: background 0.15s;
}

.notif-item:hover {
  background: var(--card-hover);
}

.notif-item.unread {
  background: var(--focus-ring);
}

.notif-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
}

.notif-dot.交易通知 {
  background: var(--primary);
}

.notif-dot.预警提醒 {
  background: var(--warning);
}

.notif-dot.系统消息 {
  background: var(--down);
}

.notif-body {
  flex: 1;
  min-width: 0;
}

.notif-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.notif-tag {
  font-size: 11px;
  color: var(--primary);
  font-weight: 600;
}

.notif-time {
  font-size: 11px;
  color: var(--text-3);
}

.notif-title-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 2px;
}

.notif-content {
  font-size: 12px;
  color: var(--text-2);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.notif-drop-enter-active,
.notif-drop-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.notif-drop-enter-from,
.notif-drop-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
