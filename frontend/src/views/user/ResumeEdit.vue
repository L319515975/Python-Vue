<template>
  <div class="resume-edit">
    <!-- Basic Info Card -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isCreate ? '创建简历' : '编辑简历' }}</span>
          <div style="display: flex; gap: 8px">
            <el-button icon="Download" type="success" @click="showPdfDialog = true" :disabled="!resumeId">
              导出PDF
            </el-button>
            <el-button @click="$router.push('/user')">返回</el-button>
          </div>
        </div>
      </template>

      <el-form :model="form" label-width="100px" style="max-width: 700px">
        <el-divider content-position="left">基本信息</el-divider>
        <el-form-item label="简历标题">
          <el-input v-model="form.title" placeholder="如：张三的简历" />
        </el-form-item>
        <el-form-item label="个人简介">
          <div class="textarea-with-polish">
            <el-input v-model="form.summary" type="textarea" :rows="3" placeholder="简要描述您的职业经历和优势" />
            <el-button
              class="polish-btn"
              size="small"
              type="warning"
              icon="MagicStick"
              @click="openPolish(form.summary, 'summary')"
              :disabled="!form.summary.trim()"
            >
              一键润色
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="draft">草稿</el-radio>
            <el-radio value="published">已发布</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- Tags -->
        <el-divider content-position="left">标签</el-divider>
        <el-form-item label="标签选择">
          <el-select
            v-model="selectedTagIds"
            multiple
            filterable
            placeholder="选择标签（技能、项目类型等）"
            style="width: 100%"
          >
            <el-option-group
              v-for="group in tagGroups"
              :key="group.type"
              :label="group.label"
            >
              <el-option
                v-for="tag in group.tags"
                :key="tag.id"
                :label="tag.name"
                :value="tag.id"
              />
            </el-option-group>
          </el-select>
        </el-form-item>

        <!-- Module Selection -->
        <el-divider content-position="left">模块配置（最多5个可配置模块）</el-divider>
        <el-form-item label="启用模块">
          <el-checkbox-group v-model="selectedModules" :max="5">
            <el-checkbox
              v-for="m in availableModules"
              :key="m.key"
              :value="m.key"
            >
              {{ m.label }}
            </el-checkbox>
          </el-checkbox-group>
          <div class="module-hint">
            已选 {{ selectedModules.length }}/5 个模块（个人信息模块固定包含）
          </div>
        </el-form-item>

        <!-- File Upload -->
        <el-divider content-position="left">简历文件</el-divider>
        <el-form-item label="上传文件">
          <el-upload
            :auto-upload="false"
            :limit="1"
            accept=".pdf,.doc,.docx,.md,.txt"
            :on-change="handleFileChange"
            :file-list="fileList"
          >
            <el-button icon="Upload">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 PDF、Word、Markdown 格式，最大 10MB。上传后AI将自动归类内容。</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="saveResume">保存基本信息</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Education Section -->
    <el-card style="margin-top: 16px" v-if="resumeId">
      <template #header>
        <div class="card-header">
          <span>教育经历</span>
          <el-button type="primary" icon="Plus" size="small" @click="openEduDialog()">添加</el-button>
        </div>
      </template>
      <el-table :data="educations" stripe size="small">
        <el-table-column prop="school" label="学校" />
        <el-table-column prop="degree" label="学位" width="80" />
        <el-table-column prop="major" label="专业" />
        <el-table-column prop="start_date" label="开始" width="110" />
        <el-table-column prop="end_date" label="结束" width="110">
          <template #default="{ row }">{{ row.end_date || '至今' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEduDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除?" @confirm="deleteEducation(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Work Experience Section -->
    <el-card style="margin-top: 16px" v-if="resumeId">
      <template #header>
        <div class="card-header">
          <span>工作经历</span>
          <el-button type="primary" icon="Plus" size="small" @click="openWorkDialog()">添加</el-button>
        </div>
      </template>
      <el-table :data="workExperiences" stripe size="small">
        <el-table-column prop="company" label="公司" />
        <el-table-column prop="position" label="职位" />
        <el-table-column prop="start_date" label="开始" width="110" />
        <el-table-column prop="end_date" label="结束" width="110">
          <template #default="{ row }">{{ row.end_date || '至今' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openWorkDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除?" @confirm="deleteWork(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Project Section -->
    <el-card style="margin-top: 16px" v-if="resumeId">
      <template #header>
        <div class="card-header">
          <span>项目经历</span>
          <el-button type="primary" icon="Plus" size="small" @click="openProjDialog()">添加</el-button>
        </div>
      </template>
      <el-table :data="projects" stripe size="small">
        <el-table-column prop="name" label="项目名称" />
        <el-table-column prop="role" label="角色" width="100" />
        <el-table-column prop="tech_stack" label="技术栈" show-overflow-tooltip />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openProjDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除?" @confirm="deleteProject(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Skills Section -->
    <el-card style="margin-top: 16px" v-if="resumeId">
      <template #header>
        <div class="card-header">
          <span>技能清单</span>
          <el-button type="primary" icon="Plus" size="small" @click="openSkillDialog()">添加</el-button>
        </div>
      </template>
      <div style="display: flex; flex-wrap: wrap; gap: 8px">
        <el-tag
          v-for="skill in skills"
          :key="skill.id"
          closable
          @close="deleteSkill(skill.id)"
          @click="openSkillDialog(skill)"
          style="cursor: pointer"
        >
          {{ skill.name }} ({{ skill.level }}%)
        </el-tag>
        <el-empty v-if="!skills.length" description="暂无技能" :image-size="40" />
      </div>
    </el-card>

    <!-- Module Data Section (certificate, award, language, etc.) -->
    <template v-if="resumeId">
      <el-card
        v-for="mod in moduleDataKeys"
        :key="mod.key"
        style="margin-top: 16px"
      >
        <template #header>
          <div class="card-header">
            <span>{{ mod.label }}</span>
            <el-button
              size="small"
              type="warning"
              icon="MagicStick"
              @click="openPolish(moduleData[mod.key] || '', mod.key)"
              :disabled="!(moduleData[mod.key] || '').trim()"
            >
              一键润色
            </el-button>
          </div>
        </template>
        <el-input
          v-model="moduleData[mod.key]"
          type="textarea"
          :rows="4"
          :placeholder="mod.placeholder"
        />
        <el-button
          type="primary"
          size="small"
          style="margin-top: 8px"
          @click="saveModuleData"
          :loading="savingModules"
        >
          保存{{ mod.label }}
        </el-button>
      </el-card>
    </template>

    <!-- Education Dialog -->
    <el-dialog v-model="eduDialog" :title="editingEdu ? '编辑教育经历' : '添加教育经历'" width="500px">
      <el-form :model="eduForm" label-width="80px">
        <el-form-item label="学校"><el-input v-model="eduForm.school" /></el-form-item>
        <el-form-item label="学位">
          <el-select v-model="eduForm.degree" placeholder="选择学位">
            <el-option v-for="d in ['博士','硕士','学士','专科']" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业"><el-input v-model="eduForm.major" /></el-form-item>
        <el-form-item label="开始日期"><el-date-picker v-model="eduForm.start_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="结束日期"><el-date-picker v-model="eduForm.end_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="eduForm.description" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="eduDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEducation">保存</el-button>
      </template>
    </el-dialog>

    <!-- Work Dialog -->
    <el-dialog v-model="workDialog" :title="editingWork ? '编辑工作经历' : '添加工作经历'" width="500px">
      <el-form :model="workForm" label-width="80px">
        <el-form-item label="公司"><el-input v-model="workForm.company" /></el-form-item>
        <el-form-item label="职位"><el-input v-model="workForm.position" /></el-form-item>
        <el-form-item label="开始日期"><el-date-picker v-model="workForm.start_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="结束日期"><el-date-picker v-model="workForm.end_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="描述">
          <div class="textarea-with-polish">
            <el-input v-model="workForm.description" type="textarea" :rows="3" />
            <el-button class="polish-btn" size="small" type="warning" icon="MagicStick" @click="openPolish(workForm.description, 'work_experience')" :disabled="!workForm.description?.trim()">
              一键润色
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="workDialog = false">取消</el-button>
        <el-button type="primary" @click="saveWork">保存</el-button>
      </template>
    </el-dialog>

    <!-- Project Dialog -->
    <el-dialog v-model="projDialog" :title="editingProj ? '编辑项目' : '添加项目'" width="500px">
      <el-form :model="projForm" label-width="80px">
        <el-form-item label="项目名称"><el-input v-model="projForm.name" /></el-form-item>
        <el-form-item label="角色"><el-input v-model="projForm.role" /></el-form-item>
        <el-form-item label="开始日期"><el-date-picker v-model="projForm.start_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="结束日期"><el-date-picker v-model="projForm.end_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="技术栈"><el-input v-model="projForm.tech_stack" placeholder="用逗号分隔" /></el-form-item>
        <el-form-item label="描述">
          <div class="textarea-with-polish">
            <el-input v-model="projForm.description" type="textarea" :rows="3" />
            <el-button class="polish-btn" size="small" type="warning" icon="MagicStick" @click="openPolish(projForm.description, 'project')" :disabled="!projForm.description?.trim()">
              一键润色
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="projDialog = false">取消</el-button>
        <el-button type="primary" @click="saveProject">保存</el-button>
      </template>
    </el-dialog>

    <!-- Skill Dialog -->
    <el-dialog v-model="skillDialog" :title="editingSkill ? '编辑技能' : '添加技能'" width="400px">
      <el-form :model="skillForm" label-width="80px">
        <el-form-item label="技能名称"><el-input v-model="skillForm.name" /></el-form-item>
        <el-form-item label="熟练度">
          <el-slider v-model="skillForm.level" :max="100" show-input />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="skillForm.category" placeholder="如：编程语言、前端框架" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="skillDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSkill">保存</el-button>
      </template>
    </el-dialog>

    <!-- PDF Export Dialog -->
    <el-dialog v-model="showPdfDialog" title="导出PDF简历" width="450px">
      <p style="margin-bottom: 12px; color: #666">选择要包含的模块（个人信息模块自动包含）：</p>
      <el-checkbox-group v-model="pdfModules">
        <el-checkbox
          v-for="m in availableModules"
          :key="m.key"
          :value="m.key"
          style="display: block; margin-bottom: 8px"
        >
          {{ m.label }}
        </el-checkbox>
      </el-checkbox-group>
      <div v-if="pdfModules.length === 0" style="color: #f56c6c; font-size: 12px; margin-top: 4px">
        请至少选择1个模块
      </div>
      <template #footer>
        <el-button @click="showPdfDialog = false">取消</el-button>
        <el-button type="primary" @click="exportPdf" :loading="exporting" :disabled="pdfModules.length === 0">
          导出
        </el-button>
      </template>
    </el-dialog>

    <!-- Polish Dialog -->
    <PolishDialog
      v-model="showPolishDialog"
      :text="polishTarget.text"
      :module-name="polishTarget.moduleName"
      @accept="handlePolishAccept"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { resumeApi, educationApi, workApi, projectApi, skillApi, tagApi } from '@/api'
import { ElMessage } from 'element-plus'
import PolishDialog from '@/components/PolishDialog.vue'

const resumeId = ref(null)
const isCreate = ref(true)
const saving = ref(false)
const savingModules = ref(false)
const exporting = ref(false)
const fileList = ref([])
const uploadFile = ref(null)

const form = ref({ title: '我的简历', summary: '', status: 'draft' })

const educations = ref([])
const workExperiences = ref([])
const projects = ref([])
const skills = ref([])
const allTags = ref([])
const selectedTagIds = ref([])
const selectedModules = ref([])
const moduleData = ref({})

// Dialogs
const eduDialog = ref(false)
const workDialog = ref(false)
const projDialog = ref(false)
const skillDialog = ref(false)
const editingEdu = ref(null)
const editingWork = ref(null)
const editingProj = ref(null)
const editingSkill = ref(null)
const showPdfDialog = ref(false)
const pdfModules = ref([])

const eduForm = ref({ school: '', degree: '学士', major: '', start_date: '', end_date: '', description: '' })
const workForm = ref({ company: '', position: '', start_date: '', end_date: '', description: '' })
const projForm = ref({ name: '', role: '', start_date: '', end_date: '', tech_stack: '', description: '' })
const skillForm = ref({ name: '', level: 50, category: '其他' })

// Polish dialog state
const showPolishDialog = ref(false)
const polishTarget = reactive({ text: '', moduleName: '', field: null })

const availableModules = [
  { key: 'education', label: '教育经历' },
  { key: 'work_experience', label: '工作经历' },
  { key: 'project', label: '项目经历' },
  { key: 'skill', label: '技能' },
  { key: 'certificate', label: '证书' },
  { key: 'award', label: '获奖' },
  { key: 'language', label: '语言能力' },
]

const moduleDataKeys = computed(() => {
  const dataModules = [
    { key: 'certificate', label: '证书', placeholder: '请输入持有的证书，每行一个' },
    { key: 'award', label: '获奖', placeholder: '请输入获奖信息，每行一个' },
    { key: 'language', label: '语言能力', placeholder: '请输入语言能力描述' },
  ]
  return dataModules.filter(m => selectedModules.value.includes(m.key))
})

const tagGroups = computed(() => {
  const groups = {}
  allTags.value.forEach(tag => {
    if (!groups[tag.tag_type]) groups[tag.tag_type] = []
    groups[tag.tag_type].push(tag)
  })
  const typeLabels = {
    skill: '技能', project: '项目', certificate: '证书',
    award: '获奖', language: '语言', custom: '自定义',
  }
  return Object.entries(groups).map(([type, tags]) => ({
    type,
    label: typeLabels[type] || type,
    tags,
  }))
})

function handleFileChange(file) {
  uploadFile.value = file.raw
}

function openPolish(text, moduleName) {
  polishTarget.text = text
  polishTarget.moduleName = moduleName
  showPolishDialog.value = true
}

function handlePolishAccept(polishedText) {
  // Apply polished text to the correct field
  const target = polishTarget.moduleName
  if (target === 'summary') {
    form.value.summary = polishedText
  } else if (target === 'work_experience') {
    workForm.value.description = polishedText
  } else if (target === 'project') {
    projForm.value.description = polishedText
  } else if (moduleData.value.hasOwnProperty(target)) {
    moduleData.value[target] = polishedText
  }
  ElMessage.success('已采纳润色结果')
}

async function loadAllTags() {
  try {
    const data = await tagApi.list({ page_size: 200 })
    allTags.value = data.results || data || []
  } catch { /* */ }
}

async function loadResume() {
  try {
    const list = await resumeApi.list()
    if (list.results?.length) {
      const resume = await resumeApi.detail(list.results[0].id)
      resumeId.value = resume.id
      isCreate.value = false
      form.value = { title: resume.title, summary: resume.summary, status: resume.status }
      educations.value = resume.educations || []
      workExperiences.value = resume.work_experiences || []
      projects.value = resume.projects || []
      skills.value = resume.skills || []
      selectedTagIds.value = (resume.tags_detail || []).map(t => t.id)
      selectedModules.value = resume.enabled_modules || []
      moduleData.value = resume.module_data || {}
    }
  } catch { /* */ }
}

async function saveResume() {
  saving.value = true
  try {
    const payload = {
      ...form.value,
      tags: selectedTagIds.value,
      enabled_modules: selectedModules.value,
    }

    if (isCreate.value) {
      const data = await resumeApi.create(payload)
      resumeId.value = data.id
      isCreate.value = false
      ElMessage.success('简历创建成功')
    } else {
      await resumeApi.update(resumeId.value, payload)
      ElMessage.success('基本信息已保存')
    }

    // Upload file if selected
    if (uploadFile.value && resumeId.value) {
      const fd = new FormData()
      fd.append('file', uploadFile.value)
      fd.append('auto_classify', 'true')
      await resumeApi.uploadFile(resumeId.value, fd)
      ElMessage.success('文件上传成功，AI正在自动归类内容...')
      uploadFile.value = null
      fileList.value = []
      // Reload to get classified data
      await loadResume()
    }
  } catch { /* */ } finally {
    saving.value = false
  }
}

async function saveModuleData() {
  savingModules.value = true
  try {
    await resumeApi.updateModules(resumeId.value, {
      enabled_modules: selectedModules.value,
      module_data: moduleData.value,
    })
    ElMessage.success('模块数据已保存')
  } catch { /* */ } finally {
    savingModules.value = false
  }
}

async function exportPdf() {
  if (pdfModules.value.length === 0) {
    ElMessage.warning('请至少选择1个模块')
    return
  }
  exporting.value = true
  try {
    const blob = await resumeApi.exportPdf(resumeId.value, pdfModules.value)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `resume_${form.value.title || 'export'}.pdf`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('PDF导出成功')
    showPdfDialog.value = false
  } catch { /* */ } finally {
    exporting.value = false
  }
}

// Education CRUD
function openEduDialog(item = null) {
  editingEdu.value = item
  eduForm.value = item ? { ...item } : { school: '', degree: '学士', major: '', start_date: '', end_date: '', description: '', resume: resumeId.value }
  eduDialog.value = true
}
async function saveEducation() {
  try {
    eduForm.value.resume = resumeId.value
    if (editingEdu.value) {
      await educationApi.update(editingEdu.value.id, eduForm.value)
    } else {
      await educationApi.create(eduForm.value)
    }
    ElMessage.success('保存成功')
    eduDialog.value = false
    await loadResume()
  } catch { /* */ }
}
async function deleteEducation(id) {
  await educationApi.delete(id)
  ElMessage.success('删除成功')
  await loadResume()
}

// Work CRUD
function openWorkDialog(item = null) {
  editingWork.value = item
  workForm.value = item ? { ...item } : { company: '', position: '', start_date: '', end_date: '', description: '', resume: resumeId.value }
  workDialog.value = true
}
async function saveWork() {
  try {
    workForm.value.resume = resumeId.value
    if (editingWork.value) {
      await workApi.update(editingWork.value.id, workForm.value)
    } else {
      await workApi.create(workForm.value)
    }
    ElMessage.success('保存成功')
    workDialog.value = false
    await loadResume()
  } catch { /* */ }
}
async function deleteWork(id) {
  await workApi.delete(id)
  ElMessage.success('删除成功')
  await loadResume()
}

// Project CRUD
function openProjDialog(item = null) {
  editingProj.value = item
  projForm.value = item ? { ...item } : { name: '', role: '', start_date: '', end_date: '', tech_stack: '', description: '', resume: resumeId.value }
  projDialog.value = true
}
async function saveProject() {
  try {
    projForm.value.resume = resumeId.value
    if (editingProj.value) {
      await projectApi.update(editingProj.value.id, projForm.value)
    } else {
      await projectApi.create(projForm.value)
    }
    ElMessage.success('保存成功')
    projDialog.value = false
    await loadResume()
  } catch { /* */ }
}
async function deleteProject(id) {
  await projectApi.delete(id)
  ElMessage.success('删除成功')
  await loadResume()
}

// Skill CRUD
function openSkillDialog(item = null) {
  editingSkill.value = item
  skillForm.value = item ? { ...item } : { name: '', level: 50, category: '其他', resume: resumeId.value }
  skillDialog.value = true
}
async function saveSkill() {
  try {
    skillForm.value.resume = resumeId.value
    if (editingSkill.value) {
      await skillApi.update(editingSkill.value.id, skillForm.value)
    } else {
      await skillApi.create(skillForm.value)
    }
    ElMessage.success('保存成功')
    skillDialog.value = false
    await loadResume()
  } catch { /* */ }
}
async function deleteSkill(id) {
  await skillApi.delete(id)
  ElMessage.success('删除成功')
  await loadResume()
}

onMounted(async () => {
  await Promise.all([loadAllTags(), loadResume()])
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.textarea-with-polish {
  position: relative;
  width: 100%;
}

.polish-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  z-index: 1;
}

.module-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
</style>
