<template>
  <div class="visitor-page" v-loading="loading">
    <template v-if="resume">
      <!-- Quota Banner for HR mode -->
      <div v-if="isHRMode" class="hr-quota-banner">
        <el-icon><ChatDotRound /></el-icon>
        <span>HR AI咨询剩余 <strong>{{ aiRemaining }}</strong> / {{ aiTotal }} 次</span>
        <el-tag v-if="aiRemaining <= 0" type="danger" size="small">配额已用尽</el-tag>
      </div>

      <!-- Header -->
      <div class="visitor-header">
        <div class="header-content">
          <h1 class="resume-title">{{ resume.title }}</h1>
          <p class="resume-owner">{{ resume.username }} 的个人简历</p>
          <p v-if="resume.summary" class="resume-summary">{{ resume.summary }}</p>
          <div v-if="resume.tags?.length" class="resume-tags">
            <el-tag
              v-for="(tag, i) in resume.tags"
              :key="i"
              :type="tagTypeColor(tag.type)"
              size="small"
              effect="plain"
            >
              {{ tag.name }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- Main Content (2-column when HR mode) -->
      <div :class="isHRMode ? 'visitor-content-hr' : 'visitor-content'">
        <!-- Left: Resume Modules -->
        <div class="resume-modules">
          <!-- Education -->
          <section v-if="resume.modules?.education?.length" class="module-section">
            <h2 class="section-title">
              <el-icon><School /></el-icon>
              教育经历
            </h2>
            <div class="timeline">
              <div v-for="(edu, i) in resume.modules.education" :key="i" class="timeline-item">
                <div class="timeline-date">{{ edu.start_date }} ~ {{ edu.end_date || '至今' }}</div>
                <div class="timeline-content">
                  <h3>{{ edu.school }}</h3>
                  <p class="sub-info">{{ edu.degree }} | {{ edu.major }}</p>
                  <p v-if="edu.description" class="desc">{{ edu.description }}</p>
                </div>
              </div>
            </div>
          </section>

          <!-- Work Experience -->
          <section v-if="resume.modules?.work_experience?.length" class="module-section">
            <h2 class="section-title">
              <el-icon><OfficeBuilding /></el-icon>
              工作经历
            </h2>
            <div class="timeline">
              <div v-for="(work, i) in resume.modules.work_experience" :key="i" class="timeline-item">
                <div class="timeline-date">{{ work.start_date }} ~ {{ work.end_date || '至今' }}</div>
                <div class="timeline-content">
                  <h3>{{ work.company }}</h3>
                  <p class="sub-info highlight">{{ work.position }}</p>
                  <p v-if="work.description" class="desc">{{ work.description }}</p>
                </div>
              </div>
            </div>
          </section>

          <!-- Projects -->
          <section v-if="resume.modules?.project?.length" class="module-section">
            <h2 class="section-title">
              <el-icon><FolderOpened /></el-icon>
              项目经历
            </h2>
            <div class="project-grid">
              <div v-for="(proj, i) in resume.modules.project" :key="i" class="project-card">
                <h3>{{ proj.name }}</h3>
                <el-tag v-if="proj.role" size="small" type="warning" effect="plain">{{ proj.role }}</el-tag>
                <p v-if="proj.tech_stack" class="tech-stack">技术栈: {{ proj.tech_stack }}</p>
                <p v-if="proj.description" class="desc">{{ proj.description }}</p>
              </div>
            </div>
          </section>

          <!-- Skills -->
          <section v-if="resume.modules?.skill?.length" class="module-section">
            <h2 class="section-title">
              <el-icon><TrendCharts /></el-icon>
              技能清单
            </h2>
            <div class="skills-grid">
              <div v-for="(skill, i) in resume.modules.skill" :key="i" class="skill-item">
                <div class="skill-header">
                  <span class="skill-name">{{ skill.name }}</span>
                  <span class="skill-level">{{ skill.level }}%</span>
                </div>
                <el-progress
                  :percentage="skill.level"
                  :stroke-width="8"
                  :show-text="false"
                  :color="getSkillColor(skill.level)"
                />
                <span class="skill-category">{{ skill.category }}</span>
              </div>
            </div>
          </section>

          <!-- Certificate / Award / Language -->
          <section
            v-for="mod in textModules"
            :key="mod.key"
            class="module-section"
            v-if="resume.modules?.[mod.key]"
          >
            <h2 class="section-title">
              <el-icon><component :is="mod.icon" /></el-icon>
              {{ mod.label }}
            </h2>
            <div class="text-content">{{ resume.modules[mod.key] }}</div>
          </section>

          <!-- Download section -->
          <section v-if="resume.visitor_allow_download" class="module-section download-section">
            <el-button type="primary" icon="Download" @click="downloadPdf" :loading="downloading">
              下载PDF简历
            </el-button>
          </section>
        </div>

        <!-- Right: HR AI Panel (only in HR mode) -->
        <div v-if="isHRMode" class="hr-ai-panel">
          <div class="ai-panel-header">
            <el-icon><ChatDotRound /></el-icon>
            <span>HR AI助手</span>
            <el-tag v-if="aiRemaining > 0" type="success" size="small">可用</el-tag>
            <el-tag v-else type="danger" size="small">已用尽</el-tag>
          </div>

          <!-- Chat messages -->
          <div class="ai-chat-messages" ref="chatMessagesRef">
            <div v-if="chatMessages.length === 0" class="ai-empty">
              <el-icon :size="40" color="#c0c4cc"><ChatDotRound /></el-icon>
              <p>向AI助手提问关于该候选人的问题</p>
              <p class="ai-hint">例如："该候选人适合哪些岗位？""技能优势是什么？"</p>
            </div>
            <div v-for="(msg, i) in chatMessages" :key="i" :class="['chat-msg', msg.role]">
              <div class="msg-avatar">
                <el-icon v-if="msg.role === 'user'" color="#409eff"><User /></el-icon>
                <el-icon v-else color="#67c23a"><Monitor /></el-icon>
              </div>
              <div class="msg-content">
                <div class="msg-text" v-html="msg.text"></div>
              </div>
            </div>
            <div v-if="aiLoading" class="chat-msg assistant">
              <div class="msg-avatar"><el-icon color="#67c23a"><Monitor /></el-icon></div>
              <div class="msg-content"><div class="msg-text typing">思考中...</div></div>
            </div>
          </div>

          <!-- Input area -->
          <div class="ai-input-area">
            <el-input
              v-model="chatInput"
              type="textarea"
              :rows="2"
              placeholder="输入您的问题，如"该候选人适合哪些岗位？""
              :disabled="aiRemaining <= 0 || aiLoading"
              @keydown.enter.ctrl="sendChat"
            />
            <div class="ai-input-actions">
              <el-button
                type="primary"
                icon="Promotion"
                :loading="aiLoading"
                :disabled="!chatInput.trim() || aiRemaining <= 0"
                @click="sendChat"
              >
                发送
              </el-button>
            </div>
          </div>

          <!-- Polish section -->
          <div class="ai-polish-section">
            <el-divider>文本润色</el-divider>
            <el-input
              v-model="polishInput"
              type="textarea"
              :rows="3"
              placeholder="粘贴简历片段，AI将优化表达..."
              :disabled="aiRemaining <= 0 || polishLoading"
            />
            <el-button
              type="warning"
              icon="MagicStick"
              :loading="polishLoading"
              :disabled="!polishInput.trim() || aiRemaining <= 0"
              @click="doPolish"
              style="margin-top: 8px; width: 100%"
            >
              一键润色
            </el-button>

            <!-- Polish result -->
            <div v-if="polishResult" class="polish-result">
              <h4>润色结果：</h4>
              <div class="polish-text">{{ polishResult }}</div>
            </div>
          </div>

          <!-- Quota exhausted message -->
          <div v-if="aiRemaining <= 0" class="quota-exhausted">
            <el-alert
              type="warning"
              :closable="false"
              show-icon
              title="配额已用尽"
              description="AI调用次数已达上限，请联系招聘方或管理员申请更多次数。"
            />
          </div>
        </div>
      </div>

      <!-- Footer watermark -->
      <div class="visitor-footer">
        <p>仅供展示，禁止转载 | 智能简历管理系统</p>
      </div>
    </template>

    <!-- Error state -->
    <template v-if="error && !loading">
      <div class="error-page">
        <el-icon :size="64" color="#c0c4cc"><WarningFilled /></el-icon>
        <h2>访问受限</h2>
        <p>{{ error }}</p>
        <el-button type="primary" @click="$router.push('/login')">前往登录</el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { visitorApi } from '@/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const resume = ref(null)
const loading = ref(false)
const error = ref('')
const downloading = ref(false)

// HR mode state
const isHRMode = computed(() => route.query.role === 'hr' && resume.value?.hr_enabled)
const aiRemaining = ref(0)
const aiTotal = ref(0)

// Chat state
const chatMessages = ref([])
const chatInput = ref('')
const aiLoading = ref(false)
const chatMessagesRef = ref(null)

// Polish state
const polishInput = ref('')
const polishResult = ref('')
const polishLoading = ref(false)

const textModules = [
  { key: 'certificate', label: '证书', icon: 'Stamp' },
  { key: 'award', label: '获奖荣誉', icon: 'Trophy' },
  { key: 'language', label: '语言能力', icon: 'ChatLineRound' },
]

function tagTypeColor(type) {
  const colors = { skill: '', project: 'success', certificate: 'warning', award: 'danger', language: 'info' }
  return colors[type] || ''
}

function getSkillColor(level) {
  if (level >= 80) return '#67c23a'
  if (level >= 60) return '#409eff'
  if (level >= 40) return '#e6a23c'
  return '#f56c6c'
}

function scrollToBottom() {
  nextTick(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  })
}

