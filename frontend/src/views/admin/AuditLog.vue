<!--
  操作审计页面 AuditLog.vue —— 管理员查看操作审计和访客 AI 使用日志。

  功能：
  1. 操作审计日志：记录管理员的所有敏感操作（创建/修改/删除用户、简历、标签等）
  2. 访客 AI 使用日志：记录访客使用 AI 功能的记录

  使用 el-tabs 实现两个标签页切换。
-->
<template>
  <div>
    <el-tabs v-model="activeTab">
      <!-- ========== 操作审计标签页 ========== -->
      <el-tab-pane label="操作审计" name="audit">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>操作审计日志</span>
              <el-button icon="Refresh" @click="loadLogs">刷新</el-button>
            </div>
          </template>

          <!-- 筛选表单 -->
          <el-form :inline="true" size="small" class="filter-form">
            <el-form-item label="操作类型">
              <el-select v-model="filters.action" clearable placeholder="全部" class="filter-input">
                <el-option v-for="opt in actionOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="目标用户">
              <el-input v-model="filters.target_user" clearable placeholder="用户名" class="filter-input" />
            </el-form-item>
            <el-form-item label="操作管理员">
              <el-input v-model="filters.admin_user" clearable placeholder="管理员" class="filter-input" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="Search" @click="loadLogs">查询</el-button>
              <el-button icon="Delete" @click="resetFilters">重置</el-button>
            </el-form-item>
          </el-form>

          <!-- 审计日志表格 -->
          <el-table :data="logs" v-loading="loading" stripe border class="full-width">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="admin_user" label="操作管理员" width="120" />
            <el-table-column prop="action_display" label="操作类型" width="120">
              <template #default="{ row }">
                <el-tag :type="actionTagType(row.action)" size="small">{{ row.action_display }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="target_user" label="目标用户" width="120" />
            <el-table-column prop="detail" label="操作详情" min-width="200" show-overflow-tooltip />
            <el-table-column prop="ip_address" label="IP地址" width="140" />
            <el-table-column prop="created_at" label="操作时间" width="180">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-if="total > 0"
            class="pagination"
            :current-page="page"
            :page-size="pageSize"
            :total="total"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
          />
        </el-card>
      </el-tab-pane>

      <!-- ========== 访客 AI 使用日志标签页 ========== -->
      <el-tab-pane label="访客 AI使用日志" name="visitor-ai">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>访客 AI调用日志</span>
              <el-button icon="Refresh" @click="loadHrLogs">刷新</el-button>
            </div>
          </template>

          <el-form :inline="true" size="small" class="filter-form">
            <el-form-item label="调用类型">
              <el-select v-model="hrFilters.call_type" clearable placeholder="全部" class="filter-input-sm">
                <el-option label="AI咨询" value="chat" />
                <el-option label="文本润色" value="polish" />
              </el-select>
            </el-form-item>
            <el-form-item label="用户名">
              <el-input v-model="hrFilters.username" clearable placeholder="简历所属用户" class="filter-input" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="Search" @click="loadHrLogs">查询</el-button>
              <el-button icon="Delete" @click="resetHrFilters">重置</el-button>
            </el-form-item>
          </el-form>

          <el-table :data="hrLogs" v-loading="hrLoading" stripe border class="full-width">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="username" label="简历用户" width="100" />
            <el-table-column prop="visitor_token" label="访客Token" width="140" />
            <el-table-column prop="call_type_display" label="调用类型" width="100">
              <template #default="{ row }">
                <el-tag :type="row.call_type === 'chat' ? 'primary' : 'warning'" size="small">{{ row.call_type_display }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="query_text" label="查询内容" min-width="200" show-overflow-tooltip />
            <el-table-column prop="tokens_used" label="Tokens" width="80" />
            <el-table-column prop="ip_address" label="IP地址" width="140" />
            <el-table-column prop="created_at" label="调用时间" width="180">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-if="hrTotal > 0"
            class="pagination"
            :current-page="hrPage"
            :page-size="hrPageSize"
            :total="hrTotal"
            :page-sizes="[20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            @current-change="handleHrPageChange"
            @size-change="handleHrSizeChange"
          />
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
/**
 * 操作审计页面逻辑。
 *
 * 包含两个日志模块：
 * 1. 管理员操作审计：记录所有敏感操作
 * 2. 访客 AI 使用日志：记录访客使用 AI 的记录
 */
import { ref, reactive, onMounted } from 'vue'
import { auditLogApi, visitorAiUsageApi } from '@/api'

const activeTab = ref('audit')

// ========== 操作审计日志状态 ==========
const logs = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 筛选条件（使用 reactive 创建响应式对象）
const filters = reactive({
  action: '',
  target_user: '',
  admin_user: '',
})

// 操作类型选项
const actionOptions = [
  { value: 'user_create', label: '创建用户' },
  { value: 'user_update', label: '修改用户' },
  { value: 'user_delete', label: '删除用户' },
  { value: 'resume_update', label: '修改简历' },
  { value: 'resume_delete', label: '删除简历' },
  { value: 'tag_create', label: '创建标签' },
  { value: 'tag_update', label: '修改标签' },
  { value: 'tag_delete', label: '删除标签' },
  { value: 'role_change', label: '角色变更' },
  { value: 'other', label: '其他' },
]

// ========== 访客 AI 使用日志状态 ==========
const hrLogs = ref([])
const hrLoading = ref(false)
const hrPage = ref(1)
const hrPageSize = ref(20)
const hrTotal = ref(0)

const hrFilters = reactive({
  call_type: '',
  username: '',
})

/** 根据操作类型返回标签颜色。 */
function actionTagType(action) {
  if (action.includes('delete')) return 'danger'
  if (action.includes('create')) return 'success'
  if (action.includes('update')) return 'warning'
  if (action.includes('role')) return 'info'
  return ''
}

/** 格式化 ISO 时间为本地化字符串。 */
function formatTime(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleString('zh-CN')
}

/** 加载操作审计日志。 */
async function loadLogs() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filters.action) params.action = filters.action
    if (filters.target_user) params.target_user = filters.target_user
    if (filters.admin_user) params.admin_user = filters.admin_user
    const res = await auditLogApi.list(params)
    logs.value = res.results || []
    total.value = res.count || 0
  } catch (e) {
    logs.value = []
  } finally {
    loading.value = false
  }
}

