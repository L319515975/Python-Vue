<template>
  <div class="resume-detail" v-loading="loading">
    <template v-if="resume">
      <!-- ===== Top Header Card ===== -->
      <div class="resume-hero">
        <div class="hero-main">
          <div class="hero-info">
            <h1 class="resume-title">{{ resume.title }}</h1>
            <div class="resume-badges">
              <el-tag :type="resume.status === 'published' ? 'success' : 'info'" size="default" effect="light">
                {{ resume.status === 'published' ? '已发布' : '草稿' }}
              </el-tag>
              <el-tag v-if="resume.ai_processed" type="warning" size="default" effect="light">AI 已处理</el-tag>
            </div>
          </div>
          <p v-if="resume.summary" class="summary">{{ resume.summary }}</p>
          <div v-if="resume.tags_detail && resume.tags_detail.length" class="resume-tags-row">
            <el-tag
              v-for="tag in resume.tags_detail"
              :key="tag.id"
              :type="tagTypeColor(tag.tag_type)"
              size="small"
              effect="plain"
              class="resume-tag-item"
            >
              {{ tag.name }}
            </el-tag>
          </div>
        </div>

        <div class="hero-actions">
          <div class="action-row">
            <el-select v-model="selectedTemplateKey" class="template-select" placeholder="PDF模板">
              <el-option
                v-for="item in templateOptions"
                :key="item.template_key"
                :label="item.name"
                :value="item.template_key"
              />
            </el-select>
            <el-button type="primary" icon="Download" :loading="downloading" @click="downloadResume" class="action-btn">
              下载 PDF
            </el-button>
            <el-button icon="Edit" @click="$router.push(isAdminRoute ? '/admin/my-resume-edit' : '/user/edit')" class="action-btn">
              编辑简历
            </el-button>
          </div>
          <div class="stats-row">
            <div class="mini-stat">
              <span class="mini-stat-value">{{ enabledModuleCount }}</span>
              <span class="mini-stat-label">已启用模块</span>
            </div>
            <div class="mini-stat-divider"></div>
            <div class="mini-stat">
              <span class="mini-stat-value">{{ visitorLink.visitor_ai_used || 0 }}</span>
              <span class="mini-stat-label">AI 使用次数</span>
            </div>
            <div class="mini-stat-divider"></div>
            <div class="mini-stat">
              <span class="mini-stat-value">{{ resume.updated_at ? formatDate(resume.updated_at) : '—' }}</span>
              <span class="mini-stat-label">更新时间</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== Main Content: Sidebar + Modules ===== -->
      <div class="content-grid">
        <!-- Left Sidebar: Module Navigation -->
        <div class="modules-sidebar">
          <div class="sidebar-header">
            <el-icon class="sidebar-icon"><Menu /></el-icon>
            <span>简历模块</span>
          </div>
          <div class="sidebar-nav">
            <button
              v-for="mod in moduleNavItems"
              :key="mod.key"
              class="nav-item"
              :class="{ active: activeModule === mod.key }"
              @click="scrollToModule(mod.key)"
            >
              <el-icon class="nav-icon"><component :is="mod.icon" /></el-icon>
              <span class="nav-label">{{ mod.label }}</span>
              <el-badge
                v-if="mod.enabled"
                is-dot
                class="nav-badge"
              />
            </button>
          </div>

          <div class="sidebar-divider"></div>

          <div class="sidebar-section">
            <div class="section-label">访客分享</div>
            <div class="share-status" :class="{ active: visitorLink.visitor_enabled }">
              <span class="status-dot"></span>
              {{ visitorLink.visitor_enabled ? '已启用' : '未启用' }}
            </div>
            <el-button
              size="small"
              type="primary"
              plain
              @click="scrollToModule('visitor')"
              class="share-btn"
            >
              分享设置
            </el-button>
          </div>
        </div>

        <!-- Right Content: Module Cards -->
        <div class="modules-content">
          <!-- Education -->
          <el-card ref="educationRef" class="section-card" id="module-education">
            <template #header>
              <div class="section-header">
                <div class="section-title">
                  <el-icon><School /></el-icon>
                  <span>教育经历</span>
                </div>
                <el-tag size="small" effect="plain">{{ resume.educations?.length || 0 }} 项</el-tag>
              </div>
            </template>
            <el-timeline v-if="resume.educations && resume.educations.length">
              <el-timeline-item
                v-for="edu in resume.educations"
                :key="edu.id"
                :timestamp="edu.start_date + ' ~ ' + (edu.end_date || '至今')"
                placement="top"
              >
                <div class="timeline-content">
                  <h4 class="timeline-title">{{ edu.school }}</h4>
                  <p class="timeline-sub">{{ edu.degree }} | {{ edu.major }}</p>
                  <p v-if="edu.description" class="timeline-desc">{{ edu.description }}</p>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无教育经历" :image-size="64" />
          </el-card>

          <!-- Work Experience -->
          <el-card ref="workRef" class="section-card" id="module-work">
            <template #header>
              <div class="section-header">
                <div class="section-title">
                  <el-icon><OfficeBuilding /></el-icon>
                  <span>工作经历</span>
                </div>
                <el-tag size="small" effect="plain">{{ resume.work_experiences?.length || 0 }} 项</el-tag>
              </div>
            </template>
            <el-timeline v-if="resume.work_experiences && resume.work_experiences.length">
              <el-timeline-item
                v-for="work in resume.work_experiences"
                :key="work.id"
                :timestamp="work.start_date + ' ~ ' + (work.end_date || '至今')"
                placement="top"
              >
                <div class="timeline-content">
                  <h4 class="timeline-title">{{ work.company }}</h4>
                  <p class="timeline-sub work-position">{{ work.position }}</p>
                  <p v-if="work.description" class="timeline-desc">{{ work.description }}</p>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无工作经历" :image-size="64" />
          </el-card>

          <!-- Projects -->
          <el-card ref="projectRef" class="section-card" id="module-project">
            <template #header>
              <div class="section-header">
                <div class="section-title">
                  <el-icon><FolderOpened /></el-icon>
                  <span>项目经历</span>
                </div>
                <el-tag size="small" effect="plain">{{ resume.projects?.length || 0 }} 项</el-tag>
              </div>
            </template>
            <div v-if="resume.projects && resume.projects.length" class="project-grid">
              <div v-for="proj in resume.projects" :key="proj.id" class="project-card">
                <div class="project-header">
                  <h4 class="project-title">{{ proj.name }}</h4>
                  <el-tag v-if="proj.role" size="small" type="warning" effect="light">{{ proj.role }}</el-tag>
                </div>
                <p v-if="proj.tech_stack" class="project-tech">
                  <span class="tech-label">技术栈</span>
                  {{ proj.tech_stack }}
                </p>
                <p v-if="proj.description" class="project-desc">{{ proj.description }}</p>
              </div>
            </div>
            <el-empty v-else description="暂无项目经历" :image-size="64" />
          </el-card>

          <!-- Skills -->
          <el-card ref="skillRef" class="section-card" id="module-skill">
            <template #header>
              <div class="section-header">
                <div class="section-title">
                  <el-icon><TrendCharts /></el-icon>
                  <span>技能清单</span>
                </div>
                <el-tag size="small" effect="plain">{{ groupedSkills.length }} 类</el-tag>
              </div>
            </template>
            <div v-if="resume.skills && resume.skills.length" class="skills-container">
              <div v-for="skill in groupedSkills" :key="skill.category" class="skill-group">
                <h4 class="skill-category-title">{{ skill.category }}</h4>
                <div class="skill-items">
                  <div v-for="s in skill.items" :key="s.id" class="skill-item">
                    <div class="skill-header">
                      <span class="skill-name">{{ s.name }}</span>
                      <span class="skill-level">{{ s.level }}%</span>
                    </div>
                    <el-progress :percentage="s.level" :stroke-width="6" :color="getSkillColor(s.level)" />
                  </div>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无技能" :image-size="64" />
          </el-card>

          <!-- Custom Modules -->
          <template v-for="(content, key) in resume.module_data" :key="key">
            <el-card v-if="content && moduleLabels[key]" class="section-card" :id="`module-${key}`">
              <template #header>
                <div class="section-header">
                  <div class="section-title">
                    <el-icon><component :is="moduleIcons[key] || 'Document'" /></el-icon>
                    <span>{{ moduleLabels[key] }}</span>
                  </div>
                </div>
              </template>
              <div class="module-content">{{ content }}</div>
            </el-card>
          </template>

          <!-- Visitor Settings -->
          <el-card ref="visitorRef" class="section-card" id="module-visitor">
            <template #header>
              <div class="section-header">
                <div class="section-title">
                  <el-icon><Share /></el-icon>
                  <span>访客分享链接</span>
                  <el-tag v-if="visitorLink.visitor_enabled" type="success" size="small" effect="light">已启用</el-tag>
                  <el-tag v-else type="info" size="small" effect="light">未启用</el-tag>
                </div>
              </div>
            </template>

            <div v-if="visitorLink.visitor_enabled && visitorLink.visitor_url" class="visitor-link-section">
              <div class="visitor-alert" role="alert">
                <el-icon class="alert-icon"><InfoFilled /></el-icon>
                <div class="alert-content">
                  <div class="alert-title">访客可通过以下链接查看您的公开简历模块</div>
                  <div v-if="visitorLink.visitor_expires" class="alert-desc">
                    有效期至: {{ formatDate(visitorLink.visitor_expires) }}
                  </div>
                </div>
              </div>
              <div class="url-input-row">
                <el-input :model-value="visitorLink.visitor_url" readonly>
                  <template #append>
                    <el-button icon="CopyDocument" @click="copyVisitorUrl">复制</el-button>
                  </template>
                </el-input>
              </div>
            </div>

            <el-form label-position="top" size="default" class="visitor-form">
              <el-row :gutter="20">
                <el-col :xs="24" :sm="12">
                  <el-form-item label="启用访客链接">
                    <el-switch v-model="visitorForm.enabled" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12">
                  <el-form-item label="允许下载 PDF">
                    <el-switch v-model="visitorForm.allow_download" :disabled="!visitorForm.enabled" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="有效期（天）">
                <el-input-number v-model="visitorForm.expires_days" :min="1" :max="365" :disabled="!visitorForm.enabled" />
              </el-form-item>

              <el-form-item label="公开模块">
                <el-checkbox-group v-model="visitorForm.public_modules" :disabled="!visitorForm.enabled">
                  <el-checkbox v-for="mod in availableModules" :key="mod.value" :label="mod.value">
                    {{ mod.label }}
                  </el-checkbox>
                </el-checkbox-group>
                <div class="form-tip">不选择则默认公开所有已启用模块</div>
              </el-form-item>

              <el-divider />

              <div class="ai-section">
                <div class="ai-section-header">
                  <div class="ai-section-title">
                    <el-icon><ChatDotRound /></el-icon>
                    <span>AI 访客模式</span>
                  </div>
                  <el-switch v-model="visitorForm.visitor_ai_mode_enabled" :disabled="!visitorForm.enabled" />
                </div>

                <template v-if="visitorForm.visitor_ai_mode_enabled">
                  <el-form-item label="AI 功能">
                    <el-switch v-model="visitorForm.ai_enabled" :disabled="!visitorForm.enabled" />
                  </el-form-item>

                  <el-form-item label="AI 自定义提示词">
                    <div class="prompt-config">
                      <el-input
                        v-model="visitorForm.ai_system_prompt"
                        type="textarea"
                        :rows="4"
                        placeholder="例如：你是一个专业的求职助手，关于候选人的信息如下..."
                        :disabled="!visitorForm.enabled"
                      />
                      <div class="prompt-actions">
                        <el-button size="small" @click="showPromptDrawer = true">
                          <el-icon><Setting /></el-icon>
                          可视化编辑
                        </el-button>
                      </div>
                      <div class="form-tip">HR 使用 AI 模式时，系统将以此提示词为基础进行对话</div>
                    </div>
                  </el-form-item>

                  <el-form-item label="AI 调用配额">
                    <div class="quota-config">
                      <el-input-number v-model="visitorForm.ai_quota" :min="1" :max="100" :disabled="!visitorForm.enabled" />
                      <span v-if="visitorLink.visitor_ai_mode_enabled" class="quota-usage">
                        已用: {{ visitorLink.visitor_ai_used || 0 }} / {{ visitorLink.visitor_ai_quota || 10 }}
                      </span>
                    </div>
                  </el-form-item>
                </template>
              </div>

              <el-form-item>
                <div class="form-actions">
                  <el-button type="primary" icon="Check" :loading="visitorSaving" @click="saveVisitorLink">
                    {{ visitorLink.visitor_enabled ? '更新链接设置' : '生成链接' }}
                  </el-button>
                  <el-button v-if="visitorLink.visitor_enabled" type="danger" plain :loading="visitorSaving" @click="disableVisitorLink">
                    禁用链接
                  </el-button>
                </div>
              </el-form-item>
            </el-form>
          </el-card>
        </div>
      </div>
    </template>

    <el-empty v-else-if="!loading" description="暂无简历信息">
      <el-button type="primary" @click="$router.push(isAdminRoute ? '/admin/my-resume-edit' : '/user/edit')">创建简历</el-button>
    </el-empty>

    <!-- AI Prompt Drawer -->
    <AiPromptDrawer
      v-model="showPromptDrawer"
      :prompt="visitorForm.ai_system_prompt"
      :default-value="DEFAULT_AI_PROMPT"
      @save="handlePromptSave"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, markRaw } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { resumeApi } from '@/api'
