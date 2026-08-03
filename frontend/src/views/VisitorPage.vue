<template>
  <div class="visitor-page" v-loading="loading">
    <template v-if="error && !loading">
      <div class="error-page">
        <el-icon :size="64" color="#c0c4cc"><WarningFilled /></el-icon>
        <h2>访问受限</h2>
        <p>{{ error }}</p>
        <el-button type="primary" @click="$router.push('/login')">前往登录</el-button>
      </div>
    </template>

    <template v-else-if="loading && !resume">
      <div class="skeleton-wrapper">
        <div class="skeleton-header">
          <div class="skeleton-line skeleton-title"></div>
          <div class="skeleton-line skeleton-subtitle"></div>
          <div class="skeleton-line skeleton-text"></div>
        </div>
        <div class="skeleton-body">
          <div v-for="i in 3" :key="i" class="skeleton-card">
            <div class="skeleton-line skeleton-card-title"></div>
            <div class="skeleton-line skeleton-card-text"></div>
            <div class="skeleton-line skeleton-card-text short"></div>
          </div>
        </div>
      </div>
    </template>

    <template v-else-if="resume">
      <div v-if="isAiMode" class="ai-quota-banner">
        <el-icon><ChatDotRound /></el-icon>
        <span>AI咨询剩余 <strong>{{ aiRemaining }}</strong> / {{ aiTotal }} 次</span>
        <el-tag v-if="aiRemaining <= 0" type="danger" size="small">配额已用尽</el-tag>
      </div>

      <header class="visitor-header">
        <div class="header-content">
          <h1 class="resume-title">{{ resume.title }}</h1>
          <p class="resume-owner">{{ resume.username }} 的个人简历</p>
          <p v-if="resume.summary" class="resume-summary">{{ resume.summary }}</p>
          <div v-if="resume.tags?.length" class="resume-tags">
            <el-tag
              v-for="(tag, index) in resume.tags"
              :key="`${tag.name}-${index}`"
              :type="tagTypeColor(tag.type)"
              size="small"
              effect="plain"
            >
              {{ tag.name }}
            </el-tag>
          </div>
        </div>
        <div class="header-shape header-shape-1"></div>
        <div class="header-shape header-shape-2"></div>
      </header>

      <div :class="isAiMode ? 'visitor-content-ai' : 'visitor-content'">
        <main class="resume-modules">
          <section
            v-for="section in structuredSections"
            :key="section.key"
            class="module-section"
          >
            <h2 class="section-title">
              <el-icon><component :is="section.icon" /></el-icon>
              {{ section.label }}
            </h2>

            <div v-if="section.type === 'timeline'" class="timeline">
              <div v-for="(item, index) in section.items" :key="index" class="timeline-item">
                <div class="timeline-dot"></div>
                <div class="timeline-date">{{ section.dateText(item) }}</div>
                <div class="timeline-content">
                  <h3>{{ section.titleText(item) }}</h3>
                  <p v-if="section.subtitleText(item)" class="sub-info" :class="section.subtitleClass">
                    {{ section.subtitleText(item) }}
                  </p>
                  <p v-if="item.description" class="desc">{{ item.description }}</p>
                </div>
              </div>
            </div>

            <div v-else-if="section.type === 'grid'" class="project-grid">
              <article v-for="(item, index) in section.items" :key="index" class="project-card">
                <h3>{{ item.name }}</h3>
                <el-tag v-if="item.role" size="small" type="warning" effect="plain">
                  {{ item.role }}
                </el-tag>
                <p v-if="item.tech_stack" class="tech-stack">技术栈: {{ item.tech_stack }}</p>
                <p v-if="item.description" class="desc">{{ item.description }}</p>
              </article>
            </div>

            <div v-else-if="section.type === 'skills'" class="skills-grid">
              <div v-for="(item, index) in section.items" :key="index" class="skill-item">
                <div class="skill-header">
                  <span class="skill-name">{{ item.name }}</span>
                  <span class="skill-level">{{ item.level }}%</span>
                </div>
                <el-progress
                  :percentage="item.level"
                  :stroke-width="8"
                  :show-text="false"
                  :color="getSkillColor(item.level)"
                />
                <span class="skill-category">{{ item.category }}</span>
              </div>
            </div>
          </section>

          <section
            v-for="mod in textSections"
            :key="mod.key"
            class="module-section"
          >
            <h2 class="section-title">
              <el-icon><component :is="mod.icon" /></el-icon>
              {{ mod.label }}
            </h2>
            <div class="text-content">{{ mod.value }}</div>
          </section>

          <section v-if="resume.visitor_allow_download" class="module-section download-section">
            <el-button type="primary" icon="Download" :loading="downloading" @click="downloadPdf">
              下载PDF简历
            </el-button>
          </section>
        </main>

        <aside v-if="isAiMode" class="ai-panel">
          <div class="ai-panel-header">
            <div class="ai-panel-header-left">
              <div class="ai-panel-icon">
                <el-icon><ChatDotRound /></el-icon>
              </div>
              <span>AI助手</span>
            </div>
            <el-tag v-if="aiRemaining > 0" type="success" size="small">可用</el-tag>
            <el-tag v-else type="danger" size="small">已用尽</el-tag>
          </div>

          <div class="ai-chat-messages" ref="chatMessagesRef">
            <div v-if="chatMessages.length === 0" class="ai-empty">
              <div class="ai-empty-icon">
                <el-icon :size="36" color="#409eff"><ChatDotRound /></el-icon>
              </div>
              <p class="ai-empty-title">向 AI 助手提问关于这份简历的问题</p>
              <p class="ai-hint">例如：这位候选人适合哪些岗位？</p>
            </div>

            <div v-for="(msg, index) in chatMessages" :key="index" :class="['chat-msg', msg.role]">
              <div class="msg-avatar" :class="msg.role">
                <el-icon v-if="msg.role === 'user'"><User /></el-icon>
                <el-icon v-else><Monitor /></el-icon>
              </div>
              <div class="msg-content">
                <div class="msg-text" v-html="msg.text"></div>
              </div>
            </div>

            <div v-if="aiLoading" class="chat-msg assistant">
              <div class="msg-avatar assistant"><el-icon><Monitor /></el-icon></div>
              <div class="msg-content">
                <div class="msg-text typing">
                  <div class="typing-dots"><span></span><span></span><span></span></div>
                </div>
              </div>
            </div>
          </div>

          <div class="ai-input-area">
            <el-input
              v-model="chatInput"
              type="textarea"
              :rows="2"
              placeholder="输入你的问题，例如：这位候选人适合哪些岗位？"
              :disabled="aiRemaining <= 0 || aiLoading"
              @keydown.enter.ctrl.prevent="sendChat"
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

          <div class="ai-polish-section">
            <el-divider>文本润色</el-divider>
            <el-input
              v-model="polishInput"
              type="textarea"
              :rows="3"
              placeholder="粘贴简历片段，AI 将优化表达。"
              :disabled="aiRemaining <= 0 || polishLoading"
            />
            <el-button
              type="warning"
              icon="MagicStick"
              :loading="polishLoading"
              :disabled="!polishInput.trim() || aiRemaining <= 0"
              @click="doPolish"
              class="polish-btn"
            >
              一键润色
            </el-button>
            <div v-if="polishResult" class="polish-result">
              <h4>润色结果</h4>
              <div class="polish-text">{{ polishResult }}</div>
            </div>
          </div>

          <div v-if="aiRemaining <= 0" class="quota-exhausted">
            <el-alert
              type="warning"
              :closable="false"
              show-icon
              title="配额已用尽"
              description="AI 调用次数已达上限。"
            />
          </div>
        </aside>
      </div>

      <footer class="visitor-footer">
        <p>仅供展示，禁止转载 | 智能简历管理系统</p>
      </footer>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { visitorApi } from '@/api'

