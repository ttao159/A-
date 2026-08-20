<template>
  <div class="login-container">
    <div class="login-box">
      <h2 v-if="isLogin" class="title">登录</h2>
      <h2 v-else class="title">注册</h2>

      <div class="form-group">
        <label>用户名</label>
        <input
          v-model="username"
          type="text"
          placeholder="请输入用户名"
          class="input"
          :class="{ 'input-error': fieldErrors.username }"
          @keyup.enter="focusPassword"
        />
        <span v-if="fieldErrors.username" class="field-err">{{ fieldErrors.username }}</span>
      </div>

      <div class="form-group">
        <label>密码</label>
        <div class="pw-wrap">
          <input
            ref="pwInput"
            v-model="password"
            :type="showPw ? 'text' : 'password'"
            placeholder="请输入密码"
            class="input"
            :class="{ 'input-error': fieldErrors.password }"
            @keyup.enter="handleSubmit"
          />
          <button class="pw-toggle" type="button" @click="showPw = !showPw" tabindex="-1">
            <Icon :name="showPw ? 'eye-off' : 'eye'" :size="16" />
          </button>
        </div>
        <span v-if="fieldErrors.password" class="field-err">{{ fieldErrors.password }}</span>
      </div>

      <button
        class="submit-btn"
        :disabled="loading"
        @click="handleSubmit"
      >
        {{ loading ? '处理中...' : isLogin ? '登录' : '注册' }}
      </button>

      <div class="toggle-link" v-if="isLogin">
        还没有账号？<a @click="toggleMode">去注册</a>
      </div>
      <div class="toggle-link" v-else>
        已有账号？<a @click="toggleMode">去登录</a>
      </div>

      <div v-if="isLogin" class="aux-links">
        <a @click="handleForgotPw">忘记密码？</a>
        <span class="sep">|</span>
        <a @click="handleResetConfig">重置配置</a>
      </div>

      <div v-if="!isLogin" class="demo-entry">
        <button class="demo-btn" @click="handleDemo">
          体验 Demo 策略（免注册只读）
        </button>
      </div>

      <div class="error-msg" v-if="errorMsg">{{ errorMsg }}</div>

      <div class="tip">
        提示：本系统的登录仅用于保护个人配置，不涉及真实资金交易
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../api'
import { useUserStore } from '../stores/user'
import { confirmDialog } from '../utils/confirm'
import { toast } from '../utils/toast'
import Icon from '../components/Icon.vue'

const router = useRouter()
const userStore = useUserStore()
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')
const isLogin = ref(true)
const showPw = ref(false)
const pwInput = ref<HTMLInputElement | null>(null)
const fieldErrors = ref<Record<string, string>>({})

function focusPassword() {
  pwInput.value?.focus()
}

function toggleMode() {
  isLogin.value = !isLogin.value
  errorMsg.value = ''
  fieldErrors.value = {}
}

function validateFields(): boolean {
  const errs: Record<string, string> = {}
  if (!username.value.trim()) errs.username = '请输入用户名'
  if (!password.value) errs.password = '请输入密码'
  fieldErrors.value = errs
  return Object.keys(errs).length === 0
}

async function handleSubmit() {
  errorMsg.value = ''
  if (!validateFields()) return

  try {
    loading.value = true

    if (isLogin.value) {
      const data = await authApi.login(username.value.trim(), password.value)
      userStore.login(data.access_token, data.username)
      userStore.setDemo(false)
      router.push('/')
    } else {
      await authApi.register(username.value.trim(), password.value)
      isLogin.value = true
      errorMsg.value = '注册成功，请登录'
      username.value = ''
      password.value = ''
      fieldErrors.value = {}
    }
  } catch (e) {
    errorMsg.value = (e as Error).message || '网络错误'
  } finally {
    loading.value = false
  }
}

async function handleForgotPw() {
  await confirmDialog({
    title: '忘记密码',
    message: '当前版本未接邮件服务，请联系管理员重置密码。或使用下方「重置配置」清空本地数据后重新注册。',
    confirmText: '知道了',
  })
}

async function handleResetConfig() {
  const ok = await confirmDialog({
    title: '重置配置',
    message: '将清除所有本地数据（画线、持仓缓存、策略配置等），不可恢复。确认重置？',
    confirmText: '确认重置',
    danger: true,
  })
  if (!ok) return
  localStorage.clear()
  toast('配置已重置')
}

function handleDemo() {
  localStorage.setItem('token', 'demo')
  localStorage.setItem('username', 'Demo体验')
  localStorage.setItem('demo_mode', '1')
  userStore.setDemo(true)
  router.push('/')
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: var(--bg);
}

.login-box {
  background: var(--card);
  padding: 40px 32px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  width: 350px;
  max-width: 92vw;
}

.title {
  color: var(--text);
  text-align: center;
  margin-bottom: 28px;
  font-size: 22px;
  font-weight: 700;
}

.form-group {
  margin-bottom: 18px;
}

.form-group label {
  display: block;
  color: var(--text-2);
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
}

.input {
  width: 100%;
  min-height: 44px;
  padding: 0 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: var(--radius);
  font-size: 16px;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--focus-ring);
}

.input-error {
  border-color: var(--danger) !important;
  box-shadow: 0 0 0 3px rgba(245, 108, 108, 0.15);
}

.field-err {
  display: block;
  color: var(--danger);
  font-size: 12px;
  margin-top: 4px;
}

.pw-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.pw-wrap .input {
  padding-right: 38px;
}

.pw-toggle {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  color: var(--text-2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.pw-toggle:active {
  color: var(--primary);
}

.submit-btn {
  width: 100%;
  padding: 12px;
  min-height: 44px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
  transition: opacity 0.15s, transform 0.1s;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-btn:active:not(:disabled) {
  opacity: 0.85;
  transform: scale(0.97);
}

.toggle-link {
  text-align: center;
  margin-top: 16px;
  color: var(--text-2);
  font-size: 14px;
}

.toggle-link a {
  color: var(--primary);
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
}

.error-msg {
  color: var(--danger);
  margin-top: 12px;
  font-size: 14px;
  text-align: center;
  min-height: 20px;
}

.aux-links {
  text-align: center;
  margin-top: 14px;
  font-size: 13px;
  color: var(--text-2);
}

.aux-links a {
  color: var(--primary);
  cursor: pointer;
}

.aux-links .sep {
  margin: 0 8px;
  opacity: 0.4;
}

.demo-entry {
  margin-top: 14px;
  text-align: center;
}

.demo-btn {
  width: 100%;
  padding: 10px;
  min-height: 42px;
  background: none;
  border: 1px dashed var(--border);
  border-radius: var(--radius);
  color: var(--text-2);
  font-size: 14px;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.demo-btn:active {
  border-color: var(--primary);
  color: var(--primary);
}

.tip {
  margin-top: 24px;
  padding: 12px;
  background: var(--border-light);
  border-radius: var(--radius-sm);
  color: var(--text-2);
  font-size: 12px;
  text-align: center;
  line-height: 1.5;
}
</style>
