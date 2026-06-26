<!--
  润色结果弹窗 PolishDialog.vue —— 展示 AI 润色前后的对比。

  作用：让用户看到原始文本和润色后文本的对比，决定是否采纳润色结果。

  功能：
  1. 左右对比：原始文本 vs 润色后文本
  2. 差异高亮：标记润色后新增/修改的部分
  3. 采纳/取消：用户可以选择采纳或拒绝润色结果

  知识点（Vue 3 组件通信）：
  - defineProps()：定义组件接收的属性（父组件传数据给子组件）
  - defineEmits()：定义组件可触发的事件（子组件传数据给父组件）
  - v-model：双向绑定语法糖（等价于 :modelValue + @update:modelValue）
  - watch()：监听属性变化，执行副作用（如属性变化时触发 AI 润色）
-->
<template>
  <el-dialog
    v-model="visible"
    title="AI 润色结果"
    width="700px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-loading="loading" class="polish-dialog">
      <!-- 润色完成状态 -->
      <template v-if="!loading && polishedText">
        <el-alert
          type="success"
          :closable="false"
          show-icon
          class="polish-alert"
        >
          <template #title>
            润色完成 <span v-if="tokensUsed > 0">（消耗 {{ tokensUsed }} tokens）</span>
          </template>
        </el-alert>

        <!-- 左右对比：原始文本 | 润色后文本 -->
        <el-row :gutter="16">
          <el-col :span="12">
            <h4 class="diff-title">原始文本</h4>
            <div class="diff-box original">{{ originalText }}</div>
          </el-col>
          <el-col :span="12">
            <h4 class="diff-title polished">润色后文本</h4>
            <!-- v-html：渲染带高亮标记的 HTML -->
            <div class="diff-box polished-text" v-html="highlightDiff(originalText, polishedText)"></div>
          </el-col>
        </el-row>
      </template>

      <!-- 错误状态 -->
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
/**
 * 润色结果弹窗的逻辑部分。
 *
 * 工作流程：
 * 1. 父组件通过 v-model 控制弹窗显示
 * 2. 弹窗打开时自动调用 AI 润色接口
 * 3. 展示原始文本和润色后的对比
 * 4. 用户点击"采纳"或"取消"，通过事件通知父组件
 */
import { ref, watch } from 'vue'
import { useMobile } from '@/composables/useMobile'
import { aiApi } from '@/api'
import { ElMessage } from 'element-plus'

const { isMobile } = useMobile()

// ========== 组件属性（父组件传入） ==========
const props = defineProps({
  modelValue: { type: Boolean, default: false },    // 弹窗是否显示（v-model 双向绑定）
  text: { type: String, default: '' },               // 需要润色的原始文本
  moduleName: { type: String, default: '' },         // 所属模块名（可选）
})

// ========== 组件事件（通知父组件） ==========
const emit = defineEmits([
  'update:modelValue',  // 更新 modelValue（v-model 双向绑定所需）
  'accept',             // 用户采纳润色结果
  'reject',             // 用户取消润色
])

// 响应式状态
const visible = ref(false)         // 弹窗实际可见状态
const loading = ref(false)         // 是否正在润色
const originalText = ref('')       // 原始文本
const polishedText = ref('')       // 润色后的文本
const tokensUsed = ref(0)          // 消耗的 token 数
const error = ref('')              // 错误信息

/**
 * 监听 modelValue 变化。
 * 当父组件打开弹窗时（modelValue → true），自动开始润色。
 *
 * 知识点：watch() 用于监听响应式数据的变化并执行副作用。
 */
watch(() => props.modelValue, async (val) => {
  visible.value = val
  if (val && props.text) {
    await doPolish()
  }
})

/**
 * 监听 visible 变化，同步回父组件。
 * 这样用户点击弹窗右上角的 X 关闭时，也能通知父组件。
 */
watch(visible, (val) => {
  emit('update:modelValue', val)
})

/**
 * 执行 AI 润色。
 * 调用 AI API 获取润色结果。
 */
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

/**
 * 差异高亮函数 —— 标记润色后新增/修改的词汇。
 *
 * 简单实现：
 * 1. 将原始文本按空格分词，放入集合
 * 2. 遍历润色后文本的每个词
 * 3. 如果词不在原始文本集合中，用高亮标记
 *
 * 注意：这是一种简化的差异比较，不是精确的 diff 算法。
 */
function highlightDiff(original, polished) {
  if (!polished) return ''
  // 将原始文本按空格分词
  const origWords = original.split(/(\s+)/)

  // HTML 转义（防止 XSS）
  const result = polished
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 将原始文本的词汇放入 Set（快速查找）
  const origSet = new Set(origWords.filter(w => w.trim()))
  const parts = result.split(/(\s+)/)
  return parts.map(part => {
    if (!part.trim()) return part
    // 如果润色后的词不在原始文本中，标记为高亮
    if (!origSet.has(part.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>'))) {
      return `<span class="diff-highlight">${part}</span>`
    }
    return part
  }).join('')
}

/** 用户点击"采纳"按钮。 */
function handleAccept() {
  emit('accept', polishedText.value)
  visible.value = false
}

/** 用户点击"取消"按钮。 */
function handleReject() {
  emit('reject')
  visible.value = false
}

/** 弹窗关闭时触发。 */
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

/* 文本对比框 */
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

/* 差异高亮样式 */
:deep(.diff-highlight) {
  background: #fdf6ec;
  color: #e6a23c;
  padding: 1px 3px;
  border-radius: 2px;
  font-weight: 500;
}

/* 移动端响应式 */
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

.polish-alert {
  margin-bottom: 16px;
}
</style>