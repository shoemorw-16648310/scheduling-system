import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

const TOKEN_KEY = 'schedule_token'
const USER_KEY = 'schedule_user'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const userInfo = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')
  const displayName = computed(() => userInfo.value?.real_name || userInfo.value?.username || '未登录')

  const login = async (username, password) => {
    const res = await authApi.login(username, password)
    token.value = res.access_token
    userInfo.value = res.user
    localStorage.setItem(TOKEN_KEY, res.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(res.user))
    return res
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  const fetchUserInfo = async () => {
    try {
      const user = await authApi.getMe()
      userInfo.value = user
      localStorage.setItem(USER_KEY, JSON.stringify(user))
      return user
    } catch (e) {
      logout()
      throw e
    }
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    displayName,
    login,
    logout,
    fetchUserInfo,
  }
})
