import { resumeApi, tagApi, aiApi, pdfTemplateApi } from '../../../api/index'
import { formatTemplateName, savePdfResponse } from '../../../utils/pdf'

const moduleLabelMap = {
  education: '教育经历',
  work_experience: '工作经历',
  project: '项目经历',
  skill: '技能',
  certificate: '证书',
  award: '奖项',
  language: '语言',
}

function unwrapList(result) {
  if (Array.isArray(result)) return result
  if (result && Array.isArray(result.results)) return result.results
  return []
}

function formatDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'), String(date.getDate()).padStart(2, '0')].join('-')
}

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return formatDate(value) + ' ' + [String(date.getHours()).padStart(2, '0'), String(date.getMinutes()).padStart(2, '0')].join(':')
}

function joinText(values, separator) {
  return (values || []).filter(function (item) {
    return item !== undefined && item !== null && item !== ''
  }).join(separator || ', ')
}

function formatModuleNames(values) {
  return joinText((values || []).map(function (item) {
    return moduleLabelMap[item] || item
  }), '、') || '-'
}

function emptyVisitor() {
  return {
    enabled: false,
    url: '',
    expires: '-',
    allowDownload: false,
    aiModeEnabled: false,
    aiEnabled: false,
    quota: 0,
    used: 0,
    remaining: 0,
    publicModules: [],
    publicModulesText: '-',
  }
}

