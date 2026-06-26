<!--
  布局组件 Layout.vue —— 管理后台和用户中心的公共布局。

  作用：所有登录后的页面都使用这个组件作为容器，它提供：
  1. 左侧导航菜单（侧边栏）：根据用户角色动态显示不同菜单项
  2. 顶部栏：显示面包屑导航和用户操作菜单
  3. 内容区域：通过 <router-view> 渲染子页面
  4. 修改密码弹窗
  5. AI 浮窗助手

  知识点（Vue 3 Composition API）：
  - ref()：创建响应式变量（基本类型或对象）
  - computed()：创建计算属性（自动根据依赖重新计算）
  - useRoute()：获取当前路由信息
  - useRouter()：获取路由实例（用于跳转页面）
  - useUserStore()：获取用户状态管理实例
-->
<template>
  <el-container class="layout-container">
    <!-- 移动端遮罩层：点击后关闭侧边栏 -->
    <div v-if="mobileMenuVisible" class="mobile-overlay" @click="mobileMenuVisible = false"></div>

    <!-- ========== 左侧侧边栏 ========== -->
    <el-aside :width="asideWidth" class="layout-aside" :class="{ 'mobile-aside': mobileMenuVisible }">
      <!-- Logo 区域 -->
      <div class="logo-area">
        <div class="logo-icon">
          <el-icon :size="22" color="#fff"><Document /></el-icon>
        </div>
        <!-- v-show：控制显示/隐藏（保留DOM），比 v-if 性能更好 -->
        <span v-show="!isCollapse" class="logo-text">简历管理系统</span>
      </div>

      <!-- 导航菜单 -->
      <!-- :router="true"：启用路由模式，点击菜单项会自动跳转对应路径 -->
      <el-menu
        :default-active="currentRoute"
        :collapse="isCollapse"
        :router="true"
        background-color="#001529"
        text-color="#ffffffb3"
        active-text-color="#409eff"
        class="side-menu"
        @select="mobileMenuVisible = false"  <!-- 点击菜单后关闭移动端侧边栏 -->
      >
        <!-- 动态生成菜单项：v-for 遍历 menuItems 数组 -->
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
        >
          <!-- 动态图标：使用 <component :is="..."> 渲染不同图标 -->
          <el-icon><component :is="item.meta?.icon || 'Document'" /></el-icon>
          <template #title>{{ item.meta?.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- ========== 右侧主内容区 ========== -->
    <el-container>
      <!-- 顶部栏 -->
      <el-header class="layout-header">
        <div class="header-left">
          <!-- 移动端汉堡菜单按钮（仅移动端显示） -->
          <el-icon class="hamburger-btn" :size="20" @click="mobileMenuVisible = !mobileMenuVisible">
            <Expand />
          </el-icon>
          <!-- 桌面端折叠按钮（仅桌面端显示） -->
          <el-icon
            class="collapse-btn"
            :size="20"
            @click="isCollapse = !isCollapse"
          >
            <component :is="isCollapse ? 'Expand' : 'Fold'" />
          </el-icon>
          <!-- 面包屑导航：显示当前位置 -->
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>{{ isAdmin ? '管理后台' : '个人中心' }}</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentTitle">{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <!-- 用户操作区 -->
        <div class="header-right">
          <!-- 下拉菜单：点击触发 -->
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

      <!-- 主内容区域：通过 router-view 渲染子页面 -->
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>

    <!-- 修改密码弹窗 -->
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

    <!-- AI 浮窗助手：固定在右下角 -->
    <AiAssistant />
  </el-container>
</template>

<script setup>
/**
 * 组件逻辑部分（Vue 3 Composition API）。
 *
 * <script setup> 语法糖说明：
 * - 所有顶层变量/函数自动暴露给模板使用
 * - 不需要 return、不需要 export default
 * - import 的组件自动注册
 */
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useMobile } from '@/composables/useMobile'
import { userApi } from '@/api'
import { ElMessage } from 'element-plus'
import AiAssistant from '@/components/AiAssistant.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { isMobile } = useMobile()

// 响应式状态
const isCollapse = ref(false)           // 侧边栏是否折叠
const mobileMenuVisible = ref(false)    // 移动端菜单是否展开
const pwdDialogVisible = ref(false)     // 修改密码弹窗是否显示
const pwdForm = ref({ old_password: '', new_password: '' })  // 密码表单

// 计算属性
const isAdmin = computed(() => userStore.isAdmin)           // 是否管理员
const currentRoute = computed(() => route.path)             // 当前路由路径
const currentTitle = computed(() => route.meta?.title || '') // 当前页面标题
// 侧边栏宽度：移动端根据菜单状态决定，桌面端根据折叠状态决定
const asideWidth = computed(() => {
  if (isMobile.value) return mobileMenuVisible.value ? '220px' : '0px'
  return isCollapse.value ? '64px' : '220px'
})

// 动态生成菜单项：根据用户角色选择对应的路由配置
const menuItems = computed(() => {
  const parent = isAdmin.value ? '/admin' : '/user'
  const parentRoute = router.options.routes.find(r => r.path === parent)
  return (parentRoute?.children || []).map(child => ({
    path: `${parent}/${child.path}`,
    meta: child.meta,
  }))
})

// 处理用户下拉菜单命令
function handleCommand(cmd) {
  if (cmd === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (cmd === 'password') {
    pwdForm.value = { old_password: '', new_password: '' }
    pwdDialogVisible.value = true
  } else if (cmd === 'profile') {
    router.push(isAdmin.value ? '/admin' : '/user')
  }
}

// 修改密码
async function handleChangePassword() {
  try {
    await userApi.changePassword(pwdForm.value)
    ElMessage.success('密码修改成功')
    pwdDialogVisible.value = false
  } catch {
    // 错误已由请求拦截器统一处理
  }
}
</script>

<style scoped>
/*
 * scoped：表示这些样式只作用于当前组件，不会影响其他组件。
 * 这是 Vue 的样式隔离机制，通过给元素添加唯一属性实现。
 */
.layout-container {
  height: 100vh;
}

.layout-aside {
  background-color: #001529;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid #ffffff1a;
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
  transition: color 0.2s;
}
.collapse-btn:hover {
  color: #409eff;
}

/* 汉堡按钮：桌面端隐藏，移动端显示 */
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

/* 移动端遮罩层 */
.mobile-overlay {
  display: none;
}

/* ========== 移动端响应式样式 ========== */
@media (max-width: 768px) {
  .hamburger-btn {
    display: block;  /* 移动端显示汉堡按钮 */
  }

  .collapse-btn {
    display: none;   /* 移动端隐藏折叠按钮 */
  }

  .layout-aside {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 2000;
    width: 0 !important;
    transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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
    backdrop-filter: blur(2px);
  }

  .layout-header {
    padding: 0 12px;
  }

  .layout-main {
    padding: 12px;
  }

  .username {
    display: none;  /* 移动端隐藏用户名文字 */
  }
}
</style>