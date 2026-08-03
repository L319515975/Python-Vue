<!--
  用户管理页面 UserManage.vue —— 管理员管理所有用户。

  功能：
  1. 用户列表：分页展示所有用户信息
  2. 搜索筛选：按用户名搜索、按角色筛选
  3. 新增/编辑用户：弹窗表单，支持设置角色和状态
  4. 删除用户：带确认提示的删除操作

  知识点（Element Plus 表格和分页）：
  - el-table：数据表格组件
  - el-table-column：表格列，prop 对应数据字段名
  - el-pagination：分页组件
  - v-loading：指令式 loading 状态
-->
<template>
  <div class="user-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" icon="Plus" @click="openDialog()">新增用户</el-button>
        </div>
      </template>

      <!-- 搜索筛选区域 -->
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

      <!-- 用户数据表格 -->
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
        <!-- 操作列：编辑和删除按钮 -->
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link icon="Edit" @click="openDialog(row)">编辑</el-button>
            <!-- el-popconfirm：删除前的确认气泡 -->
            <el-popconfirm title="确认删除?" @confirm="deleteUser(row.id)">
              <template #reference>
                <el-button type="danger" link icon="Delete">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页组件 -->
      <el-pagination
        v-if="total > pageSize"
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        class="pagination"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 新增/编辑用户弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingUser ? '编辑用户' : '新增用户'"
      :width="isMobile ? '95%' : '500px'"
    >
      <el-form :model="form" label-width="80px" :rules="formRules" ref="formRef">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!editingUser" />
        </el-form-item>
        <!-- 新增时密码必填，编辑时可选 -->
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
/**
 * 用户管理页面逻辑。
 *
 * CRUD 流程：
 * - Create：打开空表单弹窗 → 填写信息 → 调用 API 创建
 * - Read：onMounted 时加载用户列表，支持搜索和分页
 * - Update：点击编辑 → 打开预填表单 → 调用 API 更新
 * - Delete：点击删除 → 确认提示 → 调用 API 删除
 */
import { ref, onMounted } from 'vue'
import { useMobile } from '@/composables/useMobile'
import { userApi } from '@/api'
import { ElMessage } from 'element-plus'

const { isMobile } = useMobile()

// ========== 状态变量 ==========
const users = ref([])              // 用户列表数据
const loading = ref(false)         // 表格 loading 状态
const total = ref(0)               // 总记录数
const pageSize = ref(20)           // 每页条数
const currentPage = ref(1)         // 当前页码
const search = ref('')             // 搜索关键词
const filterRole = ref('')         // 角色筛选条件
const dialogVisible = ref(false)   // 弹窗是否显示
const editingUser = ref(null)      // 正在编辑的用户（null 表示新增）
const saving = ref(false)          // 保存按钮 loading 状态
const formRef = ref(null)          // 表单引用

// 表单默认值
const defaultForm = {
  username: '', password: '', email: '', phone: '', role: 'user', is_active: true,
}
const form = ref({ ...defaultForm })

// 表单验证规则
const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

/** 加载用户列表（支持搜索和筛选）。 */
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

/** 分页切换。 */
function handlePageChange(page) {
  currentPage.value = page
  loadUsers()
}

/** 打开新增/编辑弹窗。 */
function openDialog(user = null) {
  editingUser.value = user
  if (user) {
    form.value = { ...user, password: '' }  // 编辑时预填数据，密码留空
  } else {
    form.value = { ...defaultForm }          // 新增时使用默认值
  }
  dialogVisible.value = true
}

/** 保存用户（新增或更新）。 */
async function saveUser() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editingUser.value) {
      // 更新：如果密码为空则不传密码字段
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
    loadUsers()  // 刷新列表
  } catch { /* */ } finally {
    saving.value = false
  }
}

/** 删除用户。 */
async function deleteUser(id) {
  try {
    await userApi.delete(id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch { /* */ }
}

// 组件挂载时加载数据
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
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .search-form :deep(.el-form-item) {
    margin-bottom: 8px;
  }
}
</style>