const route = useRoute()
const resume = ref(null)
const loading = ref(false)
const error = ref('')
const downloading = ref(false)

const aiRemaining = ref(0)
const aiTotal = ref(0)
const chatMessages = ref([])
const chatInput = ref('')
const aiLoading = ref(false)
const chatMessagesRef = ref(null)
const polishInput = ref('')
const polishResult = ref('')
const polishLoading = ref(false)

const textModules = [
  { key: 'certificate', label: '证书', icon: 'Stamp' },
  { key: 'award', label: '获奖荣誉', icon: 'Trophy' },
  { key: 'language', label: '语言能力', icon: 'ChatLineRound' },
]

const structuredSections = computed(() => {
  const modules = resume.value?.modules || {}
  return [
    {
      key: 'education',
      label: '教育经历',
      icon: 'School',
      type: 'timeline',
      items: modules.education || [],
      titleText: (item) => item.school,
      subtitleText: (item) => [item.degree, item.major].filter(Boolean).join(' | '),
      subtitleClass: '',
      dateText: (item) => `${item.start_date || ''} ~ ${item.end_date || '至今'}`,
    },
    {
      key: 'work_experience',
      label: '工作经历',
      icon: 'OfficeBuilding',
      type: 'timeline',
      items: modules.work_experience || [],
      titleText: (item) => item.company,
      subtitleText: (item) => item.position,
      subtitleClass: 'highlight',
      dateText: (item) => `${item.start_date || ''} ~ ${item.end_date || '至今'}`,
    },
    {
      key: 'project',
      label: '项目经历',
      icon: 'FolderOpened',
      type: 'grid',
      items: modules.project || [],
    },
    {
      key: 'skill',
      label: '技能清单',
      icon: 'TrendCharts',
      type: 'skills',
      items: modules.skill || [],
    },
  ].filter((section) => section.items.length > 0)
})

const textSections = computed(() => {
  const modules = resume.value?.modules || {}
  return textModules
    .map((mod) => ({ ...mod, value: modules[mod.key] }))
    .filter((mod) => Boolean(mod.value))
})