/** 加载访客 AI 使用日志。 */
async function loadHrLogs() {
  hrLoading.value = true
  try {
    const params = { page: hrPage.value, page_size: hrPageSize.value }
    if (hrFilters.call_type) params.call_type = hrFilters.call_type
    if (hrFilters.username) params.username = hrFilters.username
    const res = await visitorAiUsageApi.list(params)
    hrLogs.value = res.results || []
    hrTotal.value = res.count || 0
  } catch (e) {
    hrLogs.value = []
  } finally {
    hrLoading.value = false
  }
}

// 分页和筛选处理函数
function handlePageChange(val) { page.value = val; loadLogs() }
function handleSizeChange(val) { pageSize.value = val; page.value = 1; loadLogs() }
function handleHrPageChange(val) { hrPage.value = val; loadHrLogs() }
function handleHrSizeChange(val) { hrPageSize.value = val; hrPage.value = 1; loadHrLogs() }

function resetFilters() {
  filters.action = ''
  filters.target_user = ''
  filters.admin_user = ''
  page.value = 1
  loadLogs()
}

function resetHrFilters() {
  hrFilters.call_type = ''
  hrFilters.username = ''
  hrPage.value = 1
  loadHrLogs()
}

// 组件挂载时加载两种日志
onMounted(() => {
  loadLogs()
  loadHrLogs()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filter-form {
  margin-bottom: 16px;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .filter-form :deep(.el-form-item) { margin-bottom: 8px; }
  .filter-form :deep(.el-form-item__content) { flex-wrap: wrap; }
}

.filter-input { width: 150px; }
.filter-input-sm { width: 120px; }
.full-width { width: 100%; }
</style>
