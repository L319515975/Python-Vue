<!-- ============================================================
  文件：VisitorPage.vue
  作用：访客简历展示页面
  说明：
    - 当用户通过"访客链接"访问简历时，会打开这个页面
    - 根据 URL 参数决定是否为 AI 模式（role=ai）
    - AI 模式下会显示右侧 AI 助手面板，支持对话问答和文本润色
    - 普通访客模式只展示简历内容
  关键 Vue 3 知识点：
    - ref()：创建响应式变量，值变化时页面自动更新
    - computed()：计算属性，依赖的数据变化时自动重新计算
    - onMounted()：组件挂载到页面后执行的生命周期钩子
    - nextTick()：等待 DOM 更新完成后再执行代码
    - useRoute()：获取当前路由信息（URL参数、查询参数等）
    - v-loading：Element Plus 指令，给元素添加加载遮罩
    - v-if / v-else-if：条件渲染，根据条件决定是否渲染元素
    - v-for：列表渲染，遍历数组生成多个元素
    - v-model：双向绑定，输入框的值和变量保持同步
    - @click / @keydown.enter.ctrl：事件监听
============================================================ -->
<template>
  <!--
    最外层容器：
    - v-loading="loading" 表示当 loading 为 true 时显示加载遮罩
    - 访客打开链接时先看到加载动画，数据加载完成后展示简历
  -->
  <div class="visitor-page" v-loading="loading">
    <!-- ========== 有简历数据时显示主内容 ========== -->
    <template v-if="resume">
      <!--
        AI 配额横幅：只在 AI 模式下显示
        显示 AI 咨询剩余次数 / 总次数
      -->
      <div v-if="isAiMode" class="ai-quota-banner">
        <el-icon><ChatDotRound /></el-icon>
        <span>AI咨询剩余 <strong>{{ aiRemaining }}</strong> / {{ aiTotal }} 次</span>
        <el-tag v-if="aiRemaining <= 0" type="danger" size="small">配额已用尽</el-tag>
      </div>
      <!--
        页面顶部头部区域：
        - 深色渐变背景 + 装饰性浮动圆形
        - 显示简历标题、所属用户、个人简介、标签
      -->
      <div class="visitor-header">
        <div class="header-content">
          <h1 class="resume-title">{{ resume.title }}</h1>
          <p class="resume-owner">{{ resume.username }} 的个人简历</p>
          <p v-if="resume.summary" class="resume-summary">{{ resume.summary }}</p>
          <!-- 标签列表：遍历 resume.tags 数组，每个标签用不同颜色区分类型 -->
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
        <!-- 装饰性浮动圆形，纯视觉效果 -->
        <div class="header-shape header-shape-1"></div>
        <div class="header-shape header-shape-2"></div>
      </div>
      <!--
        主内容区域：
        - AI 模式用双列布局（visitor-content-ai）
        - 普通模式用单列居中布局（visitor-content）
      -->
      <div :class="isAiMode ? 'visitor-content-ai' : 'visitor-content'">
        <!-- ========== 左侧：简历模块展示区 ========== -->
        <div class="resume-modules">
          <!-- 教育经历模块：用时间线样式展示 -->
          <section v-if="resume.modules?.education?.length" class="module-section">
            <h2 class="section-title">
              <el-icon><School /></el-icon>
              教育经历
            </h2>
            <div class="timeline">
              <div v-for="(edu, i) in resume.modules.education" :key="i" class="timeline-item">
                <div class="timeline-dot"></div>
                <div class="timeline-date">{{ edu.start_date }} ~ {{ edu.end_date || '至今' }}</div>
                <div class="timeline-content">
                  <h3>{{ edu.school }}</h3>
                  <p class="sub-info">{{ edu.degree }} | {{ edu.major }}</p>
                  <p v-if="edu.description" class="desc">{{ edu.description }}</p>
                </div>
              </div>
            </div>
          </section>
          <!-- 工作经历模块：同样用时间线样式，职位名高亮 -->
          <section v-if="resume.modules?.work_experience?.length" class="module-section">
            <h2 class="section-title">
              <el-icon><OfficeBuilding /></el-icon>
              工作经历
            </h2>
            <div class="timeline">
              <div v-for="(work, i) in resume.modules.work_experience" :key="i" class="timeline-item">
                <div class="timeline-dot"></div>
                <div class="timeline-date">{{ work.start_date }} ~ {{ work.end_date || '至今' }}</div>
                <div class="timeline-content">
                  <h3>{{ work.company }}</h3>
                  <p class="sub-info highlight">{{ work.position }}</p>
                  <p v-if="work.description" class="desc">{{ work.description }}</p>
                </div>
              </div>
            </div>
          </section>
          <!-- 项目经历模块：用卡片网格布局 -->
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
          <!-- 技能清单模块：用进度条可视化展示技能熟练度 -->
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
          <!--
            纯文本模块（证书、获奖荣誉、语言能力）：
            textModules 数组定义模块的 key、标题、图标
            动态渲染 component :is="mod.icon" 显示对应图标
          -->
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
          <!-- 下载区域：只有简历设置了"允许下载"时才显示 -->
          <section v-if="resume.visitor_allow_download" class="module-section download-section">
            <el-button type="primary" icon="Download" @click="downloadPdf" :loading="downloading">
              下载PDF简历
            </el-button>
          </section>
        </div>
        <!-- ========== 右侧：AI 面板（仅 AI 模式显示） ========== -->
        <div v-if="isAiMode" class="ai-panel">
          <!-- AI 面板头部：显示状态和配额信息 -->
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
          <!--
            聊天消息区域：
            - 根据 msg.role 决定消息样式（user=蓝色靠右, assistant=灰色靠左）
            - aiLoading 时显示"正在输入"跳动圆点动画
          -->
          <div class="ai-chat-messages" ref="chatMessagesRef">
            <div v-if="chatMessages.length === 0" class="ai-empty">
              <div class="ai-empty-icon">
                <el-icon :size="36" color="#409eff"><ChatDotRound /></el-icon>
              </div>
              <p class="ai-empty-title">向AI助手提问关于该候选人的问题</p>
              <p class="ai-hint">例如："该候选人适合哪些岗位？" "技能优势是什么？"</p>
            </div>
            <div v-for="(msg, i) in chatMessages" :key="i" :class="['chat-msg', msg.role]">
              <div class="msg-avatar" :class="msg.role">
                <el-icon v-if="msg.role === 'user'"><User /></el-icon>
                <el-icon v-else><Monitor /></el-icon>
              </div>
              <div class="msg-content">
                <div class="msg-text" v-html="msg.text"></div>
              </div>
            </div>
            <!-- 正在输入的加载动画（三个跳动的圆点） -->
            <div v-if="aiLoading" class="chat-msg assistant">
              <div class="msg-avatar assistant"><el-icon><Monitor /></el-icon></div>
              <div class="msg-content">
                <div class="msg-text typing">
                  <div class="typing-dots"><span></span><span></span><span></span></div>
                </div>
              </div>
            </div>
          </div>
          <!-- 输入区域：Ctrl+Enter 发送消息 -->
          <div class="ai-input-area">
            <el-input
              v-model="chatInput"
              type="textarea"
              :rows="2"
              placeholder="输入您的问题，如：该候选人适合哪些岗位？"
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
          <!-- 文本润色区域：访客可粘贴简历片段，AI 优化表达 -->
          <div class="ai-polish-section">
            <el-divider>文本润色</el-divider>
            <el-input
              v-model="polishInput"
              type="textarea"
              :rows="3"
              placeholder="粘贴简历片段，AI将优化表达.."
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
            <!-- 润色结果展示 -->
            <div v-if="polishResult" class="polish-result">
              <h4>润色结果：</h4>
              <div class="polish-text">{{ polishResult }}</div>
            </div>
          </div>
          <!-- 配额用尽提示 -->
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
      <!-- 页脚水印信息 -->
      <div class="visitor-footer">
        <p>仅供展示，禁止转载 | 智能简历管理系统</p>
      </div>
    </template>
    <!-- ========== 加载骨架屏：数据加载中时显示占位动画 ========== -->
    <template v-else-if="loading">
      <div class="skeleton-wrapper">
        <div class="skeleton-header">
          <div class="skeleton-line skeleton-title"></div>
          <div class="skeleton-line skeleton-subtitle"></div>
          <div class="skeleton-line skeleton-text"></div>
        </div>
        <div class="skeleton-body">
          <div class="skeleton-card" v-for="i in 3" :key="i">
            <div class="skeleton-line skeleton-card-title"></div>
            <div class="skeleton-line skeleton-card-text"></div>
            <div class="skeleton-line skeleton-card-text short"></div>
          </div>
        </div>
      </div>
    </template>
    <!-- ========== 错误状态：链接无效或访问被拒绝时显示 ========== -->
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
// ==================== 导入依赖 ====================
// ref：创建响应式变量（值变化时页面自动更新）
// computed：创建计算属性（依赖变化时自动重新计算）
// onMounted：组件挂载到 DOM 后执行的钩子函数
// nextTick：等待下一次 DOM 更新完成后执行回调
import { ref, computed, onMounted, nextTick } from 'vue'
// useRoute：获取当前路由对象（包含 URL 参数、查询参数等）
import { useRoute } from 'vue-router'
// visitorApi：访客相关的 API 请求函数（定义在 @/api/index.js 中）
import { visitorApi } from '@/api'
// ElMessage：Element Plus 的消息提示组件
import { ElMessage } from 'element-plus'

