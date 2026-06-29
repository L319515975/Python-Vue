App({
  globalData: {
    baseUrl: 'http://localhost:8000/api',
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
