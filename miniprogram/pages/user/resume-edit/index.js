import { resumeApi, educationApi, workApi, projectApi, skillApi } from '../../../api/index'

function unwrapList(result) {
  if (Array.isArray(result)) return result
  if (result && Array.isArray(result.results)) return result.results
  return []
}

function emptySubForm(type) {
  if (type === 'education') {
    return { school: '', degree: '', major: '', start_date: '', end_date: '', description: '', order: 0 }
  }
  if (type === 'work') {
    return { company: '', position: '', start_date: '', end_date: '', description: '', order: 0 }
  }
  if (type === 'project') {
    return { name: '', role: '', start_date: '', end_date: '', description: '', tech_stack: '', order: 0 }
  }
  return { name: '', level: 50, category: 'Skill', order: 0 }
}

function normalizeSubForm(type, data, resumeId) {
  const payload = Object.assign({}, data, { resume: resumeId })
  if (type === 'skill') {
    payload.level = Number(payload.level || 0)
  }
  if (payload.order !== undefined) {
    payload.order = Number(payload.order || 0)
  }
  return payload
}

Page({
  data: {
    resumeId: '',
    resume: null,
    loading: false,
    form: { title: '', summary: '' },
    educations: [],
    workExperiences: [],
    projects: [],
    skills: [],
    showSubForm: false,
    subFormType: '',
    subFormData: {},
  },

  onLoad(options) {
    this.setData({ resumeId: options && options.id ? String(options.id) : '' })
    this.loadResume()
  },

  onPullDownRefresh() {
    this.loadResume().finally(function () {
      wx.stopPullDownRefresh()
    })
  },

  async loadResume() {
    this.setData({ loading: true })
    try {
      let detail = null
      if (this.data.resumeId) {
        detail = await resumeApi.detail(this.data.resumeId)
      } else {
        const list = await resumeApi.list({ page_size: 1 })
        const item = unwrapList(list)[0]
        if (item) detail = await resumeApi.detail(item.id)
      }

      if (!detail) {
        this.setData({ resume: null, loading: false })
        return
      }

      this.setData({
        resume: detail,
        resumeId: String(detail.id),
        form: { title: detail.title || '', summary: detail.summary || '' },
        educations: detail.educations || [],
        workExperiences: detail.work_experiences || [],
        projects: detail.projects || [],
        skills: detail.skills || [],
      })
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : 'Load failed', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  goDetail() {
    const url = this.data.resumeId ? '/pages/user/resume-detail/index?id=' + this.data.resumeId : '/pages/user/resume-detail/index'
    wx.reLaunch({ url: url })
  },

  onTitleInput(e) {
    this.setData({ form: Object.assign({}, this.data.form, { title: e.detail.value }) })
  },

  onSummaryInput(e) {
    this.setData({ form: Object.assign({}, this.data.form, { summary: e.detail.value }) })
  },

  async saveResume() {
    if (!this.data.resume) {
      await this.createResume()
      return
    }

    try {
      const detail = await resumeApi.update(this.data.resume.id, {
        title: this.data.form.title,
        summary: this.data.form.summary,
      })
      this.setData({ resume: detail, resumeId: String(detail.id) })
      wx.showToast({ title: 'Saved', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : 'Save failed', icon: 'none' })
    }
  },

  async createResume() {
    try {
      const detail = await resumeApi.create({
        title: this.data.form.title || 'My Resume',
        summary: this.data.form.summary || '',
      })
      this.setData({ resume: detail, resumeId: String(detail.id) })
      wx.showToast({ title: 'Created', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : 'Create failed', icon: 'none' })
    }
  },

  getSubItemApi(type) {
    if (type === 'education') return educationApi
    if (type === 'work') return workApi
    if (type === 'project') return projectApi
    return skillApi
  },

  getSubItemList(type) {
    if (type === 'education') return this.data.educations
    if (type === 'work') return this.data.workExperiences
    if (type === 'project') return this.data.projects
    return this.data.skills
  },

  showAddSubItem(e) {
    const type = e.currentTarget.dataset.type
    this.setData({ showSubForm: true, subFormType: type, subFormData: emptySubForm(type) })
  },

  editSubItem(e) {
    const type = e.currentTarget.dataset.type
    const id = Number(e.currentTarget.dataset.id)
    const item = this.getSubItemList(type).find(function (entry) {
      return Number(entry.id) === id
    })

    if (item) {
      this.setData({ showSubForm: true, subFormType: type, subFormData: Object.assign({}, item) })
    }
  },

  hideSubForm() {
    this.setData({ showSubForm: false })
  },

  subFormInput(e) {
    const field = e.currentTarget.dataset.field
    const next = Object.assign({}, this.data.subFormData)
    next[field] = e.detail.value
    this.setData({ subFormData: next })
  },

  async saveSubItem() {
    if (!this.data.resume) return

    const type = this.data.subFormType
    const api = this.getSubItemApi(type)
    const payload = normalizeSubForm(type, this.data.subFormData, this.data.resume.id)

    try {
      if (payload.id) {
        await api.update(payload.id, payload)
      } else {
        await api.create(payload)
      }
      wx.showToast({ title: 'Saved', icon: 'success' })
      this.hideSubForm()
      this.loadResume()
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : 'Save failed', icon: 'none' })
    }
  },

  deleteSubItem(e) {
    const type = e.currentTarget.dataset.type
    const id = e.currentTarget.dataset.id
    const api = this.getSubItemApi(type)
    const that = this

    wx.showModal({
      title: 'Delete item',
      content: 'Confirm delete this record?',
      success: async function (result) {
        if (!result.confirm) return
        try {
          await api.delete(id)
          wx.showToast({ title: 'Deleted', icon: 'success' })
          that.loadResume()
        } catch (error) {
          wx.showToast({ title: error && error.message ? error.message : 'Delete failed', icon: 'none' })
        }
      },
    })
  },
})
