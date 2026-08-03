<!--
  AI 助手浮窗组件 AiAssistant.vue —— 固定在右下角的 AI 对话窗口。

  作用：让用户在任何页面都能与 AI 助手对话，查询简历信息或润色文本。

  功能：
  1. 浮动按钮：固定在右下角，点击展开对话窗口
  2. AI 对话：基于用户的简历数据回答问题
  3. 文本润色：优化简历中的文字表达
  4. 快捷问题：预设常见问题，一键发送
  5. 消息动画：消息出现时有淡入动画
  6. 打字指示器：AI 回答时显示"正在输入..."动画
  7. 未读提醒：有新消息时按钮显示红点

  知识点（Vue 3 动画）：
  - <transition>：Vue 内置组件，用于实现进入/离开动画
  - @keyframes：CSS 关键帧动画，定义动画的各个阶段
  - v-html：将字符串作为 HTML 渲染（用于渲染 Markdown）
-->
<template>
  <!-- 仅在用户登录后显示 -->
  <div class="ai-assistant-float" v-if="userStore.isLoggedIn">
    <!-- ========== 浮动按钮 ========== -->
    <el-tooltip content="AI简历助手" placement="left" :show-after="400">
      <div class="float-btn" :class="{ 'has-unread': hasUnread, 'is-open': visible }" @click="toggleChat">
        <!-- 脉冲光环：吸引用户注意力的动画效果 -->
        <div class="btn-ring"></div>
        <el-icon :size="26"><ChatDotRound /></el-icon>
      </div>
    </el-tooltip>

    <!-- ========== 对话窗口（带滑入动画） ========== -->
    <transition name="slide-up">
      <div v-if="visible" class="chat-dialog" :class="{ 'is-mobile': isMobile }">
        <!-- 对话窗口头部 -->
        <div class="chat-dialog-header">
          <div class="header-info">
            <div class="header-avatar">
              <el-icon :size="18"><ChatDotRound /></el-icon>
            </div>
            <div class="header-text">
              <span class="header-title">AI简历助手</span>
              <span class="header-subtitle">基于您的简历数据</span>
            </div>
          </div>
          <div class="header-actions">
            <el-tooltip content="文本润色" placement="top">
              <el-button text size="small" @click="openPolishMode">
                <el-icon><MagicStick /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="清空对话" placement="top">
              <el-button text size="small" @click="clearChat">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="最小化" placement="top">
              <el-button text size="small" @click="visible = false">
                <el-icon><Close /></el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </div>

        <!-- 消息列表区域 -->
        <div class="chat-messages" ref="messagesRef">
          <!-- 欢迎区域：没有消息时显示 -->
          <div v-if="!messages.length" class="welcome-area">
            <div class="welcome-icon">
              <el-icon :size="36" color="#409eff"><ChatDotRound /></el-icon>
            </div>
            <p class="welcome-title">你好！我是AI简历助手</p>
            <p class="welcome-sub">可以帮你查询简历信息或润色文本</p>
            <!-- 快捷问题按钮：点击直接发送预设问题 -->
            <div class="quick-queries">
              <el-button
                v-for="q in quickQueries"
                :key="q"
                size="small"
                round
                @click="sendMessage(q)"
              >
                {{ q }}
              </el-button>
            </div>
          </div>

          <!-- 消息列表：v-for 渲染每条消息 -->
          <div
            v-for="(msg, i) in messages"
            :key="i"
            :class="['message', msg.role === 'user' ? 'message-user' : 'message-ai']"
          >
            <!-- AI 头像（左侧） -->
            <el-avatar v-if="msg.role === 'ai'" :size="30" class="avatar-ai">
              <el-icon><ChatDotRound /></el-icon>
            </el-avatar>
            <!-- 消息气泡 -->
            <div class="message-bubble">
              <!-- v-html：将 Markdown 渲染为 HTML -->
              <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
              <div class="message-time">{{ msg.time }}</div>
            </div>
            <!-- 用户头像（右侧） -->
            <el-avatar v-if="msg.role === 'user'" :size="30" class="avatar-user">
              <el-icon><User /></el-icon>
            </el-avatar>
          </div>

          <!-- 打字指示器：AI 正在回答时显示三个跳动的点 -->
          <div v-if="loading" class="message message-ai">
            <el-avatar :size="30" class="avatar-ai">
              <el-icon><ChatDotRound /></el-icon>
            </el-avatar>
            <div class="message-bubble">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <el-input
            v-model="inputText"
            placeholder="输入问题... (Enter发送)"
            :disabled="loading"
            @keyup.enter="sendMessage()"
          >
            <template #append>
              <el-button :icon="loading ? 'Loading' : 'Promotion'" @click="sendMessage()" :loading="loading" />
            </template>
          </el-input>
        </div>
      </div>
    </transition>

    <!-- 文本润色输入弹窗 -->
    <el-dialog v-model="polishDialogVisible" title="文本润色" :width="isMobile ? '95%' : '500px'" append-to-body>
      <el-input
        v-model="polishText"
        type="textarea"
        :rows="5"
        placeholder="粘贴需要润色的简历文本..."
      />
      <template #footer>
        <el-button @click="polishDialogVisible = false">取消</el-button>
        <el-button type="warning" icon="MagicStick" :loading="polishLoading" @click="doPolish">
          润色
        </el-button>
      </template>
    </el-dialog>

    <!-- 润色结果弹窗 -->
    <PolishDialog
      v-model="showPolishResult"
      :text="polishOriginalText"
      @accept="handlePolishResult"
    />
  </div>
