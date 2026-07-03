import userStore from '../../store/user'

function launchPage(url) {
  return new Promise(function (resolve, reject) {
    wx.reLaunch({
      url: url,
      success: resolve,
      fail: reject,
    })
  })
}

async function navigateAfterLogin(primaryUrl, fallbackUrl) {
  try {
    await launchPage(primaryUrl)
    return
  } catch (primaryError) {
    if (fallbackUrl) {
      await launchPage(fallbackUrl)
      return
    }
    throw primaryError
  }
}

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
    const username = (this.data.username || '').trim()
    const password = this.data.password || ''

    if (!username || !password) {
      wx.showToast({ title: '请输入账号和密码', icon: 'none' })
      return
    }

    if (this.data.loading) return

    this.setData({ loading: true })
    try {
      const userInfo = await userStore.login(username, password)
      const isAdmin = userInfo && userInfo.role === 'admin'
      const primaryUrl = isAdmin
        ? '/pages/admin/dashboard/index'
        : '/pages/user/resume-detail/index'
      const fallbackUrl = isAdmin
        ? '/pages/admin/user-manage/index'
        : '/pages/user/resume-edit/index'

      await navigateAfterLogin(primaryUrl, fallbackUrl)
    } catch (error) {
      wx.showToast({ title: error.message || '登录失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },
})
