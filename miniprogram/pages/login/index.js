import { userApi } from '../../api/index'
import userStore from '../../store/user'
import { setAuth } from '../../utils/auth'

Page({
  data: { username: '', password: '', loading: false },

  onUsernameInput(e) {
    this.setData({ username: e.detail.value })
  },

  onPasswordInput(e) {
    this.setData({ password: e.detail.value })
  },

  fillAdmin() {
    this.setData({ username: 'admin', password: 'admin123' })
  },

  fillUser() {
    this.setData({ username: 'zhangsan', password: 'user123' })
  },

  async handleLogin() {
    if (!this.data.username || !this.data.password) {
      wx.showToast({ title: '请输入账号密码', icon: 'none' })
      return
    }

    this.setData({ loading: true })
    try {
      const data = await userApi.login({ username: this.data.username, password: this.data.password })
      userStore.state.token = data.access
      userStore.state.refreshToken = data.refresh
      userStore.state.userInfo = data.user
      setAuth({ access: data.access, refresh: data.refresh, user: data.user })
      const target = data.user && data.user.role === 'admin'
        ? '/pages/admin/dashboard/index'
        : '/pages/user/resume-detail/index'
      wx.reLaunch({ url: target })
    } catch (error) {
      wx.showToast({ title: error.message || '登录失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  }
})
