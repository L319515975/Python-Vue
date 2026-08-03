<template>
  <el-container class="layout-shell">
    <div v-if="mobileMenuVisible" class="mobile-overlay" @click="mobileMenuVisible = false"></div>

    <el-aside :width="asideWidth" class="layout-aside" :class="{ 'is-mobile-open': mobileMenuVisible && isMobile }">
      <div class="logo-area">
        <div class="logo-icon">
          <el-icon :size="20" color="#fff"><Document /></el-icon>
        </div>
        <span v-show="!isCollapse || isMobile" class="logo-text">ResumeAI</span>
      </div>

      <div class="menu-section-title" v-show="!isCollapse || isMobile">
        <span>{{ isAdmin ? '管理中心' : '工作台' }}</span>
      </div>

      <el-menu
        :default-active="currentRoute"
        :collapse="isCollapse && !isMobile"
        :router="true"
        :collapse-transition="false"
        background-color="transparent"
        text-color="rgba(255,255,255,0.56)"
        active-text-color="#ffffff"
        class="side-menu"
        @select="mobileMenuVisible = false"
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path" class="menu-item">
          <el-icon class="menu-icon"><component :is="item.meta?.icon || 'Document'" /></el-icon>
          <template #title>
            <span class="menu-label">{{ item.meta?.title }}</span>
          </template>
        </el-menu-item>
      </el-menu>

      <div class="aside-footer" v-show="!isCollapse || isMobile">
        <div class="aside-footer-text">v2.0.0</div>
      </div>
    </el-aside>

    <el-container class="layout-content">
      <el-header class="layout-header" height="64px">
        <div class="header-left">
          <el-icon v-if="isMobile" class="hamburger-btn" :size="20" @click="mobileMenuVisible = !mobileMenuVisible">
            <Expand />
          </el-icon>
          <el-icon v-else class="collapse-btn" :size="18" @click="isCollapse = !isCollapse">
            <component :is="isCollapse ? 'Expand' : 'Fold'" />
          </el-icon>
          <el-breadcrumb separator="/" class="header-breadcrumb">
            <el-breadcrumb-item>{{ isAdmin ? '管理后台' : '个人中心' }}</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentTitle">{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-dropdown">
              <el-avatar :size="32" class="user-avatar">{{ userInitial }}</el-avatar>
              <span class="username">{{ userStore.username || '用户' }}</span>
              <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人信息
                </el-dropdown-item>
                <el-dropdown-item command="password">
                  <el-icon><Lock /></el-icon>修改密码
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="layout-main">
        <div class="content-wrapper">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </el-main>
    </el-container>

    <el-dialog v-model="pwdDialogVisible" title="修改密码" :width="isMobile ? '92%' : '420px'">
      <el-form :model="pwdForm" label-position="top">
        <el-form-item label="原密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password clearable />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password clearable />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword">确认</el-button>
      </template>
    </el-dialog>

    <AiAssistant />
  </el-container>
</template>

<script setup>
import { ref, computed, defineAsyncComponent, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useMobile } from '@/composables/useMobile'
import { userApi } from '@/api'
import { ElMessage } from 'element-plus'

const AiAssistant = defineAsyncComponent(() => import('@/components/AiAssistant.vue'))

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { isMobile } = useMobile()

const isCollapse = ref(false)
const mobileMenuVisible = ref(false)
const pwdDialogVisible = ref(false)
const pwdForm = ref({ old_password: '', new_password: '' })

const isAdmin = computed(() => userStore.isAdmin)
const currentRoute = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '')
const userInitial = computed(() => (userStore.username || 'U').slice(0, 1).toUpperCase())
const asideWidth = computed(() => {
  if (isMobile.value) return mobileMenuVisible.value ? '248px' : '0px'
  return isCollapse.value ? '72px' : '248px'
})

const menuItems = computed(() => {
  const parent = isAdmin.value ? '/admin' : '/user'
  const parentRoute = router.options.routes.find(routeItem => routeItem.path === parent)
  return (parentRoute?.children || [])
    .filter(child => child.meta?.title)
    .map(child => ({
      path: child.path ? `${parent}/${child.path}` : parent,
      meta: child.meta,
    }))
})

