<template>
  <div class="ai-logs">
    <el-card>
      <template #header>
        <span>AI助手日志管理</span>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- Query Logs Tab -->
        <el-tab-pane label="查询日志" name="query">
          <el-table :data="queryLogs" stripe v-loading="loading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="username" label="用户" width="100" />
            <el-table-column prop="query" label="查询内容" show-overflow-tooltip />
            <el-table-column prop="intent" label="意图" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ intentMap[row.intent] || row.intent }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="tokens_used" label="Token" width="80" />
            <el-table-column prop="created_at" label="时间" width="180" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button type="primary" link @click="showQueryDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Polish Logs Tab -->
        <el-tab-pane label="润色日志" name="polish">
          <el-table :data="polishLogs" stripe v-loading="loading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="username" label="用户" width="100" />
            <el-table-column prop="original_text" label="原始文本" show-overflow-tooltip />
            <el-table-column prop="polished_text" label="润色结果" show-overflow-tooltip />
            <el-table-column prop="module_name" label="模块" width="100">
              <template #default="{ row }">
                <el-tag size="small" v-if="row.module_name">{{ row.module_name }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="tokens_used" label="Token" width="80" />
            <el-table-column prop="created_at" label="时间" width="180" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button type="primary" link @click="showPolishDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Classification Logs Tab -->
        <el-tab-pane label="归类日志" name="classification">
          <el-table :data="classificationLogs" stripe v-loading="loading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="username" label="用户" width="100" />
            <el-table-column prop="file_name" label="文件名" width="200" />
            <el-table-column prop="modules_assigned" label="分配模块" width="200">
              <template #default="{ row }">
                <el-tag
                  v-for="m in (row.modules_assigned || [])"
                  :key="m"
                  size="small"
                  style="margin-right: 4px"
                >
                  {{ moduleLabels[m] || m }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="180" />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button type="primary" link @click="showClassificationDetail(row)">详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>

      <el-pagination
        v-if="total > pageSize"
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        class="pagination"
        @current-change="p => { currentPage = p; loadCurrentTab() }"
      />
    </el-card>

    <!-- Query Detail Dialog -->
    <el-dialog v-model="queryDetailVisible" title="查询详情" :width="isMobile ? '95%' : '600px'">
      <template v-if="currentQueryLog">
        <h4>用户查询:</h4>
        <p style="background: #f5f5f5; padding: 12px; border-radius: 6px; margin-bottom: 16px">
          {{ currentQueryLog.query }}
        </p>
        <h4>AI回复:</h4>
        <div style="background: #f0f9ff; padding: 12px; border-radius: 6px; white-space: pre-wrap">
          {{ currentQueryLog.response }}
        </div>
        <div style="margin-top: 12px; color: #999; font-size: 13px">
          意图: {{ intentMap[currentQueryLog.intent] || currentQueryLog.intent }} | Token: {{ currentQueryLog.tokens_used }} | 时间: {{ currentQueryLog.created_at }}
        </div>
      </template>
    </el-dialog>

    <!-- Polish Detail Dialog -->
    <el-dialog v-model="polishDetailVisible" title="润色详情" :width="isMobile ? '95%' : '700px'">
      <template v-if="currentPolishLog">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12">
            <h4>原始文本:</h4>
            <div style="background: #fafafa; padding: 12px; border-radius: 6px; white-space: pre-wrap; min-height: 100px">
              {{ currentPolishLog.original_text }}
            </div>
          </el-col>
          <el-col :xs="24" :sm="12">
            <h4>润色结果:</h4>
            <div style="background: #f0f9eb; padding: 12px; border-radius: 6px; white-space: pre-wrap; min-height: 100px">
              {{ currentPolishLog.polished_text }}
            </div>
          </el-col>
        </el-row>
        <div style="margin-top: 12px; color: #999; font-size: 13px">
          用户: {{ currentPolishLog.username }} | 模块: {{ currentPolishLog.module_name || '-' }} | Token: {{ currentPolishLog.tokens_used }} | 时间: {{ currentPolishLog.created_at }}
        </div>
      </template>
    </el-dialog>

    <!-- Classification Detail Dialog -->
    <el-dialog v-model="classDetailVisible" title="归类详情" :width="isMobile ? '95%' : '600px'">
      <template v-if="currentClassLog">
        <h4>文件: {{ currentClassLog.file_name }}</h4>
        <h4 style="margin-top: 12px">归类结果:</h4>
        <div style="background: #f5f5f5; padding: 12px; border-radius: 6px; white-space: pre-wrap">
          {{ JSON.stringify(currentClassLog.classification_result, null, 2) }}
        </div>
        <div style="margin-top: 12px; color: #999; font-size: 13px">
          用户: {{ currentClassLog.username }} | 状态: {{ currentClassLog.status }} | 时间: {{ currentClassLog.created_at }}
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { aiApi } from '@/api'

const isMobile = computed(() => window.innerWidth <= 768)
const activeTab = ref('query')
const loading = ref(false)
const total = ref(0)
const pageSize = ref(20)
const currentPage = ref(1)

const queryLogs = ref([])
const polishLogs = ref([])
const classificationLogs = ref([])

const queryDetailVisible = ref(false)
const polishDetailVisible = ref(false)
const classDetailVisible = ref(false)
const currentQueryLog = ref(null)
const currentPolishLog = ref(null)
const currentClassLog = ref(null)

const intentMap = {
  education: '教育背景',
  work_experience: '工作经历',
  project: '项目经历',
  skill: '技能列表',
  summary: '个人简介',
  general: '综合查询',
}

const moduleLabels = {
  education: '教育经历',
  work_experience: '工作经历',
  project: '项目经历',
  skill: '技能',
  certificate: '证书',
  award: '获奖',
  language: '语言能力',
}

async function loadCurrentTab() {
  loading.value = true
  try {
    const params = { page: currentPage.value }
    if (activeTab.value === 'query') {
      const data = await aiApi.logs(params)
      queryLogs.value = data.results || []
      total.value = data.count || 0
    } else if (activeTab.value === 'polish') {
      const data = await aiApi.polishLogs(params)
      polishLogs.value = data.results || []
      total.value = data.count || 0
    } else if (activeTab.value === 'classification') {
      const data = await aiApi.classificationLogs(params)
      classificationLogs.value = data.results || []
      total.value = data.count || 0
    }
  } catch { /* */ } finally {
    loading.value = false
  }
}

function handleTabChange() {
  currentPage.value = 1
  total.value = 0
  loadCurrentTab()
}

function showQueryDetail(row) {
  currentQueryLog.value = row
  queryDetailVisible.value = true
}

function showPolishDetail(row) {
  currentPolishLog.value = row
  polishDetailVisible.value = true
}

function showClassificationDetail(row) {
  currentClassLog.value = row
  classDetailVisible.value = true
}

onMounted(loadCurrentTab)
</script>

<style scoped>
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .el-table {
    font-size: 12px;
  }
  .el-table-column--mini {
    width: auto !important;
  }
  .pagination {
    justify-content: center;
  }
  .el-dialog {
    width: 95% !important;
  }
  .el-row {
    flex-direction: column;
  }
  .el-col {
    width: 100% !important;
    max-width: 100% !important;
    margin-bottom: 12px;
  }
}
</style>