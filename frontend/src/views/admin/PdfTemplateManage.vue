<template>
  <div class="pdf-template-manage">
    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="page-header">
          <div>
            <h2>PDF模板管理</h2>
            <p>上传 HTML 模板，控制启用状态，并供导出时选择。</p>
          </div>
          <el-tag type="info" effect="plain">模板库</el-tag>
        </div>
      </template>

      <el-form class="upload-form" label-width="92px">
        <el-row :gutter="12">
          <el-col :xs="24" :md="8">
            <el-form-item label="模板名称">
              <el-input v-model="form.name" placeholder="例如：商务简洁版" clearable />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="10">
            <el-form-item label="模板描述">
              <el-input v-model="form.description" placeholder="可选，简单说明模板风格" clearable />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="6">
            <el-form-item label="启用状态">
              <el-switch v-model="form.is_active" active-text="启用" inactive-text="停用" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="模板文件">
          <div class="file-row">
            <el-upload
              :auto-upload="false"
              :show-file-list="false"
              accept=".html,.htm"
              :on-change="handleFileChange"
            >
              <el-button icon="Upload">选择 HTML 文件</el-button>
            </el-upload>
            <span class="file-name">{{ selectedFileName || '未选择文件' }}</span>
          </div>
          <div class="form-tip">仅支持 HTML/HTM 文件，内容会直接作为 PDF 模板渲染。</div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" icon="UploadFilled" :loading="uploading" @click="submitTemplate">上传模板</el-button>
          <el-button icon="Refresh" @click="reloadTemplates">刷新列表</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="page-card table-card">
      <template #header>
        <div class="page-header">
          <div>
            <h2>模板列表</h2>
            <p>内置模板可直接选用，自定义模板可启停或删除。</p>
          </div>
          <el-tag type="success" effect="plain">{{ templates.length }} 个模板</el-tag>
        </div>
      </template>

      <el-skeleton v-if="loading" animated :rows="6" />
      <el-table v-else :data="templates" row-key="template_key" stripe>
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column prop="template_key" label="模板键" min-width="150" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
        <el-table-column prop="template_file_name" label="文件" min-width="160" show-overflow-tooltip />
        <el-table-column label="来源" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_builtin ? 'info' : 'warning'" size="small">
              {{ row.is_builtin ? '内置' : '自定义' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.updated_at || row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-switch
              v-if="!row.is_builtin"
              v-model="row.is_active"
              class="row-switch"
              active-text="启用"
              inactive-text="停用"
              :loading="togglingId === row.id"
              @change="value => handleToggle(row, value)"
            />
            <el-button
              v-if="!row.is_builtin"
              type="danger"
              link
              icon="Delete"
              :loading="deletingId === row.id"
              @click="deleteTemplate(row)"
            >
              删除
            </el-button>
            <el-tag v-else type="info" size="small">只读</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { resumeApi } from '@/api'

const templates = ref([])
const loading = ref(false)
const uploading = ref(false)
const togglingId = ref(null)
const deletingId = ref(null)
const selectedFile = ref(null)
const form = reactive({
  name: '',
  description: '',
  is_active: true,
})

const selectedFileName = ref('')

async function reloadTemplates() {
  loading.value = true
  try {
    const data = await resumeApi.pdfTemplates({ include_inactive: 1 })
    templates.value = Array.isArray(data) ? data : []
  } catch {
    templates.value = []
  } finally {
    loading.value = false
  }
}

function handleFileChange(uploadFile) {
  selectedFile.value = uploadFile.raw || null
  selectedFileName.value = uploadFile.name || ''
}

function resetForm() {
  form.name = ''
  form.description = ''
  form.is_active = true
  selectedFile.value = null
  selectedFileName.value = ''
}

async function submitTemplate() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写模板名称')
    return
  }
  if (!selectedFile.value) {
    ElMessage.warning('请选择模板文件')
    return
  }

  const formData = new FormData()
  formData.append('name', form.name.trim())
  formData.append('description', form.description || '')
  formData.append('is_active', form.is_active ? 'true' : 'false')
  formData.append('template_file', selectedFile.value)

  uploading.value = true
  try {
    await resumeApi.createPdfTemplate(formData)
    ElMessage.success('模板上传成功')
    resetForm()
    await reloadTemplates()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '模板上传失败')
  } finally {
    uploading.value = false
  }
}

async function handleToggle(row, value) {
  togglingId.value = row.id
  const previous = !value
  const formData = new FormData()
  formData.append('is_active', value ? 'true' : 'false')
  try {
    await resumeApi.updatePdfTemplate(row.id, formData)
    ElMessage.success(value ? '模板已启用' : '模板已停用')
  } catch (error) {
    row.is_active = previous
    ElMessage.error(error.response?.data?.detail || '状态更新失败')
  } finally {
    togglingId.value = null
  }
}

async function deleteTemplate(row) {
  try {
    await ElMessageBox.confirm(`确认删除模板“${row.name}”吗？`, '删除模板', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  deletingId.value = row.id
  try {
    await resumeApi.deletePdfTemplate(row.id)
    ElMessage.success('模板已删除')
    await reloadTemplates()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  } finally {
    deletingId.value = null
  }
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

onMounted(reloadTemplates)
</script>

<style scoped>
.pdf-template-manage {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-card {
  border: 1px solid #ebeef5;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.page-header p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #666;
}

.upload-form {
  max-width: 1120px;
}

.file-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.file-name {
  color: #606266;
  font-size: 13px;
}

.form-tip {
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

.table-card {
  overflow: hidden;
}

.row-switch {
  margin-right: 10px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
