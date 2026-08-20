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
        />
      </div>
      
      <div class="form-group">
        <label>密码</label>
        <input
          v-model="password"
          type="password"
          placeholder="请输入密码"
          class="input"
          @keyup.enter="handleSubmit"
        />
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

const router = useRouter()
const userStore = useUserStore()
const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')
const isLogin = ref(true)

function toggleMode() {
  isLogin.value = !isLogin.value
  errorMsg.value = ''
}

async function handleSubmit() {
  errorMsg.value = ''
  
  if (!username.value.trim()) {
    errorMsg.value = '请输入用户名'
    return
  }
  if (!password.value) {
    errorMsg.value = '请输入密码'
    return
  }
  
  try {
    loading.value = true
    
    if (isLogin.value) {
      const data = await authApi.login(username.value.trim(), password.value)
      userStore.login(data.access_token, data.username)
      router.push('/')
    } else {
      await authApi.register(username.value.trim(), password.value)
      isLogin.value = true
      errorMsg.value = '注册成功，请登录'
      username.value = ''
      password.value = ''
    }
  } catch (e) {
    errorMsg.value = (e as Error).message || '网络错误'
  } finally {
    loading.value = false
  }
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
  font-size: 15px;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--focus-ring);
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
