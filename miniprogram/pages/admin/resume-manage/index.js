import { resumeApi } from '../../../api/index'

Page({
  data: { resumes: [], searchKey: '', loading: false, filterStatus: '', statusOptions: ['draft', 'published', 'archived'], editFormVisible: false, form: { title: '', summary: '', status: 'draft' }, editId: null },

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
        wx.showToast({ title: 'Updated successfully', icon: 'success' })
      } else {
        await resumeApi.create(payload)
        wx.showToast({ title: 'Created successfully', icon: 'success' })
      }
      this.closeForm()
      this.loadResumes()
    } catch (error) {
      wx.showToast({ title: error.message || '淇濆瓨澶辫触', icon: 'none' })
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
      wx.showToast({ title: error.message || '鍔犺浇澶辫触', icon: 'none' })
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
      title: '纭鍒犻櫎',
      content: 'Confirm delete this resume?',
      success: async function (result) {
        if (!result.confirm) return
        try {
          await resumeApi.delete(id)
          wx.showToast({ title: 'Deleted successfully', icon: 'success' })
          that.loadResumes()
        } catch (error) {
          wx.showToast({ title: error.message || '鍒犻櫎澶辫触', icon: 'none' })
        }
      },
    })
  },
})