import { downloadBlob } from '@/utils/download'
import AiPromptDrawer from '@/components/AiPromptDrawer.vue'

const DEFAULT_AI_PROMPT = `你是一个专业的求职助手，关于候选人的信息如下：他是一名全栈工程师，拥有 5 年以上的开发经验。在回答 HR 问题时，请客观、专业地介绍候选人的核心优势和技术能力。`

const route = useRoute()
const isAdminRoute = computed(() => route.path.startsWith('/admin'))

const resume = ref(null)
const loading = ref(false)
const downloading = ref(false)
const showPromptDrawer = ref(false)
const templateOptions = ref([
  { template_key: 'default', name: '经典简历' },
  { template_key: 'modern', name: '现代简历' },
])
const selectedTemplateKey = ref('default')

const visitorLink = ref({
  visitor_enabled: false,
  visitor_token: '',
  visitor_expires: null,
  visitor_allow_download: false,
  public_modules: [],
  visitor_url: '',
  visitor_ai_mode_enabled: false,
  visitor_ai_used: 0,
  visitor_ai_quota: 10,
})

const visitorSaving = ref(false)
const visitorForm = reactive({
  enabled: false,
  expires_days: 30,
  allow_download: false,
  public_modules: [],
  visitor_ai_mode_enabled: false,
  ai_enabled: true,
  ai_quota: 10,
  ai_system_prompt: '',
})

