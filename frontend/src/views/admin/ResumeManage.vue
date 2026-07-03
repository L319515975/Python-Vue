<template>
  <div class="resume-manage">
    <el-card shadow="never" class="page-card">
      <template #header>
        <div class="page-header">
          <div>
            <h2>简历管理</h2>
            <p>支持搜索、筛选和详情查看。</p>
          </div>
          <el-tag type="info" effect="plain">列表视图</el-tag>
        </div>
      </template>

      <el-form class="search-form" label-width="72px">
        <el-row :gutter="12">
          <el-col :xs="24" :md="10">
            <el-form-item label="搜索">
              <el-input
                v-model="search"
                placeholder="标题 / 简介"
                clearable
                @clear="handleSearch"
                @keyup.enter="handleSearch"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-form-item label="状态">
              <el-select v-model="filterStatus" clearable placeholder="全部" @change="handleSearch">
                <el-option label="草稿" value="draft" />
                <el-option label="已发布" value="published" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="6" class="search-actions">
            <el-button type="primary" icon="Search" @click="handleSearch">查询</el-button>
            <el-button @click="resetFilter">重置</el-button>
          </el-col>
        </el-row>
      </el-form>

      <el-skeleton v-if="loading" animated :rows="8" />
      <template v-else>
        <el-table v-if="resumes.length" :data="resumes" stripe>
          <el-table-column prop="id" label="ID" width="72" />
          <el-table-column prop="username" label="用户" width="120" />
          <el-table-column prop="title" label="简历标题" min-width="180" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
                {{ row.status === 'published' ? '已发布' : '草稿' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="内容" min-width="210">
            <template #default="{ row }">
              <span class="content-summary">
                教育 {{ row.educations_count }} | 工作 {{ row.work_experiences_count }} | 项目 {{ row.projects_count }} | 技能 {{ row.skills_count }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="file_name" label="文件" min-width="140" show-overflow-tooltip />
          <el-table-column prop="updated_at" label="更新时间" width="180" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link icon="View" @click="viewDetail(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无简历数据" :image-size="64" />
      </template>

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

    <el-drawer v-model="drawerVisible" :title="currentResume?.title || '简历详情'" :size="isMobile ? '92%' : '620px'">
      <div class="drawer-body" v-loading="detailLoading">
        <template v-if="currentResume">
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

          <h4 class="section-title">教育经历</h4>
          <el-timeline v-if="detailData.educations?.length">
            <el-timeline-item v-for="edu in detailData.educations" :key="edu.id" :timestamp="edu.start_date">
              {{ edu.school }} - {{ edu.degree }} - {{ edu.major }}
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无教育经历" :image-size="56" />

          <h4 class="section-title">工作经历</h4>
          <el-timeline v-if="detailData.work_experiences?.length">
            <el-timeline-item v-for="work in detailData.work_experiences" :key="work.id" :timestamp="work.start_date">
              {{ work.company }} - {{ work.position }}
              <p class="detail-desc">{{ work.description }}</p>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无工作经历" :image-size="56" />

          <h4 class="section-title">项目经历</h4>
          <el-timeline v-if="detailData.projects?.length">
            <el-timeline-item v-for="project in detailData.projects" :key="project.id" :timestamp="project.start_date">
              {{ project.name }} ({{ project.role }})
              <p class="detail-desc">技术栈: {{ project.tech_stack }}</p>
              <p class="detail-text">{{ project.description }}</p>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无项目经历" :image-size="56" />

          <h4 class="section-title">技能</h4>
          <div v-if="detailData.skills?.length" class="skills-list">
            <el-tag v-for="skill in detailData.skills" :key="skill.id">{{ skill.name }} ({{ skill.level }}%)</el-tag>
          </div>
          <el-empty v-else description="暂无技能" :image-size="56" />
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMobile } from '@/composables/useMobile'
import { resumeApi } from '@/api'

const { isMobile } = useMobile()

const resumes = ref([])
const loading = ref(false)
const detailLoading = ref(false)
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
  } catch {
    resumes.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  loadResumes()
}

function resetFilter() {
  search.value = '
'
  filterStatus.value = ''
  currentPage.value = 1
  loadResumes()
}

function handlePageChange(page) {
  currentPage.value = page
  loadResumes()
}

async function viewDetail(row) {
  currentResume.value = row
  drawerVisible.value = true
  detailLoading.value = true
  try {
    detailData.value = await resumeApi.detail(row.id)
  } catch {
    detailData.value = {}
  } finally {
    detailLoading.value = false
  }
}

onMounted(loadResumes)
</script>

<style scoped>
.resume-manage {
  min-width: 0;
}

.page-card {
  border: 1px solid #ebeef5;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
  color: #333333;
}

.page-header p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #666666;
}

.search-form {
  margin-bottom: 12px;
}

.search-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

.content-summary {
  font-size: 13px;
  color: #666666;
}

.drawer-body {
  min-height: 240px;
}

.section-title {
  margin: 16px 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #333333;
}

.detail-desc,
.detail-text {
  margin-top: 4px;
  color: #666666;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .search-actions {
    justify-content: flex-start;
    margin-top: 4px;
  }

  .pagination {
    justify-content: center;
  }
}
</style>