// ==================== 路由和基础状态 ====================
// 获取当前路由对象，用于读取 URL 中的 token 和查询参数
const route = useRoute()
// 简历数据（加载成功后赋值，页面会自动渲染）
const resume = ref(null)
// 整体加载状态（为 true 时显示加载遮罩）
const loading = ref(false)
// 错误信息（加载失败时显示对应的错误提示）
const error = ref('')
// PDF 下载中的加载状态
const downloading = ref(false)

// ==================== AI 模式相关 ====================
// isAiMode 计算属性：URL 参数 role=ai 且简历启用AI功能时为 true
const isAiMode = computed(() => route.query.role === 'ai' && resume.value?.visitor_ai_mode_enabled)
// AI 剩余调用次数
const aiRemaining = ref(0)
// AI 总配额次数
const aiTotal = ref(0)

// ==================== 聊天功能相关 ====================
// 聊天消息列表，每条消息：{ role: 'user'|'assistant', text: '...' }
const chatMessages = ref([])
// 用户当前输入的文本
const chatInput = ref('')
// AI 是否正在回复（控制加载动画）
const aiLoading = ref(false)
// 聊天消息容器的 DOM 引用（用于自动滚动到底部）
const chatMessagesRef = ref(null)

// ==================== 润色功能相关 ====================
// 润色输入框的文本
const polishInput = ref('')
// 润色结果文本
const polishResult = ref('')
// 润色请求是否正在加载
const polishLoading = ref(false)

