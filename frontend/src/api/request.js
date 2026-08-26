import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

// 请求拦截器：附加token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('schedule_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const status = error.response?.status
    const msg = error.response?.data?.detail || error.message || '请求失败'
    const url = error.config?.url || ''

    if (status === 401) {
      // 登录接口的 401 是用户名密码错误，不要当作 token 过期处理
      if (url.includes('/auth/login')) {
        ElMessage.error(msg)
      } else {
        // token过期或未登录，清除并跳转到登录页
        localStorage.removeItem('schedule_token')
        localStorage.removeItem('schedule_user')
        ElMessage.error('登录已过期，请重新登录')
        router.push('/login')
      }
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default request
