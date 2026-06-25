<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stat-cards">
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #409eff20; color: #409eff">
            <el-icon :size="32"><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.userCount }}</div>
            <div class="stat-label">用户总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #67c23a20; color: #67c23a">
            <el-icon :size="32"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.resumeCount }}</div>
            <div class="stat-label">简历总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #e6a23c20; color: #e6a23c">
            <el-icon :size="32"><ChatDotRound /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.queryCount }}</div>
            <div class="stat-label">AI查询次数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #f56c6c20; color: #f56c6c">
            <el-icon :size="32"><Checked /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.publishedCount }}</div>
            <div class="stat-label">已发布简历</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="detail-rows">
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <span>最近注册用户</span>
          </template>
          <el-table :data="recentUsers" stripe size="small">
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="role_display" label="角色">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : 'success'" size="small">
                  {{ row.role_display }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="注册时间" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card>
          <template #header>
            <span>最近AI查询</span>
          </template>
          <el-table :data="recentQueries" stripe size="small">
            <el-table-column prop="username" label="用户" width="80" />
            <el-table-column prop="query" label="查询内容" show-overflow-tooltip />
            <el-table-column prop="intent" label="意图" width="90">
              <template #default="{ row }">
                <el-tag size="small">{{ intentMap[row.intent] || row.intent }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="160" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { userApi, resumeApi, aiApi } from '@/api'

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

onMounted(async () => {
  try {
    const [users, resumes, logs] = await Promise.all([
      userApi.list({ page_size: 100 }),
      resumeApi.list({ page_size: 100 }),
      aiApi.logs({ page_size: 100 }),
    ])
    stats.value.userCount = users.count || 0
    stats.value.resumeCount = resumes.count || 0
    stats.value.queryCount = logs.count || 0
    stats.value.publishedCount = (resumes.results || []).filter(r => r.status === 'published').length
    recentUsers.value = (users.results || []).slice(0, 5)
    recentQueries.value = (logs.results || []).slice(0, 5)
  } catch {
    // silently fail on initial load
  }
})
</script>

<style scoped>
.stat-cards {
  margin-bottom: 0;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}

.detail-rows {
  margin-top: 20px;
}

@media (max-width: 768px) {
  .stat-card :deep(.el-card__body) {
    padding: 12px;
    gap: 10px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
  }

  .stat-icon .el-icon {
    font-size: 24px !important;
  }

  .stat-value {
    font-size: 20px;
  }

  .stat-label {
    font-size: 12px;
  }

  .detail-rows {
    margin-top: 12px;
  }

  .detail-rows .el-col {
    margin-bottom: 12px;
  }
}
</style>