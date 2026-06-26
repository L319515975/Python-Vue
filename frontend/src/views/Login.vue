<!--
  登录页面 Login.vue —— 用户输入用户名和密码登录系统。

  作用：系统的入口页面，所有用户必须先登录才能使用系统功能。

  功能：
  1. 用户名/密码登录表单（带表单验证）
  2. 装饰性浮动背景动画
  3. 测试账号快捷填充（方便演示）
  4. 登录后根据角色跳转到对应后台

  知识点（Element Plus 表单）：
  - el-form：表单容器，支持数据绑定和验证规则
  - el-form-item：表单项，包含标签和验证提示
  - el-input：输入框组件
  - rules：验证规则对象，定义每个字段的验证条件
  - formRef.validate()：手动触发表单验证
-->
<template>
  <div class="login-page">
    <!-- 背景装饰：三个浮动的半透明圆形 -->
    <div class="login-bg">
      <div class="bg-shape bg-shape-1"></div>
      <div class="bg-shape bg-shape-2"></div>
      <div class="bg-shape bg-shape-3"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- 头部 Logo 和标题 -->
      <div class="login-header">
        <div class="logo-icon">
          <el-icon :size="28" color="#fff"><Document /></el-icon>
        </div>
        <h2>智能简历管理系统</h2>
        <p class="subtitle">AI驱动的个人简历管理平台</p>
      </div>

      <!-- 登录表单 -->
      <!-- ref="formRef"：获取表单组件的引用（用于手动调用验证方法） -->
      <!-- :rules="rules"：绑定验证规则 -->
      <!-- @keyup.enter：按回车键时触发登录 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="0"
        size="large"
        @keyup.enter="handleLogin"
      >
        <!-- 用户名输入框 -->
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            prefix-icon="User"
          />
        </el-form-item>

        <!-- 密码输入框 -->
        <!-- show-password：显示密码可见性切换按钮 -->
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <!-- 登录按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 测试账号区域 -->
      <div class="login-footer">
        <el-divider>测试账号</el-divider>
        <div class="demo-accounts">
          <!-- 点击标签自动填充账号密码 -->
          <el-tag
            class="account-tag"
            effect="plain"
            @click="fillAccount('admin', 'admin123')"
          >
            管理员: admin / admin123
          </el-tag>
          <el-tag
            class="account-tag"
            type="success"
            effect="plain"
            @click="fillAccount('zhangsan', 'user123')"
          >
            用户: zhangsan / user123
          </el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 登录页面的逻辑部分。
 *
 * 登录流程：
 * 1. 用户输入用户名和密码
 * 2. 点击登录按钮，触发表单验证
 * 3. 验证通过后，调用 userStore.login() 发送登录请求
 * 4. 后端验证成功后返回 JWT 令牌和用户信息
 * 5. 保存令牌和用户信息，跳转到对应角色的后台页面
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)    // 表单引用，用于调用验证方法
const loading = ref(false)   // 登录按钮的加载状态

// 表单数据
const form = ref({
  username: '',
  password: '',
})

// 表单验证规则
// required: true → 必填项
// message → 验证失败时的提示文字
// trigger: 'blur' → 失去焦点时触发验证
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// 快捷填充测试账号
function fillAccount(username, password) {
  form.value.username = username
  form.value.password = password
}

// 处理登录
async function handleLogin() {
  // 手动触发表单验证，validate() 返回 Promise
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    // 调用用户状态管理中的登录方法
    await userStore.login(form.value.username, form.value.password)
    ElMessage.success('登录成功')
    // 根据用户角色跳转到对应后台
    router.push(userStore.isAdmin ? '/admin' : '/user')
  } catch {
    // 错误已由请求拦截器统一处理（显示错误消息）
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

/* 渐变背景 */
.login-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 装饰性浮动圆形 */
.bg-shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.12;
  background: #fff;
}

.bg-shape-1 {
  width: 400px;
  height: 400px;
  top: -100px;
  right: -80px;
  animation: float 8s ease-in-out infinite;
}

.bg-shape-2 {
  width: 250px;
  height: 250px;
  bottom: -60px;
  left: -40px;
  animation: float 10s ease-in-out infinite reverse;
}

.bg-shape-3 {
  width: 150px;
  height: 150px;
  top: 40%;
  left: 15%;
  animation: float 6s ease-in-out infinite 1s;
}

/* 浮动动画 */
@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(5deg); }
}

/* 登录卡片 */
.login-card {
  position: relative;
  width: 420px;
  max-width: 90vw;
  padding: 40px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.35);
}

.login-header h2 {
  margin: 0 0 6px;
  color: #1a1a2e;
  font-size: 22px;
  font-weight: 700;
}

.subtitle {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  border-radius: 8px;
}

.login-footer {
  margin-top: 10px;
}

.demo-accounts {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.account-tag {
  cursor: pointer;
  font-size: 13px;
  transition: opacity 0.2s;
}
.account-tag:hover {
  opacity: 0.8;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .login-card {
    padding: 28px 24px;
    margin: 16px;
    border-radius: 12px;
  }

  .login-header h2 {
    font-size: 18px;
  }

  .bg-shape-1 { width: 200px; height: 200px; }
  .bg-shape-2 { width: 150px; height: 150px; }
  .bg-shape-3 { display: none; }
}
</style>