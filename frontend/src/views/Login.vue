<template>
  <div class="login-page">
    <div class="login-bg"></div>
    <div class="login-card">
      <div class="login-header">
        <el-icon :size="40" color="#409eff"><Document /></el-icon>
        <h2>智能简历管理系统</h2>
        <p class="subtitle">AI驱动的个人简历管理平台</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="0"
        size="large"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

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

      <div class="login-footer">
        <el-divider>测试账号</el-divider>
        <div class="demo-accounts">
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = ref({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function fillAccount(username, password) {
  form.value.username = username
  form.value.password = password
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form.value.username, form.value.password)
    ElMessage.success('登录成功')
    router.push(userStore.isAdmin ? '/admin' : '/user')
  } catch {
    // Error handled by interceptor
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

.login-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  position: relative;
  width: 420px;
  max-width: 90vw;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  margin: 12px 0 4px;
  color: #333;
  font-size: 22px;
}

.subtitle {
  color: #999;
  font-size: 14px;
}

.login-btn {
  width: 100%;
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
}
.account-tag:hover {
  opacity: 0.8;
}

@media (max-width: 768px) {
  .login-card {
    padding: 24px 20px;
    margin: 16px;
  }

  .login-header h2 {
    font-size: 18px;
  }

  .login-header .el-icon {
    font-size: 32px !important;
  }
}
</style>