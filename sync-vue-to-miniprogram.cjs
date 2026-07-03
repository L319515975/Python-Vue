#!/usr/bin/env node
/**
 * Vue3 -> 微信小程序同步脚本。
 *
 * 这个脚本不是把 Vue 单文件组件硬翻译成 WXML。
 * 原因：Vue/Element Plus 和微信小程序的运行时、组件模型、样式隔离都不同，机械转换通常不可维护。
 *
 * 它做三件更稳定的事：
 * 1. 维护小程序 app.json 页面清单，避免新增页面后漏注册。
 * 2. 从 Vue3 路由和 API 定义中生成同步快照，方便核对小程序是否漏功能或接口。
 * 3. 支持 --watch，当前端 frontend/src 变化时自动重新生成快照。
 *
 * 使用：
 * - 手动同步一次：node sync-vue-to-miniprogram.cjs
 * - 持续监听同步：node sync-vue-to-miniprogram.cjs --watch
 */
const fs = require('fs')
const path = require('path')
const crypto = require('crypto')

const rootDir = __dirname
const frontendSrcDir = path.join(rootDir, 'frontend', 'src')
const miniprogramDir = path.join(rootDir, 'miniprogram')
const generatedDir = path.join(miniprogramDir, 'generated')

const expectedMiniPages = [
  'pages/login/index',
  'pages/user/resume-detail/index',
  'pages/user/resume-edit/index',
  'pages/visitor/index',
  'pages/admin/dashboard/index',
  'pages/admin/user-manage/index',
  'pages/admin/resume-manage/index',
  'pages/admin/tag-manage/index',
  'pages/admin/ai-logs/index',
  'pages/admin/audit-log/index',
  'pages/admin/hr-ai-logs/index',
]

const pageTitles = {
  'pages/login/index': '登录',
  'pages/user/resume-detail/index': '我的简历',
  'pages/user/resume-edit/index': '编辑简历',
  'pages/visitor/index': '访客查看',
  'pages/admin/dashboard/index': '管理后台',
  'pages/admin/user-manage/index': '用户管理',
  'pages/admin/resume-manage/index': '简历管理',
  'pages/admin/tag-manage/index': '标签管理',
  'pages/admin/ai-logs/index': 'AI 日志',
  'pages/admin/audit-log/index': '审计日志',
  'pages/admin/hr-ai-logs/index': 'HR AI 日志',
}

function readText(filePath) {
  if (!fs.existsSync(filePath)) return ''
  return fs.readFileSync(filePath, 'utf8').replace(/^\uFEFF/, '')
}

function writeText(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true })
  fs.writeFileSync(filePath, content, 'utf8')
}

function fileHash(filePath) {
  const content = readText(filePath)
  return crypto.createHash('sha256').update(content).digest('hex')
}

function listFiles(dir, extensions, output = []) {
  if (!fs.existsSync(dir)) return output
  fs.readdirSync(dir, { withFileTypes: true }).forEach(function (entry) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (!['node_modules', 'dist', '.git'].includes(entry.name)) listFiles(fullPath, extensions, output)
      return
    }
    if (extensions.includes(path.extname(entry.name))) output.push(fullPath)
  })
  return output
}

