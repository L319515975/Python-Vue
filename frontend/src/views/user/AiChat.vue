<template>
  <div class="ai-chat">
    <el-card class="chat-card">
      <template #header>
        <div class="chat-header">
          <div class="header-info">
            <el-icon :size="24" color="#409eff"><ChatDotRound /></el-icon>
            <span>AI简历助手</span>
            <el-tag size="small" type="info">基于您的简历数据</el-tag>
          </div>
          <div style="display: flex; gap: 8px">
            <el-button text icon="MagicStick" @click="openPolishMode">文本润色</el-button>
            <el-button text icon="Delete" @click="clearChat">清空对话</el-button>
          </div>
        </div>
      </template>

      <!-- Messages -->
      <div class="chat-messages" ref="messagesRef">
        <div v-if="!messages.length" class="welcome-area">
          <el-icon :size="48" color="#c0c4cc"><ChatDotRound /></el-icon>
          <p>你好！我是AI简历助手，可以帮你查询简历信息或润色文本。</p>
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
          <el-avatar v-if="msg.role === 'ai'" :size="36" icon="ChatDotRound" style="background: #409eff" />
          <div class="message-bubble">
            <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
          <el-avatar v-if="msg.role === 'user'" :size="36" icon="User" />
        </div>

        <div v-if="loading" class="message message-ai">
          <el-avatar :size="36" icon="ChatDotRound" style="background: #409eff" />
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
          placeholder="输入问题，例如：我的项目经历有哪些？"
          :disabled="loading"
          @keyup.enter="sendMessage()"
        >
          <template #append>
            <el-button :icon="loading ? 'Loading' : 'Promotion'" @click="sendMessage()" :loading="loading" />
          </template>
        </el-input>
      </div>
    </el-card>

    <!-- History sidebar -->
    <el-card class="history-card">
      <template #header>
        <span>查询历史</span>
      </template>
      <div v-if="history.length" class="history-list">
        <div
          v-for="item in history"
          :key="item.id"
          class="history-item"
          @click="loadFromHistory(item)"
        >
          <div class="history-query">{{ item.query }}</div>
          <div class="history-meta">
            <el-tag size="small">{{ intentMap[item.intent] || item.intent }}</el-tag>
            <span class="history-time">{{ item.created_at }}</span>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无查询历史" :image-size="60" />
    </el-card>

    <!-- Polish Dialog -->
    <el-dialog v-model="polishDialogVisible" title="文本润色" width="500px">
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
import { ref, nextTick, onMounted } from 'vue'
import { aiApi } from '@/api'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'
import PolishDialog from '@/components/PolishDialog.vue'

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const history = ref([])
const messagesRef = ref(null)

// Polish state
const polishDialogVisible = ref(false)
const polishText = ref('')
const polishLoading = ref(false)
const showPolishResult = ref(false)
const polishOriginalText = ref('')

const quickQueries = [
  '我的教育背景是什么？',
  '介绍一下我的工作经历',
  '我参与过哪些项目？',
  '我有哪些技能？',
  '给我一份简历概要',
]

const intentMap = {
  education: '教育背景',
  work_experience: '工作经历',
  project: '项目经历',
  skill: '技能列表',
  summary: '个人简介',
  general: '综合查询',
}

function renderMarkdown(text) {
  try {
    return marked(text || '')
  } catch {
    return text
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
    loadHistory()
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

function loadFromHistory(item) {
  sendMessage(item.query)
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

async function loadHistory() {
  try {
    const data = await aiApi.history({ limit: 20 })
    history.value = data || []
  } catch { /* */ }
}

onMounted(loadHistory)
</script>

<style scoped>
.ai-chat {
  display: flex;
  gap: 16px;
  height: calc(100vh - 140px);
}

.chat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #999;
}

.quick-queries {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
}

.message {
  display: flex;
  gap: 10px;
  max-width: 80%;
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
  padding: 12px 16px;
  border-radius: 12px;
  max-width: 100%;
}

.message-user .message-bubble {
  background: #409eff;
  color: #fff;
}

.message-content {
  line-height: 1.6;
  word-break: break-word;
}

.message-content :deep(p) {
  margin: 4px 0;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 20px;
}

.message-time {
  font-size: 11px;
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
  width: 8px;
  height: 8px;
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

.chat-input {
  padding: 16px;
  border-top: 1px solid #eee;
}

/* History sidebar */
.history-card {
  width: 300px;
  flex-shrink: 0;
}

.history-card :deep(.el-card__body) {
  overflow-y: auto;
  max-height: calc(100% - 50px);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.history-item:hover {
  border-color: #409eff;
}

.history-query {
  font-size: 13px;
  color: #333;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-time {
  font-size: 11px;
  color: #999;
}
</style>
