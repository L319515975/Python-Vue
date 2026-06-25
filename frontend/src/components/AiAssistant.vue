<template>
  <div class="ai-assistant-float" v-if="userStore.isLoggedIn">
    <!-- Floating Button -->
    <div class="float-btn" :class="{ 'has-unread': hasUnread }" @click="toggleChat">
      <el-icon :size="24"><ChatDotRound /></el-icon>
    </div>

    <!-- Chat Dialog -->
    <transition name="slide-up">
      <div v-if="visible" class="chat-dialog" :class="{ 'is-mobile': isMobile }">
        <!-- Header -->
        <div class="chat-dialog-header">
          <div class="header-info">
            <el-icon :size="18" color="#409eff"><ChatDotRound /></el-icon>
            <span>AI简历助手</span>
            <el-tag size="small" type="info">基于您的简历数据</el-tag>
          </div>
          <div class="header-actions">
            <el-tooltip content="文本润色" placement="top">
              <el-button text size="small" icon="MagicStick" @click="openPolishMode" />
            </el-tooltip>
            <el-tooltip content="清空对话" placement="top">
              <el-button text size="small" icon="Delete" @click="clearChat" />
            </el-tooltip>
            <el-tooltip content="最小化" placement="top">
              <el-button text size="small" icon="Close" @click="visible = false" />
            </el-tooltip>
          </div>
        </div>

        <!-- Messages -->
        <div class="chat-messages" ref="messagesRef">
          <div v-if="!messages.length" class="welcome-area">
            <el-icon :size="40" color="#c0c4cc"><ChatDotRound /></el-icon>
            <p>你好！我是AI简历助手</p>
            <p class="welcome-sub">可以帮你查询简历信息或润色文本</p>
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

          <div
            v-for="(msg, i) in messages"
            :key="i"
            :class="['message', msg.role === 'user' ? 'message-user' : 'message-ai']"
          >
            <el-avatar v-if="msg.role === 'ai'" :size="28" icon="ChatDotRound" style="background: #409eff" />
            <div class="message-bubble">
              <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
              <div class="message-time">{{ msg.time }}</div>
            </div>
            <el-avatar v-if="msg.role === 'user'" :size="28" icon="User" />
          </div>

          <div v-if="loading" class="message message-ai">
            <el-avatar :size="28" icon="ChatDotRound" style="background: #409eff" />
            <div class="message-bubble">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="chat-input">
          <el-input
            v-model="inputText"
            placeholder="输入问题..."
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

    <!-- Polish Dialog -->
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

    <!-- Polish Result Dialog -->
    <PolishDialog
      v-model="showPolishResult"
      :text="polishOriginalText"
      @accept="handlePolishResult"
    />
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { aiApi } from '@/api'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'
import PolishDialog from '@/components/PolishDialog.vue'

const userStore = useUserStore()
const visible = ref(false)
const hasUnread = ref(false)
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const messagesRef = ref(null)

// Polish state
const polishDialogVisible = ref(false)
const polishText = ref('')
const polishLoading = ref(false)
const showPolishResult = ref(false)
const polishOriginalText = ref('')

const isMobile = computed(() => window.innerWidth <= 768)

const quickQueries = [
  '我的教育背景是什么？',
  '介绍一下我的工作经历',
  '我参与过哪些项目？',
  '我有哪些技能？',
  '给我一份简历概要',
]

function renderMarkdown(text) {
  try { return marked(text || '') } catch { return text }
}

function toggleChat() {
  visible.value = !visible.value
  if (visible.value) {
    hasUnread.value = false
    nextTick(scrollToBottom)
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function formatTime() {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

async function sendMessage(text) {
  const query = text || inputText.value.trim()
  if (!query || loading.value) return

  messages.value.push({ role: 'user', content: query, time: formatTime() })
  inputText.value = ''
  scrollToBottom()

  loading.value = true
  try {
    const data = await aiApi.chat(query)
    messages.value.push({
      role: 'ai',
      content: data.response,
      time: formatTime(),
      intent: data.intent,
    })
  } catch {
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

function clearChat() {
  messages.value = []
}

function openPolishMode() {
  polishText.value = ''
  polishDialogVisible.value = true
}

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
  bottom: 24px;
  right: 24px;
  z-index: 9999;
}

.float-btn {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff, #337ecc);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.4);
  transition: all 0.3s ease;
}

.float-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 24px rgba(64, 158, 255, 0.5);
}

.float-btn.has-unread::after {
  content: '';
  position: absolute;
  top: 2px;
  right: 2px;
  width: 12px;
  height: 12px;
  background: #f56c6c;
  border-radius: 50%;
  border: 2px solid #fff;
}

/* Chat Dialog */
.chat-dialog {
  position: absolute;
  bottom: 68px;
  right: 0;
  width: 400px;
  height: 560px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-dialog.is-mobile {
  position: fixed;
  bottom: 0;
  right: 0;
  left: 0;
  width: 100%;
  height: calc(100vh - 60px);
  border-radius: 12px 12px 0 0;
}

/* Header */
.chat-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 0;
}

/* Messages */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.welcome-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #999;
}

.welcome-area p {
  margin: 0;
  font-size: 14px;
}

.welcome-sub {
  font-size: 12px !important;
  color: #c0c4cc !important;
}

.quick-queries {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  margin-top: 8px;
}

.message {
  display: flex;
  gap: 8px;
  max-width: 85%;
}

.message-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-ai {
  align-self: flex-start;
}

.message-bubble {
  background: #f4f4f5;
  padding: 10px 14px;
  border-radius: 12px;
  max-width: 100%;
}

.message-user .message-bubble {
  background: #409eff;
  color: #fff;
}

.message-content {
  line-height: 1.5;
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

/* Typing indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #aaa;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Input */
.chat-input {
  padding: 12px 16px;
  border-top: 1px solid #eee;
  flex-shrink: 0;
}

/* Transition */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@media (max-width: 768px) {
  .ai-assistant-float {
    bottom: 16px;
    right: 16px;
  }

  .float-btn {
    width: 48px;
    height: 48px;
  }
}
</style>