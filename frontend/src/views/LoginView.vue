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
  background: #1a1a2e;
}

.login-box {
  background: #16213e;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  width: 350px;
}

.title {
  color: #e0e0e0;
  text-align: center;
  margin-bottom: 30px;
  font-size: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  color: #a0a0a0;
  margin-bottom: 8px;
  font-size: 14px;
}

.input {
  width: 100%;
  padding: 10px 12px;
  background: #1e2a47;
  border: 1px solid #2d3748;
  color: #fff;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.input:focus {
  border-color: #4a9eff;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #4a9eff;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  margin-top: 10px;
}

.submit-btn:disabled {
  background: #666;
  cursor: not-allowed;
}

.submit-btn:hover:not(:disabled) {
  background: #3a8eef;
}

.toggle-link {
  text-align: center;
  margin-top: 15px;
  color: #a0a0a0;
  font-size: 14px;
}

.toggle-link a {
  color: #4a9eff;
  cursor: pointer;
  text-decoration: none;
}

.error-msg {
  color: #ff4757;
  margin-top: 10px;
  font-size: 14px;
  text-align: center;
}

.tip {
  margin-top: 20px;
  padding: 10px;
  background: rgba(74, 158, 255, 0.1);
  border-radius: 6px;
  color: #88c0d0;
  font-size: 12px;
  text-align: center;
}
</style>
