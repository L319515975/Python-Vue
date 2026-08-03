const TOKEN_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'
const USER_KEY = 'user_info'

function safeGet(key, fallback = '') {
  try {
    return wx.getStorageSync(key) || fallback
  } catch (error) {
    return fallback
  }
}

function safeSet(key, value) {
  try {
    wx.setStorageSync(key, value)
  } catch (error) {}
}

function safeRemove(key) {
  try {
    wx.removeStorageSync(key)
  } catch (error) {}
}

function getAccessToken() {
  return safeGet(TOKEN_KEY, '')
}

function getRefreshToken() {
  return safeGet(REFRESH_KEY, '')
}

function getUserInfo() {
  return safeGet(USER_KEY, null)
}

function setAuth({ access, refresh, user }) {
  if (access) safeSet(TOKEN_KEY, access)
  if (refresh) safeSet(REFRESH_KEY, refresh)
  if (user) safeSet(USER_KEY, user)
}

function clearAuth() {
  safeRemove(TOKEN_KEY)
  safeRemove(REFRESH_KEY)
  safeRemove(USER_KEY)
}

export {
  TOKEN_KEY,
  REFRESH_KEY,
  USER_KEY,
  getAccessToken,
  getRefreshToken,
  getUserInfo,
  setAuth,
  clearAuth,
}

