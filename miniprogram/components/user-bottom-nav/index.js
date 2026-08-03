Component({
  properties: {
    active: {
      type: String,
      value: 'detail',
    },
  },
  methods: {
    switchPage(e) {
      const page = e.currentTarget.dataset.page
      if (page === this.properties.active) return
      const url = page === 'edit' ? '/pages/user/resume-edit/index' : '/pages/user/resume-detail/index'
      wx.reLaunch({ url: url })
    },
  },
})