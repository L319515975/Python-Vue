<template>
  <div class="resume-detail" v-loading="loading">
    <template v-if="resume">
      <el-card class="resume-header-card">
        <div class="resume-header">
          <div>
            <h2>{{ resume.title }}</h2>
            <div style="margin-top: 8px; display: flex; gap: 8px; align-items: center">
              <el-tag :type="resume.status === 'published' ? 'success' : 'info'" size="small">
                {{ resume.status === 'published' ? '已发布' : '草稿' }}
              </el-tag>
              <el-tag v-if="resume.ai_processed" type="warning" size="small">AI已处理</el-tag>
            </div>
          </div>
          <el-button type="primary" icon="Edit" @click="$router.push('/user/edit')">编辑简历</el-button>
        </div>
        <p v-if="resume.summary" class="summary">{{ resume.summary }}</p>
        <div v-if="resume.tags_detail && resume.tags_detail.length" style="margin-top: 12px">
          <el-tag v-for="tag in resume.tags_detail" :key="tag.id" :type="tagTypeColor(tag.tag_type)" size="small" style="margin-right: 6px; margin-bottom: 4px">{{ tag.name }}</el-tag>
        </div>
      </el-card>

      <el-card style="margin-top: 16px">
        <template #header><div class="section-header"><el-icon><School /></el-icon><span>教育经历</span></div></template>
        <el-timeline v-if="resume.educations && resume.educations.length">
          <el-timeline-item v-for="edu in resume.educations" :key="edu.id" :timestamp="edu.start_date + ' ~ ' + (edu.end_date || '至今')" placement="top">
            <el-card shadow="never"><h4>{{ edu.school }}</h4><p>{{ edu.degree }} | {{ edu.major }}</p><p v-if="edu.description" style="color: #666; margin-top: 8px">{{ edu.description }}</p></el-card>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无教育经历" :image-size="80" />
      </el-card>

      <el-card style="margin-top: 16px">
        <template #header><div class="section-header"><el-icon><OfficeBuilding /></el-icon><span>工作经历</span></div></template>
        <el-timeline v-if="resume.work_experiences && resume.work_experiences.length">
          <el-timeline-item v-for="work in resume.work_experiences" :key="work.id" :timestamp="work.start_date + ' ~ ' + (work.end_date || '至今')" placement="top">
            <el-card shadow="never"><h4>{{ work.company }}</h4><p style="color: #409eff">{{ work.position }}</p><p v-if="work.description" style="color: #666; margin-top: 8px; white-space: pre-wrap">{{ work.description }}</p></el-card>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无工作经历" :image-size="80" />
      </el-card>

      <el-card style="margin-top: 16px">
        <template #header><div class="section-header"><el-icon><FolderOpened /></el-icon><span>项目经历</span></div></template>
        <div v-if="resume.projects && resume.projects.length" class="project-list">
          <el-card v-for="proj in resume.projects" :key="proj.id" shadow="hover" class="project-item">
            <h4>{{ proj.name }}</h4>
            <el-tag v-if="proj.role" size="small" type="warning" style="margin: 4px 0">{{ proj.role }}</el-tag>
            <p v-if="proj.tech_stack" style="color: #67c23a; font-size: 13px; margin: 4px 0">技术栈: {{ proj.tech_stack }}</p>
            <p v-if="proj.description" style="color: #666; font-size: 13px; margin-top: 8px">{{ proj.description }}</p>
          </el-card>
        </div>
        <el-empty v-else description="暂无项目经历" :image-size="80" />
      </el-card>

      <el-card style="margin-top: 16px">
        <template #header><div class="section-header"><el-icon><TrendCharts /></el-icon><span>技能清单</span></div></template>
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
        <el-card v-if="content && moduleLabels[key]" style="margin-top: 16px">
          <template #header><div class="section-header"><el-icon><component :is="moduleIcons[key] || 'Document'" /></el-icon><span>{{ moduleLabels[key] }}</span></div></template>
          <div class="module-content">{{ content }}</div>
        </el-card>
      </template>

      <el-card v-if="resume.file" style="margin-top: 16px">
        <template #header><span>附件</span></template>
        <el-link :href="resume.file" target="_blank" type="primary" icon="Download">{{ resume.file_name || '下载简历文件' }}</el-link>
      </el-card>

      <el-card style="margin-top: 16px">
        <template #header>
          <div class="section-header">
            <el-icon><Share /></el-icon>
            <span>游客分享链接</span>
            <el-tag v-if="visitorLink.visitor_enabled" type="success" size="small" style="margin-left: 8px">已启用</el-tag>
            <el-tag v-else type="info" size="small" style="margin-left: 8px">未启用</el-tag>
          </div>
        </template>
        <div v-if="visitorLink.visitor_enabled && visitorLink.visitor_url" class="visitor-link-display">
          <el-alert type="success" :closable="false" show-icon style="margin-bottom: 16px">
            <template #title>游客可通过以下链接查看您的公开简历模块</template>
            <template #default v-if="visitorLink.visitor_expires">有效期至: {{ formatDate(visitorLink.visitor_expires) }}</template>
          </el-alert>
          <el-input :model-value="visitorLink.visitor_url" readonly class="visitor-url-input">
            <template #append><el-button icon="CopyDocument" @click="copyVisitorUrl">复制链接</el-button></template>
          </el-input>
        </div>
        <el-divider />
        <el-form label-width="120px" size="default" style="max-width: 600px">
          <el-form-item label="启用游客链接">
            <el-switch v-model="visitorForm.enabled" active-text="启用" inactive-text="禁用" />
          </el-form-item>
          <el-form-item label="有效期(天)">
            <el-input-number v-model="visitorForm.expires_days" :min="1" :max="365" :disabled="!visitorForm.enabled" />
          </el-form-item>
          <el-form-item label="允许下载PDF">
            <el-switch v-model="visitorForm.allow_download" active-text="允许" inactive-text="禁止" :disabled="!visitorForm.enabled" />
          </el-form-item>
          <el-form-item label="公开模块">
            <el-checkbox-group v-model="visitorForm.public_modules" :disabled="!visitorForm.enabled">
              <el-checkbox v-for="mod in availableModules" :key="mod.value" :label="mod.value">{{ mod.label }}</el-checkbox>
            </el-checkbox-group>
            <div class="form-tip">选择对游客可见的模块，不选则公开所有已启用模块</div>
          </el-form-item>
                    <el-form-item label="启用HR模式">
            <el-switch v-model="visitorForm.hr_enabled" active-text="启用" inactive-text="禁用" :disabled="!visitorForm.enabled" />
            <div class="form-tip">启用后HR可通过链接使用AI助手</div>
          </el-form-item>
          <el-form-item v-if="visitorForm.hr_enabled" label="AI功能开关">
            <el-switch v-model="visitorForm.ai_enabled" active-text="开启" inactive-text="关闭" :disabled="!visitorForm.enabled" />
          </el-form-item>
          <el-form-item v-if="visitorForm.hr_enabled" label="AI调用配额">
            <el-input-number v-model="visitorForm.ai_quota" :min="1" :max="100" :disabled="!visitorForm.enabled" />
            <span v-if="visitorLink.visitor_hr_enabled" style="margin-left: 12px; color: #909399; font-size: 13px">
              已用: {{ visitorLink.visitor_ai_used || 0 }} / {{ visitorLink.visitor_ai_quota || 10 }}
            </span>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" icon="Check" :loading="visitorSaving" @click="saveVisitorLink">{{ visitorLink.visitor_enabled ? '更新链接设置' : '生成链接' }}</el-button>
            <el-button v-if="visitorLink.visitor_enabled" type="danger" icon="Close" :loading="visitorSaving" @click="disableVisitorLink">禁用链接</el-button>
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
import { ref, computed, reactive, onMounted } from 'vue'
import { resumeApi } from '@/api'
import { ElMessage } from 'element-plus'

