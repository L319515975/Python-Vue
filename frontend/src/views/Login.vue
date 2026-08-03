<template>
  <div class="login-page">
    <div class="login-panel">
      <section class="brand-panel">
        <div class="brand-icon">
          <el-icon :size="28" color="#fff"><Document /></el-icon>
        </div>
        <h1>智能简历管理系统</h1>
        <p>面向企业后台的简历编辑、审核与分发工作台。</p>
        <ul class="brand-points">
          <li>统一的简历编辑与发布流程</li>
          <li>AI 润色、访客链接、PDF 导出</li>
          <li>管理员与个人中心分角色管理</li>
        </ul>
      </section>

      <section class="form-panel">
        <el-card shadow="never" class="login-card">
          <div class="login-header">
            <h2>登录</h2>
            <p>请输入账号信息进入系统</p>
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
              <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" clearable />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
                prefix-icon="Lock"
                show-password
                clearable
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">
                登录
              </el-button>
            </el-form-item>
          </el-form>

          <div class="login-footer">
            <el-divider>测试账号</el-divider>
            <div class="demo-accounts">
              <el-tag class="account-tag" effect="plain" @click="fillAccount('乐福利', '123456')">
                管理员: 乐福利 / 123456
              </el-tag>
              <el-tag class="account-tag" type="success" effect="plain" @click="fillAccount('zhangsan', 'user123')">
                用户: zhangsan / user123
              </el-tag>
            </div>
          </div>
        </el-card>
      </section>
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
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form.value.username, form.value.password)
    ElMessage.success('登录成功')
    router.push(userStore.isAdmin ? '/admin' : '/user')
  } catch {
    // 错误由统一拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(circle at top left, rgba(64, 158, 255, 0.14), transparent 34%),
    linear-gradient(180deg, #f5f7fa 0%, #eef2f7 100%);
}

.login-panel {
  width: min(1120px, 100%);
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(360px, 460px);
  gap: 24px;
  align-items: stretch;
}

.brand-panel {
  padding: 40px;
  border-radius: 16px;
  background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 520px;
}

.brand-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.16);
  margin-bottom: 18px;
}

.brand-panel h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.2;
}

.brand-panel p {
  margin: 14px 0 0;
  max-width: 28rem;
  color: rgba(255, 255, 255, 0.82);
  font-size: 14px;
}

.brand-points {
  margin: 24px 0 0;
  padding-left: 18px;
  color: rgba(255, 255, 255, 0.92);
  display: grid;
  gap: 10px;
}

.form-panel {
  display: flex;
  align-items: center;
}

.login-card {
  width: 100%;
  border: 1px solid #ebeef5;
  border-radius: 16px;
  box-shadow: 0 12px 36px rgba(15, 23, 42, 0.08);
}

.login-header {
  margin-bottom: 20px;
}

.login-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333333;
}

.login-header p {
  margin: 6px 0 0;
  font-size: 14px;
  color: #666666;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  border-radius: 8px;
}

.login-footer {
  margin-top: 8px;
}

.demo-accounts {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.account-tag {
  cursor: pointer;
  width: fit-content;
  font-size: 13px;
}

@media (max-width: 960px) {
  .login-panel {
    grid-template-columns: 1fr;
  }

  .brand-panel {
    min-height: auto;
    padding: 28px;
  }
}

@media (max-width: 768px) {
  .login-page {
    padding: 12px;
  }

  .brand-panel {
    border-radius: 14px 14px 0 0;
  }

  .login-card {
    border-radius: 0 0 14px 14px;
  }
}
</style>