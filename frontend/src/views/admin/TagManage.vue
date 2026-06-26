<!--
  标签管理页面 TagManage.vue —— 管理员管理简历标签。

  功能：
  1. 标签列表：展示所有标签（名称、类型、是否系统标签）
  2. 按类型筛选标签
  3. 新增/编辑标签：设置名称和类型
  4. 删除标签

  标签类型：技能、项目、证书、获奖、语言、自定义
-->
<template>
  <div class="tag-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>标签管理</span>
          <div class="header-actions">
            <!-- 标签类型筛选 -->
            <el-select v-model="filterType" placeholder="筛选类型" clearable class="filter-type-select" @change="loadTags">
              <el-option v-for="t in tagTypes" :key="t.value" :label="t.label" :value="t.value" />
            </el-select>
            <el-button type="primary" icon="Plus" @click="openDialog()">新增标签</el-button>
          </div>
        </div>
      </template>

      <!-- 标签数据表格 -->
      <el-table :data="tags" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="标签名称" width="200" />
        <el-table-column prop="tag_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="tagTypeColor(row.tag_type)" size="small">
              {{ tagTypeName(row.tag_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_system" label="系统标签" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_system ? 'success' : 'info'" size="small">
              {{ row.is_system ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除此标签?" @confirm="deleteTag(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        class="pagination"
        @current-change="p => { currentPage = p; loadTags() }"
      />
    </el-card>

    <!-- 新增/编辑标签弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingTag ? '编辑标签' : '新增标签'" :width="isMobile ? '95%' : '400px'">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标签名称" required>
          <el-input v-model="form.name" placeholder="如：Python、获奖" maxlength="100" />
        </el-form-item>
        <el-form-item label="标签类型" required>
          <el-select v-model="form.tag_type" placeholder="选择类型" class="full-width">
            <el-option v-for="t in tagTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveTag">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 标签管理逻辑 —— 标签的 CRUD 操作。
 * 标签用于给简历打标记，方便分类和搜索。
 */
import { ref, onMounted } from 'vue'
import { useMobile } from '@/composables/useMobile'
import { tagApi } from '@/api'
import { ElMessage } from 'element-plus'

const { isMobile } = useMobile()

// 状态变量
const tags = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(20)
const currentPage = ref(1)
const filterType = ref('')           // 按标签类型筛选
const dialogVisible = ref(false)
const saving = ref(false)
const editingTag = ref(null)
const form = ref({ name: '', tag_type: 'skill' })

// 标签类型选项
const tagTypes = [
  { value: 'skill', label: '技能' },
  { value: 'project', label: '项目' },
  { value: 'certificate', label: '证书' },
  { value: 'award', label: '获奖' },
  { value: 'language', label: '语言' },
  { value: 'custom', label: '自定义' },
]

/** 获取标签类型的中文名称。 */
function tagTypeName(type) {
  return tagTypes.find(t => t.value === type)?.label || type
}

/** 获取标签类型对应的颜色。 */
function tagTypeColor(type) {
  const colors = { skill: '', project: 'success', certificate: 'warning', award: 'danger', language: 'info', custom: '' }
  return colors[type] || ''
}

/** 加载标签列表。 */
async function loadTags() {
  loading.value = true
  try {
    const params = { page: currentPage.value }
    if (filterType.value) params.tag_type = filterType.value
    const data = await tagApi.list(params)
    tags.value = data.results || []
    total.value = data.count || 0
  } catch { /* */ } finally {
    loading.value = false
  }
}

/** 打开新增/编辑弹窗。 */
function openDialog(tag = null) {
  editingTag.value = tag
  form.value = tag ? { name: tag.name, tag_type: tag.tag_type } : { name: '', tag_type: 'skill' }
  dialogVisible.value = true
}

/** 保存标签。 */
async function saveTag() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入标签名称')
    return
  }
  saving.value = true
  try {
    if (editingTag.value) {
      await tagApi.update(editingTag.value.id, form.value)
      ElMessage.success('标签更新成功')
    } else {
      await tagApi.create(form.value)
      ElMessage.success('标签创建成功')
    }
    dialogVisible.value = false
    await loadTags()
  } catch { /* */ } finally {
    saving.value = false
  }
}

/** 删除标签。 */
async function deleteTag(id) {
  try {
    await tagApi.delete(id)
    ElMessage.success('标签删除成功')
    await loadTags()
  } catch { /* */ }
}

onMounted(loadTags)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

.filter-type-select {
  width: 140px;
}
.full-width {
  width: 100%;
}
</style>