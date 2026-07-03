import { visitorAiUsageApi } from '../../../api/index'

Page({
  data: { logs: [], loading: false, searchUsername: '' },

  onLoad() {
    this.loadLogs()
  },

  onSearchInput(e) {
    this.setData({ searchUsername: e.detail.value })
  },

  async loadLogs() {
    this.setData({ loading: true })
    try {
      const params = { page_size: 100 }
      if (this.data.searchUsername) params.username = this.data.searchUsername
      const res = await visitorAiUsageApi.list(params)
      this.setData({ logs: Array.isArray(res) ? res : (res.results || []) })
    } catch (error) {
      wx.showToast({ title: error.message || '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },
})
