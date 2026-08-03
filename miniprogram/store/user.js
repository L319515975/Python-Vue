import { getAccessToken, getRefreshToken, getUserInfo, setAuth, clearAuth } from '../utils/auth'
import { userApi } from '../api/index'

const state = {
  token: getAccessToken(),
  refreshToken: getRefreshToken(),
  userInfo: getUserInfo(),
}

function syncAppUser(userInfo) {
  try {
    const app = getApp()
    if (app && app.globalData) {
      app.globalData.userInfo = userInfo || null
    }
  } catch (error) {
    void error
  }
}

function extractPayload(response) {
  if (!response || typeof response !== 'object') return {}

  const directKeys = [
    'access',
    'refresh',
    'token',
    'access_token',
    'refresh_token',
    'user',
    'userInfo',
    'user_info',
    'profile',
  ]

  for (let index = 0; index < directKeys.length; index += 1) {
    if (Object.prototype.hasOwnProperty.call(response, directKeys[index])) {
      return response
    }
  }

  if (response.data && typeof response.data === 'object') return response.data
  if (response.result && typeof response.result === 'object') return response.result
  if (response.payload && typeof response.payload === 'object') return response.payload
  return response
}

function normalizeLoginResponse(response) {
  const payload = extractPayload(response)
  return {
    access: payload.access || payload.access_token || payload.token || '',
    refresh: payload.refresh || payload.refresh_token || payload.refreshToken || '',
    user: payload.user || payload.userInfo || payload.user_info || payload.profile || null,
  }
}

function binaryToUtf8(binaryText) {
  let percentEncoded = ''

  for (let index = 0; index < binaryText.length; index += 1) {
    const hex = binaryText.charCodeAt(index).toString(16)
    percentEncoded += '%' + (hex.length === 1 ? '0' + hex : hex)
  }

  try {
    return decodeURIComponent(percentEncoded)
  } catch (error) {
    void error
    return binaryText
  }
}

function decodeBase64Url(base64Text) {
  if (!base64Text) return ''
  const normalized = base64Text.replace(/-/g, '+').replace(/_/g, '/')
  const padding = normalized.length % 4
  const padded = normalized + (padding ? '='.repeat(4 - padding) : '')

  try {
    if (typeof wx !== 'undefined' && typeof wx.base64ToArrayBuffer === 'function') {
      const arrayBuffer = wx.base64ToArrayBuffer(padded)
      const bytes = new Uint8Array(arrayBuffer)
      let binaryText = ''
      for (let index = 0; index < bytes.length; index += 1) {
        binaryText += String.fromCharCode(bytes[index])
      }
      return binaryToUtf8(binaryText)
    }
  } catch (error) {
    void error
  }

  try {
    if (typeof atob === 'function') {
      return binaryToUtf8(atob(padded))
    }
  } catch (error) {
    void error
  }

  return ''
}

function decodeJwtPayload(token) {
  if (!token || typeof token !== 'string') return null

  const parts = token.split('.')
  if (parts.length < 2) return null

  const jsonText = decodeBase64Url(parts[1])
  if (!jsonText) return null

  try {
    return JSON.parse(jsonText)
  } catch (error) {
    void error
    return null
  }
}

function buildUserFromToken(token) {
  const payload = decodeJwtPayload(token)
  if (!payload) return null

  return {
    id: payload.user_id || payload.userId || payload.sub || null,
    username: payload.username || '',
    role: payload.role || 'user',
  }
}

function isLoggedIn() {
  return !!state.token
}

function isAdmin() {
  return state.userInfo && state.userInfo.role === 'admin'
}

async function fetchMe() {
  const data = await userApi.getMe()
  state.userInfo = data
  setAuth({ user: data })
  syncAppUser(data)
  return data
}

function refreshMeInBackground() {
  fetchMe().catch(function () {})
}

async function login(username, password) {
  const response = await userApi.login({ username, password })
  const normalized = normalizeLoginResponse(response)

  if (!normalized.access) {
    throw new Error('登录成功，但接口未返回令牌')
  }

  state.token = normalized.access
  state.refreshToken = normalized.refresh

  const resolvedUser = normalized.user || buildUserFromToken(normalized.access)
  if (resolvedUser) {
    state.userInfo = resolvedUser
    setAuth({ access: normalized.access, refresh: normalized.refresh, user: resolvedUser })
    syncAppUser(resolvedUser)
    refreshMeInBackground()
    return resolvedUser
  }

  setAuth({ access: normalized.access, refresh: normalized.refresh })

  try {
    const me = await fetchMe()
    return me
  } catch (error) {
    void error
    const fallbackUser = { role: 'user' }
    state.userInfo = fallbackUser
    setAuth({ user: fallbackUser })
    syncAppUser(fallbackUser)
    refreshMeInBackground()
    return fallbackUser
  }
}

function logout() {
  state.token = ''
  state.refreshToken = ''
  state.userInfo = null
  clearAuth()
  syncAppUser(null)
}

export default {
  state,
  isLoggedIn,
  isAdmin,
  login,
  fetchMe,
  logout,
}
