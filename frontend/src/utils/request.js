/**
 * HTTP 请求工具 —— 封装 Axios，处理所有与后端的通信。
 *
 * 作用：
 * 1. 统一配置请求的基础 URL、超时时间
 * 2. 自动在请求头中附加 JWT 令牌（实现登录认证）
 * 3. 统一处理响应错误（401未授权、403禁止访问等）
 * 4. 自动尝试刷新过期的 JWT 令牌
 *
 * 知识点（Axios）：
 * - axios.create()：创建一个 Axios 实例，配置默认值
 * - 请求拦截器（request interceptor）：在每个请求发出前执行
 * - 响应拦截器（response interceptor）：在每个响应返回后执行
 *
 * 知识点（JWT 认证流程）：
 * 1. 用户登录后，后端返回 access_token（短期有效）和 refresh_token（长期有效）
 * 2. 每次请求时，在请求头中附加 access_token
 * 3. 如果 access_token 过期（401错误），用 refresh_token 获取新的 access_token
 * 4. 如果 refresh_token 也过期了，重定向到登录页
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'  // Element Plus 的消息提示组件
import router from '@/router'

// 创建 Axios 实例，配置默认值
const request = axios.create({
  baseURL: '/api',       // 所有请求的基础路径（通过 Vite 代理到后端）
  timeout: 30000,        // 请求超时时间：30秒
  headers: {
    'Content-Type': 'application/json',  // 默认发送 JSON 格式数据
  },
})

/**
 * 请求拦截器 —— 在每个请求发出前自动执行。
 *
 * 作用：从 localStorage 读取 JWT 令牌，附加到请求头中。
 * 格式：Authorization: Bearer <token>
 *
 * 这样后端就能识别请求者是谁，实现"已登录"状态。
 */
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

/**
 * 响应拦截器 —— 在每个响应返回后自动执行。
 *
 * 成功时：直接返回 response.data（跳过 Axios 包装层）
 * 失败时：根据 HTTP 状态码进行不同处理
 *
 * 状态码含义：
 * - 401：未授权（token 过期或无效）→ 尝试刷新 token
 * - 403：禁止访问（权限不足）
 * - 404：资源不存在
 * - 500+：服务器错误
 */
request.interceptors.response.use(
  // 成功回调：直接返回数据部分（省去每次都要写 .data）
  (response) => response.data,
  // 错误回调：统一处理各种错误情况
  async (error) => {
    const { response } = error

    // 网络错误（后端未启动或网络断开）
    if (!response) {
      ElMessage.error('网络错误，请检查后端服务是否启动')
      return Promise.reject(error)
    }

    const { status, data } = response

    if (status === 401) {
      // 401 未授权：尝试用 refresh_token 获取新的 access_token
      const refreshToken = localStorage.getItem('refresh_token')
      // _retry 标志防止无限重试（只尝试刷新一次）
      if (refreshToken && !error.config._retry) {
        error.config._retry = true
        try {
          // 使用 refresh_token 请求新的 access_token
          const res = await axios.post('/api/users/token/refresh/', {
            refresh: refreshToken,
          })
          // 保存新的令牌
          localStorage.setItem('access_token', res.data.access)
          if (res.data.refresh) {
            localStorage.setItem('refresh_token', res.data.refresh)
          }
          // 用新令牌重试原来的请求
          error.config.headers.Authorization = `Bearer ${res.data.access}`
          return request(error.config)
        } catch {
          // 刷新失败 → 令牌全部失效，清除并跳转登录页
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          router.push('/login')
          ElMessage.error('登录已过期，请重新登录')
          return Promise.reject(error)
        }
      }
      // 没有 refresh_token 或已重试过，直接跳转登录页
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
      // 其他错误：显示后端返回的错误信息
      const msg = data?.detail || data?.message || '请求失败'
      ElMessage.error(msg)
    }

    return Promise.reject(error)
  }
)

export default request