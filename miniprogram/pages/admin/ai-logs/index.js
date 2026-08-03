import { aiApi } from '../../../api/index'

Page({
  data: { logs: [], loading: false, tab: 'chat' },

  onLoad() {
    this.loadLogs()
  },

  switchTab(e) {
    this.setData({ tab: e.currentTarget.dataset.tab }, () => this.loadLogs())
  },

  getApiByTab() {
    if (this.data.tab === 'chat') return aiApi.logs
    if (this.data.tab === 'polish') return aiApi.polishLogs
    return aiApi.classificationLogs
  },

  async loadLogs() {
    this.setData({ loading: true })
    try {
      const api = this.getApiByTab()
      const res = await api({ page_size: 100 })
      this.setData({ logs: Array.isArray(res) ? res : (res.results || []) })
    } catch (error) {
      wx.showToast({ title: error.message || '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },
})
