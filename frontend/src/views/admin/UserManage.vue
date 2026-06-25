<template>
  <div class="user-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" icon="Plus" @click="openDialog()">新增用户</el-button>
        </div>
      </template>

      <!-- Search bar -->
      <el-form :inline="true" class="search-form">
        <el-form-item label="搜索">
          <el-input v-model="search" placeholder="用户名/邮箱/手机" clearable @clear="loadUsers" @keyup.enter="loadUsers" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="filterRole" clearable placeholder="全部" @change="loadUsers">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="loadUsers">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- Table -->
      <el-table :data="users" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'success'" size="small">
              {{ row.role_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link icon="Edit" @click="openDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除?" @confirm="deleteUser(row.id)">
              <template #reference>
                <el-button type="danger" link icon="Delete">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <el-pagination
        v-if="total > pageSize"
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingUser ? '编辑用户' : '新增用户'"
      width="500px"
    >
      <el-form :model="form" label-width="80px" :rules="formRules" ref="formRef">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!editingUser" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!editingUser">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="密码" v-else>
          <el-input v-model="form.password" type="password" show-password placeholder="留空则不修改" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { userApi } from '@/api'
import { ElMessage } from 'element-plus'

const users = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(20)
const currentPage = ref(1)
const search = ref('')
const filterRole = ref('')
const dialogVisible = ref(false)
const editingUser = ref(null)
const saving = ref(false)
const formRef = ref(null)

const defaultForm = {
  username: '', password: '', email: '', phone: '', role: 'user', is_active: true,
}
const form = ref({ ...defaultForm })

const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

async function loadUsers() {
  loading.value = true
  try {
    const params = { page: currentPage.value }
    if (search.value) params.search = search.value
    if (filterRole.value) params.role = filterRole.value
    const data = await userApi.list(params)
    users.value = data.results || []
    total.value = data.count || 0
  } catch { /* */ } finally {
    loading.value = false
  }
}

function handlePageChange(page) {
  currentPage.value = page
  loadUsers()
}

function openDialog(user = null) {
  editingUser.value = user
  if (user) {
    form.value = { ...user, password: '' }
  } else {
    form.value = { ...defaultForm }
  }
  dialogVisible.value = true
}

async function saveUser() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editingUser.value) {
      const payload = { ...form.value }
      if (!payload.password) delete payload.password
      delete payload.id
      await userApi.update(editingUser.value.id, payload)
      ElMessage.success('更新成功')
    } else {
      await userApi.create(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadUsers()
  } catch { /* */ } finally {
    saving.value = false
  }
}

async function deleteUser(id) {
  try {
    await userApi.delete(id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch { /* */ }
}

onMounted(loadUsers)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.search-form {
  margin-bottom: 16px;
}
</style>
