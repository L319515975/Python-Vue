<template>
  <el-dialog
    v-model="visible"
    title="AI 润色结果"
    width="700px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-loading="loading" class="polish-dialog">
      <template v-if="!loading && polishedText">
        <el-alert
          type="success"
          :closable="false"
          show-icon
          style="margin-bottom: 16px"
        >
          <template #title>
            润色完成 <span v-if="tokensUsed > 0">（消耗 {{ tokensUsed }} tokens）</span>
          </template>
        </el-alert>

        <el-row :gutter="16">
          <el-col :span="12">
            <h4 class="diff-title">原始文本</h4>
            <div class="diff-box original">{{ originalText }}</div>
          </el-col>
          <el-col :span="12">
            <h4 class="diff-title polished">润色后文本</h4>
            <div class="diff-box polished-text" v-html="highlightDiff(originalText, polishedText)"></div>
          </el-col>
        </el-row>
      </template>

      <template v-if="!loading && error">
        <el-alert type="error" :closable="false" show-icon>
          <template #title>{{ error }}</template>
        </el-alert>
      </template>
    </div>

    <template #footer>
      <el-button @click="handleReject" :disabled="loading">取消</el-button>
      <el-button type="primary" @click="handleAccept" :disabled="loading || !polishedText">
        采纳润色结果
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { aiApi } from '@/api'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  text: { type: String, default: '' },
  moduleName: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'accept', 'reject'])

const visible = ref(false)
const loading = ref(false)
const originalText = ref('')
const polishedText = ref('')
const tokensUsed = ref(0)
const error = ref('')

watch(() => props.modelValue, async (val) => {
  visible.value = val
  if (val && props.text) {
    await doPolish()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

async function doPolish() {
  loading.value = true
  error.value = ''
  polishedText.value = ''
  originalText.value = props.text

  try {
    const result = await aiApi.polish(props.text, props.moduleName)
    if (result.status === 'success') {
      polishedText.value = result.polished_text
      tokensUsed.value = result.tokens_used || 0
    } else {
      error.value = result.error || '润色失败，请稍后重试'
    }
  } catch (e) {
    error.value = '请求失败，请检查网络连接或AI服务配置'
  } finally {
    loading.value = false
  }
}

function highlightDiff(original, polished) {
  if (!polished) return ''
  // Simple word-level diff: highlight added/changed parts
  const origWords = original.split(/(\s+)/)
  const polishWords = polished.split(/(\s+)/)

  // Use a simple approach: just show polished text with highlights
  // For a more sophisticated diff, we could use a diff library
  const result = polished
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Highlight parts that differ from original
  const origSet = new Set(origWords.filter(w => w.trim()))
  const parts = result.split(/(\s+)/)
  return parts.map(part => {
    if (!part.trim()) return part
    if (!origSet.has(part.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>'))) {
      return `<span class="diff-highlight">${part}</span>`
    }
    return part
  }).join('')
}

function handleAccept() {
  emit('accept', polishedText.value)
  visible.value = false
}

function handleReject() {
  emit('reject')
  visible.value = false
}

function handleClose() {
  emit('reject')
}
</script>

<style scoped>
.polish-dialog {
  min-height: 200px;
}

.diff-title {
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.diff-title.polished {
  color: #67c23a;
}

.diff-box {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px;
  min-height: 150px;
  max-height: 300px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.diff-box.original {
  background: #fafafa;
  color: #666;
}

.diff-box.polished-text {
  background: #f0f9eb;
  color: #333;
}

:deep(.diff-highlight) {
  background: #fdf6ec;
  color: #e6a23c;
  padding: 1px 3px;
  border-radius: 2px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .el-dialog {
    width: 95% !important;
    margin: 10px auto !important;
  }
  .el-row {
    flex-direction: column;
  }
  .el-col {
    width: 100% !important;
    max-width: 100% !important;
    margin-bottom: 12px;
  }
  .diff-box {
    min-height: 80px;
    max-height: 200px;
  }
}
</style>
