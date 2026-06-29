import { auditLogApi } from '../../../api/index'

Page({
  data: { logs: [], loading: false, searchAction: '' },

  onLoad() {
    this.loadLogs()
  },

  onActionInput(e) {
    this.setData({ searchAction: e.detail.value })
  },

  async loadLogs() {
    this.setData({ loading: true })
    try {
      const params = { page_size: 100 }
      if (this.data.searchAction) params.action = this.data.searchAction
      const res = await auditLogApi.list(params)
      this.setData({ logs: Array.isArray(res) ? res : (res.results || []) })
    } catch (error) {
      wx.showToast({ title: error.message || '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },
})
