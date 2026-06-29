import { userApi } from '../../../api/index'

Page({
  data: {
    users: [],
    loading: false,
    searchKey: '',
    formVisible: false,
    editId: null,
    form: { username: '', email: '', phone: '', role: 'user', password: '', is_active: true },
  },

  onLoad() {
    this.loadUsers()
  },

  onSearchInput(e) {
    this.setData({ searchKey: e.detail.value })
  },

  openCreate() {
    this.setData({
      formVisible: true,
      editId: null,
      form: { username: '', email: '', phone: '', role: 'user', password: '', is_active: true },
    })
  },

  openEdit(e) {
    const id = Number(e.currentTarget.dataset.id)
    const item = this.data.users.find(function (user) { return Number(user.id) === id })
    if (!item) return
    this.setData({
      formVisible: true,
      editId: item.id,
      form: {
        username: item.username || '',
        email: item.email || '',
        phone: item.phone || '',
        role: item.role || 'user',
        password: '',
        is_active: item.is_active !== false,
      },
    })
  },

  closeForm() {
    this.setData({ formVisible: false })
  },

  onFormInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ ['form.' + field]: e.detail.value })
  },

  onRoleChange(e) {
    const roles = ['user', 'admin']
    this.setData({ ['form.role']: roles[Number(e.detail.value)] || 'user' })
  },

  onActiveChange(e) {
    this.setData({ ['form.is_active']: !!e.detail.value })
  },

  async saveUser() {
    const form = this.data.form
    if (!form.username.trim()) {
      wx.showToast({ title: '请输入用户名', icon: 'none' })
      return
    }
    try {
      const payload = {
        username: form.username.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        role: form.role,
        is_active: form.is_active,
      }
      if (form.password) payload.password = form.password
      if (this.data.editId) {
        await userApi.update(this.data.editId, payload)
        wx.showToast({ title: '已更新', icon: 'success' })
      } else {
        if (!form.password) {
          wx.showToast({ title: '新增用户需要密码', icon: 'none' })
          return
        }
        await userApi.create(payload)
        wx.showToast({ title: '已创建', icon: 'success' })
      }
      this.closeForm()
      this.loadUsers()
    } catch (error) {
      wx.showToast({ title: error.message || '保存失败', icon: 'none' })
    }
  },

  async loadUsers() {
    this.setData({ loading: true })
    try {
      const params = { page_size: 100 }
      if (this.data.searchKey) params.search = this.data.searchKey
      const res = await userApi.list(params)
      this.setData({ users: Array.isArray(res) ? res : (res.results || []) })
    } catch (error) {
      wx.showToast({ title: error.message || '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  deleteUser(e) {
    const id = e.currentTarget.dataset.id
    const that = this
    wx.showModal({
      title: '确认删除',
      content: '确定删除此用户吗？',
      success: async function (result) {
        if (!result.confirm) return
        try {
          await userApi.delete(id)
          wx.showToast({ title: '已删除', icon: 'success' })
          that.loadUsers()
        } catch (error) {
          wx.showToast({ title: error.message || '删除失败', icon: 'none' })
        }
      },
    })
  },
})
