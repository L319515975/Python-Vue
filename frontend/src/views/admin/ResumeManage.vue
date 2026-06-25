<template>
  <div class="resume-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>简历管理</span>
        </div>
      </template>

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
        <el-table-column label="内容" width="200">
          <template #default="{ row }">
            <span style="font-size: 13px; color: #666">
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
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="p => { currentPage = p; loadResumes() }"
      />
    </el-card>

    <!-- Detail Drawer -->
    <el-drawer v-model="drawerVisible" :title="currentResume?.title || '简历详情'" size="600px">
      <template v-if="currentResume">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户">{{ currentResume.username }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentResume.status === 'published' ? 'success' : 'info'" size="small">
              {{ currentResume.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="简介" :span="2">{{ currentResume.summary || '暂无' }}</el-descriptions-item>
          <el-descriptions-item label="文件" :span="2">{{ currentResume.file_name || '未上传' }}</el-descriptions-item>
        </el-descriptions>

        <!-- Education -->
        <h4 style="margin: 16px 0 8px">教育经历</h4>
        <el-timeline v-if="detailData.educations?.length">
          <el-timeline-item v-for="edu in detailData.educations" :key="edu.id" :timestamp="edu.start_date">
            {{ edu.school }} - {{ edu.degree }} - {{ edu.major }}
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无" :image-size="60" />

        <!-- Work -->
        <h4 style="margin: 16px 0 8px">工作经历</h4>
        <el-timeline v-if="detailData.work_experiences?.length">
          <el-timeline-item v-for="w in detailData.work_experiences" :key="w.id" :timestamp="w.start_date">
            {{ w.company }} - {{ w.position }}
            <p style="color: #666; font-size: 13px; margin-top: 4px">{{ w.description }}</p>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无" :image-size="60" />

        <!-- Projects -->
        <h4 style="margin: 16px 0 8px">项目经历</h4>
        <el-timeline v-if="detailData.projects?.length">
          <el-timeline-item v-for="p in detailData.projects" :key="p.id" :timestamp="p.start_date">
            {{ p.name }} ({{ p.role }})
            <p style="color: #666; font-size: 13px; margin-top: 4px">技术栈: {{ p.tech_stack }}</p>
            <p style="color: #666; font-size: 13px">{{ p.description }}</p>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无" :image-size="60" />

        <!-- Skills -->
        <h4 style="margin: 16px 0 8px">技能</h4>
        <div v-if="detailData.skills?.length" style="display: flex; flex-wrap: wrap; gap: 8px">
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
import { ref, onMounted } from 'vue'
import { resumeApi } from '@/api'

const resumes = ref([])
const loading = ref(false)
const total = ref(0)
const pageSize = ref(20)
const currentPage = ref(1)
const search = ref('')
const filterStatus = ref('')
const drawerVisible = ref(false)
const currentResume = ref(null)
const detailData = ref({})

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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.search-form {
  margin-bottom: 16px;
}
</style>
