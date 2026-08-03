import { userApi, resumeApi, tagApi, aiApi } from '../../../api/index'
import { clearAuth, getUserInfo } from '../../../utils/auth'

function unwrapList(result) {
  if (Array.isArray(result)) return result
  if (result && Array.isArray(result.results)) return result.results
  return []
}

function countOf(result) {
  if (!result) return 0
  if (typeof result.count === 'number') return result.count
  if (Array.isArray(result)) return result.length
  return unwrapList(result).length
}

Page({
  data: {
    stats: { userCount: 0, resumeCount: 0, tagCount: 0 },
    loading: false,
    userInfo: null,
    recentLogs: [],
    floatingVisible: false,
    floatingQuestion: '',
    floatingSubmitting: false,
  },

  onLoad() {
    this.setData({ userInfo: getUserInfo() })
    this.refreshPage()
  },

  onPullDownRefresh() {
    this.refreshPage().finally(function () {
      wx.stopPullDownRefresh()
    })
  },

  async refreshPage() {
    this.setData({ loading: true })
    try {
      const [users, resumes, tags, logs] = await Promise.all([
        userApi.list({ page_size: 1 }).catch(function () { return null }),
        resumeApi.list({ page_size: 1 }).catch(function () { return null }),
        tagApi.list({ page_size: 1 }).catch(function () { return null }),
        aiApi.logs({ page_size: 3 }).catch(function () { return null }),
      ])

      this.setData({
        stats: {
          userCount: countOf(users),
          resumeCount: countOf(resumes),
          tagCount: countOf(tags),
        },
        recentLogs: unwrapList(logs),
      })
    } catch (error) {
      wx.showToast({ title: error.message || '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  navTo(e) {
    const url = e.currentTarget.dataset.url
    if (url) wx.navigateTo({ url: url })
  },

  onFloatingInput(e) {
    this.setData({ floatingQuestion: e.detail.value })
  },

  toggleFloating() {
    this.setData({ floatingVisible: !this.data.floatingVisible })
  },

  closeFloating() {
    this.setData({ floatingVisible: false })
  },

  async askFloatingAi() {
    const question = (this.data.floatingQuestion || '').trim()
    if (!question) {
      wx.showToast({ title: '请输入问题', icon: 'none' })
      return
    }
    if (this.data.floatingSubmitting) return

    this.setData({ floatingSubmitting: true })
    try {
      const data = await aiApi.chat('你是管理后台 AI 助手，可以根据指定用户或简历信息回答。用户问题：' + question)
      wx.showModal({
        title: 'AI 回复',
        content: data.response || '暂无回复',
        showCancel: false,
      })
      this.setData({ floatingQuestion: '', floatingVisible: false })
    } catch (error) {
      wx.showToast({ title: error.message || 'AI 请求失败', icon: 'none' })
    } finally {
      this.setData({ floatingSubmitting: false })
    }
  },

  handleLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确认退出当前账号？',
      success: function (result) {
        if (!result.confirm) return
        clearAuth()
        wx.reLaunch({ url: '/pages/login/index' })
      },
    })
  },
})