const enabledModuleCount = computed(() => {
  if (!resume.value?.enabled_modules) return 0
  return resume.value.enabled_modules.length
})

const moduleLabels = { certificate: '证书', award: '获奖荣誉', language: '语言能力' }
const moduleIcons = { certificate: 'Stamp', award: 'Trophy', language: 'ChatLineRound' }
const availableModules = [
  { value: 'education', label: '教育经历' },
  { value: 'work_experience', label: '工作经历' },
  { value: 'project', label: '项目经历' },
  { value: 'skill', label: '技能清单' },
  { value: 'certificate', label: '证书' },
  { value: 'award', label: '获奖荣誉' },
  { value: 'language', label: '语言能力' },
]

const moduleNavItems = computed(() => [
  { key: 'education', label: '教育经历', icon: 'School', enabled: !!resume.value?.educations?.length },
  { key: 'work', label: '工作经历', icon: 'OfficeBuilding', enabled: !!resume.value?.work_experiences?.length },
  { key: 'project', label: '项目经历', icon: 'FolderOpened', enabled: !!resume.value?.projects?.length },
  { key: 'skill', label: '技能清单', icon: 'TrendCharts', enabled: !!resume.value?.skills?.length },
  ...Object.entries(moduleLabels).map(([key, label]) => ({
    key,
    label,
    icon: moduleIcons[key] || 'Document',
    enabled: !!resume.value?.module_data?.[key],
  })),
])

