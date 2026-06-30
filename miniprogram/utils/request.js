import config from './config'
import { getAccessToken, getRefreshToken, clearAuth, setAuth } from './auth'

let refreshing = false
let waitQueue = []

function buildUrl(url) {
  if (/^https?:\/\//.test(url)) return url
  return config.baseUrl + url
}

function serializeQuery(params = {}) {
  const parts = []
  Object.keys(params).forEach(function (key) {
    const value = params[key]
    if (value === undefined || value === null || value === '') return
    parts.push(encodeURIComponent(key) + '=' + encodeURIComponent(value))
  })
  return parts.length ? '?' + parts.join('&') : ''
}

function normalizeError(res) {
  const body = res && res.data ? res.data : {}
  const message = body.detail || body.message || '请求失败(' + (res ? res.statusCode : 'network') + ')'
  return new Error(message)
}

function refreshToken() {
  const refresh = getRefreshToken()
  if (!refresh) return Promise.reject(new Error('缺少刷新令牌'))

  return new Promise(function (resolve, reject) {
    wx.request({
      url: buildUrl('/users/token/refresh/'),
      method: 'POST',
      data: { refresh: refresh },
      header: { 'content-type': 'application/json' },
      success: function (res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          const access = (res.data && res.data.access) || ''
          const nextRefresh = (res.data && res.data.refresh) || refresh
          setAuth({ access: access, refresh: nextRefresh })
          resolve(access)
          return
        }
        reject(normalizeError(res))
      },
      fail: function (err) {
        if (err && /timeout/i.test(err.errMsg || '')) {
          reject(new Error('请求超时，请确认后端已启动，且小程序基址配置正确'))
          return
        }
        reject(err)
      },
    })
  })
}

function flushQueue(error, retryRequest) {
  const queued = waitQueue
  waitQueue = []
  queued.forEach(function (item) {
    if (error) {
      item.reject(error)
      return
    }
    retryRequest().then(item.resolve).catch(item.reject)
  })
}

function handle401(retryRequest) {
  if (refreshing) {
    return new Promise(function (resolve, reject) {
      waitQueue.push({ resolve: resolve, reject: reject, retryRequest: retryRequest })
    })
  }

  refreshing = true
  return refreshToken()
    .then(function () {
      return retryRequest()
        .then(function (result) {
          flushQueue(null, retryRequest)
          return result
        })
        .catch(function (error) {
          flushQueue(error, retryRequest)
          throw error
        })
    })
    .catch(function (error) {
      clearAuth()
      flushQueue(error, retryRequest)
      throw error
    })
    .finally(function () {
      refreshing = false
    })
}

function request(opts) {
  const url = opts.url
  const method = opts.method || 'GET'
  const data = opts.data || {}
  const params = opts.params || {}
  const header = opts.header || {}
  const skipAuth = opts.skipAuth || false
  const responseType = opts.responseType || 'json'
  const timeout = opts.timeout || config.timeout || 15000

  return new Promise(function (resolve, reject) {
    const finalHeader = { 'content-type': 'application/json' }
    Object.keys(header).forEach(function (key) {
      finalHeader[key] = header[key]
    })

    if (!skipAuth) {
      const token = getAccessToken()
      if (token) finalHeader.Authorization = 'Bearer ' + token
    }

    wx.request({
      url: buildUrl(url) + serializeQuery(params),
      method: method,
      data: data,
      header: finalHeader,
      responseType: responseType,
      timeout: timeout,
      success: function (res) {
        if (responseType !== 'json') {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res)
            return
          }
          reject(normalizeError(res))
          return
        }

        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }

        if (res.statusCode === 401 && !skipAuth) {
          handle401(function () {
            return request(opts)
          }).then(resolve).catch(reject)
          return
        }

        reject(normalizeError(res))
      },
      fail: function (err) {
        if (err && /timeout/i.test(err.errMsg || '')) {
          reject(new Error('请求超时，请确认后端已启动，且小程序基址配置正确'))
          return
        }
        reject(err)
      },
    })
  })
}

function get(url, params, options) {
  return request(Object.assign({ url: url, method: 'GET', params: params || {} }, options || {}))
}

function post(url, data, options) {
  return request(Object.assign({ url: url, method: 'POST', data: data || {} }, options || {}))
}

function del(url, data, options) {
  return request(Object.assign({ url: url, method: 'DELETE', data: data || {} }, options || {}))
}

function uploadFile(url, filePath, name, formData) {
  const token = getAccessToken()
  return new Promise(function (resolve, reject) {
    wx.uploadFile({
      url: buildUrl(url),
      filePath: filePath,
      name: name || 'file',
      formData: formData || {},
      header: token ? { Authorization: 'Bearer ' + token } : {},
      success: function (res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(res.data))
          } catch (error) {
            resolve(res.data)
          }
          return
        }
        reject(new Error('上传失败'))
      },
      fail: function (err) {
        if (err && /timeout/i.test(err.errMsg || '')) {
          reject(new Error('请求超时，请确认后端已启动，且小程序基址配置正确'))
          return
        }
        reject(err)
      },
    })
  })
}

function download(url, options) {
  const params = (options && options.params) || {}
  const header = (options && options.header) || {}
  const skipAuth = (options && options.skipAuth) || false
  const finalHeader = {}
  Object.keys(header).forEach(function (key) {
    finalHeader[key] = header[key]
  })
  if (!skipAuth) {
    const token = getAccessToken()
    if (token) finalHeader.Authorization = 'Bearer ' + token
  }

  return new Promise(function (resolve, reject) {
    wx.downloadFile({
      url: buildUrl(url) + serializeQuery(params),
      header: finalHeader,
      success: function (res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res)
          return
        }
        reject(normalizeError(res))
      },
      fail: function (err) {
        if (err && /timeout/i.test(err.errMsg || '')) {
          reject(new Error('请求超时，请确认后端已启动，且小程序基址配置正确'))
          return
        }
        reject(err)
      },
    })
  })
}

export default {
  request: request,
  get: get,
  post: post,
  patch: function (url, data, options) {
    return request(Object.assign({ url: url, method: 'PATCH', data: data || {} }, options || {}))
  },
  delete: del,
  uploadFile: uploadFile,
  download: download,
}

