<!--
  AI 日志管理页面 AiLogs.vue —— 管理员查看 AI 功能的使用日志。

  功能：
  1. 查询日志：记录用户的 AI 对话（问了什么、AI 回答了什么）
  2. 润色日志：记录文本润色操作（原文和润色结果对比）
  3. 归类日志：记录文件自动分类的结果

  使用 el-tabs 组件实现三个标签页切换。
-->
<template>
  <div class="ai-logs">
    <el-card>
      <template #header>
        <span>AI助手日志管理</span>
      </template>

      <!-- 标签页切换：查询日志 / 润色日志 / 归类日志 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 查询日志标签页 -->
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

        <!-- 润色日志标签页 -->
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

        <!-- 归类日志标签页 -->
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
                  class="module-tag"
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

    <!-- 查询详情弹窗 -->
    <el-dialog v-model="queryDetailVisible" title="查询详情" :width="isMobile ? '95%' : '600px'">
      <template v-if="currentQueryLog">
        <h4>用户查询:</h4>
        <p class="detail-query-box">{{ currentQueryLog.query }}</p>
        <h4>AI回复:</h4>
        <div class="detail-response-box">{{ currentQueryLog.response }}</div>
        <div class="detail-meta">
          意图: {{ intentMap[currentQueryLog.intent] || currentQueryLog.intent }} | Token: {{ currentQueryLog.tokens_used }} | 时间: {{ currentQueryLog.created_at }}
        </div>
      </template>
    </el-dialog>

    <!-- 润色详情弹窗 -->
    <el-dialog v-model="polishDetailVisible" title="润色详情" :width="isMobile ? '95%' : '700px'">
      <template v-if="currentPolishLog">
        <el-row :gutter="16">
          <el-col :xs="24" :sm="12">
            <h4>原始文本:</h4>
            <div class="detail-original-box">{{ currentPolishLog.original_text }}</div>
          </el-col>
          <el-col :xs="24" :sm="12">
            <h4>润色结果:</h4>
            <div class="detail-polished-box">{{ currentPolishLog.polished_text }}</div>
          </el-col>
        </el-row>
        <div class="detail-meta">
          用户: {{ currentPolishLog.username }} | 模块: {{ currentPolishLog.module_name || '-' }} | Token: {{ currentPolishLog.tokens_used }} | 时间: {{ currentPolishLog.created_at }}
        </div>
      </template>
    </el-dialog>

    <!-- 归类详情弹窗 -->
    <el-dialog v-model="classDetailVisible" title="归类详情" :width="isMobile ? '95%' : '600px'">
      <template v-if="currentClassLog">
        <h4>文件: {{ currentClassLog.file_name }}</h4>
        <h4 style="margin-top: 12px">归类结果:</h4>
        <div class="detail-json-box">
          {{ JSON.stringify(currentClassLog.classification_result, null, 2) }}
        </div>
        <div class="detail-meta">
          用户: {{ currentClassLog.username }} | 状态: {{ currentClassLog.status }} | 时间: {{ currentClassLog.created_at }}
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * AI 日志管理逻辑。
 *
 * 使用 el-tabs 实现三种日志的分类查看：
 * - 查询日志：用户与 AI 的对话记录
 * - 润色日志：文本润色的原文和结果
 * - 归类日志：文件上传后的自动分类结果
 */
import { ref, onMounted } from 'vue'
import { useMobile } from '@/composables/useMobile'
import { aiApi } from '@/api'

const { isMobile } = useMobile()

// 状态变量
const activeTab = ref('query')       // 当前激活的标签页
const loading = ref(false)
const total = ref(0)
const pageSize = ref(20)
const currentPage = ref(1)

// 三种日志数据
const queryLogs = ref([])
const polishLogs = ref([])
const classificationLogs = ref([])

// 详情弹窗状态
const queryDetailVisible = ref(false)
const polishDetailVisible = ref(false)
const classDetailVisible = ref(false)
const currentQueryLog = ref(null)
const currentPolishLog = ref(null)
const currentClassLog = ref(null)

// 意图类型中文映射
const intentMap = {
  education: '教育背景',
  work_experience: '工作经历',
  project: '项目经历',
  skill: '技能列表',
  summary: '个人简介',
  general: '综合查询',
}

// 模块类型中文映射
const moduleLabels = {
  education: '教育经历',
  work_experience: '工作经历',
  project: '项目经历',
  skill: '技能',
  certificate: '证书',
  award: '获奖',
  language: '语言能力',
}

/** 根据当前标签页加载对应日志数据。 */
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

/** 标签页切换时重置分页并重新加载数据。 */
function handleTabChange() {
  currentPage.value = 1
  total.value = 0
  loadCurrentTab()
}

function showQueryDetail(row) { currentQueryLog.value = row; queryDetailVisible.value = true }
function showPolishDetail(row) { currentPolishLog.value = row; polishDetailVisible.value = true }
function showClassificationDetail(row) { currentClassLog.value = row; classDetailVisible.value = true }

onMounted(loadCurrentTab)
</script>

<style scoped>
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .el-table { font-size: 12px; }
  .el-table-column--mini { width: auto !important; }
  .pagination { justify-content: center; }
  .el-dialog { width: 95% !important; }
  .el-row { flex-direction: column; }
  .el-col { width: 100% !important; max-width: 100% !important; margin-bottom: 12px; }
}

.module-tag { margin-right: 4px; }
.detail-query-box { background: #f5f5f5; padding: 12px; border-radius: 6px; margin-bottom: 16px; }
.detail-response-box { background: #f0f9ff; padding: 12px; border-radius: 6px; white-space: pre-wrap; }
.detail-meta { margin-top: 12px; color: #999; font-size: 13px; }
.detail-original-box { background: #fafafa; padding: 12px; border-radius: 6px; white-space: pre-wrap; min-height: 100px; }
.detail-polished-box { background: #f0f9eb; padding: 12px; border-radius: 6px; white-space: pre-wrap; min-height: 100px; }
.detail-json-box { background: #f5f5f5; padding: 12px; border-radius: 6px; white-space: pre-wrap; }
</style>