import { reactive } from 'vue'

export interface NetStatusState {
  online: boolean
  lastOfflineAt: number
}

export const netStatus = reactive<NetStatusState>({
  online: typeof navigator === 'undefined' ? true : navigator.onLine,
  lastOfflineAt: 0,
})

export function markOnline() {
  netStatus.online = true
}

export function markOffline() {
  if (netStatus.online) {
    netStatus.lastOfflineAt = Date.now()
  }
  netStatus.online = false
}

if (typeof window !== 'undefined') {
  window.addEventListener('online', markOnline)
  window.addEventListener('offline', markOffline)
}