async function sendChat() {
  if (!chatInput.value.trim() || aiRemaining.value <= 0) return
  const query = chatInput.value.trim()
  chatMessages.value.push({ role: 'user', text: query })
  chatInput.value = ''
  aiLoading.value = true
  scrollToBottom()

  try {
    const token = route.params.token
    const params = { sig: route.query.sig || '', expires: route.query.expires || 0, role: 'hr' }
    const res = await visitorApi.aiChat(token, params, { query, call_type: 'chat' })
    chatMessages.value.push({ role: 'assistant', text: res.response || '无回复' })
    aiRemaining.value = res.remaining ?? aiRemaining.value
  } catch (e) {
    if (e.response?.status === 429) {
      aiRemaining.value = 0
      chatMessages.value.push({ role: 'assistant', text: '配额已用尽，无法继续调用AI服务' })
    } else {
      chatMessages.value.push({ role: 'assistant', text: 'AI服务调用失败，请稍后重试' })
    }
  } finally {
    aiLoading.value = false
    scrollToBottom()
  }
}

async function doPolish() {
  if (!polishInput.value.trim() || aiRemaining.value <= 0) return
  polishLoading.value = true
  polishResult.value = ''

  try {
    const token = route.params.token
    const params = { sig: route.query.sig || '', expires: route.query.expires || 0, role: 'hr' }
    const res = await visitorApi.aiChat(token, params, { query: polishInput.value.trim(), call_type: 'polish' })
    polishResult.value = res.polished_text || res.response || '润色失败'
    aiRemaining.value = res.remaining ?? aiRemaining.value
  } catch (e) {
    if (e.response?.status === 429) {
      aiRemaining.value = 0
      ElMessage.error('配额已用尽')
    } else {
      ElMessage.error('AI润色失败')
    }
  } finally {
    polishLoading.value = false
  }
}

