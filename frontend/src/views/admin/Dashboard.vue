<template>
  <div class="dashboard-page">
    <el-row :gutter="16" class="stat-grid">
      <el-col v-for="item in statCards" :key="item.key" :xs="12" :md="6">
        <el-card shadow="never" class="stat-card">
          <template v-if="loading">
            <el-skeleton animated :rows="2" />
          </template>
          <template v-else>
            <div class="stat-body">
              <div class="stat-icon" :class="item.className">
                <el-icon :size="28"><component :is="item.icon" /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats[item.key] }}</div>
                <div class="stat-label">{{ item.label }}</div>
              </div>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="content-grid">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="card-header">
              <span>最近注册用户</span>
              <el-tag type="info" size="small">近 5 条</el-tag>
            </div>
          </template>

          <el-skeleton v-if="loading" animated :rows="5" />
          <template v-else>
            <el-table v-if="recentUsers.length" :data="recentUsers" stripe size="small">
              <el-table-column prop="username" label="用户名" />
              <el-table-column prop="role_display" label="角色" width="110">
                <template #default="{ row }">
                  <el-tag :type="row.role === 'admin' ? 'danger' : 'success'" size="small">
                    {{ row.role_display }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="注册时间" width="170" />
            </el-table>
            <el-empty v-else description="暂无用户" :image-size="56" />
          </template>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="card-header">
              <span>最近 AI 查询</span>
              <el-tag type="info" size="small">近 5 条</el-tag>
            </div>
          </template>

          <el-skeleton v-if="loading" animated :rows="5" />
          <template v-else>
            <el-table v-if="recentQueries.length" :data="recentQueries" stripe size="small">
              <el-table-column prop="username" label="用户" width="90" />
              <el-table-column prop="query" label="查询内容" show-overflow-tooltip />
              <el-table-column prop="intent" label="意图" width="110">
                <template #default="{ row }">
                  <el-tag size="small">{{ intentMap[row.intent] || row.intent }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="时间" width="170" />
            </el-table>
            <el-empty v-else description="暂无查询" :image-size="56" />
          </template>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { userApi, resumeApi, aiApi } from '@/api'

const loading = ref(true)
const stats = ref({ userCount: 0, resumeCount: 0, queryCount: 0, publishedCount: 0 })
const recentUsers = ref([])
const recentQueries = ref([])

const intentMap = {
  education: '教育背景',
  work_experience: '工作经历',
  project: '项目经历',
  skill: '技能列表',
  summary: '个人简介',
  general: '综合查询',
}

const statCards = computed(() => ([
  { key: 'userCount', label: '用户总数', icon: 'User', className: 'stat-blue' },
  { key: 'resumeCount', label: '简历总数', icon: 'Document', className: 'stat-green' },
  { key: 'queryCount', label: 'AI 查询次数', icon: 'ChatDotRound', className: 'stat-orange' },
  { key: 'publishedCount', label: '已发布简历', icon: 'Checked', className: 'stat-red' },
]))

async function loadDashboard() {
  loading.value = true
  try {
    const [users, resumes, logs] = await Promise.all([
      userApi.list({ page_size: 100 }),
      resumeApi.list({ page_size: 100 }),
      aiApi.logs({ page_size: 100 }),
    ])

    stats.value.userCount = users.count || 0
    stats.value.resumeCount = resumes.count || 0
    stats.value.queryCount = logs.count || 0
    stats.value.publishedCount = (resumes.results || []).filter(item => item.status === 'published').length
    recentUsers.value = (users.results || []).slice(0, 5)
    recentQueries.value = (logs.results || []).slice(0, 5)
  } catch {
    recentUsers.value = []
    recentQueries.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-card,
.panel-card {
  border: 1px solid #ebeef5;
}

.stat-body {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 76px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-blue {
  color: #409eff;
  background: #ecf5ff;
}

.stat-green {
  color: #67c23a;
  background: #f0f9eb;
}

.stat-orange {
  color: #e6a23c;
  background: #fdf6ec;
}

.stat-red {
  color: #f56c6c;
  background: #fef0f0;
}

.stat-value {
  font-size: 28px;
  line-height: 1.2;
  font-weight: 700;
  color: #333333;
}

.stat-label {
  margin-top: 4px;
  font-size: 12px;
  color: #666666;
}

.content-grid {
  margin-top: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-card :deep(.el-card__body) {
  min-height: 320px;
}

@media (max-width: 768px) {
  .dashboard-page {
    gap: 12px;
  }

  .stat-body {
    min-height: 64px;
    gap: 10px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 10px;
  }

  .stat-value {
    font-size: 22px;
  }
}
</style>