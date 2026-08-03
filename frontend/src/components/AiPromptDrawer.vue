<template>
  <el-drawer
    v-model="visible"
    title="AI 自定义 System Prompt"
    direction="rtl"
    size="640px"
    :close-on-click-modal="false"
    class="ai-prompt-drawer"
  >
    <div class="drawer-content">
      <!-- Left Panel - Prompt Editor -->
      <div class="editor-panel">
        <div class="panel-label">
          <el-icon><EditPen /></el-icon>
          <span>提示词编写区</span>
        </div>

        <el-input
          v-model="localPrompt"
          type="textarea"
          :rows="14"
          placeholder="在此输入您的 AI System Prompt..."
          class="prompt-textarea"
          resize="none"
        />

        <div class="textarea-footer">
          <span class="char-count">{{ localPrompt.length }} 字</span>
          <span class="hint">建议 200-500 字效果最佳</span>
        </div>
      </div>

      <!-- Right Panel - Preview & Info -->
      <div class="preview-panel">
        <div class="panel-label">
          <el-icon><View /></el-icon>
          <span>AI 角色设定说明</span>
        </div>

        <div class="role-info">
          <h3 class="role-title">HR 专属 AI 助手</h3>
          <p class="role-desc">
            当 HR 使用 AI 模式访问您的简历时，系统将以您设定的 System Prompt 为基础进行对话。
          </p>
        </div>

        <div class="preview-section">
          <div class="preview-label">效果预览</div>
          <div class="preview-box">
            <div class="preview-header">
              <div class="ai-avatar">AI</div>
              <div class="ai-meta">
                <span class="ai-name">智能助手</span>
                <span class="ai-status">已连接</span>
              </div>
            </div>
            <div class="preview-content">
              <p class="preview-question">请问候选人的技术栈是什么？</p>
              <p class="preview-answer">
                <template v-if="localPrompt.trim()">
                  {{ generatePreview(localPrompt) }}
                </template>
                <template v-else>
                  你是一个专业的求职助手，关于候选人（开发者）的信息如下：他是一名全栈工程师，拥有 5 年以上的开发经验...
                </template>
              </p>
            </div>
          </div>
        </div>

        <div class="preset-section">
          <div class="preset-label">快速模板</div>
          <div class="preset-list">
            <button
              v-for="preset in presets"
              :key="preset.name"
              class="preset-btn"
              @click="applyPreset(preset)"
            >
              {{ preset.name }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Actions -->
    <template #footer>
      <div class="drawer-footer">
        <el-button @click="resetToDefault" class="reset-btn">
          <el-icon><RefreshLeft /></el-icon>
          恢复默认
        </el-button>
        <div class="footer-right">
          <el-button @click="cancelEdit">取消</el-button>
          <el-button type="primary" @click="savePrompt" :loading="saving" class="save-btn">
            <el-icon><Check /></el-icon>
            保存配置
          </el-button>
        </div>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>import { ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
const props = defineProps({
 modelValue: { type: Boolean, default: false },
 prompt: { type: String, default: '' },
 defaultValue: { type: String, default: '' },
});
const emit = defineEmits(['update:modelValue', 'save']);
const visible = ref(false);
const localPrompt = ref('');
const saving = ref(false);
watch(() => props.modelValue, (val) => {
 visible.value = val;
 if (val) {
 localPrompt.value = props.prompt || props.defaultValue || '';
 }
});
watch(visible, (val) => {
 emit('update:modelValue', val);
});
const presets = [
 {
 name: '技术岗模板',
 content: `你是一个专业的技术招聘助手，关于候选人的信息如下：\n\n候选人是一名 [职位名称]，主要技术栈包括 [技术栈列表]。在回答 HR 问题时，请：\n1. 突出候选人在相关技术领域的深度经验\n2. 提及具体的项目案例和成果\n3. 用简洁专业的语言回答`,
 },
 {
 name: '产品岗模板',
 content: `你是一个专业的产品招聘助手，关于候选人的信息如下：\n\n候选人是一名 [产品岗位]，具备产品规划、需求分析、用户研究等能力。在回答 HR 问题时，请：\n1. 强调候选人的产品思维和数据驱动决策能力\n2. 举例说明候选人主导的产品项目和成果\n3. 展示候选人的沟通协作和跨部门协调能力`,
 },
 {
 name: '综合岗位模板',
 content: `你是一个专业的求职助手，关于候选人的信息如下：\n\n候选人具有 [工作年限] 年工作经验，擅长 [核心技能]。在回答 HR 问题时，请：\n1. 全面展示候选人的专业背景和核心优势\n2. 突出与目标岗位的匹配度\n3. 以客观、专业的口吻进行介绍`,
 },
];
function generatePreview(prompt) {
 if (prompt.length < 30) {
 return '提示词过短，建议补充更多描述以获得更好的 AI 对话效果。';
 }
 const lines = prompt.split('\n').filter(l => l.trim());
 if (lines.length > 3) {
 return `${lines[0]}... 已根据您的提示词配置，AI 将以专业、客观的方式介绍候选人的核心优势和匹配度。`;
 }
 return '已根据您的提示词配置，AI 将按照您设定的角色和语气进行对话。';
}
function applyPreset(preset) {
 localPrompt.value = preset.content;
 ElMessage.success(`已应用「${preset.name}」模板`);
}
function resetToDefault() {
 localPrompt.value = props.defaultValue || '';
 ElMessage.success('已恢复为默认提示词');
}
function cancelEdit() {
 visible.value = false;
}
async function savePrompt() {
 saving.value = true;
 try {
 emit('save', localPrompt.value);
 ElMessage.success('配置已保存');
 visible.value = false;
 }
 finally {
 saving.value = false;
 }
}
</script>

<style scoped>
.ai-prompt-drawer :deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-divider-soft);
}

