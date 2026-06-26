/**
 * 应用入口文件 —— Vue 3 应用的启动点。
 *
 * 作用：初始化 Vue 应用，注册全局插件和组件。
 *
 * 知识点（Vue 3 启动流程）：
 * 1. createApp()：创建 Vue 应用实例
 * 2. app.use()：注册插件（Pinia 状态管理、Vue Router 路由、Element Plus UI 库）
 * 3. app.component()：注册全局组件（如图标组件）
 * 4. app.mount('#app')：将应用挂载到 HTML 中 id="app" 的元素上
 */
import { createApp } from 'vue'         // Vue 3 核心：创建应用实例
import { createPinia } from 'pinia'     // Pinia：Vue 3 的状态管理库（类似 Vuex 的替代品）
import ElementPlus from 'element-plus'  // Element Plus：基于 Vue 3 的 UI 组件库
import 'element-plus/dist/index.css'    // Element Plus 的 CSS 样式文件
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'  // Element Plus 中文语言包
import * as ElementPlusIconsVue from '@element-plus/icons-vue'  // Element Plus 图标库

import App from './App.vue'             // 根组件
import router from './router'           // 路由配置

const app = createApp(App)              // 创建 Vue 应用实例

// 批量注册所有 Element Plus 图标为全局组件
// 这样在任何组件中都能直接使用 <el-icon><Document /></el-icon>
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())                  // 注册 Pinia 状态管理插件
app.use(router)                         // 注册 Vue Router 路由插件
app.use(ElementPlus, { locale: zhCn })  // 注册 Element Plus 插件，设置为中文

app.mount('#app')                       // 挂载应用到 DOM