<!--
  简历管理页面 ResumeManage.vue —— 管理员查看和管理所有简历。

  功能：
  1. 简历列表：分页展示所有简历（标题、用户、状态、内容统计）
  2. 搜索筛选：按标题搜索、按状态筛选
  3. 简历详情抽屉：查看简历的完整信息（教育、工作、项目、技能）

  使用 el-drawer（抽屉组件）展示简历详情。
-->
<template>
  <div class="resume-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>简历管理</span>
        </div>
      </template>

      <!-- 搜索筛选 -->
      <el-form :inline="true" class="search-form">
        <el-form-item label="搜索">
          <el-input v-model="search" placeholder="标题/简介" clearable @clear="loadResumes" @keyup.enter="loadResumes" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterStatus" clearable placeholder="全部" @change="loadResumes">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="loadResumes">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- 简历列表 -->
      <el-table :data="resumes" stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户" width="100" />
        <el-table-column prop="title" label="简历标题" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
              {{ row.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <!-- 内容统计列 -->
        <el-table-column label="内容" width="200">
          <template #default="{ row }">
            <span class="content-summary">
              教育 {{ row.educations_count }} | 工作 {{ row.work_experiences_count }} | 项目 {{ row.projects_count }} | 技能 {{ row.skills_count }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="file_name" label="文件" width="140" show-overflow-tooltip />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link icon="View" @click="viewDetail(row)">查看</el-button>
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
        @current-change="p => { currentPage = p; loadResumes() }"
      />
    </el-card>

    <!-- 简历详情抽屉（从右侧滑出） -->
    <el-drawer v-model="drawerVisible" :title="currentResume?.title || '简历详情'" :size="isMobile ? '90%' : '600px'">
      <template v-if="currentResume">
        <!-- 基本信息描述列表 -->
        <el-descriptions :column="isMobile ? 1 : 2" border>
          <el-descriptions-item label="用户">{{ currentResume.username }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentResume.status === 'published' ? 'success' : 'info'" size="small">
              {{ currentResume.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="简介" :span="isMobile ? 1 : 2">{{ currentResume.summary || '暂无' }}</el-descriptions-item>
          <el-descriptions-item label="文件" :span="isMobile ? 1 : 2">{{ currentResume.file_name || '未上传' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 教育经历时间线 -->
        <h4 class="section-title">教育经历</h4>
        <el-timeline v-if="detailData.educations?.length">
          <el-timeline-item v-for="edu in detailData.educations" :key="edu.id" :timestamp="edu.start_date">
            {{ edu.school }} - {{ edu.degree }} - {{ edu.major }}
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无" :image-size="60" />

        <!-- 工作经历时间线 -->
        <h4 class="section-title">工作经历</h4>
        <el-timeline v-if="detailData.work_experiences?.length">
          <el-timeline-item v-for="w in detailData.work_experiences" :key="w.id" :timestamp="w.start_date">
            {{ w.company }} - {{ w.position }}
            <p class="detail-desc">{{ w.description }}</p>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无" :image-size="60" />

        <!-- 项目经历时间线 -->
        <h4 class="section-title">项目经历</h4>
        <el-timeline v-if="detailData.projects?.length">
          <el-timeline-item v-for="p in detailData.projects" :key="p.id" :timestamp="p.start_date">
            {{ p.name }} ({{ p.role }})
            <p class="detail-desc">技术栈: {{ p.tech_stack }}</p>
            <p class="detail-text">{{ p.description }}</p>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无" :image-size="60" />

        <!-- 技能列表 -->
        <h4 class="section-title">技能</h4>
        <div v-if="detailData.skills?.length" class="skills-list">
          <el-tag v-for="s in detailData.skills" :key="s.id">
            {{ s.name }} ({{ s.level }}%)
          </el-tag>
        </div>
        <el-empty v-else description="暂无" :image-size="60" />
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
/**
 * 简历管理逻辑 —— 管理员查看所有简历。
 * 只读操作，不支持编辑（编辑由用户自己完成）。
 */
import { ref, onMounted } from 'vue'
import { useMobile } from '@/composables/useMobile'
import { resumeApi } from '@/api'

const { isMobile } = useMobile()

// 状态变量
const resumes = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(20)
const currentPage = ref(1)
const search = ref('')
const filterStatus = ref('')
const drawerVisible = ref(false)     // 详情抽屉是否显示
const currentResume = ref(null)      // 当前查看的简历
const detailData = ref({})           // 简历详细数据

/** 加载简历列表。 */
async function loadResumes() {
  loading.value = true
  try {
    const params = { page: currentPage.value }
    if (search.value) params.search = search.value
    if (filterStatus.value) params.status = filterStatus.value
    const data = await resumeApi.list(params)
    resumes.value = data.results || []
    total.value = data.count || 0
  } catch { /* */ } finally {
    loading.value = false
  }
}

/** 查看简历详情（打开抽屉）。 */
async function viewDetail(row) {
  currentResume.value = row
  drawerVisible.value = true
  try {
    const data = await resumeApi.detail(row.id)
    detailData.value = data
  } catch { /* */ }
}

onMounted(loadResumes)
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.search-form { margin-bottom: 16px; }
.pagination { margin-top: 16px; justify-content: flex-end; }
@media (max-width: 768px) { .search-form :deep(.el-form-item) { margin-bottom: 8px; } }
.content-summary { font-size: 13px; color: #666; }
.section-title { margin: 16px 0 8px; font-weight: 600; }
.detail-desc { color: #666; font-size: 13px; margin-top: 4px; }
.detail-text { color: #666; font-size: 13px; }
.skills-list { display: flex; flex-wrap: wrap; gap: 8px; }
</style>