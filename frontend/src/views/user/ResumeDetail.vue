<template>
  <div class="resume-detail" v-loading="loading">
    <template v-if="resume">
      <el-card class="resume-header-card">
        <div class="resume-header">
          <div class="resume-main">
            <h2 class="resume-title">{{ resume.title }}</h2>
            <div class="resume-badges">
              <el-tag :type="resume.status === 'published' ? 'success' : 'info'" size="small">
                {{ resume.status === 'published' ? '已发布' : '草稿' }}
              </el-tag>
              <el-tag v-if="resume.ai_processed" type="warning" size="small">AI已处理</el-tag>
            </div>
          </div>

          <div class="header-actions">
            <el-select v-model="selectedTemplateKey" class="template-select" placeholder="PDF模板">
              <el-option
                v-for="item in templateOptions"
                :key="item.template_key"
                :label="item.name"
                :value="item.template_key"
              />
            </el-select>
            <el-button type="primary" icon="Download" :loading="downloading" @click="downloadResume">
              下载PDF
            </el-button>
            <el-button icon="Edit" @click="$router.push('/user/edit')">编辑简历</el-button>
          </div>
        </div>

        <p v-if="resume.summary" class="summary">{{ resume.summary }}</p>

        <div v-if="resume.tags_detail && resume.tags_detail.length" class="resume-tags-row">
          <el-tag
            v-for="tag in resume.tags_detail"
            :key="tag.id"
            :type="tagTypeColor(tag.tag_type)"
            size="small"
            class="resume-tag-item"
          >
            {{ tag.name }}
          </el-tag>
        </div>
      </el-card>

      <el-card class="section-card">
        <template #header>
          <div class="section-header"><el-icon><School /></el-icon><span>教育经历</span></div>
        </template>
        <el-timeline v-if="resume.educations && resume.educations.length">
          <el-timeline-item
            v-for="edu in resume.educations"
            :key="edu.id"
            :timestamp="edu.start_date + ' ~ ' + (edu.end_date || '至今')"
            placement="top"
          >
            <el-card shadow="never" class="timeline-card">
              <h4 class="timeline-card-title">{{ edu.school }}</h4>
              <p class="timeline-card-sub">{{ edu.degree }} | {{ edu.major }}</p>
              <p v-if="edu.description" class="timeline-card-desc">{{ edu.description }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无教育经历" :image-size="80" />
      </el-card>

      <el-card class="section-card">
        <template #header>
          <div class="section-header"><el-icon><OfficeBuilding /></el-icon><span>工作经历</span></div>
        </template>
        <el-timeline v-if="resume.work_experiences && resume.work_experiences.length">
          <el-timeline-item
            v-for="work in resume.work_experiences"
            :key="work.id"
            :timestamp="work.start_date + ' ~ ' + (work.end_date || '至今')"
            placement="top"
          >
            <el-card shadow="never" class="timeline-card">
              <h4 class="timeline-card-title">{{ work.company }}</h4>
              <p class="work-position">{{ work.position }}</p>
              <p v-if="work.description" class="timeline-card-desc work-desc">{{ work.description }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无工作经历" :image-size="80" />
      </el-card>

      <el-card class="section-card">
        <template #header>
          <div class="section-header"><el-icon><FolderOpened /></el-icon><span>项目经历</span></div>
        </template>
        <div v-if="resume.projects && resume.projects.length" class="project-list">
          <el-card v-for="proj in resume.projects" :key="proj.id" shadow="hover" class="project-item">
            <h4 class="project-item-title">{{ proj.name }}</h4>
            <el-tag v-if="proj.role" size="small" type="warning" class="project-role-tag">{{ proj.role }}</el-tag>
            <p v-if="proj.tech_stack" class="project-tech">技术栈: {{ proj.tech_stack }}</p>
            <p v-if="proj.description" class="project-desc">{{ proj.description }}</p>
          </el-card>
        </div>
        <el-empty v-else description="暂无项目经历" :image-size="80" />
      </el-card>

      <el-card class="section-card">
        <template #header>
          <div class="section-header"><el-icon><TrendCharts /></el-icon><span>技能清单</span></div>
        </template>
        <div v-if="resume.skills && resume.skills.length" class="skills-grid">
          <div v-for="skill in groupedSkills" :key="skill.category" class="skill-group">
            <h4 class="skill-category">{{ skill.category }}</h4>
            <div class="skill-items">
              <div v-for="s in skill.items" :key="s.id" class="skill-item">
                <div class="skill-name">{{ s.name }}</div>
                <el-progress :percentage="s.level" :stroke-width="8" :color="getSkillColor(s.level)" />
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无技能" :image-size="80" />
      </el-card>

      <template v-for="(content, key) in resume.module_data" :key="key">
        <el-card v-if="content && moduleLabels[key]" class="section-card">
          <template #header>
            <div class="section-header">
              <el-icon><component :is="moduleIcons[key] || 'Document'" /></el-icon>
              <span>{{ moduleLabels[key] }}</span>
            </div>
          </template>
          <div class="module-content">{{ content }}</div>
        </el-card>
      </template>

      <el-card v-if="resume.file" class="section-card">
        <template #header><span>附件</span></template>
        <el-link :href="resume.file" target="_blank" type="primary" icon="Download">
          {{ resume.file_name || '下载简历文件' }}
        </el-link>
      </el-card>

      <el-card class="section-card">
        <template #header>
          <div class="section-header">
            <el-icon><Share /></el-icon>
            <span>访客分享链接</span>
            <el-tag v-if="visitorLink.visitor_enabled" type="success" size="small" class="status-tag">已启用</el-tag>
            <el-tag v-else type="info" size="small" class="status-tag">未启用</el-tag>
          </div>
        </template>

        <div v-if="visitorLink.visitor_enabled && visitorLink.visitor_url" class="visitor-link-display">
          <el-alert type="success" :closable="false" show-icon class="visitor-alert">
            <template #title>访客可通过以下链接查看您的公开简历模块</template>
            <template #default v-if="visitorLink.visitor_expires">
              有效期至: {{ formatDate(visitorLink.visitor_expires) }}
            </template>
          </el-alert>
          <el-input :model-value="visitorLink.visitor_url" readonly class="visitor-url-input">
            <template #append>
              <el-button icon="CopyDocument" @click="copyVisitorUrl">复制链接</el-button>
            </template>
          </el-input>
        </div>

        <el-divider />

        <el-form label-width="120px" size="default" class="visitor-form">
          <el-form-item label="启用访客链接">
            <el-switch v-model="visitorForm.enabled" active-text="启用" inactive-text="禁用" />
          </el-form-item>
          <el-form-item label="有效期（天）">
            <el-input-number v-model="visitorForm.expires_days" :min="1" :max="365" :disabled="!visitorForm.enabled" />
          </el-form-item>
          <el-form-item label="允许下载PDF">
            <el-switch v-model="visitorForm.allow_download" active-text="允许" inactive-text="禁止" :disabled="!visitorForm.enabled" />
          </el-form-item>
          <el-form-item label="公开模块">
            <el-checkbox-group v-model="visitorForm.public_modules" :disabled="!visitorForm.enabled">
              <el-checkbox v-for="mod in availableModules" :key="mod.value" :label="mod.value">
                {{ mod.label }}
              </el-checkbox>
            </el-checkbox-group>
            <div class="form-tip">不选择则默认公开所有已启用模块</div>
          </el-form-item>
          <el-form-item label="启用AI模式">
            <el-switch v-model="visitorForm.visitor_ai_mode_enabled" active-text="启用" inactive-text="禁用" :disabled="!visitorForm.enabled" />
          </el-form-item>
          <el-form-item v-if="visitorForm.visitor_ai_mode_enabled" label="AI功能开关">
            <el-switch v-model="visitorForm.ai_enabled" active-text="开启" inactive-text="关闭" :disabled="!visitorForm.enabled" />
          </el-form-item>
          <el-form-item v-if="visitorForm.visitor_ai_mode_enabled" label="AI调用配额">
            <el-input-number v-model="visitorForm.ai_quota" :min="1" :max="100" :disabled="!visitorForm.enabled" />
            <span v-if="visitorLink.visitor_ai_mode_enabled" class="quota-usage">
              已用: {{ visitorLink.visitor_ai_used || 0 }} / {{ visitorLink.visitor_ai_quota || 10 }}
            </span>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="Check" :loading="visitorSaving" @click="saveVisitorLink">
              {{ visitorLink.visitor_enabled ? '更新链接设置' : '生成链接' }}
            </el-button>
            <el-button v-if="visitorLink.visitor_enabled" type="danger" icon="Close" :loading="visitorSaving" @click="disableVisitorLink">
              禁用链接
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </template>

    <el-empty v-else-if="!loading" description="暂无简历信息">
      <el-button type="primary" @click="$router.push('/user/edit')">创建简历</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { resumeApi } from '@/api'
import { downloadBlob } from '@/utils/download'

const resume = ref(null)
const loading = ref(false)
const downloading = ref(false)
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
  if (level >= 80) return '#67c23a'
  if (level >= 60) return '#409eff'
  if (level >= 40) return '#e6a23c'
  return '#f56c6c'
}

function tagTypeColor(type) {
  const colors = { skill: '', project: 'success', certificate: 'warning', award: 'danger', language: 'info', custom: '' }
  return colors[type] || ''
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
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
    const list = await resumeApi.list()
    const first = list?.results?.[0]
    if (!first) {
      resume.value = null
      return
    }
    resume.value = await resumeApi.detail(first.id)
    await loadVisitorLinkInfo()
  } catch {
    resume.value = null
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
.resume-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.resume-main {
  min-width: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.template-select {
  width: 160px;
}

.resume-title {
  margin: 0 0 8px 0;
}

.resume-badges {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
}

.summary {
  margin-top: 12px;
  color: #666;
  line-height: 1.6;
}

.resume-tags-row {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.resume-tag-item {
  margin: 0;
}

.section-card {
  margin-top: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.status-tag {
  margin-left: 8px;
}

.timeline-card :deep(.el-card__body) {
  padding: 16px;
}

.timeline-card-title {
  margin: 0 0 4px 0;
  font-size: 16px;
}

.timeline-card-sub {
  margin: 0;
  color: #606266;
}

.timeline-card-desc {
  color: #666;
  margin-top: 8px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.work-position {
  color: #409eff;
  margin: 0;
  font-weight: 500;
}

.work-desc {
  white-space: pre-wrap;
}

.project-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.project-item-title {
  margin: 0 0 4px 0;
}

.project-role-tag {
  margin: 4px 0;
}

.project-tech {
  color: #67c23a;
  font-size: 13px;
  margin: 4px 0;
}

.project-desc {
  color: #666;
  font-size: 13px;
  margin-top: 8px;
  line-height: 1.6;
}

.skills-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.skill-category {
  margin-bottom: 10px;
  color: #333;
  font-size: 14px;
}

.skill-items {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.skill-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.skill-name {
  font-size: 13px;
  color: #666;
}

.module-content {
  white-space: pre-wrap;
  line-height: 1.8;
  color: #333;
  font-size: 14px;
}

.visitor-link-display {
  margin-bottom: 16px;
}

.visitor-alert {
  margin-bottom: 16px;
}

.visitor-url-input {
  max-width: 100%;
}

.visitor-form {
  max-width: 680px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.quota-usage {
  margin-left: 12px;
  color: #909399;
  font-size: 13px;
}

@media (max-width: 768px) {
  .resume-header {
    flex-direction: column;
  }

  .project-list {
    grid-template-columns: 1fr;
  }

  .skill-items {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }
}
</style>
