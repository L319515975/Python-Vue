import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - attach JWT token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors
request.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const { response } = error

    if (!response) {
      ElMessage.error('网络错误，请检查后端服务是否启动')
      return Promise.reject(error)
    }

    const { status, data } = response

    if (status === 401) {
      // Try refresh token
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && !error.config._retry) {
        error.config._retry = true
        try {
          const res = await axios.post('/api/users/token/refresh/', {
            refresh: refreshToken,
          })
          localStorage.setItem('access_token', res.data.access)
          if (res.data.refresh) {
            localStorage.setItem('refresh_token', res.data.refresh)
          }
          error.config.headers.Authorization = `Bearer ${res.data.access}`
          return request(error.config)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          router.push('/login')
          ElMessage.error('登录已过期，请重新登录')
          return Promise.reject(error)
        }
      }
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      router.push('/login')
      ElMessage.error('请先登录')
    } else if (status === 403) {
      ElMessage.error('没有权限执行此操作')
    } else if (status === 404) {
      ElMessage.error('请求的资源不存在')
    } else if (status >= 500) {
      ElMessage.error('服务器错误，请稍后重试')
    } else {
      const msg = data?.detail || data?.message || '请求失败'
      ElMessage.error(msg)
    }

    return Promise.reject(error)
  }
)

export default request
