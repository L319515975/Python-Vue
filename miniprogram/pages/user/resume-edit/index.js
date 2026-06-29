import { resumeApi, educationApi, workApi, projectApi, skillApi, aiApi } from '../../../api/index'

const formDefaults = {
  education: { school: '', degree: '', major: '', start_date: '', end_date: '', description: '', order: 0 },
  work: { company: '', position: '', start_date: '', end_date: '', description: '', order: 0 },
  project: { name: '', role: '', start_date: '', end_date: '', description: '', tech_stack: '', order: 0 },
  skill: { name: '', level: 50, category: '通用', order: 0 },
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
    showPolisher: false,
    polishText: '',
    polishResult: '',
    polishLoading: false,
    polishModule: '',
    showSubForm: false,
    subFormType: '',
    subFormData: {},
  },

  onLoad(options) {
    this.setData({ resumeId: options.id || '' }, () => this.loadResume())
  },

  async loadResume() {
    this.setData({ loading: true })
    try {
      let detail = null
      if (this.data.resumeId) {
        detail = await resumeApi.detail(this.data.resumeId)
      } else {
        const list = await resumeApi.list({ page_size: 1 })
        const item = Array.isArray(list) ? list[0] : (list.results || [])[0]
        if (item) detail = await resumeApi.detail(item.id)
      }
      if (!detail) {
        this.setData({ resume: null, loading: false })
        return
      }
      this.setData({
        resume: detail,
        resumeId: detail.id,
        form: { title: detail.title || '', summary: detail.summary || '' },
        educations: detail.educations || [],
        workExperiences: detail.work_experiences || [],
        projects: detail.projects || [],
        skills: detail.skills || [],
      })
    } catch (error) {
      wx.showToast({ title: error.message || '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  onTitleInput(e) {
    this.setData({ form: Object.assign({}, this.data.form, { title: e.detail.value }) })
  },

  onSummaryInput(e) {
    this.setData({ form: Object.assign({}, this.data.form, { summary: e.detail.value }) })
  },

  goDetail() {
    const url = this.data.resumeId ? '/pages/user/resume-detail/index?id=' + this.data.resumeId : '/pages/user/resume-detail/index'
    wx.navigateTo({ url: url })
  },

  async saveResume() {
    if (!this.data.resume) {
      await this.createResume()
      return
    }
    try {
      const detail = await resumeApi.update(this.data.resume.id, { title: this.data.form.title, summary: this.data.form.summary })
      this.setData({ resume: detail, resumeId: detail.id })
      wx.showToast({ title: '已保存', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error.message || '保存失败', icon: 'none' })
    }
  },

  async createResume() {
    try {
      const detail = await resumeApi.create({ title: this.data.form.title || '我的简历', summary: this.data.form.summary || '' })
      this.setData({ resume: detail, resumeId: detail.id })
      wx.showToast({ title: '已创建', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error.message || '创建失败', icon: 'none' })
    }
  },

  showAddSubItem(e) {
    const type = e.currentTarget.dataset.type
    this.setData({ showSubForm: true, subFormType: type, subFormData: Object.assign({}, formDefaults[type]) })
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

  async saveSubItem() {
    if (!this.data.resume) return
    const type = this.data.subFormType
    const api = this.getSubItemApi(type)
    const data = Object.assign({}, this.data.subFormData, { resume: this.data.resume.id })
    try {
      if (data.id) await api.update(data.id, data)
      else await api.create(data)
      wx.showToast({ title: '已保存', icon: 'success' })
      this.hideSubForm()
      this.loadResume()
    } catch (error) {
      wx.showToast({ title: error.message || '保存失败', icon: 'none' })
    }
  },

  editSubItem(e) {
    const type = e.currentTarget.dataset.type
    const id = Number(e.currentTarget.dataset.id)
    const list = this.getSubItemList(type)
    const item = list.find(function (entry) { return Number(entry.id) === id })
    if (item) this.setData({ showSubForm: true, subFormType: type, subFormData: Object.assign({}, item) })
  },

  deleteSubItem(e) {
    const type = e.currentTarget.dataset.type
    const id = e.currentTarget.dataset.id
    const api = this.getSubItemApi(type)
    const that = this
    wx.showModal({
      title: '确认删除',
      content: '确定删除这条记录吗？',
      success: async function (result) {
        if (!result.confirm) return
        try {
          await api.delete(id)
          that.loadResume()
        } catch (error) {
          wx.showToast({ title: error.message || '删除失败', icon: 'none' })
        }
      },
    })
  },

  openPolisher(e) {
    this.setData({ showPolisher: true, polishText: e.currentTarget.dataset.text || '', polishResult: '', polishModule: e.currentTarget.dataset.module || '' })
  },

  closePolisher() {
    this.setData({ showPolisher: false })
  },

  onPolishTextInput(e) {
    this.setData({ polishText: e.detail.value })
  },

  async doPolish() {
    if (!this.data.polishText.trim()) {
      wx.showToast({ title: '请输入要润色的文本', icon: 'none' })
      return
    }
    this.setData({ polishLoading: true })
    try {
      const data = await aiApi.polish(this.data.polishText.trim(), this.data.polishModule)
      this.setData({ polishResult: data.polished_text || data.response || '' })
    } catch (error) {
      wx.showToast({ title: error.message || '润色失败', icon: 'none' })
    } finally {
      this.setData({ polishLoading: false })
    }
  },

  applyPolish() {
    this.setData({ polishText: this.data.polishResult, polishResult: '' })
  },
})
