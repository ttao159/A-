import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const isDemo = ref(localStorage.getItem('demo_mode') === '1')

  const isAuthenticated = computed(() => !!token.value)

  function login(t: string, u: string) {
    token.value = t
    username.value = u
    localStorage.setItem('token', t)
    localStorage.setItem('username', u)
  }

  function setDemo(d: boolean) {
    isDemo.value = d
    if (d) {
      localStorage.setItem('demo_mode', '1')
    } else {
      localStorage.removeItem('demo_mode')
    }
  }

  function logout() {
    token.value = ''
    username.value = ''
    isDemo.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('demo_mode')
  }

  return { token, username, isDemo, isAuthenticated, login, setDemo, logout }
})