// ==================== 静态配置数据 ====================
// 纯文本模块配置：key=数据键名, label=显示标题, icon=图标组件名
const textModules = [
  { key: 'certificate', label: '证书', icon: 'Stamp' },
  { key: 'award', label: '获奖荣誉', icon: 'Trophy' },
  { key: 'language', label: '语言能力', icon: 'ChatLineRound' },
]

// ==================== 工具函数 ====================

/**
 * 根据标签类型返回 Element Plus 标签颜色类型
 * @param {string} type - 标签类型（skill/project/certificate/award/language）
 * @returns {string} Element Plus 的 type 属性值
 */
function tagTypeColor(type) {
  const colors = { skill: '', project: 'success', certificate: 'warning', award: 'danger', language: 'info' }
  return colors[type] || ''
}

/**
 * 根据技能熟练度返回进度条颜色
 * >= 80: 绿色(熟练), >= 60: 蓝色(良好), >= 40: 橙色(一般), < 40: 红色(入门)
 */
function getSkillColor(level) {
  if (level >= 80) return '#67c23a'
  if (level >= 60) return '#409eff'
  if (level >= 40) return '#e6a23c'
  return '#f56c6c'
}

/**
 * 将聊天消息容器滚动到底部
 * nextTick 确保 DOM 更新后再滚动，这样新消息才会被滚到可见区域
 */
function scrollToBottom() {
  nextTick(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  })
}

// ==================== 核心业务函数 ====================

