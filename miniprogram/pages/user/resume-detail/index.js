import { resumeApi, tagApi } from '../../../api/index'

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

function emptyVisitor() {
  return {
    enabled: false,
    url: '',
    expires: '-',
    allowDownload: false,
    hrEnabled: false,
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

  async fetchDetail() {
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
          loading: false,
        })
        return
      }

      this.applyDetail(detail, tagList)
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : 'Load failed', icon: 'none' })
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
      loading: false,
    })
  },

  buildSections(detail) {
    const sections = []
    const enabledModulesText = joinText(detail.enabled_modules, ', ') || '-'

    sections.push({
      title: 'Overview',
      kind: 'text',
      items: [
        'Title: ' + (detail.title || '-'),
        'Status: ' + (detail.status || '-'),
        'Summary: ' + (detail.summary || '-'),
        'Modules: ' + enabledModulesText,
      ],
    })

    if (detail.educations && detail.educations.length) {
      sections.push({
        title: 'Education',
        kind: 'object',
        items: detail.educations.map(function (item) {
          return {
            title: (item.school || '-') + ' - ' + (item.major || '-'),
            desc: joinText([item.degree, formatDate(item.start_date) + ' ~ ' + formatDate(item.end_date), item.description], '\n'),
          }
        }),
      })
    }

    if (detail.work_experiences && detail.work_experiences.length) {
      sections.push({
        title: 'Work',
        kind: 'object',
        items: detail.work_experiences.map(function (item) {
          return {
            title: (item.company || '-') + ' - ' + (item.position || '-'),
            desc: joinText([formatDate(item.start_date) + ' ~ ' + formatDate(item.end_date), item.description], '\n'),
          }
        }),
      })
    }

    if (detail.projects && detail.projects.length) {
      sections.push({
        title: 'Projects',
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
        title: 'Skills',
        kind: 'object',
        items: detail.skills.map(function (item) {
          return {
            title: item.name || '-',
            desc: joinText(['Category: ' + (item.category || '-'), 'Level: ' + String(item.level || 0) + '%'], '\n'),
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
      hrEnabled: !!detail.visitor_hr_enabled,
      aiEnabled: !!detail.visitor_ai_enabled,
      quota: quota,
      used: used,
      remaining: Math.max(0, quota - used),
      publicModules: detail.public_modules || [],
      publicModulesText: joinText(detail.public_modules, ', ') || '-',
    }
  },

  buildModuleOptions(detail) {
    const moduleMap = {
      education: 'Education',
      work_experience: 'Work',
      project: 'Project',
      skill: 'Skill',
      certificate: 'Certificate',
      award: 'Award',
      language: 'Language',
    }
    const enabledModules = detail.enabled_modules || []
    return Object.keys(moduleMap).map(function (name) {
      return { name: name, label: moduleMap[name], checked: enabledModules.indexOf(name) >= 0 }
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
      wx.showToast({ title: error && error.message ? error.message : 'Update failed', icon: 'none' })
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
      wx.showToast({ title: error && error.message ? error.message : 'Update failed', icon: 'none' })
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
      wx.showToast({ title: error && error.message ? error.message : 'Refresh failed', icon: 'none' })
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
      const merged = Object.assign({}, this.data.resume, response || {})
      this.setData({ resume: merged, visitor: this.buildVisitor(merged) })
      wx.showToast({ title: 'Generated', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : 'Generate failed', icon: 'none' })
    }
  },

  async disableVisitorLink() {
    if (!this.data.resume) return

    try {
      const response = await resumeApi.disableVisitorLink(this.data.resume.id)
      const merged = Object.assign({}, this.data.resume, response || {})
      this.setData({ resume: merged, visitor: this.buildVisitor(merged) })
      wx.showToast({ title: 'Disabled', icon: 'success' })
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : 'Disable failed', icon: 'none' })
    }
  },

  copyVisitorLink() {
    if (!this.data.visitor.url) {
      wx.showToast({ title: 'No link', icon: 'none' })
      return
    }

    wx.setClipboardData({
      data: this.data.visitor.url,
      success: function () {
        wx.showToast({ title: 'Copied', icon: 'success' })
      },
    })
  },

  async exportPdf() {
    if (!this.data.resume) return

    try {
      const modules = this.data.exportModuleNames.length ? this.data.exportModuleNames : this.data.resume.enabled_modules
      const response = await resumeApi.exportPdf(this.data.resume.id, modules)
      const filePath = wx.env.USER_DATA_PATH + '/resume.pdf'
      const fileContent = response && response.data ? response.data : response
      const fileSystem = wx.getFileSystemManager()

      if (fileContent instanceof ArrayBuffer) {
        fileSystem.writeFileSync(filePath, fileContent)
      } else {
        fileSystem.writeFileSync(filePath, fileContent, 'binary')
      }

      wx.openDocument({ filePath: filePath, fileType: 'pdf' })
    } catch (error) {
      wx.showToast({ title: error && error.message ? error.message : 'Export failed', icon: 'none' })
    }
  },
})
