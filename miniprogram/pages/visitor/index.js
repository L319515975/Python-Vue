import { visitorApi } from '../../api/index'

Page({
  data: {
    token: '',
    sig: '',
    expires: '',
    role: 'hr',
    resume: null,
    sections: [],
    loading: false,
    aiQuestion: '',
    aiAnswer: '',
    aiLoading: false,
    aiEnabled: false,
    aiQuota: 0,
    aiUsed: 0,
  },

  onLoad(options) {
    const data = {
      token: options.token || '',
      sig: options.sig || '',
      expires: options.expires || '',
      role: options.role || 'hr',
    }
    this.setData(data)
    if (data.token) this.loadResume()
  },

  onTokenInput(e) {
    this.setData({ token: e.detail.value })
  },

  getVisitorParams() {
    const params = {}
    if (this.data.sig) params.sig = this.data.sig
    if (this.data.expires) params.expires = this.data.expires
    if (this.data.role) params.role = this.data.role
    return params
  },

  buildSections(data) {
    const sections = []
    if (data.educations && data.educations.length) {
      sections.push({ title: '鏁欒偛缁忓巻', items: data.educations.map(function (item) { return (item.school || '') + ' ' + (item.degree || '') + ' ' + (item.major || '') }) })
    }
    if (data.work_experiences && data.work_experiences.length) {
      sections.push({ title: '宸ヤ綔缁忓巻', items: data.work_experiences.map(function (item) { return (item.company || '') + ' - ' + (item.position || '') }) })
    }
    if (data.projects && data.projects.length) {
      sections.push({ title: '椤圭洰缁忓巻', items: data.projects.map(function (item) { return item.name || '' }) })
    }
    if (data.skills && data.skills.length) {
      sections.push({ title: 'Skills', items: data.skills.map(function (item) { return (item.name || '') + ' (' + (item.level || 0) + '%)' }) })
    }
    return sections
  },

  async loadResume() {
    if (!this.data.token) {
      wx.showToast({ title: 'Please enter a token', icon: 'none' })
      return
    }
    this.setData({ loading: true })
    try {
      const data = await visitorApi.getResume(this.data.token, this.getVisitorParams())
      this.setData({
        resume: data,
        sections: this.buildSections(data),
        aiEnabled: data.visitor_ai_enabled || false,
        aiQuota: data.visitor_ai_quota || 0,
        aiUsed: data.visitor_ai_used || 0,
      })
    } catch (error) {
      wx.showToast({ title: error.message || '鍔犺浇澶辫触', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  onAiInput(e) {
    this.setData({ aiQuestion: e.detail.value })
  },

  async askAi() {
    if (!this.data.aiQuestion.trim()) {
      wx.showToast({ title: 'Please enter a question', icon: 'none' })
      return
    }
    this.setData({ aiLoading: true })
    try {
      const data = await visitorApi.aiChat(this.data.token, this.getVisitorParams(), { query: this.data.aiQuestion.trim() })
      this.setData({ aiAnswer: data.response || data.polished_text || '鏆傛棤鍥炲' })
    } catch (error) {
      wx.showToast({ title: error.message || 'AI 璇锋眰澶辫触', icon: 'none' })
    } finally {
      this.setData({ aiLoading: false })
    }
  },
})