const activeModule = ref('education')

const groupedSkills = computed(() => {
  if (!resume.value?.skills?.length) return []
  const groups = {}
  resume.value.skills.forEach((item) => {
    const category = item.category || '其他'
    if (!groups[category]) groups[category] = []
    groups[category].push(item)
  })
  return Object.entries(groups).map(([category, items]) => ({ category, items }))
})

function getSkillColor(level) {
  if (level >= 80) return '#16a34a'
  if (level >= 60) return '#0066cc'
  if (level >= 40) return '#ea580c'
  return '#ef4444'
}

function tagTypeColor(type) {
  const colors = { skill: '', project: 'success', certificate: 'warning', award: 'danger', language: 'info', custom: '' }
  return colors[type] || ''
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

function scrollToModule(key) {
  activeModule.value = key
  const el = document.getElementById(`module-${key}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function handlePromptSave(prompt) {
  visitorForm.ai_system_prompt = prompt
  showPromptDrawer.value = false
}

function buildPdfFilename() {
  const title = resume.value?.title || resume.value?.user?.username || 'resume'
  return `${title.replace(/[\\/:*?"<>|]/g, '_')}.pdf`
}

async function loadTemplates() {
  try {
    const data = await resumeApi.pdfTemplates()
    if (Array.isArray(data) && data.length) {
      templateOptions.value = data.filter(item => item.is_active !== false)
    }
    if (!templateOptions.value.some(item => item.template_key === selectedTemplateKey.value)) {
      selectedTemplateKey.value = templateOptions.value[0]?.template_key || 'default'
    }
  } catch {
    // 保持内置模板
  }
}

async function loadResume() {
  loading.value = true
  try {
    resume.value = await resumeApi.myResume()
    await loadVisitorLinkInfo()
  } catch {
    try {
      const list = await resumeApi.list()
      const first = list?.results?.[0]
      if (!first) { resume.value = null; return }
      resume.value = await resumeApi.detail(first.id)
      await loadVisitorLinkInfo()
    } catch { resume.value = null }
  } finally {
    loading.value = false
  }
}

async function downloadResume() {
  if (!resume.value?.id) return
  downloading.value = true
  try {
    const modules = resume.value.enabled_modules?.length
      ? resume.value.enabled_modules
      : ['education', 'work_experience', 'project', 'skill']
    const blob = await resumeApi.exportPdf(resume.value.id, modules, selectedTemplateKey.value)
    downloadBlob(blob, buildPdfFilename())
    ElMessage.success('PDF 下载成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || 'PDF 下载失败')
  } finally {
    downloading.value = false
  }
}

async function copyVisitorUrl() {
  try {
    await navigator.clipboard.writeText(visitorLink.value.visitor_url)
    ElMessage.success('链接已复制到剪贴板')
  } catch {
    const input = document.createElement('input')
    input.value = visitorLink.value.visitor_url
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    ElMessage.success('链接已复制到剪贴板')
  }
}

async function loadVisitorLinkInfo() {
  if (!resume.value?.id) return
  try {
    const info = await resumeApi.visitorLinkInfo(resume.value.id)
    visitorLink.value = info
    visitorForm.enabled = info.visitor_enabled || false
    visitorForm.allow_download = info.visitor_allow_download || false
    visitorForm.public_modules = info.public_modules || []
    visitorForm.visitor_ai_mode_enabled = info.visitor_ai_mode_enabled || false
    visitorForm.ai_enabled = info.visitor_ai_enabled !== false
    visitorForm.ai_quota = info.visitor_ai_quota || 10
    visitorForm.ai_system_prompt = info.visitor_ai_system_prompt || ""
  } catch {
    // 忽略
  }
}

async function saveVisitorLink() {
  if (!resume.value?.id) return
  visitorSaving.value = true
  try {
    const payload = {
      enabled: visitorForm.enabled,
      expires_days: visitorForm.expires_days,
      allow_download: visitorForm.allow_download,
      public_modules: visitorForm.public_modules,
      visitor_ai_mode_enabled: visitorForm.visitor_ai_mode_enabled,
      ai_enabled: visitorForm.ai_enabled,
      ai_quota: visitorForm.ai_quota,
      ai_system_prompt: visitorForm.ai_system_prompt,
    }
    const result = await resumeApi.generateVisitorLink(resume.value.id, payload)
    visitorLink.value = result
    ElMessage.success('访客链接已保存')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    visitorSaving.value = false
  }
}

async function disableVisitorLink() {
  if (!resume.value?.id) return
  visitorSaving.value = true
  try {
    const result = await resumeApi.disableVisitorLink(resume.value.id)
    visitorLink.value = result
    visitorForm.enabled = false
    ElMessage.success('访客链接已禁用')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    visitorSaving.value = false
  }
}

onMounted(async () => {
  await loadTemplates()
  await loadResume()
})
</script>

<style scoped>
.resume-detail {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ===== Hero Card ===== */
.resume-hero {
  background: var(--color-canvas);
  border: 1px solid var(--color-divider-soft);
  border-radius: 16px;
  padding: 28px;
  display: flex;
  gap: 28px;
  justify-content: space-between;
  flex-wrap: wrap;
}

.hero-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.resume-title {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  color: var(--color-ink);
  letter-spacing: -0.3px;
}

.resume-badges {
  display: flex;
  gap: 8px;
}

.summary {
  margin: 0;
  color: var(--color-ink-muted-48);
  line-height: 1.7;
  font-size: 14px;
}

.resume-tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.resume-tag-item {
  margin: 0;
}

.hero-actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 320px;
}

.action-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.template-select {
  width: 140px;
}

.action-btn {
  border-radius: 10px;
}

.stats-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--color-surface-pearl);
  border-radius: 12px;
}

.mini-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.mini-stat-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-ink);
}

.mini-stat-label {
  font-size: 11px;
  color: var(--color-ink-muted-48);
}

.mini-stat-divider {
  width: 1px;
  height: 32px;
  background: var(--color-divider-soft);
}

/* ===== Content Grid ===== */
.content-grid {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 24px;
  align-items: start;
}

/* ===== Sidebar ===== */
.modules-sidebar {
  position: sticky;
  top: 0;
  background: var(--color-canvas);
  border: 1px solid var(--color-divider-soft);
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink);
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-divider-soft);
}