async function downloadPdf() {
  downloading.value = true
  try {
    const token = route.params.token
    const role = route.query.role || 'visitor'
    const sig = route.query.sig || ''
    const expires = route.query.expires || 0
    const blob = await visitorApi.downloadPdf(token, { sig, expires, role })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = resume.value.username + '_resume.pdf'
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch {
    ElMessage.error('下载失败')
  } finally {
    downloading.value = false
  }
}

onMounted(async () => {
  loading.value = true
  error.value = ''
  try {
    const token = route.params.token
    const params = {
      sig: route.query.sig || '',
      expires: route.query.expires || 0,
    }
    if (route.query.role) {
      params.role = route.query.role
    }
    const data = await visitorApi.getResume(token, params)
    resume.value = data
    if (data.hr_enabled) {
      aiRemaining.value = data.ai_remaining || 0
      aiTotal.value = data.ai_quota || 0
    }
  } catch (e) {
    if (e.response?.status === 404) {
      error.value = e.response?.data?.detail || '访问链接无效或已过期'
    } else if (e.response?.status === 403) {
      error.value = e.response?.data?.detail || '访问被拒绝'
    } else {
      error.value = '加载失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.visitor-page {
  min-height: 100vh;
  background: #f5f7fa;
}

/* HR Quota Banner */
.hr-quota-banner {
  background: linear-gradient(135deg, #ecf5ff 0%, #e8f4fd 100%);
  border-bottom: 1px solid #d9ecff;
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #409eff;
  position: sticky;
  top: 0;
  z-index: 100;
}

.hr-quota-banner strong {
  font-size: 18px;
  color: #303133;
}

.visitor-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: #fff;
  padding: 48px 20px;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
}

.resume-title {
  font-size: 32px;
  margin-bottom: 8px;
  font-weight: 700;
}

.resume-owner {
  font-size: 16px;
  color: #a0c4ff;
  margin-bottom: 16px;
}

.resume-summary {
  font-size: 15px;
  line-height: 1.8;
  color: #e0e0e0;
  margin-bottom: 16px;
}

.resume-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* Standard visitor layout */
.visitor-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 20px;
}

/* HR 2-column layout */
.visitor-content-hr {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px 20px;
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.resume-modules {
  flex: 1;
  min-width: 0;
}

/* HR AI Panel */
.hr-ai-panel {
  width: 420px;
  min-width: 380px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 60px;
  max-height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ai-panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  background: #fafafa;
}

.ai-chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  min-height: 200px;
  max-height: 400px;
}

.ai-empty {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.ai-empty p {
  margin-top: 8px;
  font-size: 14px;
}

.ai-hint {
  font-size: 12px !important;
  color: #c0c4cc !important;
}

.chat-msg {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.chat-msg.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.msg-content {
  max-width: 80%;
}

.msg-text {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.chat-msg.user .msg-text {
  background: #409eff;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-msg.assistant .msg-text {
  background: #f4f4f5;
  color: #303133;
  border-bottom-left-radius: 4px;
}

.msg-text.typing {
  color: #909399;
}

.ai-input-area {
  padding: 12px 16px;
  border-top: 1px solid #ebeef5;
}

.ai-input-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.ai-polish-section {
  padding: 0 16px 16px;
}

.polish-result {
  margin-top: 12px;
  padding: 12px;
  background: #f0f9eb;
  border-radius: 8px;
  border: 1px solid #e1f3d8;
}

.polish-result h4 {
  font-size: 13px;
  color: #67c23a;
  margin-bottom: 8px;
}

.polish-text {
  font-size: 14px;
  line-height: 1.7;
  color: #303133;
  white-space: pre-wrap;
}

.quota-exhausted {
  padding: 12px 16px;
}

/* Module sections */
.module-section {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #409eff;
}

/* Timeline */
.timeline {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.timeline-item {
  display: flex;
  gap: 20px;
}

.timeline-date {
  min-width: 180px;
  color: #909399;
  font-size: 13px;
  padding-top: 4px;
}

.timeline-content h3 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 4px;
}

.sub-info {
  color: #606266;
  font-size: 14px;
}

.sub-info.highlight {
  color: #409eff;
  font-weight: 500;
}

.desc {
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* Project grid */
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.project-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
}

.project-card h3 {
  font-size: 15px;
  margin-bottom: 8px;
}

.tech-stack {
  color: #67c23a;
  font-size: 13px;
  margin: 6px 0;
}

/* Skills */
.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.skill-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.skill-header {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.skill-name {
  color: #303133;
  font-weight: 500;
}

.skill-level {
  color: #909399;
}

.skill-category {
  font-size: 11px;
  color: #c0c4cc;
}

/* Text content */
.text-content {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #606266;
  font-size: 14px;
}

/* Download */
.download-section {
  text-align: center;
}

/* Footer */
.visitor-footer {
  text-align: center;
  padding: 20px;
  color: #c0c4cc;
  font-size: 12px;
  border-top: 1px solid #ebeef5;
  background: #fff;
}

/* Error page */
.error-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  gap: 16px;
  color: #909399;
}

.error-page h2 {
  color: #303133;
}

.error-page p {
  max-width: 400px;
  text-align: center;
}

/* Responsive */
@media (max-width: 1024px) {
  .visitor-content-hr {
    flex-direction: column;
  }
  .hr-ai-panel {
    width: 100%;
    min-width: auto;
    position: static;
    max-height: none;
  }
}

@media (max-width: 768px) {
  .visitor-header {
    padding: 32px 16px;
  }
  .resume-title {
    font-size: 24px;
  }
  .timeline-item {
    flex-direction: column;
    gap: 4px;
  }
  .timeline-date {
    min-width: auto;
  }
  .project-grid {
    grid-template-columns: 1fr;
  }
  .skills-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
}
</style>