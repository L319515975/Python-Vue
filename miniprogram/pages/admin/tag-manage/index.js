import { tagApi } from '../../../api/index'

const tagTypes = ['skill', 'project', 'certificate', 'award', 'language', 'custom']

Page({
  data: { tags: [], loading: false, formVisible: false, editId: null, name: '', tagType: 'skill' },

  onLoad() {
    this.loadTags()
  },

  async loadTags() {
    this.setData({ loading: true })
    try {
      const res = await tagApi.list({ page_size: 200 })
      this.setData({ tags: Array.isArray(res) ? res : (res.results || []) })
    } catch (error) {
      wx.showToast({ title: error.message || '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  showCreate() {
    this.setData({ formVisible: true, editId: null, name: '', tagType: 'skill' })
  },

  hideForm() {
    this.setData({ formVisible: false })
  },

  onNameInput(e) {
    this.setData({ name: e.detail.value })
  },

  onTypeChange(e) {
    this.setData({ tagType: tagTypes[Number(e.detail.value)] || 'skill' })
  },

  async saveTag() {
    const name = (this.data.name || '').trim()
    if (!name) {
      wx.showToast({ title: '请输入标签名称', icon: 'none' })
      return
    }
    try {
      if (this.data.editId) {
        await tagApi.update(this.data.editId, { name: name, tag_type: this.data.tagType })
        wx.showToast({ title: '已更新', icon: 'success' })
      } else {
        await tagApi.create({ name: name, tag_type: this.data.tagType })
        wx.showToast({ title: '已创建', icon: 'success' })
      }
      this.hideForm()
      this.loadTags()
    } catch (error) {
      wx.showToast({ title: error.message || '保存失败', icon: 'none' })
    }
  },

  editTag(e) {
    const id = Number(e.currentTarget.dataset.id)
    const item = this.data.tags.find(function (tag) { return Number(tag.id) === id })
    if (item) {
      this.setData({
        formVisible: true,
        editId: item.id,
        name: item.name,
        tagType: item.tag_type || 'skill',
      })
    }
  },

  deleteTag(e) {
    const id = e.currentTarget.dataset.id
    const that = this
    wx.showModal({
      title: '确认删除',
      content: '确定删除此标签吗？',
      success: async function (result) {
        if (!result.confirm) return
        try {
          await tagApi.delete(id)
          wx.showToast({ title: '已删除', icon: 'success' })
          that.loadTags()
        } catch (error) {
          wx.showToast({ title: error.message || '删除失败', icon: 'none' })
        }
      },
    })
  },
})