</template>

<script setup>
/**
 * AI 助手组件的逻辑部分。
 *
 * 核心功能：
 * 1. 对话管理：发送消息、接收回复、清空历史
 * 2. Markdown 渲染：将 AI 回答的 Markdown 格式转为 HTML
 * 3. 文本润色：调用 AI 润色接口优化文本
 * 4. 自动滚动：新消息出现时自动滚动到底部
 */
import { ref, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { useMobile } from '@/composables/useMobile'
import { aiApi } from '@/api'
import { marked } from 'marked'  // Markdown 解析库
import { ElMessage } from 'element-plus'
import PolishDialog from '@/components/PolishDialog.vue'

const userStore = useUserStore()
const { isMobile } = useMobile()

// ========== 响应式状态 ==========
const visible = ref(false)              // 对话窗口是否展开
const hasUnread = ref(false)            // 是否有未读消息
const messages = ref([])                // 消息列表（role: 'user'|'ai', content, time）
const inputText = ref('')               // 输入框文本
const loading = ref(false)              // AI 是否正在回答
const messagesRef = ref(null)           // 消息列表的 DOM 引用（用于滚动）

// 润色相关状态
const polishDialogVisible = ref(false)  // 润色输入弹窗是否显示
const polishText = ref('')              // 待润色文本
const polishLoading = ref(false)        // 润色是否进行中
const showPolishResult = ref(false)     // 润色结果弹窗是否显示
const polishOriginalText = ref('')      // 润色原文（传给 PolishDialog）

// 预设的快捷问题
const quickQueries = [
  '我的教育背景是什么？',
  '介绍一下我的工作经历',
  '我参与过哪些项目？',
  '我有哪些技能？',
  '给我一份简历概要',
]

/**
 * 将 Markdown 文本渲染为 HTML。
 * marked 库会将 Markdown 语法（如 **加粗**、- 列表）转为 HTML。
 */
function renderMarkdown(text) {
  try { return marked(text || '') } catch { return text }
}

/**
 * 切换对话窗口的显示/隐藏。
 * 打开时清除未读标记。
 */
function toggleChat() {
  visible.value = !visible.value
  if (visible.value) {
    hasUnread.value = false
    nextTick(scrollToBottom)
  }
}

/**
 * 自动滚动到消息列表底部。
 * nextTick 确保在 DOM 更新后再执行滚动。
 */
function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

/** 格式化当前时间为 HH:MM 格式。 */
function formatTime() {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

/**
 * 发送消息给 AI 助手。
 *
 * 流程：
 * 1. 将用户消息添加到消息列表
 * 2. 调用 AI API 获取回答
 * 3. 将 AI 回答添加到消息列表
 * 4. 自动滚动到底部
 */
async function sendMessage(text) {
  const query = text || inputText.value.trim()
  if (!query || loading.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: query, time: formatTime() })
  inputText.value = ''
  scrollToBottom()

  loading.value = true
  try {
    const data = await aiApi.chat(query)
    // 添加 AI 回答
    messages.value.push({
      role: 'ai',
      content: data.response,
      time: formatTime(),
      intent: data.intent,
    })
  } catch {
    // 请求失败时显示错误消息
    messages.value.push({
      role: 'ai',
      content: '抱歉，查询失败，请稍后重试。',
      time: formatTime(),
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

/** 清空所有对话记录。 */
function clearChat() {
  messages.value = []
}

/** 打开润色输入弹窗。 */
function openPolishMode() {
  polishText.value = ''
  polishDialogVisible.value = true
}

/** 执行文本润色。 */
async function doPolish() {
  if (!polishText.value.trim()) {
    ElMessage.warning('请输入需要润色的文本')
    return
  }
  polishLoading.value = true
  polishOriginalText.value = polishText.value
  polishDialogVisible.value = false
  showPolishResult.value = true
  polishLoading.value = false
}

/** 处理润色结果：将润色后的文本添加到对话中。 */
function handlePolishResult(polished) {
  messages.value.push({
    role: 'ai',
    content: `**润色结果：**\n\n${polished}`,
    time: formatTime(),
  })
  scrollToBottom()
  ElMessage.success('润色结果已添加到对话中')
}
</script>

<style scoped>
.ai-assistant-float {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 9999;
}

/* ========== 浮动按钮样式 ========== */
.float-btn {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 40%, #337ecc 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow:
    0 4px 20px rgba(64, 158, 255, 0.45),
    0 0 40px rgba(64, 158, 255, 0.15);
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  backdrop-filter: blur(4px);
}

.float-btn:hover {
  transform: scale(1.15) translateY(-2px);
  box-shadow:
    0 8px 32px rgba(64, 158, 255, 0.55),
    0 0 60px rgba(64, 158, 255, 0.25);
}

.float-btn:active {
  transform: scale(1.05);
  transition-duration: 0.15s;
}

/* 按钮展开时的样式 */
.float-btn.is-open {
  background: linear-gradient(135deg, #337ecc 0%, #2a6cb8 100%);
  box-shadow:
    0 4px 16px rgba(51, 126, 204, 0.4),
    0 0 30px rgba(51, 126, 204, 0.15);
  transform: scale(0.95);
}

/* ========== 脉冲光环动画 ========== */
.btn-ring {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 2px solid rgba(64, 158, 255, 0.3);
  animation: pulse-ring 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  pointer-events: none;
}

.btn-ring::before {
  content: '';
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  border: 1px solid rgba(64, 158, 255, 0.15);
  animation: pulse-ring 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  animation-delay: 0.4s;
}

.float-btn.is-open .btn-ring,
.float-btn:hover .btn-ring {
  animation: none;
  opacity: 0;
}

@keyframes pulse-ring {
  0% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.4); opacity: 0; }
  100% { transform: scale(1.4); opacity: 0; }
}

/* ========== 未读消息红点 ========== */
.float-btn.has-unread::after {
  content: '';
  position: absolute;
  top: 2px;
  right: 2px;
  width: 14px;
  height: 14px;
  background: linear-gradient(135deg, #f56c6c, #e74c3c);
  border-radius: 50%;
  border: 2.5px solid #fff;
  box-shadow: 0 2px 8px rgba(245, 108, 108, 0.5);
  animation: badge-pulse 2s ease-in-out infinite;
}

/* 呼吸发光动画 */
@keyframes breathe-glow {
  0%, 100% {
    box-shadow:
      0 4px 20px rgba(64, 158, 255, 0.45),
      0 0 40px rgba(64, 158, 255, 0.15);
  }
  50% {
    box-shadow:
      0 4px 28px rgba(64, 158, 255, 0.6),
      0 0 56px rgba(64, 158, 255, 0.25);
  }
}

.float-btn.is-open,
.float-btn:hover {
  animation: none;
}

/* 消息进入动画 */
@keyframes msg-enter {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.message {
  animation: msg-enter 0.3s ease-out;
}

/* 未读红点脉冲动画 */
@keyframes badge-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

/* ========== 对话窗口样式 ========== */
.chat-dialog {
  position: absolute;
  bottom: 72px;
  right: 0;
  width: 400px;
  height: 560px;
  background: #fff;
  border-radius: 20px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.12),
    0 8px 24px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  backdrop-filter: blur(20px);
}

/* 移动端：对话窗口占满屏幕 */
.chat-dialog.is-mobile {
  position: fixed;
  bottom: 0;
  right: 0;
  left: 0;
  width: 100%;
  height: calc(100vh - 60px);
  border-radius: 16px 16px 0 0;
}

/* 对话窗口头部 */
.chat-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 18px;
  background: linear-gradient(135deg, #f0f5ff 0%, #e8f0fe 50%, #f0f5ff 100%);
  border-bottom: 1px solid #e4e8ee;
  flex-shrink: 0;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-avatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, #409eff, #337ecc);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.header-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  line-height: 1.3;
}

.header-subtitle {
  font-size: 11px;
  color: #7a7a7a;
  line-height: 1.3;
}

.header-actions {
  display: flex;
  gap: 0;
}

/* ========== 消息列表 ========== */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.chat-messages::-webkit-scrollbar {
  width: 4px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 2px;
}

/* 欢迎区域 */
.welcome-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #999;
}

.welcome-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #ecf5ff 0%, #e0edff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.welcome-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.welcome-sub {
  margin: 0;
  font-size: 12px;
  color: #c0c4cc;
}

.quick-queries {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  margin-top: 12px;
}

/* 消息样式 */
.message {
  display: flex;
  gap: 10px;
  max-width: 85%;
}

.message-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-ai {
  align-self: flex-start;
}

.avatar-ai {
  background: linear-gradient(135deg, #409eff, #337ecc);
}

.avatar-user {
  background: linear-gradient(135deg, #67c23a, #529b2e);
}

.message-bubble {
  background: #f4f4f5;
  padding: 10px 14px;
  border-radius: 14px;
  max-width: 100%;
}

.message-user .message-bubble {
  background: linear-gradient(135deg, #409eff, #337ecc);
  color: #fff;
}

.message-content {
  line-height: 1.6;
  word-break: break-word;
  font-size: 13px;
}

.message-content :deep(p) {
  margin: 2px 0;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 18px;
}

.message-time {
  font-size: 10px;
  color: #aaa;
  margin-top: 4px;
  text-align: right;
}

.message-user .message-time {
  color: #ffffffaa;
}

/* 打字指示器动画：三个跳动的点 */
.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #a0a3b1;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 输入区域 */
.chat-input {
  padding: 12px 16px;
  border-top: 1px solid #eee;
  flex-shrink: 0;
  background: #fafbfc;
}

/* 对话窗口进入/离开动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.97);
}

@media (max-width: 768px) {
  .ai-assistant-float {
    bottom: 20px;
    right: 16px;
  }

  .float-btn {
    width: 52px;
    height: 52px;
  }

  .chat-dialog {
    width: calc(100vw - 32px);
    right: -12px;
    border-radius: 18px;
  }
}
</style>