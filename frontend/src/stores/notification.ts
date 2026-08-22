import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { alertApi, type Alert } from '../api'

export interface Notification {
  id: number
  category: '交易通知' | '预警提醒' | '系统消息'
  title: string
  content: string
  time: string
  read: boolean
}

function alertToNotification(a: Alert): Notification {
  const profit = a.type === 'profit' || a.type === 'take_profit' || a.type === 'breakout'
  return {
    id: a.id,
    category: '预警提醒',
    title: profit ? '盈利预警触发' : '风险预警触发',
    content: `${a.name} (${a.code})：${a.message}`,
    time: a.created_at || '',
    read: false,
  }
}

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref<Notification[]>([])
  const loading = ref(false)
  const lastSynced = ref(0)

  const unreadCount = computed(() => notifications.value.filter((n) => !n.read).length)

  async function sync() {
    loading.value = true
    try {
      const alerts = await alertApi.list(50)
      const converted = alerts.map(alertToNotification)
      const seen = new Set(notifications.value.map((n) => `alert:${n.id}`))
      const fresh = converted.filter((n) => !seen.has(`alert:${n.id}`))
      notifications.value = [...fresh, ...notifications.value].slice(0, 100)
      lastSynced.value = Date.now()
    } catch {
      // 同步失败保持现状
    } finally {
      loading.value = false
    }
  }

  function markAllRead() {
    notifications.value.forEach((n) => (n.read = true))
  }

  function markRead(id: number) {
    const n = notifications.value.find((x) => x.id === id)
    if (n) n.read = true
  }

  return { notifications, loading, unreadCount, lastSynced, sync, markAllRead, markRead }
})
