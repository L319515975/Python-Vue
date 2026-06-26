<!-- ============================================================
  文件：ResumeDetail.vue
  作用：用户简历详情页（查看自己的完整简历）
  说明：
    - 登录用户进入"我的简历"页面后看到此页面
    - 展示简历的所有模块：教育经历、工作经历、项目、技能等
    - 包含"访客分享链接"管理功能：
      * 生成/禁用访客链接
      * 设置有效期、公开模块、允许下载
      * 启用 HR 模式（HR 可使用 AI 助手）
      * 设置 AI 调用配额
    - 点击"编辑简历"按钮跳转到 ResumeEdit.vue
  关键 Vue 3 知识点：
    - ref()：创建响应式变量
    - computed()：计算属性（如 groupedSkills 按分类分组技能）
    - reactive()：创建响应式对象（如 visitorForm 表单数据）
    - onMounted()：页面加载时自动执行的钩子
    - v-loading：加载遮罩
    - el-timeline：Element Plus 时间线组件
    - el-switch：开关组件
    - el-checkbox-group：多选框组
    - el-input-number：数字输入框
============================================================ -->
<template>
  <!-- 最外层容器，v-loading 控制加载遮罩 -->
  <div class="resume-detail" v-loading="loading">
    <template v-if="resume">

      <!-- ========== 简历头部卡片：标题 + 状态 + 操作按钮 ========== -->
      <el-card class="resume-header-card">
        <div class="resume-header">
          <div>
            <h2 class="resume-title">{{ resume.title }}</h2>
            <div class="resume-badges">
              <!-- 根据 status 显示"已发布"或"草稿"标签 -->
              <el-tag :type="resume.status === 'published' ? 'success' : 'info'" size="small">
                {{ resume.status === 'published' ? '已发布' : '草稿' }}
              </el-tag>
              <!-- 如果 AI 已处理过简历内容，显示黄色标签 -->
              <el-tag v-if="resume.ai_processed" type="warning" size="small">AI已处理</el-tag>
            </div>
          </div>
          <!-- 点击跳转到编辑页面 -->
          <el-button type="primary" icon="Edit" @click="$router.push('/user/edit')">编辑简历</el-button>
        </div>
        <!-- 个人简介 -->
        <p v-if="resume.summary" class="summary">{{ resume.summary }}</p>
        <!-- 标签列表：显示技能、项目类型等标签 -->
        <div v-if="resume.tags_detail && resume.tags_detail.length" class="resume-tags-row">
          <el-tag v-for="tag in resume.tags_detail" :key="tag.id" :type="tagTypeColor(tag.tag_type)" size="small" class="resume-tag-item">{{ tag.name }}</el-tag>
        </div>
      </el-card>

      <!-- ========== 教育经历卡片 ========== -->
      <!-- 使用 el-timeline 时间线组件展示教育经历 -->
      <el-card class="section-card">
        <template #header><div class="section-header"><el-icon><School /></el-icon><span>教育经历</span></div></template>
        <el-timeline v-if="resume.educations && resume.educations.length">
          <!--
            el-timeline-item：时间线条目
            - timestamp：显示时间范围
            - placement="top"：时间戳显示在顶部
          -->
          <el-timeline-item v-for="edu in resume.educations" :key="edu.id" :timestamp="edu.start_date + ' ~ ' + (edu.end_date || '至今')" placement="top">
            <el-card shadow="never" class="timeline-card">
              <h4 class="timeline-card-title">{{ edu.school }}</h4>
              <p class="timeline-card-sub">{{ edu.degree }} | {{ edu.major }}</p>
              <p v-if="edu.description" class="timeline-card-desc">{{ edu.description }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
        <!-- 没有数据时显示空状态 -->
        <el-empty v-else description="暂无教育经历" :image-size="80" />
      </el-card>

      <!-- ========== 工作经历卡片 ========== -->
      <el-card class="section-card">
        <template #header><div class="section-header"><el-icon><OfficeBuilding /></el-icon><span>工作经历</span></div></template>
        <el-timeline v-if="resume.work_experiences && resume.work_experiences.length">
          <el-timeline-item v-for="work in resume.work_experiences" :key="work.id" :timestamp="work.start_date + ' ~ ' + (work.end_date || '至今')" placement="top">
            <el-card shadow="never" class="timeline-card">
              <h4 class="timeline-card-title">{{ work.company }}</h4>
              <p class="work-position">{{ work.position }}</p>
              <p v-if="work.description" class="timeline-card-desc work-desc">{{ work.description }}</p>
            </el-card>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-else description="暂无工作经历" :image-size="80" />
      </el-card>

      <!-- ========== 项目经历卡片 ========== -->
      <!-- 用网格布局展示项目卡片 -->
      <el-card class="section-card">
        <template #header><div class="section-header"><el-icon><FolderOpened /></el-icon><span>项目经历</span></div></template>
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

      <!-- ========== 技能清单卡片 ========== -->
      <!-- 技能按分类（category）分组显示，每组内用进度条展示熟练度 -->
      <el-card class="section-card">
        <template #header><div class="section-header"><el-icon><TrendCharts /></el-icon><span>技能清单</span></div></template>
        <div v-if="resume.skills && resume.skills.length" class="skills-grid">
          <!--
            groupedSkills 是 computed 计算属性：
            将技能数组按 category 分组，返回 [{ category, items }] 结构
          -->
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

      <!-- ========== 动态模块（证书、获奖、语言能力） ========== -->
      <!--
        resume.module_data 是一个对象，key 是模块名，value 是文本内容
        moduleLabels 和 moduleIcons 定义了模块的中文名和图标
        只渲染有数据且有对应标签定义的模块
      -->
      <template v-for="(content, key) in resume.module_data" :key="key">
        <el-card v-if="content && moduleLabels[key]" class="section-card">
          <template #header><div class="section-header"><el-icon><component :is="moduleIcons[key] || 'Document'" /></el-icon><span>{{ moduleLabels[key] }}</span></div></template>
          <div class="module-content">{{ content }}</div>
        </el-card>
      </template>

      <!-- ========== 附件下载 ========== -->
      <el-card v-if="resume.file" class="section-card">
        <template #header><span>附件</span></template>
        <el-link :href="resume.file" target="_blank" type="primary" icon="Download">{{ resume.file_name || '下载简历文件' }}</el-link>
      </el-card>

      <!-- ========== 访客分享链接管理 ========== -->
      <!--
        这是此页面最复杂的部分：
        1. 显示当前访客链接状态（已启用/未启用）
        2. 提供链接配置表单：
           - 启用/禁用访客链接
           - 设置有效期（天数）
           - 是否允许下载 PDF
           - 选择公开哪些模块给访客看
           - 启用 HR 模式（HR 可使用 AI 助手）
           - AI 功能开关和调用配额
        3. 一键复制链接功能
      -->
      <el-card class="section-card">
        <template #header>
          <div class="section-header">
            <el-icon><Share /></el-icon>
            <span>访客分享链接</span>
            <!-- 根据是否启用显示绿色/灰色标签 -->
            <el-tag v-if="visitorLink.visitor_enabled" type="success" size="small" class="status-tag">已启用</el-tag>
            <el-tag v-else type="info" size="small" class="status-tag">未启用</el-tag>
          </div>
        </template>

        <!-- 已启用时显示链接地址和复制按钮 -->
        <div v-if="visitorLink.visitor_enabled && visitorLink.visitor_url" class="visitor-link-display">
          <el-alert type="success" :closable="false" show-icon class="visitor-alert">
            <template #title>访客可通过以下链接查看您的公开简历模块</template>
            <template #default v-if="visitorLink.visitor_expires">有效期至: {{ formatDate(visitorLink.visitor_expires) }}</template>
          </el-alert>
          <!-- 链接输入框（只读），右侧有复制按钮 -->
          <el-input :model-value="visitorLink.visitor_url" readonly class="visitor-url-input">
            <template #append><el-button icon="CopyDocument" @click="copyVisitorUrl">复制链接</el-button></template>
          </el-input>
        </div>

        <el-divider />

        <!-- 访客链接配置表单 -->
        <el-form label-width="120px" size="default" class="visitor-form">
          <!-- 启用/禁用开关 -->
          <el-form-item label="启用访客链接">
            <el-switch v-model="visitorForm.enabled" active-text="启用" inactive-text="禁用" />
          </el-form-item>
          <!-- 有效期天数 -->
          <el-form-item label="有效期（天）">
            <el-input-number v-model="visitorForm.expires_days" :min="1" :max="365" :disabled="!visitorForm.enabled" />
          </el-form-item>
          <!-- 是否允许下载 PDF -->
          <el-form-item label="允许下载PDF">
            <el-switch v-model="visitorForm.allow_download" active-text="允许" inactive-text="禁止" :disabled="!visitorForm.enabled" />
          </el-form-item>
          <!-- 公开模块选择：哪些模块对访客可见 -->
          <el-form-item label="公开模块">
            <el-checkbox-group v-model="visitorForm.public_modules" :disabled="!visitorForm.enabled">
              <el-checkbox v-for="mod in availableModules" :key="mod.value" :label="mod.value">{{ mod.label }}</el-checkbox>
            </el-checkbox-group>
            <div class="form-tip">选择对访客可见的模块，不选则公开所有已启用模块</div>
          </el-form-item>
          <!-- HR 模式：启用后 HR 可使用 AI 助手 -->
          <el-form-item label="启用HR模式">
            <el-switch v-model="visitorForm.hr_enabled" active-text="启用" inactive-text="禁用" :disabled="!visitorForm.enabled" />
            <div class="form-tip">启用后HR可通过链接使用AI助手</div>
          </el-form-item>
          <!-- AI 功能开关（仅 HR 模式启用时显示） -->
          <el-form-item v-if="visitorForm.hr_enabled" label="AI功能开关">
            <el-switch v-model="visitorForm.ai_enabled" active-text="开启" inactive-text="关闭" :disabled="!visitorForm.enabled" />
          </el-form-item>
          <!-- AI 调用配额（仅 HR 模式启用时显示） -->
          <el-form-item v-if="visitorForm.hr_enabled" label="AI调用配额">
            <el-input-number v-model="visitorForm.ai_quota" :min="1" :max="100" :disabled="!visitorForm.enabled" />
            <!-- 显示已用/总数配额 -->
            <span v-if="visitorLink.visitor_hr_enabled" class="quota-usage">
              已用: {{ visitorLink.visitor_ai_used || 0 }} / {{ visitorLink.visitor_ai_quota || 10 }}
            </span>
          </el-form-item>
          <!-- 提交按钮 -->
          <el-form-item>
            <el-button type="primary" icon="Check" :loading="visitorSaving" @click="saveVisitorLink">{{ visitorLink.visitor_enabled ? '更新链接设置' : '生成链接' }}</el-button>
            <el-button v-if="visitorLink.visitor_enabled" type="danger" icon="Close" :loading="visitorSaving" @click="disableVisitorLink">禁用链接</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </template>

    <!-- 没有简历时的空状态 -->
    <el-empty v-else-if="!loading" description="暂无简历信息">
      <el-button type="primary" @click="$router.push('/user/edit')">创建简历</el-button>
    </el-empty>
  </div>
</template>

<script setup>
// ==================== 导入依赖 ====================
// ref：响应式变量, computed：计算属性, reactive：响应式对象, onMounted：生命周期钩子
import { ref, computed, reactive, onMounted } from 'vue'
// resumeApi：简历相关的 API 请求函数
import { resumeApi } from '@/api'
// ElMessage：Element Plus 消息提示
import { ElMessage } from 'element-plus'

// ==================== 简历数据和加载状态 ====================
// 简历数据对象（包含所有模块数据）
const resume = ref(null)
const loading = ref(false)

// ==================== 访客链接相关状态 ====================
// visitorLink：存储从后端获取的访客链接信息
// 包含：是否启用、token、过期时间、允许下载、公开模块、URL等
const visitorLink = ref({
  visitor_enabled: false,
  visitor_token: '',
  visitor_expires: null,
  visitor_allow_download: false,
  public_modules: [],
  visitor_url: ''
})
// 保存访客链接设置时的加载状态
const visitorSaving = ref(false)

// ==================== 访客链接配置表单 ====================
// reactive() 创建响应式对象：对象内任何属性变化都会触发页面更新
// 适合用于表单数据，因为表单通常有多个相关联的字段
const visitorForm = reactive({
  enabled: false,         // 是否启用访客链接
  expires_days: 30,       // 有效期天数
  allow_download: false,  // 是否允许下载 PDF
  public_modules: [],     // 公开的模块列表
  hr_enabled: false,      // 是否启用 HR 模式
  ai_enabled: true,       // AI 功能是否开启
  ai_quota: 10            // AI 调用配额
})

// ==================== 静态配置数据 ====================
// 模块中文名映射：key -> 中文标签
const moduleLabels = { certificate: '证书', award: '获奖荣誉', language: '语言能力' }
// 模块图标映射：key -> Element Plus 图标组件名
const moduleIcons = { certificate: 'Stamp', award: 'Trophy', language: 'ChatLineRound' }

// 可选的公开模块列表（用于访客链接配置中的多选框）
const availableModules = [
  { value: 'education', label: '教育经历' },
  { value: 'work_experience', label: '工作经历' },
  { value: 'project', label: '项目经历' },
  { value: 'skill', label: '技能清单' },
  { value: 'certificate', label: '证书' },
  { value: 'award', label: '获奖荣誉' },
  { value: 'language', label: '语言能力' },
]

// ==================== 计算属性 ====================

/**
 * 将技能列表按分类（category）分组
 *
 * 输入：skills = [{ name: 'Vue', level: 90, category: '前端' }, { name: 'Python', level: 80, category: '后端' }]
 * 输出：[{ category: '前端', items: [{ name: 'Vue', ... }] }, { category: '后端', items: [{ name: 'Python', ... }] }]
 *
 * computed() 会自动追踪 resume.value.skills 的变化
 * 当技能数据变化时，分组结果会自动更新
 */
const groupedSkills = computed(() => {
  if (!resume.value || !resume.value.skills) return []
  const groups = {}
  // 遍历技能数组，按 category 分组
  resume.value.skills.forEach(s => {
    const cat = s.category || '其他'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(s)
  })
  // 将分组对象转为数组格式
  return Object.entries(groups).map(([category, items]) => ({ category, items }))
})

// ==================== 工具函数 ====================

/**
 * 根据技能熟练度返回进度条颜色
 * 绿色(>=80) -> 蓝色(>=60) -> 橙色(>=40) -> 红色(<40)
 */
function getSkillColor(level) {
  if (level >= 80) return '#67c23a'
  if (level >= 60) return '#409eff'
  if (level >= 40) return '#e6a23c'
  return '#f56c6c'
}

/**
 * 根据标签类型返回 Element Plus 标签颜色
 */
function tagTypeColor(type) {
  const c = { skill: '', project: 'success', certificate: 'warning', award: 'danger', language: 'info', custom: '' }
  return c[type] || ''
}

/**
 * 格式化日期为中文格式
 * 例如：2024-01-15 -> "2024年1月15日"
 * @param {string} d - ISO 格式的日期字符串
 * @returns {string} 中文格式的日期
 */
function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

// ==================== 访客链接管理函数 ====================

/**
 * 复制访客链接到剪贴板
 * 优先使用现代 Clipboard API，如果不支持则降级使用 document.execCommand
 */
async function copyVisitorUrl() {
  try {
    // 现代 API：navigator.clipboard.writeText()
    await navigator.clipboard.writeText(visitorLink.value.visitor_url)
    ElMessage.success('链接已复制到剪贴板')
  } catch {
    // 降级方案：创建临时 input 元素 -> 选中 -> 复制 -> 移除
    const i = document.createElement('input')
    i.value = visitorLink.value.visitor_url
    document.body.appendChild(i)
    i.select()
    document.execCommand('copy')
    document.body.removeChild(i)
    ElMessage.success('链接已复制到剪贴板')
  }
}

/**
 * 加载访客链接信息
 * 从后端获取当前简历的访客链接配置，并同步到表单
 */
async function loadVisitorLinkInfo() {
  if (!resume.value || !resume.value.id) return
  try {
    const info = await resumeApi.visitorLinkInfo(resume.value.id)
    // 更新链接信息
    visitorLink.value = info
    // 将后端数据同步到表单（用于编辑）
    visitorForm.enabled = info.visitor_enabled || false
    visitorForm.allow_download = info.visitor_allow_download || false
    visitorForm.public_modules = info.public_modules || []
    visitorForm.hr_enabled = info.visitor_hr_enabled || false
    visitorForm.ai_enabled = info.visitor_ai_enabled !== false
    visitorForm.ai_quota = info.visitor_ai_quota || 10
  } catch (e) {
    // 静默失败，不影响页面展示
  }
}

/**
 * 保存（生成/更新）访客链接
 * 将表单数据发送到后端，后端会生成或更新访客链接
 */
async function saveVisitorLink() {
  if (!resume.value || !resume.value.id) return
  visitorSaving.value = true
  try {
    const data = {
      enabled: visitorForm.enabled,
      expires_days: visitorForm.expires_days,
      allow_download: visitorForm.allow_download,
      public_modules: visitorForm.public_modules,
      hr_enabled: visitorForm.hr_enabled,
      ai_enabled: visitorForm.ai_enabled,
      ai_quota: visitorForm.ai_quota
    }
    const r = await resumeApi.generateVisitorLink(resume.value.id, data)
    visitorLink.value = r
    ElMessage.success(r.visitor_url ? '访客链接已更新' : '设置已保存')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    visitorSaving.value = false
  }
}

/**
 * 禁用访客链接
 * 调用后端 API 禁用链接，然后更新前端状态
 */
async function disableVisitorLink() {
  if (!resume.value || !resume.value.id) return
  visitorSaving.value = true
  try {
    const r = await resumeApi.disableVisitorLink(resume.value.id)
    visitorLink.value = r
    visitorForm.enabled = false
    ElMessage.success('访客链接已禁用')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    visitorSaving.value = false
  }
}

// ==================== 生命周期钩子 ====================

/**
 * onMounted：页面加载时自动执行
 * 流程：
 * 1. 调用 resumeApi.list() 获取简历列表
 * 2. 取第一条简历的 ID，调用 resumeApi.detail() 获取详情
 * 3. 加载访客链接信息
 */
onMounted(async () => {
  loading.value = true
  try {
    const list = await resumeApi.list()
    if (list.results && list.results.length) {
      // 获取第一条简历的完整详情
      resume.value = await resumeApi.detail(list.results[0].id)
      // 加载访客链接配置
      await loadVisitorLinkInfo()
    }
  } catch (e) {
    // 静默失败，页面会显示空状态
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.resume-header { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; }
.resume-title { margin: 0 0 8px 0; }
.resume-badges { display: flex; gap: 8px; align-items: center; margin-top: 8px; }
.summary { margin-top: 12px; color: #666; line-height: 1.6; }
.resume-tags-row { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 6px; }
.resume-tag-item { margin: 0; }
.section-card { margin-top: 16px; }
.section-header { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; }
.status-tag { margin-left: 8px; }

/* Timeline cards */
.timeline-card :deep(.el-card__body) { padding: 16px; }
.timeline-card-title { margin: 0 0 4px 0; font-size: 16px; }
.timeline-card-sub { margin: 0; color: #606266; }
.timeline-card-desc { color: #666; margin-top: 8px; line-height: 1.6; white-space: pre-wrap; }
.work-position { color: #409eff; margin: 0; font-weight: 500; }
.work-desc { white-space: pre-wrap; }

/* Project list */
.project-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.project-item-title { margin: 0 0 4px 0; }
.project-role-tag { margin: 4px 0; }
.project-tech { color: #67c23a; font-size: 13px; margin: 4px 0; }
.project-desc { color: #666; font-size: 13px; margin-top: 8px; line-height: 1.6; }

/* Skills */
.skills-grid { display: flex; flex-direction: column; gap: 20px; }
.skill-category { margin-bottom: 10px; color: #333; font-size: 14px; }
.skill-items { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.skill-item { display: flex; flex-direction: column; gap: 4px; }
.skill-name { font-size: 13px; color: #666; }

/* Module content */
.module-content { white-space: pre-wrap; line-height: 1.8; color: #333; font-size: 14px; }

/* Visitor link section */
.visitor-link-display { margin-bottom: 16px; }
.visitor-alert { margin-bottom: 16px; }
.visitor-url-input { max-width: 100%; }
.visitor-form { max-width: 600px; }
.form-tip { font-size: 12px; color: #909399; margin-top: 4px; }
.quota-usage { margin-left: 12px; color: #909399; font-size: 13px; }

@media (max-width: 768px) {
  .resume-header { flex-direction: column; }
  .project-list { grid-template-columns: 1fr; }
  .skill-items { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
}
</style>