const isAiMode = computed(() => route.query.role === 'ai' && resume.value?.visitor_ai_mode_enabled)

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
    const params = { sig: route.query.sig || '', expires: route.query.expires || 0, role: 'ai' }
    const res = await visitorApi.aiChat(token, params, { query, call_type: 'chat' })
    chatMessages.value.push({ role: 'assistant', text: res.response || '暂无回复' })
    aiRemaining.value = res.remaining ?? aiRemaining.value
  } catch (e) {
    if (e.response?.status === 429) {
      aiRemaining.value = 0
      chatMessages.value.push({ role: 'assistant', text: '配额已用尽，无法继续调用 AI 服务' })
    } else {
      chatMessages.value.push({ role: 'assistant', text: 'AI 服务调用失败，请稍后重试' })
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
    const params = { sig: route.query.sig || '', expires: route.query.expires || 0, role: 'ai' }
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
  if (!resume.value?.username) return
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
    a.download = `${resume.value.username}_resume.pdf`
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
    if (data.visitor_ai_mode_enabled) {
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

.ai-quota-banner {
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

.ai-quota-banner strong {
  font-size: 18px;
  color: #303133;
}

.visitor-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: #fff;
  padding: 56px 20px 48px;
  position: relative;
  overflow: hidden;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 2;
}

.header-shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.06;
  pointer-events: none;
}

.header-shape-1 {
  width: 300px;
  height: 300px;
  background: #409eff;
  top: -80px;
  right: -60px;
}

.header-shape-2 {
  width: 200px;
  height: 200px;
  background: #67c23a;
  bottom: -60px;
  left: 10%;
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
  max-width: 700px;
}

.resume-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.visitor-content,
.visitor-content-ai {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px 20px;
}

.visitor-content {
  max-width: 800px;
}

.visitor-content-ai {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.resume-modules {
  flex: 1;
  min-width: 0;
}

.ai-panel {
  width: 420px;
  min-width: 380px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08);
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
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid #ebeef5;
  background: linear-gradient(135deg, #f8fafc 0%, #f0f5ff 100%);
}

.ai-panel-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.ai-panel-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #409eff, #337ecc);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
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
  padding: 32px 20px;
  color: #909399;
}

.ai-empty-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #ecf5ff 0%, #e0edff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
}

.ai-empty-title {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.ai-hint {
  font-size: 12px;
  color: #c0c4cc;
  margin: 0;
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
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
}

.msg-avatar.user {
  background: linear-gradient(135deg, #409eff, #337ecc);
}

.msg-avatar.assistant {
  background: linear-gradient(135deg, #67c23a, #529b2e);
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
  background: linear-gradient(135deg, #409eff, #337ecc);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-msg.assistant .msg-text {
  background: #f4f4f5;
  color: #303133;
  border-bottom-left-radius: 4px;
}

.typing-dots {
  display: flex;
  gap: 5px;
  padding: 4px 0;
}

.typing-dots span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #a0a3b1;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

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

.polish-btn {
  margin-top: 8px;
  width: 100%;
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

.module-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
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

.timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
  position: relative;
  padding-left: 20px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 5px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: linear-gradient(180deg, #409eff 0%, #d9ecff 100%);
  border-radius: 1px;
}

.timeline-item {
  display: flex;
  gap: 20px;
  padding: 16px 0;
  position: relative;
}

.timeline-dot {
  position: absolute;
  left: -20px;
  top: 22px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #409eff;
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px #409eff;
  z-index: 1;
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

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.project-card {
  border: 1px solid #ebeef5;
  border-radius: 10px;
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

.text-content {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #606266;
  font-size: 14px;
}

.download-section {
  text-align: center;
}

.visitor-footer {
  text-align: center;
  padding: 20px;
  color: #c0c4cc;
  font-size: 12px;
  border-top: 1px solid #ebeef5;
  background: #fff;
}

.skeleton-wrapper {
  max-width: 800px;
  margin: 0 auto;
  padding: 48px 20px;
}

.skeleton-header {
  padding: 40px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 16px;
  margin-bottom: 32px;
}

.skeleton-line {
  border-radius: 6px;
  background: linear-gradient(90deg, #e0e0e0 25%, #f0f0f0 50%, #e0e0e0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-title {
  height: 32px;
  width: 60%;
  margin-bottom: 12px;
}

.skeleton-subtitle {
  height: 16px;
  width: 40%;
  margin-bottom: 16px;
  opacity: 0.5;
}

.skeleton-text {
  height: 14px;
  width: 80%;
  opacity: 0.3;
}

.skeleton-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.skeleton-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.skeleton-card-title {
  height: 20px;
  width: 40%;
  margin-bottom: 16px;
}

.skeleton-card-text {
  height: 14px;
  width: 90%;
  margin-bottom: 10px;
}

.skeleton-card-text.short {
  width: 60%;
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

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

@media (max-width: 1024px) {
  .visitor-content-ai {
    flex-direction: column;
  }

  .ai-panel {
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
