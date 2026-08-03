<template>
  <div class="dashboard">
    <!-- ===== Header Section ===== -->
    <div class="page-header">
      <div class="page-title-wrap">
        <h1 class="page-title">管理中心</h1>
        <p class="page-subtitle">欢迎回来，查看系统概览和统计数据</p>
      </div>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading" class="refresh-btn">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- ===== Stat Overview Cards ===== -->
    <div class="stats-grid">
      <div
        v-for="item in statCards"
        :key="item.key"
        class="stat-card"
        :class="item.className"
      >
        <div class="stat-icon-wrap">
          <el-icon :size="22"><component :is="item.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            <span v-if="!loading">{{ stats[item.key] }}</span>
            <span v-else class="stat-skeleton">—</span>
          </div>
          <div class="stat-label">{{ item.label }}</div>
          <div v-if="item.trend" class="stat-trend" :class="item.trendDirection">
            <el-icon><component :is="item.trendIcon" /></el-icon>
            {{ item.trend }}
          </div>
        </div>
      </div>
    </div>

    <!-- ===== Content Panels ===== -->
    <div class="panels-grid">
      <!-- Recent Users -->
      <div class="panel-card">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon class="panel-icon"><User /></el-icon>
            <span>最近注册用户</span>
          </div>
          <el-tag size="small" effect="plain" class="panel-badge">近 5 条</el-tag>
        </div>
        <div class="panel-body">
          <el-skeleton v-if="loading" animated :rows="5" />
          <template v-else-if="recentUsers.length">
            <div v-for="user in recentUsers" :key="user.id" class="list-item">
              <div class="user-avatar-sm">{{ user.username?.[0]?.toUpperCase() }}</div>
              <div class="user-info">
                <div class="user-name">{{ user.username }}</div>
                <div class="user-meta">{{ user.created_at }}</div>
              </div>
              <el-tag
                :type="user.role === 'admin' ? 'danger' : 'success'"
                size="small"
                effect="light"
                class="user-role"
              >
                {{ user.role_display }}
              </el-tag>
            </div>
          </template>
          <el-empty v-else description="暂无用户" :image-size="56" />
        </div>
      </div>

      <!-- Recent AI Queries -->
      <div class="panel-card">
        <div class="panel-header">
          <div class="panel-title">
            <el-icon class="panel-icon"><ChatDotRound /></el-icon>
            <span>最近 AI 查询</span>
          </div>
          <el-tag size="small" effect="plain" class="panel-badge">近 5 条</el-tag>
        </div>
        <div class="panel-body">
          <el-skeleton v-if="loading" animated :rows="5" />
          <template v-else-if="recentQueries.length">
            <div v-for="query in recentQueries" :key="query.id" class="list-item">
              <div class="query-icon">
                <el-icon :size="16"><ChatLineRound /></el-icon>
              </div>
              <div class="query-info">
                <div class="query-text">{{ query.query }}</div>
                <div class="query-meta">
                  <span class="query-user">{{ query.username }}</span>
                  <span class="query-time">{{ query.created_at }}</span>
                </div>
              </div>
              <el-tag size="small" effect="light" class="query-intent">
                {{ intentMap[query.intent] || query.intent }}
              </el-tag>
            </div>
          </template>
          <el-empty v-else description="暂无查询" :image-size="56" />
        </div>
      </div>
    </div>
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
  {
    key: 'userCount',
    label: '用户总数',
    icon: 'User',
    className: 'stat-blue',
    trend: '+12%',
    trendDirection: 'up',
    trendIcon: 'ArrowUp',
  },
  {
    key: 'resumeCount',
    label: '简历总数',
    icon: 'Document',
    className: 'stat-green',
    trend: '+8%',
    trendDirection: 'up',
    trendIcon: 'ArrowUp',
  },
  {
    key: 'queryCount',
    label: 'AI 查询次数',
    icon: 'ChatDotRound',
    className: 'stat-purple',
    trend: '+24%',
    trendDirection: 'up',
    trendIcon: 'ArrowUp',
  },
  {
    key: 'publishedCount',
    label: '已发布简历',
    icon: 'Checked',
    className: 'stat-orange',
    trend: '+5%',
    trendDirection: 'up',
    trendIcon: 'ArrowUp',
  },
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

