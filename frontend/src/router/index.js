/**
 * 路由配置文件 —— 定义应用的所有页面路由。
 *
 * 作用：根据 URL 路径决定渲染哪个页面组件。
 *
 * 知识点（Vue Router 核心概念）：
 * 1. 路由（Route）：URL 路径到组件的映射关系
 * 2. 路由懒加载：() => import('...') 按需加载组件，减少首次加载时间
 * 3. 嵌套路由（children）：在 Layout 组件内部渲染子页面
 * 4. 导航守卫（beforeEach）：在每次路由跳转前执行的钩子函数，用于权限控制
 * 5. meta：路由元数据，用于存储额外信息（如标题、图标、权限要求）
 *
 * 路由结构：
 * - /login → 登录页（公开）
 * - /visitor/:token → 访客简历页（公开）
 * - /admin/* → 管理员后台页面（需 admin 权限）
 * - /user/* → 普通用户页面（需 user 权限）
 * - / → 重定向到登录页
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

// 路由表 —— 定义所有页面的 URL 和对应组件
const routes = [
  // ========== 公开页面（无需登录） ==========
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),   // 懒加载：只在访问此路由时才加载组件
    meta: { requiresAuth: false },                   // 不需要登录认证
  },
  // 访客简历页：通过唯一 token 访问，无需登录
  // token 是每个简历的唯一标识，由后端生成
  {
    path: '/visitor/:token',
    name: 'VisitorResume',
    component: () => import('@/views/VisitorPage.vue'),
    meta: { requiresAuth: false },
  },

  // ========== 管理员页面（需要 admin 角色） ==========
  {
    path: '/admin',
    component: () => import('@/components/Layout.vue'),  // 公共布局组件（侧边栏+顶栏）
    meta: { requiresAuth: true, role: 'admin' },          // 需要登录且角色为 admin
    children: [                                            // 嵌套路由：在 Layout 内部渲染
      {
        path: '',                                          // /admin → 管理面板首页
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '管理面板', icon: 'DataBoard' },    // 用于面包屑和菜单显示
      },
      {
        path: 'users',                                     // /admin/users → 用户管理
        name: 'UserManage',
        component: () => import('@/views/admin/UserManage.vue'),
        meta: { title: '用户管理', icon: 'User' },
      },
      {
        path: 'resumes',                                   // /admin/resumes → 简历管理
        name: 'ResumeManage',
        component: () => import('@/views/admin/ResumeManage.vue'),
        meta: { title: '简历管理', icon: 'Document' },
      },
      {
        path: 'pdf-templates',                              // /admin/pdf-templates → PDF模板管理
        name: 'PdfTemplateManage',
        component: () => import('@/views/admin/PdfTemplateManage.vue'),
        meta: { title: 'PDF模板', icon: 'Files' },
      },
      {
        path: 'tags',                                      // /admin/tags → 标签管理
        name: 'TagManage',
        component: () => import('@/views/admin/TagManage.vue'),
        meta: { title: '标签管理', icon: 'PriceTag' },
      },
      {
        path: 'ai-logs',                                   // /admin/ai-logs → AI 日志
        name: 'AiLogs',
        component: () => import('@/views/admin/AiLogs.vue'),
        meta: { title: 'AI日志', icon: 'ChatDotRound' },
      },
      {
        path: 'audit-logs',                                // /admin/audit-logs → 操作审计
        name: 'AuditLog',
        component: () => import('@/views/admin/AuditLog.vue'),
        meta: { title: '操作审计', icon: 'Monitor' },
      },
    ],
  },

  // ========== 普通用户页面（需要 user 角色） ==========
  {
    path: '/user',
    component: () => import('@/components/Layout.vue'),  // 复用同一个 Layout 组件
    meta: { requiresAuth: true, role: 'user' },
    children: [
      {
        path: '',                                          // /user → 我的简历
        name: 'ResumeDetail',
        component: () => import('@/views/user/ResumeDetail.vue'),
        meta: { title: '我的简历', icon: 'User' },
      },
      {
        path: 'edit',                                      // /user/edit → 编辑简历
        name: 'ResumeEdit',
        component: () => import('@/views/user/ResumeEdit.vue'),
        meta: { title: '编辑简历', icon: 'Edit' },
      },
    ],
  },

  // ========== 默认路由 ==========
  {
    path: '/',
    redirect: '/login',    // 访问根路径时重定向到登录页
  },
  {
    path: '/:pathMatch(.*)*',   // 匹配所有未定义的路径
    redirect: '/login',         // 未知路径也重定向到登录页
  },
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),   // 使用 HTML5 History 模式（URL 没有 # 号）
  routes,                        // 注册路由表
})

/**
 * 全局前置导航守卫 —— 每次路由跳转前执行。
 *
 * 作用：控制页面访问权限，实现以下逻辑：
 * 1. 公开页面（login、visitor）：直接放行
 * 2. 已登录用户访问登录页：重定向到对应后台
 * 3. 未登录用户访问受保护页面：重定向到登录页
 * 4. 角色不匹配：重定向到对应角色的首页
 *
 * 知识点：
 * - to：目标路由对象
 * - from：来源路由对象
 * - next()：放行（可以传路径重定向）
 */
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 公开页面：直接放行
  if (to.meta.requiresAuth === false) {
    // 已登录用户访问登录页时，重定向到对应后台
    if (to.name === 'Login' && userStore.isLoggedIn) {
      next(userStore.isAdmin ? '/admin' : '/user')
    } else {
      next()
    }
    return
  }

  // 未登录用户访问受保护页面：重定向到登录页
  if (!userStore.isLoggedIn) {
    next('/login')
    return
  }

  // 角色不匹配：重定向到对应角色的首页
  // 例如：普通用户访问 /admin 页面，会被重定向到 /user
  if (to.meta.role && userStore.userInfo?.role !== to.meta.role) {
    next(userStore.isAdmin ? '/admin' : '/user')
    return
  }

  // 权限检查通过，放行
  next()
})

export default router
