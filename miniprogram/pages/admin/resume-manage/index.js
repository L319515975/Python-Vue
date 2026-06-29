import { resumeApi } from '../../../api/index'

Page({
  data: { resumes: [], searchKey: '', loading: false, filterStatus: '', editFormVisible: false, form: { title: '', summary: '', status: 'draft' }, editId: null },

  onLoad() {
    this.loadResumes()
  },

  onSearchInput(e) {
    this.setData({ searchKey: e.detail.value })
  },

  openCreate() {
    this.setData({ editFormVisible: true, editId: null, form: { title: '', summary: '', status: 'draft' } })
  },

  openEdit(e) {
    const id = Number(e.currentTarget.dataset.id)
    const item = this.data.resumes.find(function (resume) { return Number(resume.id) === id })
    if (!item) return
    this.setData({ editFormVisible: true, editId: item.id, form: { title: item.title || '', summary: item.summary || '', status: item.status || 'draft' } })
  },

  closeForm() {
    this.setData({ editFormVisible: false })
  },

  onFormInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ ['form.' + field]: e.detail.value })
  },

  onStatusChange(e) {
    const statuses = ['draft', 'published', 'archived']
    this.setData({ ['form.status']: statuses[Number(e.detail.value)] || 'draft' })
  },

  async saveResume() {
    const form = this.data.form
    if (!form.title.trim()) {
      wx.showToast({ title: '请输入标题', icon: 'none' })
      return
    }
    try {
      const payload = { title: form.title.trim(), summary: form.summary.trim(), status: form.status }
      if (this.data.editId) {
        await resumeApi.update(this.data.editId, payload)
        wx.showToast({ title: '已更新', icon: 'success' })
      } else {
        await resumeApi.create(payload)
        wx.showToast({ title: '已创建', icon: 'success' })
      }
      this.closeForm()
      this.loadResumes()
    } catch (error) {
      wx.showToast({ title: error.message || '保存失败', icon: 'none' })
    }
  },

  async loadResumes() {
    this.setData({ loading: true })
    try {
      const params = { page_size: 100 }
      if (this.data.searchKey) params.search = this.data.searchKey
      if (this.data.filterStatus) params.status = this.data.filterStatus
      const res = await resumeApi.list(params)
      this.setData({ resumes: Array.isArray(res) ? res : (res.results || []) })
    } catch (error) {
      wx.showToast({ title: error.message || '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  openDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/user/resume-detail/index?id=' + id })
  },

  deleteResume(e) {
    const id = e.currentTarget.dataset.id
    const that = this
    wx.showModal({
      title: '确认删除',
      content: '确定删除此简历吗？',
      success: async function (result) {
        if (!result.confirm) return
        try {
          await resumeApi.delete(id)
          wx.showToast({ title: '已删除', icon: 'success' })
          that.loadResumes()
        } catch (error) {
          wx.showToast({ title: error.message || '删除失败', icon: 'none' })
        }
      },
    })
  },
})