const resume = ref(null)
const loading = ref(false)

const visitorLink = ref({ visitor_enabled: false, visitor_token: '', visitor_expires: null, visitor_allow_download: false, public_modules: [], visitor_url: '' })
const visitorSaving = ref(false)
const visitorForm = reactive({ enabled: false, expires_days: 30, allow_download: false, public_modules: [], hr_enabled: false, ai_enabled: true, ai_quota: 10 })

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
  if (!resume.value || !resume.value.skills) return []
  const groups = {}
  resume.value.skills.forEach(s => { const cat = s.category || '其他'; if (!groups[cat]) groups[cat] = []; groups[cat].push(s) })
  return Object.entries(groups).map(([category, items]) => ({ category, items }))
})

function getSkillColor(level) { if (level >= 80) return '#67c23a'; if (level >= 60) return '#409eff'; if (level >= 40) return '#e6a23c'; return '#f56c6c' }
function tagTypeColor(type) { const c = { skill: '', project: 'success', certificate: 'warning', award: 'danger', language: 'info', custom: '' }; return c[type] || '' }
function formatDate(d) { if (!d) return ''; return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }) }

async function copyVisitorUrl() {
  try { await navigator.clipboard.writeText(visitorLink.value.visitor_url); ElMessage.success('链接已复制到剪贴板') }
  catch { const i = document.createElement('input'); i.value = visitorLink.value.visitor_url; document.body.appendChild(i); i.select(); document.execCommand('copy'); document.body.removeChild(i); ElMessage.success('链接已复制到剪贴板') }
}