.sidebar-icon {
  color: var(--color-primary);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-ink-muted-48);
  cursor: pointer;
  transition: all 0.2s ease-out;
  width: 100%;
  text-align: left;
  position: relative;
}

.nav-item:hover {
  background: var(--color-surface-pearl);
  color: var(--color-ink);
}

.nav-item.active {
  background: rgba(0, 102, 204, 0.08);
  color: var(--color-primary);
  font-weight: 500;
}

.nav-icon {
  font-size: 14px;
}

.nav-label {
  flex: 1;
}

.nav-badge {
  --el-badge-size: 6px;
}

.sidebar-divider {
  height: 1px;
  background: var(--color-divider-soft);
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-ink-muted-48);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.share-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-ink-muted-48);
}

.share-status.active {
  color: #16a34a;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-ink-muted-48);
}

.share-status.active .status-dot {
  background: #16a34a;
}

.share-btn {
  width: 100%;
}

/* ===== Modules Content ===== */
.modules-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-card {
  background: var(--color-canvas);
  border: 1px solid var(--color-divider-soft);
  border-radius: 14px;
  overflow: hidden;
  transition: all 0.2s ease-out;
}

.section-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-divider-soft);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
}

.section-title .el-icon {
  color: var(--color-primary);
}

/* ===== Timeline ===== */
.timeline-content {
  padding: 8px 0;
}