Page({
  data: {
    resumeId: '',
    loading: false,
    resume: null,
    tagList: [],
    tags: [],
    selectedTagIds: [],
    sections: [],
    moduleList: [],
    exportModuleNames: [],
    visitor: emptyVisitor(),
    visitorLoading: false,
    aiVisible: false,
    aiQuestion: '',
    aiSubmitting: false,
    aiAnswer: '',
    downloadingPdf: false,
    pdfTemplates: [],
  },

  onLoad(options) {
    this.setData({ resumeId: options && options.id ? String(options.id) : '' })
    this.loadPage()
  },

  onPullDownRefresh() {
    this.loadPage().finally(function () {
      wx.stopPullDownRefresh()
    })
  },

  refresh() {
    this.loadPage()
  },

  toggleAi() {
    if (!this.data.resume) return
    this.setData({ aiVisible: !this.data.aiVisible })
  },

  closeAi() {
    this.setData({ aiVisible: false })
  },

  onAiInput(e) {
    this.setData({ aiQuestion: e.detail.value })
  },

  async askAi() {
    if (!this.data.resume) return

    const question = (this.data.aiQuestion || '').trim()
    if (!question) {
      wx.showToast({ title: '请输入问题', icon: 'none' })
      return
    }
    if (this.data.aiSubmitting) return

    const prompt = [
      '你是当前用户的简历助手，只能基于当前登录用户自己的简历信息回答。',
      '当前简历标题：' + (this.data.resume.title || '-'),
      '当前简历状态：' + (this.data.resume.status || '-'),
      '当前简历简介：' + (this.data.resume.summary || '-'),
      '已启用模块：' + formatModuleNames(this.data.resume.enabled_modules),
      '用户问题：' + question,
    ].join('\n')

    this.setData({ aiSubmitting: true })
    try {
      const data = await aiApi.chat(prompt)
      this.setData({
        aiAnswer: data.response || '暂无回复',
        aiQuestion: '',
        aiVisible: true,
      })
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : 'AI 请求失败', icon: 'none' })
    } finally {
      this.setData({ aiSubmitting: false })
    }
  },

  async fetchDetail() {
    // 优先使用 my-resume 接口获取当前用户的简历（合管理员）
    try {
      const myResume = await resumeApi.myResume()
      if (myResume && myResume.id) {
        this.setData({ resumeId: String(myResume.id) })
        return myResume
      }
    } catch (_) {
      // my-resume 失败，回退到列表查询
    }

    if (this.data.resumeId) {
      return resumeApi.detail(this.data.resumeId)
    }

    const listResult = await resumeApi.list({ page_size: 50 })
    const resumeItem = unwrapList(listResult)[0]
    if (!resumeItem) return null

    this.setData({ resumeId: String(resumeItem.id) })
    return resumeApi.detail(resumeItem.id)
  },

  async loadPage() {
    if (this.data.loading) return

    this.setData({ loading: true })
    try {
      const result = await Promise.all([
        this.fetchDetail(),
        tagApi.list({ page_size: 100 }).catch(function () { return null }),
      ])
      const detail = result[0]
      const tagList = unwrapList(result[1])

      if (!detail) {
        this.setData({
          resume: null,
          tagList: tagList,
          tags: tagList,
          selectedTagIds: [],
          sections: [],
          moduleList: [],
          exportModuleNames: [],
          visitor: emptyVisitor(),
          aiVisible: false,
          aiQuestion: '',
          aiSubmitting: false,
          aiAnswer: '',
          loading: false,
        })
        return
      }

      this.applyDetail(detail, tagList)
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : '加载失败', icon: 'none' })
      this.setData({ loading: false })
    }
  },

  applyDetail(detail, tagList) {
    const selectedTagIds = (detail.tags_detail || []).map(function (item) { return item.id })
    const tags = (tagList || []).map(function (tag) {
      return Object.assign({}, tag, { selected: selectedTagIds.indexOf(tag.id) >= 0 })
    })

    this.setData({
      resume: detail,
      tagList: tagList || [],
      tags: tags,
      selectedTagIds: selectedTagIds,
      sections: this.buildSections(detail),
      moduleList: this.buildModuleOptions(detail),
      exportModuleNames: detail.enabled_modules || [],
      visitor: this.buildVisitor(detail),
      aiAnswer: '',
      loading: false,
    })
  },

  buildSections(detail) {
    const sections = []
    const enabledModulesText = formatModuleNames(detail.enabled_modules)

    sections.push({
      title: '概览',
      kind: 'text',
      items: [
        '标题：' + (detail.title || '-'),
        '状态：' + (detail.status || '-'),
        '简介：' + (detail.summary || '-'),
        '模块：' + enabledModulesText,
      ],
    })

    if (detail.educations && detail.educations.length) {
      sections.push({
        title: '教育经历',
        kind: 'object',
        items: detail.educations.map(function (item) {
          return {
            title: (item.school || '-') + ' · ' + (item.major || '-'),
            desc: joinText([item.degree, formatDate(item.start_date) + ' ~ ' + formatDate(item.end_date), item.description], '\n'),
          }
        }),
      })
    }

    if (detail.work_experiences && detail.work_experiences.length) {
      sections.push({
        title: '工作经历',
        kind: 'object',
        items: detail.work_experiences.map(function (item) {
          return {
            title: (item.company || '-') + ' · ' + (item.position || '-'),
            desc: joinText([formatDate(item.start_date) + ' ~ ' + formatDate(item.end_date), item.description], '\n'),
          }
        }),
      })
    }

    if (detail.projects && detail.projects.length) {
      sections.push({
        title: '项目经历',
        kind: 'object',
        items: detail.projects.map(function (item) {
          return {
            title: item.name || '-',
            desc: joinText([item.role, item.tech_stack, formatDate(item.start_date) + ' ~ ' + formatDate(item.end_date), item.description], '\n'),
          }
        }),
      })
    }

    if (detail.skills && detail.skills.length) {
      sections.push({
        title: '技能',
        kind: 'object',
        items: detail.skills.map(function (item) {
          return {
            title: item.name || '-',
            desc: joinText(['分类：' + (item.category || '-'), '熟练度：' + String(item.level || 0) + '%'], '\n'),
          }
        }),
      })
    }

    return sections
  },

  buildVisitor(detail) {
    const quota = Number(detail.visitor_ai_quota || 0)
    const used = Number(detail.visitor_ai_used || 0)

    return {
      enabled: !!detail.visitor_enabled,
      url: detail.visitor_url || '',
      expires: formatDateTime(detail.visitor_expires),
      allowDownload: !!detail.visitor_allow_download,
      aiModeEnabled: !!detail.visitor_ai_mode_enabled,
      aiEnabled: !!detail.visitor_ai_enabled,
      quota: quota,
      used: used,
      remaining: Math.max(0, quota - used),
      publicModules: detail.public_modules || [],
      publicModulesText: formatModuleNames(detail.public_modules),
    }
  },

  buildModuleOptions(detail) {
    const enabledModules = detail.enabled_modules || []
    return Object.keys(moduleLabelMap).map(function (name) {
      return { name: name, label: moduleLabelMap[name], checked: enabledModules.indexOf(name) >= 0 }
    })
  },

  goEdit() {
    const url = this.data.resumeId ? '/pages/user/resume-edit/index?id=' + this.data.resumeId : '/pages/user/resume-edit/index'
    wx.reLaunch({ url: url })
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
      this.applyDetail(detail || this.data.resume, this.data.tagList)
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : '更新失败', icon: 'none' })
      this.loadPage()
    }
  },

  async toggleTag(e) {
    if (!this.data.resume) return

    const id = Number(e.currentTarget.dataset.value)
    const selectedTagIds = this.data.selectedTagIds.slice()
    const index = selectedTagIds.indexOf(id)
    if (index >= 0) selectedTagIds.splice(index, 1)
    else selectedTagIds.push(id)

    this.setData({
      selectedTagIds: selectedTagIds,
      tags: this.data.tags.map(function (tag) {
        return Object.assign({}, tag, { selected: selectedTagIds.indexOf(tag.id) >= 0 })
      }),
    })

    try {
      const detail = await resumeApi.setTags(this.data.resume.id, selectedTagIds)
      this.applyDetail(detail || this.data.resume, this.data.tagList)
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : '更新失败', icon: 'none' })
      this.loadPage()
    }
  },

  async refreshVisitorLink() {
    if (!this.data.resume) return

    this.setData({ visitorLoading: true })
    try {
      const response = await resumeApi.visitorLinkInfo(this.data.resume.id)
      this.setData({ visitor: this.buildVisitor(response || this.data.resume) })
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : '刷新失败', icon: 'none' })
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
        visitor_ai_mode_enabled: true,
        ai_enabled: true,
        ai_quota: 10,
      })
      const merged = Object.assign({}, this.data.resume, response || {})
      this.setData({ resume: merged, visitor: this.buildVisitor(merged) })
      wx.showToast({ title: '已生成', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : '生成失败', icon: 'none' })
    }
  },

  async disableVisitorLink() {
    if (!this.data.resume) return

    try {
      const response = await resumeApi.disableVisitorLink(this.data.resume.id)
      const merged = Object.assign({}, this.data.resume, response || {})
      this.setData({ resume: merged, visitor: this.buildVisitor(merged) })
      wx.showToast({ title: '已停用', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : '停用失败', icon: 'none' })
    }
  },

  copyVisitorLink() {
    if (!this.data.visitor.url) {
      wx.showToast({ title: '暂无链接', icon: 'none' })
      return
    }

    wx.setClipboardData({
      data: this.data.visitor.url,
      success: function () {
        wx.showToast({ title: '已复制', icon: 'success' })
      },
    })
  },

  async loadPdfTemplates() {
    if (this.data.pdfTemplates.length) return this.data.pdfTemplates

    try {
      const res = await pdfTemplateApi.list()
      const templates = Array.isArray(res) ? res : (res.results || [])
      const list = templates.length ? templates : [{ template_key: 'default', name: '默认模板', is_builtin: true }]
      this.setData({ pdfTemplates: list })
      return list
    } catch (error) {
      const fallback = [{ template_key: 'default', name: '默认模板', is_builtin: true }]
      this.setData({ pdfTemplates: fallback })
      return fallback
    }
  },

  choosePdfTemplate(templates) {
    const list = (templates || []).slice(0, 6)
    const items = list.map(function (item) {
      return formatTemplateName(item)
    })

    return new Promise(function (resolve, reject) {
      wx.showActionSheet({
        itemList: items,
        success: function (result) {
          resolve(list[result.tapIndex])
        },
        fail: function (error) {
          reject(error)
        },
      })
    })
  },

  async exportPdf() {
    if (!this.data.resume) return
    if (this.data.downloadingPdf) return

    this.setData({ downloadingPdf: true })
    try {
      const templates = await this.loadPdfTemplates()
      const template = await this.choosePdfTemplate(templates)
      if (!template) return

      const modules = this.data.exportModuleNames.length ? this.data.exportModuleNames : this.data.resume.enabled_modules
      const response = await resumeApi.exportPdf(this.data.resume.id, modules, template.template_key)
      const filePath = savePdfResponse(response, this.data.resume.title || 'resume', template.name)
      wx.openDocument({ filePath: filePath, fileType: 'pdf' })
    } catch (error) {
      if (error && error.errMsg && error.errMsg.indexOf('cancel') >= 0) return
      wx.showToast({ title: error && error.message ? error.message : '导出失败', icon: 'none' })
    } finally {
      this.setData({ downloadingPdf: false })
    }
  },
})
