App({
  globalData: {
    // 与 utils/config.js 保持一致，便于页面调试时统一修改
    baseUrl: 'http://127.0.0.1:8000/api',
    userInfo: null,
  },

  onLaunch() {
    try {
      const token = wx.getStorageSync('access_token')
      const user = wx.getStorageSync('user_info')
      if (token && user) {
        this.globalData.userInfo = user
      }
    } catch (error) {}
  },
})