.timeline-title {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
}

.timeline-sub {
  margin: 0;
  color: var(--color-ink-muted-48);
  font-size: 13px;
}

.work-position {
  color: var(--color-primary);
  font-weight: 500;
}

.timeline-desc {
  color: var(--color-ink-muted-48);
  margin-top: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
  font-size: 13px;
}

/* ===== Projects ===== */
.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.project-card {
  border: 1px solid var(--color-divider-soft);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s ease-out;
}

.project-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 4px 12px rgba(0, 102, 204, 0.08);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.project-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
}

.project-tech {
  display: flex;
  gap: 4px;
  font-size: 12px;
  margin: 4px 0;
  flex-wrap: wrap;
}

.tech-label {
  color: var(--color-ink-muted-48);
  font-weight: 500;
}

.project-desc {
  color: var(--color-ink-muted-48);
  font-size: 13px;
  margin: 8px 0 0;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* ===== Skills ===== */
.skills-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.skill-category-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
}

.skill-items {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.skill-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skill-name {
  font-size: 13px;
  color: var(--color-ink);
  font-weight: 500;
}

.skill-level {
  font-size: 12px;
  color: var(--color-ink-muted-48);
  font-weight: 600;
}

/* ===== Module Content ===== */
.module-content {
  white-space: pre-wrap;
  line-height: 1.8;
  color: var(--color-ink);
  font-size: 14px;
  padding: 16px 20px;
}

/* ===== Visitor Section ===== */
.visitor-link-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 20px;
}