watch(() => route.path, () => {
  mobileMenuVisible.value = false
})

function handleCommand(cmd) {
  if (cmd === 'logout') {
    userStore.logout()
    router.push('/login')
    return
  }
  if (cmd === 'password') {
    pwdForm.value = { old_password: '', new_password: '' }
    pwdDialogVisible.value = true
    return
  }
  if (cmd === 'profile') {
    router.push(isAdmin.value ? '/admin' : '/user')
  }
}

async function handleChangePassword() {
  try {
    await userApi.changePassword(pwdForm.value)
    ElMessage.success('密码修改成功')
    pwdDialogVisible.value = false
  } catch {
    // 统一由请求拦截器处理
  }
}
</script>

<style scoped>
.layout-shell {
  height: 100vh;
  overflow: hidden;
  background: var(--color-canvas-parchment);
}

/* ===== Sidebar ===== */
.layout-aside {
  height: 100vh;
  background: linear-gradient(180deg, #0f1729 0%, #1a2332 100%);
  overflow: hidden;
  transition: width 0.24s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
}

.logo-area {
  height: 64px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--color-primary) 0%, #0052a3 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3);
}

.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  letter-spacing: 0.3px;
}

.menu-section-title {
  padding: 20px 20px 8px;
  font-size: 11px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.32);
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.side-menu {
  flex: 1;
  border-right: none !important;
  overflow-y: auto;
  padding: 8px 12px;
}

.side-menu :deep(.el-menu-item) {
  height: 44px;
  margin: 2px 0;
  border-radius: 8px;
  transition: all 0.2s ease-out;
}

.side-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.06) !important;
  color: #fff !important;
}

.side-menu :deep(.el-menu-item.is-active) {
  background: var(--color-primary) !important;
  color: #fff !important;
  box-shadow: 0 4px 12px rgba(0, 102, 204, 0.35);
}

.side-menu :deep(.el-menu-item.is-active .menu-icon) {
  color: #fff;
}

.menu-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.menu-label {
  font-size: 14px;
  font-weight: 500;
}

.aside-footer {
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.aside-footer-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.28);
}

/* ===== Content Area ===== */
.layout-content {
  height: 100vh;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: saturate(180%) blur(16px);
  -webkit-backdrop-filter: saturate(180%) blur(16px);
  border-bottom: 1px solid var(--color-divider-soft);
  padding: 0 24px;
  flex-shrink: 0;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.header-breadcrumb {
  font-size: 14px;
}

.collapse-btn,
.hamburger-btn {
  cursor: pointer;
  color: var(--color-ink-muted-48);
  transition: all 0.2s ease-out;
  padding: 6px;
  border-radius: 6px;
}

.collapse-btn:hover,
.hamburger-btn:hover {
  color: var(--color-primary);
  background: rgba(0, 102, 204, 0.06);
}

.hamburger-btn {
  display: none;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: var(--color-ink);
  padding: 4px 12px 4px 4px;
  border-radius: 999px;
  background: var(--color-surface-pearl);
  transition: all 0.2s ease-out;
}

.user-dropdown:hover {
  background: var(--color-canvas-parchment);
}

.user-avatar {
  background: var(--color-primary);
  font-weight: 600;
}

.username {
  font-size: 14px;
  font-weight: 500;
}

.dropdown-icon {
  font-size: 12px;
  color: var(--color-ink-muted-48);
}

/* ===== Main Content ===== */
.layout-main {
  flex: 1;
  min-height: 0;
  padding: 32px 40px;
  overflow: auto;
}

.content-wrapper {
  max-width: 1280px;
  margin: 0 auto;
}

/* ===== Transitions ===== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease-out, transform 0.2s ease-out;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.mobile-overlay {
  display: none;
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .layout-aside {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 2000;
    width: 0 !important;
  }

  .layout-aside.is-mobile-open {
    width: 248px !important;
  }

  .hamburger-btn {
    display: block;
  }

  .collapse-btn {
    display: none;
  }

  .mobile-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.5);
    backdrop-filter: blur(2px);
    z-index: 1999;
  }

  .layout-header {
    padding: 0 16px;
  }

  .layout-main {
    padding: 20px 16px;
  }

  .username {
    display: none;
  }
}
</style>
