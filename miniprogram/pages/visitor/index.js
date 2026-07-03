import { visitorApi } from '../../api/index'

const sectionLabelMap = {
  educations: '教育经历',
  work_experiences: '工作经历',
  projects: '项目经历',
  skills: '技能',
  certificates: '证书',
  awards: '奖项',
  languages: '语言',
}

function joinText(values, separator) {
  return (values || []).filter(function (item) {
    return item !== undefined && item !== null && item !== ''
  }).join(separator || ' · ')
}

Page({
  data: {
    token: '',
    sig: '',
    expires: '',
    role: 'hr',
    resume: null,
    sections: [],
    loading: false,
    tokenFocused: false,
    questionFocused: false,
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

  onTokenFocus() {
    this.setData({ tokenFocused: true })
  },

  onTokenBlur() {
    this.setData({ tokenFocused: false })
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
      sections.push({
        title: sectionLabelMap.educations,
        items: data.educations.map(function (item) {
          return joinText([item.school, item.degree, item.major], ' · ')
        }),
      })
    }
    if (data.work_experiences && data.work_experiences.length) {
      sections.push({
        title: sectionLabelMap.work_experiences,
        items: data.work_experiences.map(function (item) {
          return joinText([item.company, item.position], ' · ')
        }),
      })
    }
    if (data.projects && data.projects.length) {
      sections.push({
        title: sectionLabelMap.projects,
        items: data.projects.map(function (item) {
          return joinText([item.name, item.role, item.tech_stack], ' · ')
        }),
      })
    }
    if (data.skills && data.skills.length) {
      sections.push({
        title: sectionLabelMap.skills,
        items: data.skills.map(function (item) {
          return joinText([item.name, '熟练度 ' + String(item.level || 0) + '%'], ' · ')
        }),
      })
    }
    return sections
  },

  async loadResume() {
    if (!this.data.token) {
      wx.showToast({ title: '请输入访客访问码', icon: 'none' })
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
        aiAnswer: '',
      })
    } catch (error) {
      wx.showToast({ title: error.message || '加载简历失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  onAiInput(e) {
    this.setData({ aiQuestion: e.detail.value })
  },

  onAiFocus() {
    this.setData({ questionFocused: true })
  },

  onAiBlur() {
    this.setData({ questionFocused: false })
  },

  async askAi() {
    if (!this.data.aiQuestion.trim()) {
      wx.showToast({ title: '请输入咨询问题', icon: 'none' })
      return
    }
    if (!this.data.token) {
      wx.showToast({ title: '请先输入访客访问码', icon: 'none' })
      return
    }
    this.setData({ aiLoading: true })
    try {
      const data = await visitorApi.aiChat(this.data.token, this.getVisitorParams(), { query: this.data.aiQuestion.trim() })
      this.setData({ aiAnswer: data.response || data.polished_text || '暂无回答' })
    } catch (error) {
      wx.showToast({ title: error.message || 'AI 请求失败', icon: 'none' })
    } finally {
      this.setData({ aiLoading: false })
    }
  },
})