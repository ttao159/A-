<template>
  <div>
    <div class="profile-card card">
      <div class="avatar">{{ avatarChar }}</div>
      <div class="profile-info">
        <div class="profile-name">{{ userStore.username || '未登录' }}</div>
        <div class="profile-sub">
          <span class="badge" :class="userStore.isDemo ? 'paper' : 'live'">
            {{ userStore.isDemo ? 'Demo 只读' : '正式账号' }}
          </span>
          <span class="muted">{{ accountStore.isLive ? '实盘模式' : '模拟盘' }}</span>
        </div>
      </div>
    </div>

    <FoldCard title="偏好设置" icon="settings" default-open>
      <div class="setting-row">
        <div class="setting-label">
          <span>外观主题</span>
          <span class="muted">跟随系统或手动指定</span>
        </div>
        <div class="seg-group">
          <button
            v-for="opt in themeOptions"
            :key="opt.value"
            class="seg-btn"
            :class="{ active: theme.mode.value === opt.value }"
            @click="theme.setMode(opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>
    </FoldCard>

    <FoldCard title="数据管理" icon="database" default-open>
      <button class="action-row" @click="onResetAccount">
        <div class="action-text">
          <span class="action-title">重置模拟账户</span>
          <span class="muted">清空持仓与交易记录，恢复初始资金</span>
        </div>
        <Icon name="chevron-right" :size="18" class="action-chev" />
      </button>
      <button class="action-row" @click="onClearCache">
        <div class="action-text">
          <span class="action-title">清除本地缓存</span>
          <span class="muted">移除本机缓存的账户与行情数据</span>
        </div>
        <Icon name="chevron-right" :size="18" class="action-chev" />
      </button>
    </FoldCard>

    <FoldCard title="关于账号" icon="user" default-open>
      <div class="info-row"><span>登录方式</span><b>用户名密码</b></div>
      <div class="info-row"><span>注册时间</span><b>{{ createdAt || '—' }}</b></div>
      <div class="info-row"><span>版本</span><b>v{{ version }}</b></div>
    </FoldCard>

    <div class="card logout-area">
      <button class="btn danger block" @click="onLogout">
        <Icon name="log-out" :size="16" /> 退出登录
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useAccountStore } from '../stores/account'
import { useTheme, type ThemeMode } from '../composables/useTheme'
import { authApi } from '../api'
import { toast } from '../utils/toast'
import { confirmDialog } from '../utils/confirm'
import Icon from '../components/Icon.vue'
import FoldCard from '../components/FoldCard.vue'
import { version } from '../../package.json'

const router = useRouter()
const userStore = useUserStore()
const accountStore = useAccountStore()
const theme = useTheme()

const themeOptions: { value: ThemeMode; label: string }[] = [
  { value: 'system', label: '跟随系统' },
  { value: 'light', label: '浅色' },
  { value: 'dark', label: '深色' },
]

const avatarChar = computed(() => {
  const u = userStore.username || '游'
  return u.slice(0, 1).toUpperCase()
})

const createdAt = ref('')

onMounted(async () => {
  try {
    const me = await authApi.me()
    if (me.created_at) {
      const d = new Date(me.created_at)
      if (!Number.isNaN(d.getTime())) {
        createdAt.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      }
    }
  } catch {
    // Demo 模式无注册信息
  }
})

async function onResetAccount() {
  const ok = await confirmDialog({
    title: '重置模拟账户',
    message: '将清空当前持仓、交易与委托记录，资产恢复为初始资金。此操作不可撤销。',
    confirmText: '确认重置',
    danger: true,
  })
  if (!ok) return
  await accountStore.reset()
  toast('账户已重置')
}

async function onClearCache() {
  const ok = await confirmDialog({
    title: '清除本地缓存',
    message: '将移除本机缓存的账户与行情数据，下次进入将重新加载。',
    confirmText: '确认清除',
  })
  if (!ok) return
  const keys: string[] = []
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i)
    if (k && k.startsWith('cache:')) keys.push(k)
  }
  keys.forEach((k) => localStorage.removeItem(k))
  await accountStore.fetch()
  toast('缓存已清除')
}

function onLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.profile-card {
  display: flex;
  align-items: center;
  gap: 14px;
}

.avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--brand-from), var(--brand-to));
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.profile-info {
  flex: 1;
  min-width: 0;
}

.profile-name {
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 4px;
}

.profile-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.setting-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 14px;
  font-weight: 500;
}

.seg-group {
  display: flex;
  background: var(--bg);
  border-radius: 8px;
  padding: 3px;
}

.seg-btn {
  border: none;
  background: transparent;
  color: var(--text-2);
  font-size: 12px;
  padding: 5px 10px;
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
}

.seg-btn.active {
  background: var(--card);
  color: var(--primary);
  font-weight: 600;
  box-shadow: var(--shadow-sm);
}

.action-row {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 0;
  border: none;
  background: none;
  cursor: pointer;
  text-align: left;
  border-bottom: 1px solid var(--border-light);
}

.action-row:last-child {
  border-bottom: none;
}

.action-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.action-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
}

.action-chev {
  color: var(--text-3);
  flex-shrink: 0;
}

.logout-area {
  padding: var(--spacing-md);
}

.block {
  width: 100%;
  justify-content: center;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-light);
}

.info-row:last-child {
  border-bottom: none;
}
</style>
