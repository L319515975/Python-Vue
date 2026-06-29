import { getAccessToken, getRefreshToken, getUserInfo, setAuth, clearAuth } from '../utils/auth'
import { userApi } from '../api/index'

const state = {
  token: getAccessToken(),
  refreshToken: getRefreshToken(),
  userInfo: getUserInfo(),
}

function isLoggedIn() {
  return !!state.token
}

function isAdmin() {
  return state.userInfo?.role === 'admin'
}

async function login(username, password) {
  const data = await userApi.login({ username, password })
  state.token = data.access
  state.refreshToken = data.refresh
  state.userInfo = data.user
  setAuth({ access: data.access, refresh: data.refresh, user: data.user })
  return data
}

async function fetchMe() {
  const data = await userApi.getMe()
  state.userInfo = data
  setAuth({ user: data })
  return data
}

function logout() {
  state.token = ''
  state.refreshToken = ''
  state.userInfo = null
  clearAuth()
}

export default {
  state,
  isLoggedIn,
  isAdmin,
  login,
  fetchMe,
  logout,
}