async function refreshData() {
  await loadDashboard()
}

onMounted(loadDashboard)
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* ===== Page Header ===== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.page-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--color-ink);
  letter-spacing: -0.3px;
}

.page-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--color-ink-muted-48);
  line-height: 1.5;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.refresh-btn {
  border-radius: 10px;
}

/* ===== Stats Grid ===== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--color-canvas);
  border: 1px solid var(--color-divider-soft);
  border-radius: 14px;
  transition: all 0.2s ease-out;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  border-radius: 14px 14px 0 0;
  transition: height 0.2s ease-out;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: var(--color-hairline);
}

.stat-blue::before { background: var(--color-primary); }
.stat-green::before { background: #16a34a; }
.stat-purple::before { background: #7c3aed; }
.stat-orange::before { background: #ea580c; }

.stat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-blue .stat-icon-wrap {
  color: var(--color-primary);
  background: rgba(0, 102, 204, 0.08);
}

.stat-green .stat-icon-wrap {
  color: #16a34a;
  background: rgba(22, 163, 74, 0.08);
}

.stat-purple .stat-icon-wrap {
  color: #7c3aed;
  background: rgba(124, 58, 237, 0.08);
}

.stat-orange .stat-icon-wrap {
  color: #ea580c;
  background: rgba(234, 88, 12, 0.08);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-ink);
  line-height: 1.2;
  letter-spacing: -0.5px;
}

.stat-skeleton {
  color: var(--color-ink-muted-48);
}

.stat-label {
  font-size: 13px;
  color: var(--color-ink-muted-48);
  font-weight: 500;
}

.stat-trend {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  font-weight: 600;
  margin-top: 2px;
}

.stat-trend.up {
  color: #16a34a;
}

.stat-trend.down {
  color: #ef4444;
}

/* ===== Panels Grid ===== */
.panels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 20px;
}

.panel-card {
  background: var(--color-canvas);
  border: 1px solid var(--color-divider-soft);
  border-radius: 14px;
  overflow: hidden;
  transition: all 0.2s ease-out;
}

.panel-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-divider-soft);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
}

.panel-icon {
  color: var(--color-primary);
}

.panel-badge {
  font-size: 11px;
}

.panel-body {
  padding: 8px 0;
  min-height: 280px;
}

/* ===== List Items ===== */
.list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 20px;
  transition: background 0.15s ease-out;
  cursor: pointer;
}

.list-item:hover {
  background: var(--color-surface-pearl);
}

.list-item + .list-item {
  border-top: 1px solid var(--color-divider-soft);
}

.user-avatar-sm {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.user-info,
.query-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-meta,
.query-meta {
  font-size: 12px;
  color: var(--color-ink-muted-48);
  margin-top: 2px;
}

.query-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(0, 102, 204, 0.08);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.query-text {
  font-size: 13px;
  color: var(--color-ink);
  line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.query-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 4px;
}

.query-user {
  font-weight: 500;
}

.query-time {
  color: var(--color-ink-muted-48);
}

.query-intent {
  font-size: 11px;
  flex-shrink: 0;
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .dashboard {
    gap: 20px;
  }

  .page-header {
    flex-direction: column;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .stat-card {
    padding: 16px;
    gap: 12px;
  }

  .stat-value {
    font-size: 22px;
  }

  .stat-icon-wrap {
    width: 40px;
    height: 40px;
  }

  .panels-grid {
    grid-template-columns: 1fr;
  }

  .panel-body {
    min-height: auto;
  }
}
</style>