.ai-prompt-drawer :deep(.el-drawer__body) {
  padding: 0;
  overflow: hidden;
}

.ai-prompt-drawer :deep(.el-drawer__footer) {
  padding: 16px 24px;
  border-top: 1px solid var(--color-divider-soft);
  background: var(--color-canvas);
}

.drawer-content {
  display: flex;
  height: 100%;
  min-height: 0;
}

/* ===== Editor Panel ===== */
.editor-panel {
  flex: 1.2;
  display: flex;
  flex-direction: column;
  padding: 24px;
  border-right: 1px solid var(--color-divider-soft);
  min-height: 0;
}

.panel-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 12px;
}

.panel-label .el-icon {
  color: var(--color-primary);
}

.prompt-textarea :deep(.el-textarea__inner) {
  min-height: 280px !important;
  font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.7;
  padding: 16px;
  background: var(--color-surface-pearl);
  border: 1px solid var(--color-divider-soft);
  border-radius: 10px;
  color: var(--color-ink);
  transition: all 0.2s ease-out;
}

.prompt-textarea :deep(.el-textarea__inner:focus) {
  border-color: var(--color-primary);
  background: var(--color-canvas);
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.08);
}

.textarea-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 12px;
  color: var(--color-ink-muted-48);
}

/* ===== Preview Panel ===== */
.preview-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
  overflow-y: auto;
  gap: 20px;
}

.role-info {
  background: var(--color-surface-pearl);
  border-radius: 12px;
  padding: 16px;
}

.role-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
}

.role-desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-ink-muted-48);
}

.preview-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-ink-muted-48);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.preview-box {
  border: 1px solid var(--color-divider-soft);
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-canvas);
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--color-surface-pearl);
  border-bottom: 1px solid var(--color-divider-soft);
}

.ai-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--color-primary) 0%, #0052a3 100%);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ai-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink);
}

.ai-status {
  font-size: 11px;
  color: #16a34a;
  display: flex;
  align-items: center;
  gap: 4px;
}

.ai-status::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #16a34a;
}

.preview-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-question {
  margin: 0;
  font-size: 13px;
  color: var(--color-ink-muted-48);
  line-height: 1.5;
}

.preview-question::before {
  content: 'HR: ';
  font-weight: 600;
  color: var(--color-primary);
}

.preview-answer {
  margin: 0;
  font-size: 13px;
  color: var(--color-ink);
  line-height: 1.6;
  padding: 12px;
  background: var(--color-surface-pearl);
  border-radius: 8px;
}

.preview-answer::before {
  content: 'AI: ';
  font-weight: 600;
}

/* ===== Presets ===== */
.preset-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preset-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-ink-muted-48);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.preset-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preset-btn {
  padding: 8px 14px;
  border: 1px solid var(--color-divider-soft);
  border-radius: 8px;
  background: var(--color-canvas);
  font-size: 13px;
  color: var(--color-ink);
  cursor: pointer;
  transition: all 0.2s ease-out;
}

.preset-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: rgba(0, 102, 204, 0.04);
}

/* ===== Footer ===== */
.drawer-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-right {
  display: flex;
  gap: 12px;
}

.reset-btn {
  border-radius: 8px;
}

.save-btn {
  border-radius: 8px;
  padding: 10px 20px;
}

/* ===== Scrollbar ===== */
.preview-panel::-webkit-scrollbar {
  width: 6px;
}

.preview-panel::-webkit-scrollbar-track {
  background: transparent;
}

.preview-panel::-webkit-scrollbar-thumb {
  background: var(--color-hairline);
  border-radius: 3px;
}

.preview-panel::-webkit-scrollbar-thumb:hover {
  background: var(--color-ink-muted-48);
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .ai-prompt-drawer :deep(.el-drawer) {
    width: 100% !important;
  }

  .drawer-content {
    flex-direction: column;
  }

  .editor-panel {
    border-right: none;
    border-bottom: 1px solid var(--color-divider-soft);
  }

  .drawer-footer {
    flex-direction: column-reverse;
    gap: 12px;
  }

  .footer-right {
    width: 100%;
  }

  .footer-right .el-button {
    flex: 1;
  }
}
</style>
