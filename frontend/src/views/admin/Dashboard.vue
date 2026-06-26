<!--
  管理面板首页 Dashboard.vue —— 展示系统整体统计数据。

  作用：管理员登录后看到的第一个页面，展示关键指标和最近活动。

  功能：
  1. 统计卡片：显示用户总数、简历总数、AI查询次数、已发布简历数
  2. 最近注册用户列表
  3. 最近 AI 查询列表

  知识点（Vue 3 生命周期）：
  - onMounted()：组件挂载到 DOM 后执行（类似 created + mounted）
  - Promise.all()：并行执行多个异步操作，全部完成后返回结果
-->
<template>
  <div class="dashboard">
    <!-- ========== 统计卡片区域 ========== -->
    <el-row :gutter="20" class="stat-cards">
      <!-- :xs/:sm/:md 是 Element Plus 的响应式栅格系统 -->
      <!-- xs=超小屏(手机) sm=小屏 md=中屏(桌面) -->
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon stat-icon-blue">
            <el-icon :size="30"><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.userCount }}</div>
            <div class="stat-label">用户总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon stat-icon-green">
            <el-icon :size="30"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.resumeCount }}</div>
            <div class="stat-label">简历总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon stat-icon-orange">
            <el-icon :size="30"><ChatDotRound /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.queryCount }}</div>
            <div class="stat-label">AI查询次数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon stat-icon-red">
            <el-icon :size="30"><Checked /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.publishedCount }}</div>
            <div class="stat-label">已发布简历</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ========== 详情区域：最近用户 + 最近AI查询 ========== -->
    <el-row :gutter="20" class="detail-rows">
      <!-- 最近注册用户 -->
      <el-col :xs="24" :md="12">
        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <span>最近注册用户</span>
              <el-tag type="info" size="small">近5条</el-tag>
            </div>
          </template>
          <!-- stripe：斑马纹样式；size="small"：紧凑模式 -->
          <el-table :data="recentUsers" stripe size="small" :show-header="true">
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="role_display" label="角色">
              <!-- #default 插槽：自定义列的渲染内容 -->
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : 'success'" size="small">
                  {{ row.role_display }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="注册时间" />
          </el-table>
          <el-empty v-if="!recentUsers.length" description="暂无用户" :image-size="48" />
        </el-card>
      </el-col>
      <!-- 最近 AI 查询 -->
      <el-col :xs="24" :md="12">
        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <span>最近AI查询</span>
              <el-tag type="info" size="small">近5条</el-tag>
            </div>
          </template>
          <el-table :data="recentQueries" stripe size="small" :show-header="true">
            <el-table-column prop="username" label="用户" width="80" />
            <el-table-column prop="query" label="查询内容" show-overflow-tooltip />
            <el-table-column prop="intent" label="意图" width="90">
              <template #default="{ row }">
                <el-tag size="small">{{ intentMap[row.intent] || row.intent }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="160" />
          </el-table>
          <el-empty v-if="!recentQueries.length" description="暂无查询" :image-size="48" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
/**
 * 管理面板首页逻辑。
 *
 * 在组件挂载时并行请求用户、简历、AI日志数据，
 * 然后计算统计数据并展示最近记录。
 */
import { ref, onMounted } from 'vue'
import { userApi, resumeApi, aiApi } from '@/api'

// 统计数据
const stats = ref({ userCount: 0, resumeCount: 0, queryCount: 0, publishedCount: 0 })
const recentUsers = ref([])      // 最近注册用户
const recentQueries = ref([])    // 最近 AI 查询

// AI 意图中文映射
const intentMap = {
  education: '教育背景',
  work_experience: '工作经历',
  project: '项目经历',
  skill: '技能列表',
  summary: '个人简介',
  general: '综合查询',
}

/**
 * 组件挂载时加载数据。
 * 使用 Promise.all 并行请求三个接口，提高加载速度。
 */
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
    // 统计已发布简历数量
    stats.value.publishedCount = (resumes.results || []).filter(r => r.status === 'published').length
    // 取最近 5 条记录
    recentUsers.value = (users.results || []).slice(0, 5)
    recentQueries.value = (logs.results || []).slice(0, 5)
  } catch {
    // 首次加载静默失败
  }
})
</script>

<style scoped>
.stat-cards {
  margin-bottom: 0;
}

.stat-card {
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
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
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon-blue {
  background: linear-gradient(135deg, #409eff20, #409eff10);
  color: #409eff;
}

.stat-icon-green {
  background: linear-gradient(135deg, #67c23a20, #67c23a10);
  color: #67c23a;
}

.stat-icon-orange {
  background: linear-gradient(135deg, #e6a23c20, #e6a23c10);
  color: #e6a23c;
}

.stat-icon-red {
  background: linear-gradient(135deg, #f56c6c20, #f56c6c10);
  color: #f56c6c;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.detail-rows {
  margin-top: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.detail-card {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .stat-card :deep(.el-card__body) {
    padding: 14px;
    gap: 12px;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 10px;
  }

  .stat-icon .el-icon {
    font-size: 22px !important;
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