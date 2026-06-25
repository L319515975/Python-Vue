<template>
  <el-container class="layout-container">
    <!-- Mobile overlay -->
    <div v-if="mobileMenuVisible" class="mobile-overlay" @click="mobileMenuVisible = false"></div>

    <!-- Sidebar -->
    <el-aside :width="asideWidth" class="layout-aside" :class="{ 'mobile-aside': mobileMenuVisible }">
      <div class="logo-area">
        <el-icon :size="28" color="#409eff"><Document /></el-icon>
        <span v-show="!isCollapse" class="logo-text">简历管理系统</span>
      </div>
      <el-menu
        :default-active="currentRoute"
        :collapse="isCollapse"
        :router="true"
        background-color="#001529"
        text-color="#ffffffb3"
        active-text-color="#409eff"
        class="side-menu"
        @select="mobileMenuVisible = false"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.meta?.icon || 'Document'" /></el-icon>
          <template #title>{{ item.meta?.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- Main -->
    <el-container>
      <!-- Header -->
      <el-header class="layout-header">
        <div class="header-left">
          <!-- Mobile hamburger -->
          <el-icon class="hamburger-btn" :size="20" @click="mobileMenuVisible = !mobileMenuVisible">
            <Expand />
          </el-icon>
          <!-- Desktop collapse -->
          <el-icon
            class="collapse-btn"
            :size="20"
            @click="isCollapse = !isCollapse"
          >
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
              <el-avatar :size="32" icon="UserFilled" />
              <span class="username">{{ userStore.username }}</span>
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

      <!-- Content -->
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>

    <!-- Password Dialog -->
    <el-dialog v-model="pwdDialogVisible" title="修改密码" :width="isMobile ? '95%' : '400px'">
      <el-form :model="pwdForm" label-width="80px">
        <el-form-item label="原密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword">确认</el-button>
      </template>
    </el-dialog>

    <!-- Floating AI Assistant -->
    <AiAssistant />
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { userApi } from '@/api'
import { ElMessage } from 'element-plus'
import AiAssistant from '@/components/AiAssistant.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isCollapse = ref(false)
const mobileMenuVisible = ref(false)
const pwdDialogVisible = ref(false)
const pwdForm = ref({ old_password: '', new_password: '' })

const isMobile = computed(() => window.innerWidth <= 768)
const isAdmin = computed(() => userStore.isAdmin)
const currentRoute = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '')
const asideWidth = computed(() => {
  if (isMobile.value) return mobileMenuVisible.value ? '220px' : '0px'
  return isCollapse.value ? '64px' : '220px'
})

const menuItems = computed(() => {
  const parent = isAdmin.value ? '/admin' : '/user'
  const parentRoute = router.options.routes.find(r => r.path === parent)
  return (parentRoute?.children || []).map(child => ({
    path: `${parent}/${child.path}`,
    meta: child.meta,
  }))
})

function handleCommand(cmd) {
  if (cmd === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (cmd === 'password') {
    pwdForm.value = { old_password: '', new_password: '' }
    pwdDialogVisible.value = true
  } else if (cmd === 'profile') {
    if (isAdmin.value) {
      router.push('/admin')
    } else {
      router.push('/user')
    }
  }
}

async function handleChangePassword() {
  try {
    await userApi.changePassword(pwdForm.value)
    ElMessage.success('密码修改成功')
    pwdDialogVisible.value = false
  } catch {
    // Error handled by interceptor
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.layout-aside {
  background-color: #001529;
  transition: width 0.3s;
  overflow: hidden;
}

.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-bottom: 1px solid #ffffff1a;
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

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 0 20px;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  color: #666;
}
.collapse-btn:hover {
  color: #409eff;
}

/* Hamburger - hidden on desktop */
.hamburger-btn {
  display: none;
  cursor: pointer;
  color: #666;
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
}

.username {
  font-size: 14px;
}

.layout-main {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

/* Mobile overlay */
.mobile-overlay {
  display: none;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .hamburger-btn {
    display: block;
  }

  .collapse-btn {
    display: none;
  }

  .layout-aside {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 2000;
    width: 0 !important;
    transition: width 0.3s;
  }

  .layout-aside.mobile-aside {
    width: 220px !important;
  }

  .mobile-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.3);
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