function extractApis(apiSource) {
  const apis = []
  const apiCallPattern = /request\.(get|post|put|patch|delete|download|uploadFile)\((`[^`]+`|'[^']+'|"[^"]+")/g
  let match
  while ((match = apiCallPattern.exec(apiSource))) {
    apis.push({ method: match[1].toUpperCase(), url: match[2].slice(1, -1) })
  }
  return apis
}

function extractRoutes(routerSource) {
  const routes = []
  const routePattern = /\{[\s\S]*?path:\s*['"]([^'"]+)['"][\s\S]*?name:\s*['"]([^'"]+)['"][\s\S]*?meta:\s*\{([\s\S]*?)\}[\s\S]*?\}/g
  let match
  while ((match = routePattern.exec(routerSource))) {
    const titleMatch = match[3].match(/title:\s*['"]([^'"]+)['"]/) || []
    routes.push({ path: match[1], name: match[2], title: titleMatch[1] || '' })
  }
  return routes
}

function syncAppJson() {
  const appJsonPath = path.join(miniprogramDir, 'app.json')
  const appJson = JSON.parse(readText(appJsonPath) || '{}')
  const existingPages = Array.isArray(appJson.pages) ? appJson.pages : []
  const mergedPages = expectedMiniPages.concat(existingPages.filter(function (page) {
    return !expectedMiniPages.includes(page)
  }))

  appJson.pages = mergedPages
  appJson.window = Object.assign({
    navigationBarTitleText: '智能简历系统',
    navigationBarBackgroundColor: '#ffffff',
    navigationBarTextStyle: 'black',
    backgroundTextStyle: 'light',
  }, appJson.window || {})
  appJson.style = appJson.style || 'v2'
  appJson.lazyCodeLoading = appJson.lazyCodeLoading || 'requiredComponents'
  appJson.usingComponents = appJson.usingComponents || {}

  writeText(appJsonPath, JSON.stringify(appJson, null, 2) + '\n')
}

function ensurePageJsonFiles() {
  expectedMiniPages.forEach(function (page) {
    const jsonPath = path.join(miniprogramDir, page + '.json')
    const content = fs.existsSync(jsonPath) ? JSON.parse(readText(jsonPath) || '{}') : {}
    content.navigationBarTitleText = content.navigationBarTitleText || pageTitles[page] || '智能简历系统'
    writeText(jsonPath, JSON.stringify(content, null, 2) + '\n')
  })
}

function buildManifest() {
  const apiPath = path.join(frontendSrcDir, 'api', 'index.js')
  const routerPath = path.join(frontendSrcDir, 'router', 'index.js')
  const miniApiPath = path.join(miniprogramDir, 'api', 'index.js')
  const vueFiles = listFiles(frontendSrcDir, ['.vue', '.js', '.ts'])

  return {
    updatedAt: new Date().toISOString(),
    note: '由 sync-vue-to-miniprogram.cjs 自动生成，用于追踪 Vue3 与小程序的同步状态。',
    sourceHashes: {
      frontendApi: fileHash(apiPath),
      frontendRouter: fileHash(routerPath),
      miniprogramApi: fileHash(miniApiPath),
    },
    frontendRoutes: extractRoutes(readText(routerPath)),
    frontendApis: extractApis(readText(apiPath)),
    miniprogramPages: expectedMiniPages,
    frontendSourceFiles: vueFiles.map(function (filePath) {
      return path.relative(rootDir, filePath).replace(/\\/g, '/')
    }),
  }
}

function syncOnce() {
  if (!fs.existsSync(frontendSrcDir)) throw new Error('未找到 frontend/src，无法同步。')
  if (!fs.existsSync(miniprogramDir)) throw new Error('未找到 miniprogram，无法同步。')

  syncAppJson()
  ensurePageJsonFiles()

  const apiPath = path.join(frontendSrcDir, 'api', 'index.js')
  const routerPath = path.join(frontendSrcDir, 'router', 'index.js')
  const manifest = buildManifest()

  writeText(path.join(generatedDir, 'vue-sync-manifest.json'), JSON.stringify(manifest, null, 2) + '\n')
  writeText(path.join(generatedDir, 'frontend-api-index.js.txt'), readText(apiPath))
  writeText(path.join(generatedDir, 'frontend-router-index.js.txt'), readText(routerPath))
  writeText(path.join(generatedDir, 'README.md'), [
    '# Vue3 同步快照',
    '',
    '本目录由根目录 `sync-vue-to-miniprogram.cjs` 自动生成。',
    '',
    '- `vue-sync-manifest.json`：Vue 路由、Vue API、小程序页面和源码哈希。',
    '- `frontend-api-index.js.txt`：Vue3 API 定义快照。',
    '- `frontend-router-index.js.txt`：Vue3 路由定义快照。',
    '',
    '这些文件用于在 Vue3 改动后快速核对小程序是否需要补功能或改接口。',
    '',
  ].join('\n'))

}

function watchFrontend() {
  let timer = null
  const rerun = function () {
    clearTimeout(timer)
    timer = setTimeout(function () {
      try {
        syncOnce()
      } catch (error) {
        void error
      }
    }, 300)
  }

  syncOnce()
  fs.watch(frontendSrcDir, { recursive: true }, function (eventName, filename) {
    if (!filename) return
    const normalized = filename.replace(/\\/g, '/')
    if (normalized.includes('node_modules') || normalized.includes('/dist/')) return
    rerun()
  })
}

if (process.argv.includes('--watch')) {
  watchFrontend()
} else {
  syncOnce()
}