async function loadVisitorLinkInfo() {
  if (!resume.value || !resume.value.id) return
  try { const info = await resumeApi.visitorLinkInfo(resume.value.id); visitorLink.value = info; visitorForm.enabled = info.visitor_enabled || false; visitorForm.allow_download = info.visitor_allow_download || false; visitorForm.public_modules = info.public_modules || []; visitorForm.hr_enabled = info.visitor_hr_enabled || false; visitorForm.ai_enabled = info.visitor_ai_enabled !== false; visitorForm.ai_quota = info.visitor_ai_quota || 10 } catch (e) {}
}

async function saveVisitorLink() {
  if (!resume.value || !resume.value.id) return
  visitorSaving.value = true
  try { const data = { enabled: visitorForm.enabled, expires_days: visitorForm.expires_days, allow_download: visitorForm.allow_download, public_modules: visitorForm.public_modules, hr_enabled: visitorForm.hr_enabled, ai_enabled: visitorForm.ai_enabled, ai_quota: visitorForm.ai_quota }; const r = await resumeApi.generateVisitorLink(resume.value.id, data); visitorLink.value = r; ElMessage.success(r.visitor_url ? '游客链接已更新' : '设置已保存') }
  catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
  finally { visitorSaving.value = false }
}

async function disableVisitorLink() {
  if (!resume.value || !resume.value.id) return
  visitorSaving.value = true
  try { const r = await resumeApi.disableVisitorLink(resume.value.id); visitorLink.value = r; visitorForm.enabled = false; ElMessage.success('游客链接已禁用') }
  catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
  finally { visitorSaving.value = false }
}

onMounted(async () => {
  loading.value = true
  try { const list = await resumeApi.list(); if (list.results && list.results.length) { resume.value = await resumeApi.detail(list.results[0].id); await loadVisitorLinkInfo() } }
  catch (e) {}
  finally { loading.value = false }
})
</script>

<style scoped>
.resume-header { display: flex; justify-content: space-between; align-items: flex-start; }
.summary { margin-top: 12px; color: #666; line-height: 1.6; }
.section-header { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; }
.project-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }
.project-item h4 { margin-bottom: 4px; }
.skills-grid { display: flex; flex-direction: column; gap: 20px; }
.skill-category { margin-bottom: 10px; color: #333; font-size: 14px; }
.skill-items { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.skill-item { display: flex; flex-direction: column; gap: 4px; }
.skill-name { font-size: 13px; color: #666; }
.module-content { white-space: pre-wrap; line-height: 1.8; color: #333; font-size: 14px; }
.visitor-link-display { margin-bottom: 16px; }
.visitor-url-input { max-width: 100%; }
.form-tip { font-size: 12px; color: #909399; margin-top: 4px; }
</style>