/**
 * 发送聊天消息给 AI 助手
 * 流程：验证输入 -> 添加用户消息到列表 -> 调用API -> 添加AI回复 -> 更新配额
 */
async function sendChat() {
  // 前置校验：输入为空或配额不足时直接返回
  if (!chatInput.value.trim() || aiRemaining.value <= 0) return
  const query = chatInput.value.trim()
  chatMessages.value.push({ role: 'user', text: query })
  chatInput.value = ''
  aiLoading.value = true
  scrollToBottom()

  try {
    // 从 URL 获取访客 token 和签名参数
    const token = route.params.token
    const params = { sig: route.query.sig || '', expires: route.query.expires || 0, role: 'ai' }
    // call_type='chat' 表示对话模式
    const res = await visitorApi.aiChat(token, params, { query, call_type: 'chat' })
    chatMessages.value.push({ role: 'assistant', text: res.response || '无回复' })
    // 更新剩余配额（服务端返回的 remaining 可能已减少）
    aiRemaining.value = res.remaining ?? aiRemaining.value
  } catch (e) {
    // HTTP 429 = Too Many Requests，表示配额用尽
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

/**
 * 执行文本润色
 * 流程：验证输入 -> 调用API(call_type='polish') -> 显示润色结果 -> 更新配额
 */
async function doPolish() {
  if (!polishInput.value.trim() || aiRemaining.value <= 0) return
  polishLoading.value = true
  polishResult.value = ''

  try {
    const token = route.params.token
    const params = { sig: route.query.sig || '', expires: route.query.expires || 0, role: 'ai' }
    const res = await visitorApi.aiChat(token, params, { query: polishInput.value.trim(), call_type: 'polish' })
    // 优先使用 polished_text，如果没有则使用 response
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

/**
 * 下载 PDF 简历
 * 流程：调用API获取Blob -> 创建临时URL -> 创建<a>标签模拟点击下载 -> 释放URL
 * Blob = Binary Large Object（二进制大对象，用于存储文件数据）
 */
async function downloadPdf() {
  downloading.value = true
  try {
    const token = route.params.token
    const role = route.query.role || 'visitor'
    const sig = route.query.sig || ''
    const expires = route.query.expires || 0
    const blob = await visitorApi.downloadPdf(token, { sig, expires, role })
    // 将 Blob 数据转为临时 URL
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = resume.value.username + '_resume.pdf'
    a.click()
    // 释放临时 URL，避免内存泄漏
    window.URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch {
    ElMessage.error('下载失败')
  } finally {
    downloading.value = false
  }
}

// ==================== 生命周期钩子 ====================

/**
 * onMounted：组件挂载到页面后自动执行（"页面打开时自动运行"）
 * 流程：读取URL参数 -> 请求简历数据 -> 初始化AI配额 -> 处理错误
 */
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
    // 如果启用了 AI 功能，初始化 AI 配额
    if (data.visitor_ai_mode_enabled) {
      aiRemaining.value = data.ai_remaining || 0
      aiTotal.value = data.ai_quota || 0
    }
  } catch (e) {
    // 根据 HTTP 错误码显示不同提示
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

/* AI Quota Banner */
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

/* Header with decorative shapes */
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
  animation: float-shape 8s ease-in-out infinite;
}

.header-shape-2 {
  width: 200px;
  height: 200px;
  background: #67c23a;
  bottom: -60px;
  left: 10%;
  animation: float-shape 10s ease-in-out infinite reverse;
}

@keyframes float-shape {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(20px, -15px); }
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

/* Standard visitor layout */
.visitor-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 20px;
}

/* AI 2-column layout */
.visitor-content-ai {
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

/* AI Panel */
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

.ai-chat-messages::-webkit-scrollbar {
  width: 4px;
}

.ai-chat-messages::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 2px;
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

/* Typing indicator */
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

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
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

/* Module sections */
.module-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.25s ease, transform 0.25s ease;
}

.module-section:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
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

/* Timeline with connector line */
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

/* Project grid */
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.project-card {
  border: 1px solid #ebeef5;
  border-radius: 10px;
  padding: 16px;
  transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease;
}

.project-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
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

/* Loading skeleton */
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

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
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