.visitor-alert {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(0, 102, 204, 0.06);
  border: 1px solid rgba(0, 102, 204, 0.12);
  border-radius: 10px;
}

.alert-icon {
  color: var(--color-primary);
  flex-shrink: 0;
  margin-top: 2px;
}

.alert-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 4px;
}

.alert-desc {
  font-size: 12px;
  color: var(--color-ink-muted-48);
}

.url-input-row {
  max-width: 100%;
}

.visitor-form {
  padding: 0 20px 20px;
}

.form-tip {
  font-size: 12px;
  color: var(--color-ink-muted-48);
  margin-top: 4px;
}

.quota-config {
  display: flex;
  align-items: center;
  gap: 12px;
}

.quota-usage {
  color: var(--color-ink-muted-48);
  font-size: 13px;
}

.ai-section {
  background: var(--color-surface-pearl);
  border-radius: 12px;
  padding: 16px;
  margin: 12px 0;
}

.ai-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.ai-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
}

.ai-section-title .el-icon {
  color: var(--color-primary);
}

.prompt-config {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prompt-actions {
  display: flex;
  justify-content: flex-end;
}

.form-actions {
  display: flex;
  gap: 12px;
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .resume-hero {
    flex-direction: column;
    padding: 20px;
  }

  .hero-actions {
    min-width: 100%;
  }

  .stats-row {
    flex-wrap: wrap;
  }

  .content-grid {
    grid-template-columns: 1fr;
  }

  .modules-sidebar {
    position: static;
  }

  .project-grid {
    grid-template-columns: 1fr;
  }

  .skill-items {
    grid-template-columns: 1fr;
  }
}
</style>
