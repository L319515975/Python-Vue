import { pdfTemplateApi } from '../../../api/index'

function unwrapList(result) {
  if (Array.isArray(result)) return result
  if (result && Array.isArray(result.results)) return result.results
  return []
}

Page({
  data: {
    templates: [],
    loading: false,
    saving: false,
    formVisible: false,
    editId: null,
    form: { name: '', description: '', is_active: true },
    filePath: '',
    fileName: '',
  },

  onLoad() {
    this.loadTemplates()
  },

  async loadTemplates() {
    this.setData({ loading: true })
    try {
      const res = await pdfTemplateApi.listAll()
      this.setData({ templates: unwrapList(res) })
    } catch (error) {
      wx.showToast({ title: error.message || '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  openCreate() {
    this.setData({
      formVisible: true,
      editId: null,
      form: { name: '', description: '', is_active: true },
      filePath: '',
      fileName: '',
    })
  },

  openEdit(e) {
    const id = Number(e.currentTarget.dataset.id)
    const item = this.data.templates.find(function (template) { return Number(template.id) === id })
    if (!item || item.is_builtin) return
    this.setData({
      formVisible: true,
      editId: item.id,
      form: {
        name: item.name || '',
        description: item.description || '',
        is_active: item.is_active !== false,
      },
      filePath: '',
      fileName: item.template_file_name || '',
    })
  },

  closeForm() {
    this.setData({ formVisible: false })
  },

  onFormInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ ['form.' + field]: e.detail.value })
  },

  onActiveChange(e) {
    this.setData({ ['form.is_active']: !!e.detail.value })
  },

  chooseTemplateFile() {
    const that = this
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['html', 'htm'],
      success(res) {
        const file = res.tempFiles && res.tempFiles[0]
        if (!file) return
        that.setData({
          filePath: file.path,
          fileName: file.name || file.path.split(/[\\/]/).pop(),
        })
      },
    })
  },

  async saveTemplate() {
    const form = this.data.form
    const name = (form.name || '').trim()
    if (!name) {
      wx.showToast({ title: '请输入模板名称', icon: 'none' })
      return
    }

    if (!this.data.editId && !this.data.filePath) {
      wx.showToast({ title: '请选择模板文件', icon: 'none' })
      return
    }

    this.setData({ saving: true })
    try {
      if (this.data.editId) {
        await pdfTemplateApi.update(this.data.editId, {
          name: name,
          description: (form.description || '').trim(),
          is_active: form.is_active,
        })
        wx.showToast({ title: '已更新', icon: 'success' })
      } else {
        await pdfTemplateApi.create(this.data.filePath, {
          name: name,
          description: (form.description || '').trim(),
          is_active: String(!!form.is_active),
        })
        wx.showToast({ title: '已上传', icon: 'success' })
      }
      this.closeForm()
      this.loadTemplates()
    } catch (error) {
      wx.showToast({ title: error.message || '保存失败', icon: 'none' })
    } finally {
      this.setData({ saving: false })
    }
  },

  async toggleActive(e) {
    const id = Number(e.currentTarget.dataset.id)
    const value = !!e.detail.value
    const item = this.data.templates.find(function (template) { return Number(template.id) === id })
    if (!item || item.is_builtin) return

    try {
      await pdfTemplateApi.update(id, { is_active: value })
      this.loadTemplates()
    } catch (error) {
      wx.showToast({ title: error.message || '更新失败', icon: 'none' })
    }
  },

  deleteTemplate(e) {
    const id = Number(e.currentTarget.dataset.id)
    const item = this.data.templates.find(function (template) { return Number(template.id) === id })
    if (!item || item.is_builtin) return

    const that = this
    wx.showModal({
      title: '删除模板',
      content: '确认删除这个模板吗？',
      success: async function (result) {
        if (!result.confirm) return
        try {
          await pdfTemplateApi.delete(id)
          wx.showToast({ title: '已删除', icon: 'success' })
          that.loadTemplates()
        } catch (error) {
          wx.showToast({ title: error.message || '删除失败', icon: 'none' })
        }
      },
    })
  },
})
