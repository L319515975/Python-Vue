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
  data: {
    username: '',
    password: '',
    loading: false,
    ready: false,
    showPassword: false,
    passwordSuffix: '\u663e\u793a',
    usernameFocused: false,
    passwordFocused: false,
    passwordAutoFocus: false,
    skeletonRows: [
      [
        { type: 'circle', size: '88rpx', marginRight: '20rpx' },
        { width: '56%', height: '32rpx', marginBottom: '12rpx' },
      ],
      [{ width: '74%', height: '24rpx' }],
      [{ width: '100%', height: '96rpx', borderRadius: '18rpx' }],
      [{ width: '100%', height: '96rpx', borderRadius: '18rpx' }],
      [{ width: '100%', height: '96rpx', borderRadius: '18rpx' }],
      [
        { width: '48%', height: '80rpx', borderRadius: '18rpx', marginRight: '14rpx' },
        { width: '48%', height: '80rpx', borderRadius: '18rpx' },
      ],
    ],
  },

  onReady() {
    this.readyTimer = setTimeout(() => {
      this.setData({ ready: true })
    }, 180)
  },

  onUnload() {
    if (this.readyTimer) {
      clearTimeout(this.readyTimer)
      this.readyTimer = null
    }
  },

  onUsernameChange(e) {
    this.setData({ username: e.detail.value })
  },

  onUsernameFocus() {
    this.setData({ usernameFocused: true, passwordFocused: false })
  },

  onUsernameBlur(e) {
    this.setData({
      usernameFocused: false,
      username: (e.detail.value || '').trim(),
    })
  },

  onPasswordChange(e) {
    this.setData({ password: e.detail.value })
  },

  onPasswordFocus() {
    this.setData({ passwordFocused: true, passwordAutoFocus: false })
  },

  onPasswordBlur() {
    this.setData({ passwordFocused: false, passwordAutoFocus: false })
  },

  focusPassword() {
    this.setData({
      usernameFocused: false,
      passwordFocused: true,
      passwordAutoFocus: true,
    })

    wx.nextTick(() => {
      this.setData({ passwordAutoFocus: false })
    })
  },

  clearUsername() {
    this.setData({ username: '' })
  },

  clearPassword() {
    this.setData({ password: '' })
  },

  togglePasswordVisible() {
    const showPassword = !this.data.showPassword
    this.setData({
      showPassword,
      passwordSuffix: showPassword ? '\u9690\u85cf' : '\u663e\u793a',
    })
  },

  fillAdmin() {
    this.setData({
      username: 'admin',
      password: 'admin123',
      showPassword: false,
      passwordSuffix: '\u663e\u793a',
    })
  },

  fillUser() {
    this.setData({
      username: 'zhangsan',
      password: 'user123',
      showPassword: false,
      passwordSuffix: '\u663e\u793a',
    })
  },

  async handleLogin() {
    const username = (this.data.username || '').trim()
    const password = this.data.password || ''

    if (!username || !password) {
      wx.showToast({ title: '\u8bf7\u8f93\u5165\u8d26\u53f7\u548c\u5bc6\u7801', icon: 'none' })
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
      wx.showToast({ title: error.message || '\u767b\u5f55\u5931\u8d25', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },
})
