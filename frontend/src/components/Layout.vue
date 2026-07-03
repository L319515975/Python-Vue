<template>
  <el-container class="layout-shell">
    <div v-if="mobileMenuVisible" class="mobile-overlay" @click="mobileMenuVisible = false"></div>

    <el-aside :width="asideWidth" class="layout-aside" :class="{ 'is-mobile-open': mobileMenuVisible && isMobile }">
      <div class="logo-area">
        <div class="logo-icon">
          <el-icon :size="22" color="#fff"><Document /></el-icon>
        </div>
        <span v-show="!isCollapse || isMobile" class="logo-text">简历管理系统</span>
      </div>

      <el-menu
        :default-active="currentRoute"
        :collapse="isCollapse && !isMobile"
        :router="true"
        :collapse-transition="false"
        background-color="#0f172a"
        text-color="#e5e7eb"
        active-text-color="#409eff"
        class="side-menu"
        @select="mobileMenuVisible = false"
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.meta?.icon || 'Document'" /></el-icon>
          <template #title>{{ item.meta?.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="layout-content">
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon v-if="isMobile" class="hamburger-btn" :size="20" @click="mobileMenuVisible = !mobileMenuVisible">
            <Expand />
          </el-icon>
          <el-icon v-else class="collapse-btn" :size="20" @click="isCollapse = !isCollapse">
            <component :is="isCollapse ? 'Expand' : 'Fold'" />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>{{ isAdmin ? '管理后台' : '个人中心' }}</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentTitle">{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-dropdown">
              <el-avatar :size="32">{{ userInitial }}</el-avatar>
              <span class="username">{{ userStore.username || '用户' }}</span>
              <el-icon><ArrowDown /></el-icon>
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
        <router-view />
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
  if (isMobile.value) return mobileMenuVisible.value ? '240px' : '0px'
  return isCollapse.value ? '64px' : '220px'
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
  min-height: 100vh;
  background: #f5f7fa;
}

.layout-aside {
  background: #0f172a;
  overflow: hidden;
  transition: width 0.24s ease;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: linear-gradient(135deg, #409eff, #337ecc);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.side-menu {
  border-right: none;
}

.side-menu :deep(.el-menu-item) {
  height: 44px;
  margin: 4px 8px;
  border-radius: 8px;
}

.side-menu :deep(.el-menu-item.is-active) {
  background: rgba(64, 158, 255, 0.16);
}

.layout-content {
  min-width: 0;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.collapse-btn,
.hamburger-btn {
  cursor: pointer;
  color: #666;
  transition: color 0.2s ease;
}

.collapse-btn:hover,
.hamburger-btn:hover {
  color: #409eff;
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
  gap: 8px;
  cursor: pointer;
  color: #333;
  padding: 6px 10px;
  border-radius: 999px;
  background: #f5f7fa;
}

.username {
  font-size: 14px;
}

.layout-main {
  min-height: calc(100vh - 60px);
  padding: 20px;
  overflow: auto;
}

.mobile-overlay {
  display: none;
}

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
    width: 240px !important;
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
    background: rgba(15, 23, 42, 0.45);
    backdrop-filter: blur(2px);
    z-index: 1999;
  }

  .layout-header {
    padding: 0 12px;
  }

  .layout-main {
    padding: 12px;
  }

  .username {
    display: none;
  }
}
</style>