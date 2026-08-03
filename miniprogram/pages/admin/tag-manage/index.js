import { tagApi } from '../../../api/index'

const tagTypes = ['skill', 'project', 'certificate', 'award', 'language', 'custom']

Page({
  data: { tags: [], loading: false, formVisible: false, editId: null, name: '', tagType: 'skill', tagTypeOptions: tagTypes },

  onLoad() {
    this.loadTags()
  },

  async loadTags() {
    this.setData({ loading: true })
    try {
      const res = await tagApi.list({ page_size: 200 })
      this.setData({ tags: Array.isArray(res) ? res : (res.results || []) })
    } catch (error) {
      wx.showToast({ title: error.message || '鍔犺浇澶辫触', icon: 'none' })
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
        wx.showToast({ title: 'Updated successfully', icon: 'success' })
      } else {
        await tagApi.create({ name: name, tag_type: this.data.tagType })
        wx.showToast({ title: 'Created successfully', icon: 'success' })
      }
      this.hideForm()
      this.loadTags()
    } catch (error) {
      wx.showToast({ title: error.message || '淇濆瓨澶辫触', icon: 'none' })
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
      title: '纭鍒犻櫎',
      content: 'Confirm delete this tag?',
      success: async function (result) {
        if (!result.confirm) return
        try {
          await tagApi.delete(id)
          wx.showToast({ title: 'Deleted successfully', icon: 'success' })
          that.loadTags()
        } catch (error) {
          wx.showToast({ title: error.message || '鍒犻櫎澶辫触', icon: 'none' })
        }
      },
    })
  },
})
