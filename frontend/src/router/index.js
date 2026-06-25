import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  // Visitor route (public, no auth)
  {
    path: '/visitor/:token',
    name: 'VisitorResume',
    component: () => import('@/views/VisitorPage.vue'),
    meta: { requiresAuth: false },
  },
  // Admin routes
  {
    path: '/admin',
    component: () => import('@/components/Layout.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '管理面板', icon: 'DataBoard' },
      },
      {
        path: 'users',
        name: 'UserManage',
        component: () => import('@/views/admin/UserManage.vue'),
        meta: { title: '用户管理', icon: 'User' },
      },
      {
        path: 'resumes',
        name: 'ResumeManage',
        component: () => import('@/views/admin/ResumeManage.vue'),
        meta: { title: '简历管理', icon: 'Document' },
      },
      {
        path: 'tags',
        name: 'TagManage',
        component: () => import('@/views/admin/TagManage.vue'),
        meta: { title: '标签管理', icon: 'PriceTag' },
      },
      {
        path: 'ai-logs',
        name: 'AiLogs',
        component: () => import('@/views/admin/AiLogs.vue'),
        meta: { title: 'AI日志', icon: 'ChatDotRound' },
      },
      {
        path: 'audit-logs',
        name: 'AuditLog',
        component: () => import('@/views/admin/AuditLog.vue'),
        meta: { title: '操作审计', icon: 'Monitor' },
      },
    ],
  },
  // Normal user routes
  {
    path: '/user',
    component: () => import('@/components/Layout.vue'),
    meta: { requiresAuth: true, role: 'user' },
    children: [
      {
        path: '',
        name: 'ResumeDetail',
        component: () => import('@/views/user/ResumeDetail.vue'),
        meta: { title: '我的简历', icon: 'User' },
      },
      {
        path: 'edit',
        name: 'ResumeEdit',
        component: () => import('@/views/user/ResumeEdit.vue'),
        meta: { title: '编辑简历', icon: 'Edit' },
      },
    ],
  },
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // Public routes (login, visitor)
  if (to.meta.requiresAuth === false) {
    if (to.name === 'Login' && userStore.isLoggedIn) {
      next(userStore.isAdmin ? '/admin' : '/user')
    } else {
      next()
    }
    return
  }

  if (!userStore.isLoggedIn) {
    next('/login')
    return
  }

  if (to.meta.role && userStore.userInfo?.role !== to.meta.role) {
    next(userStore.isAdmin ? '/admin' : '/user')
    return
  }

  next()
})

export default router