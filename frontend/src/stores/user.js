/**
 * 用户状态管理（Pinia Store）—— 管理全局的用户认证状态。
 *
 * 作用：在应用的任何组件中都能访问和修改用户状态（登录信息、token 等）。
 *
 * 知识点（Pinia 状态管理）：
 * - defineStore()：定义一个 Store（状态仓库）
 * - ref()：响应式数据（类似 Vue 组件中的 data）
 * - computed()：计算属性（自动根据依赖数据计算）
 * - function：Store 中的方法（类似 Vue 组件中的 methods）
 * - localStorage：浏览器本地存储，关闭浏览器后数据仍然保留
 *
 * 为什么需要状态管理？
 * 在 Vue 中，组件之间共享数据很麻烦（需要层层传递）。
 * Pinia 让我们可以在任何组件中直接访问和修改全局状态。
 *
 * 本 Store 管理：
 * - token：JWT 访问令牌（登录凭证）
 * - refreshToken：JWT 刷新令牌（用于续期 token）
 * - userInfo：用户信息（用户名、角色等）
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'

export const useUserStore = defineStore('user', () => {
  // ========== 状态（响应式数据） ==========

  // JWT 访问令牌 —— 从 localStorage 恢复（页面刷新后保持登录状态）
  const token = ref(localStorage.getItem('access_token') || '')
  // JWT 刷新令牌 —— 用于在 access_token 过期后获取新令牌
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  // 用户信息 —— 从 localStorage 恢复并解析 JSON
  const userInfo = ref(JSON.parse(localStorage.getItem('user_info') || 'null'))

  // ========== 计算属性 ==========

  // 是否已登录（token 有值则为已登录）
  const isLoggedIn = computed(() => !!token.value)
  // 是否是管理员（role === 'admin'）
  const isAdmin = computed(() => userInfo.value?.role === 'admin')
  // 当前用户名
  const username = computed(() => userInfo.value?.username || '')

  // ========== 方法 ==========

  /**
   * 保存 JWT 令牌。
   * 同时更新响应式数据和 localStorage（确保刷新后不丢失）。
   */
  function setTokens(access, refresh) {
    token.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  /**
   * 保存用户信息。
   * localStorage 只能存字符串，所以需要用 JSON.stringify 转换。
   */
  function setUserInfo(info) {
    userInfo.value = info
    localStorage.setItem('user_info', JSON.stringify(info))
  }

  /**
   * 登录 —— 向后端发送用户名和密码，获取令牌和用户信息。
   * 流程：
   * 1. 发送 POST 请求到 /users/login/
   * 2. 后端验证用户名密码，返回 access_token、refresh_token 和 user 信息
   * 3. 保存令牌和用户信息
   */
  async function login(username, password) {
    const data = await request.post('/users/login/', { username, password })
    setTokens(data.access, data.refresh)
    setUserInfo(data.user)
    return data
  }

  /**
   * 获取最新用户信息 —— 用于刷新用户数据。
   * 例如：用户修改了个人信息后，需要重新获取最新数据。
   */
  async function fetchUserInfo() {
    const data = await request.get('/users/me/')
    setUserInfo(data)
    return data
  }

  /**
   * 退出登录 —— 清除所有认证信息。
   * 同时清除响应式数据和 localStorage。
   */
  function logout() {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  }

  // 返回所有状态和方法，供组件使用
  return {
    token, refreshToken, userInfo,
    isLoggedIn, isAdmin, username,
    setTokens, setUserInfo, login, fetchUserInfo, logout,
  }
})