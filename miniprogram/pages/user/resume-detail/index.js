import { resumeApi, tagApi, aiApi } from '../../../api/index'
import { getUserInfo } from '../../../utils/auth'

function formatDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return date.getFullYear() + '-' + month + '-' + day
}

function toSectionRows(items, mapper) {
  return (items || []).map(function (item) {
    return mapper(item)
  })
}

Page({
  data: {
    resumeId: '',
    loading: false,
    resume: null,
    tags: [],
    selectedTagIds: [],
    sections: [],
    visitor: {},
    moduleList: [],
    exportModuleNames: [],
    aiQuestion: '',
    aiAnswer: '',
    aiLoading: false,
    userInfo: getUserInfo(),
    polishVisible: false,
    polishText: '',
    polishResult: '',
    polishLoading: false,
    polishModule: '',
    uploading: false,
    visitorLoading: false,
  },

  onLoad(options) {
    this.setData({ resumeId: options.id || '' }, () => this.loadPage())
  },

  refresh() {
    this.loadPage()
  },

  onAiQuestionInput(e) {
    this.setData({ aiQuestion: e.detail.value })
  },

  goEdit() {
    const url = this.data.resumeId ? '/pages/user/resume-edit/index?id=' + this.data.resumeId : '/pages/user/resume-edit/index'
    wx.navigateTo({ url: url })
  },

  async loadPage() {
    this.setData({ loading: true })
    try {
      const resumeId = this.data.resumeId
      let detail = null
      if (resumeId) {
        detail = await resumeApi.detail(resumeId)
      } else {
        const listResult = await resumeApi.list({ page_size: 50 })
        const resumeItem = Array.isArray(listResult) ? listResult[0] : (listResult.results || [])[0]
        if (resumeItem) detail = await resumeApi.detail(resumeItem.id)
      }
      const tagResult = await tagApi.list({ page_size: 100 })
      const tagList = Array.isArray(tagResult) ? tagResult : (tagResult.results || [])
      if (!detail) {
        this.setData({ resume: null, tags: tagList, sections: [], moduleList: [], selectedTagIds: [], exportModuleNames: [], visitor: {}, loading: false })
        return
      }
      this.applyDetail(detail, tagList)
    } catch (error) {
      wx.showToast({ title: error.message || '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  applyDetail(detail, tagList) {
    const tags = (tagList || this.data.tags || []).map(function (tag) {
      const selected = (detail.tags_detail || []).some(function (selectedTag) {
        return selectedTag.id === tag.id
      })
      return Object.assign({}, tag, { selected: selected })
    })
    this.setData({
      resume: detail,
      tags: tags,
      selectedTagIds: (detail.tags_detail || []).map(function (item) { return item.id }),
      sections: this.buildSections(detail),
      visitor: this.buildVisitor(detail),
      moduleList: this.buildModuleOptions(detail),
      exportModuleNames: detail.enabled_modules || [],
      loading: false,
    })
  },

  buildSections(detail) {
    const sections = []
    sections.push({
      title: '基础信息',
      kind: 'text',
      items: [
        '标题: ' + (detail.title || '-'),
        '状态: ' + (detail.status || '-'),
        '简介: ' + (detail.summary || '-'),
        '启用模块: ' + ((detail.enabled_modules || []).join(', ') || '-'),
      ],
    })

    if (detail.educations && detail.educations.length) {
      sections.push({
        title: '教育经历',
        kind: 'object',
        items: toSectionRows(detail.educations, function (item) {
          return {
            title: (item.school || '-') + ' - ' + (item.major || '-'),
            desc: (item.degree || '') + ' ' + formatDate(item.start_date) + ' ~ ' + formatDate(item.end_date) + (item.description ? '\n' + item.description : ''),
          }
        }),
      })
    }

    if (detail.work_experiences && detail.work_experiences.length) {
      sections.push({
        title: '工作经历',
        kind: 'object',
        items: toSectionRows(detail.work_experiences, function (item) {
          return {
            title: (item.company || '-') + ' - ' + (item.position || '-'),
            desc: formatDate(item.start_date) + ' ~ ' + formatDate(item.end_date) + (item.description ? '\n' + item.description : ''),
          }
        }),
      })
    }

    if (detail.projects && detail.projects.length) {
      sections.push({
        title: '项目经历',
        kind: 'object',
        items: toSectionRows(detail.projects, function (item) {
          return {
            title: item.name || '-',
            desc: (item.role || '') + ' ' + (item.tech_stack || '') + (item.description ? '\n' + item.description : ''),
          }
        }),
      })
    }

    if (detail.skills && detail.skills.length) {
      sections.push({
        title: '技能',
        kind: 'object',
        items: toSectionRows(detail.skills, function (item) {
          return {
            title: item.name || '-',
            desc: (item.category || '分类未知') + ' ' + (item.level || 0) + '%',
          }
        }),
      })
    }

    return sections
  },

  buildVisitor(detail) {
    return {
      enabled: detail.visitor_enabled,
      url: detail.visitor_url || '',
      expires: detail.visitor_expires || '',
      allowDownload: detail.visitor_allow_download,
      hrEnabled: detail.visitor_hr_enabled,
      aiEnabled: detail.visitor_ai_enabled,
      quota: detail.visitor_ai_quota,
      used: detail.visitor_ai_used,
      remaining: Math.max(0, (detail.visitor_ai_quota || 0) - (detail.visitor_ai_used || 0)),
      publicModules: detail.public_modules || [],
    }
  },

  buildModuleOptions(detail) {
    const moduleMap = {
      education: '教育经历',
      work_experience: '工作经历',
      project: '项目经历',
      skill: '技能',
      certificate: '证书',
      award: '获奖',
      language: '语言',
    }
    const enabled = detail.enabled_modules || []
    return Object.keys(moduleMap).map(function (name) {
      return {
        name: name,
        label: moduleMap[name],
        checked: enabled.indexOf(name) >= 0,
      }
    })
  },

  async toggleModule(e) {
    if (!this.data.resume) return
    const name = e.currentTarget.dataset.name
    const next = this.data.moduleList.map(function (item) {
      if (item.name !== name) return item
      return Object.assign({}, item, { checked: !item.checked })
    })
    const enabledModules = next.filter(function (item) { return item.checked }).map(function (item) { return item.name })
    this.setData({ moduleList: next, exportModuleNames: enabledModules })
    try {
      const detail = await resumeApi.updateModules(this.data.resume.id, { enabled_modules: enabledModules })
      this.applyDetail(detail)
    } catch (error) {
      wx.showToast({ title: error.message || '更新失败', icon: 'none' })
    }
  },

  async refreshVisitorLink() {
    if (!this.data.resume) return
    this.setData({ visitorLoading: true })
    try {
      const response = await resumeApi.visitorLinkInfo(this.data.resume.id)
      this.setData({ visitor: this.buildVisitor(response) })
    } catch (error) {
      wx.showToast({ title: error.message || '获取访客链接失败', icon: 'none' })
    } finally {
      this.setData({ visitorLoading: false })
    }
  },

  async generateVisitorLink() {
    if (!this.data.resume) return
    try {
      const response = await resumeApi.generateVisitorLink(this.data.resume.id, {
        enabled: true,
        expires_days: 30,
        allow_download: true,
        hr_enabled: true,
        ai_enabled: true,
        ai_quota: 10,
      })
      const merged = Object.assign({}, this.data.resume, response)
      this.setData({ resume: merged, visitor: this.buildVisitor(merged) })
      wx.showToast({ title: '访客链接已生成', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error.message || '生成失败', icon: 'none' })
    }
  },

  async disableVisitorLink() {
    if (!this.data.resume) return
    try {
      const response = await resumeApi.disableVisitorLink(this.data.resume.id)
      const merged = Object.assign({}, this.data.resume, response)
      this.setData({ resume: merged, visitor: this.buildVisitor(merged) })
      wx.showToast({ title: '已禁用', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error.message || '禁用失败', icon: 'none' })
    }
  },

  copyVisitorLink() {
    if (!this.data.visitor.url) {
      wx.showToast({ title: '暂无可复制链接', icon: 'none' })
      return
    }
    wx.setClipboardData({
      data: this.data.visitor.url,
      success: function () {
        wx.showToast({ title: '已复制', icon: 'success' })
      },
    })
  },

  async exportPdf() {
    if (!this.data.resume) return
    try {
      const modules = this.data.exportModuleNames.length ? this.data.exportModuleNames : this.data.resume.enabled_modules
      const response = await resumeApi.exportPdf(this.data.resume.id, modules)
      const filePath = wx.env.USER_DATA_PATH + '/resume.pdf'
      const fileContent = response.data || response
      wx.getFileSystemManager().writeFileSync(filePath, fileContent, 'binary')
      wx.openDocument({ filePath: filePath, fileType: 'pdf' })
    } catch (error) {
      wx.showToast({ title: error.message || '导出失败', icon: 'none' })
    }
  },

  async toggleTag(e) {
    const id = Number(e.currentTarget.dataset.value)
    const ids = this.data.selectedTagIds.slice()
    const index = ids.indexOf(id)
    if (index >= 0) ids.splice(index, 1)
    else ids.push(id)
    this.setData({
      selectedTagIds: ids,
      tags: this.data.tags.map(function (tag) {
        return Object.assign({}, tag, { selected: ids.indexOf(tag.id) >= 0 })
      }),
    })
    if (this.data.resume) {
      try {
        const detail = await resumeApi.setTags(this.data.resume.id, ids)
        this.applyDetail(detail)
      } catch (error) {
        wx.showToast({ title: error.message || '更新标签失败', icon: 'none' })
      }
    }
  },

  async askAi() {
    const question = (this.data.aiQuestion || '').trim()
    if (!question) {
      wx.showToast({ title: '请输入问题', icon: 'none' })
      return
    }
    this.setData({ aiLoading: true })
    try {
      const response = await aiApi.chat(question)
      this.setData({ aiAnswer: response.response || '' })
    } catch (error) {
      wx.showToast({ title: error.message || 'AI 请求失败', icon: 'none' })
    } finally {
      this.setData({ aiLoading: false })
    }
  },

  openPolisher(e) {
    this.setData({ polishVisible: true, polishText: e.currentTarget.dataset.text || '', polishResult: '', polishModule: e.currentTarget.dataset.module || '' })
  },

  closePolisher() {
    this.setData({ polishVisible: false })
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
      const response = await aiApi.polish(this.data.polishText.trim(), this.data.polishModule)
      this.setData({ polishResult: response.polished_text || response.response || '' })
    } catch (error) {
      wx.showToast({ title: error.message || '润色失败', icon: 'none' })
    } finally {
      this.setData({ polishLoading: false })
    }
  },

  applyPolish() {
    this.setData({ polishText: this.data.polishResult, polishResult: '' })
  },

  async uploadFile() {
    if (!this.data.resume) return
    const that = this
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      success: async function (result) {
        if (!result.tempFiles || !result.tempFiles.length) return
        const file = result.tempFiles[0]
        that.setData({ uploading: true })
        try {
          const detail = await resumeApi.uploadFile(that.data.resume.id, file.path, 'file', {})
          that.applyDetail(detail, that.data.tags)
          wx.showToast({ title: '上传成功', icon: 'success' })
        } catch (error) {
          wx.showToast({ title: error.message || '上传失败', icon: 'none' })
        } finally {
          that.setData({ uploading: false })
        }
      },
    })
  },
})
