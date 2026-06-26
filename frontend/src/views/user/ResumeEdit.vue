<!-- ============================================================
  文件：ResumeEdit.vue
  作用：简历编辑页面（创建/编辑简历及其所有子模块）
  说明：
    - 这是整个系统中最复杂的页面，包含：
      1. 基本信息编辑（标题、简介、状态、标签、模块配置）
      2. 子模块 CRUD（教育经历、工作经历、项目、技能）
      3. 文本模块编辑（证书、获奖、语言能力，带 AI 润色）
      4. 文件上传（AI 自动归类内容）
      5. PDF 导出（选择要包含的模块）
      6. AI 一键润色（PolishDialog 组件）
    - 每个子模块都有独立的弹窗（Dialog）用于新增和编辑
    - 保存时会根据 isCreate 判断是创建还是更新
  关键 Vue 3 知识点：
    - ref()：创建响应式变量（如 form, educations 等）
    - computed()：计算属性（如 tagGroups, moduleDataKeys）
    - reactive()：创建响应式对象（如 polishTarget）
    - onMounted()：生命周期钩子
    - Promise.all()：并发执行多个异步请求
    - el-dialog：弹窗组件（用于新增/编辑子模块）
    - el-table：表格组件（展示子模块列表）
    - el-popconfirm：气泡确认框（删除确认）
    - el-upload：文件上传组件
    - el-checkbox-group：多选框组（模块选择）
    - el-slider：滑块组件（技能熟练度）
============================================================ -->
<template>
  <div class="resume-edit">
    <!-- ========== 基本信息卡片 ========== -->
    <el-card>
      <template #header>
        <div class="card-header">
          <!-- 根据创建/编辑模式显示不同标题 -->
          <span>{{ isCreate ? '创建简历' : '编辑简历' }}</span>
          <div class="header-actions">
            <!-- 导出PDF按钮（需先保存简历后才能使用） -->
            <el-button icon="Download" type="success" @click="showPdfDialog = true" :disabled="!resumeId">
              导出PDF
            </el-button>
            <el-button @click="$router.push('/user')">返回</el-button>
          </div>
        </div>
      </template>

      <el-form :model="form" label-width="100px" class="edit-form">
        <!-- ===== 基本信息区 ===== -->
        <el-divider content-position="left">基本信息</el-divider>
        <el-form-item label="简历标题">
          <el-input v-model="form.title" placeholder="如：张三的简历" />
        </el-form-item>
        <el-form-item label="个人简介">
          <!-- 个人简介输入框 + AI润色按钮 -->
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
          <!-- 草稿/已发布 单选 -->
          <el-radio-group v-model="form.status">
            <el-radio value="draft">草稿</el-radio>
            <el-radio value="published">已发布</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- ===== 标签选择区 ===== -->
        <el-divider content-position="left">标签</el-divider>
        <el-form-item label="标签选择">
          <!--
            el-select + multiple + filterable：
            多选下拉框，支持搜索过滤
            el-option-group：按标签类型分组显示
          -->
          <el-select
            v-model="selectedTagIds"
            multiple
            filterable
            placeholder="选择标签（技能、项目类型等）"
            class="full-width"
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

        <!-- ===== 模块配置区 ===== -->
        <el-divider content-position="left">模块配置（最多5个可配置模块）</el-divider>
        <el-form-item label="启用模块">
          <!--
            el-checkbox-group + :max="5"：
            多选框组，最多选择5个模块
            个人信息模块（教育、工作等）是固定包含的，不需要选择
          -->
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

        <!-- ===== 文件上传区 ===== -->
        <el-divider content-position="left">简历文件</el-divider>
        <el-form-item label="上传文件">
          <!--
            el-upload 文件上传组件：
            - :auto-upload="false"：不自动上传，等用户点击"保存"时一起上传
            - :limit="1"：只允许上传1个文件
            - accept：限制文件类型
            - :on-change：文件选择变化时的回调
          -->
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

    <!-- ========== 教育经历管理卡片 ========== -->
    <!-- 只有简历已保存（有 resumeId）后才显示子模块管理 -->
    <el-card class="section-card" v-if="resumeId">
      <template #header>
        <div class="card-header">
          <span>教育经历</span>
          <el-button type="primary" icon="Plus" size="small" @click="openEduDialog()">添加</el-button>
        </div>
      </template>
      <!--
        el-table：表格组件展示教育经历列表
        - stripe：斑马纹
        - size="small"：紧凑模式
        - 操作列：编辑和删除按钮
      -->
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
            <!-- el-popconfirm：点击删除时弹出确认气泡 -->
            <el-popconfirm title="确认删除?" @confirm="deleteEducation(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ========== 工作经历管理卡片 ========== -->
    <el-card class="section-card" v-if="resumeId">
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

    <!-- ========== 项目经历管理卡片 ========== -->
    <el-card class="section-card" v-if="resumeId">
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

    <!-- ========== 技能管理卡片 ========== -->
    <!-- 技能用标签（tag）展示，点击可编辑，关闭可删除 -->
    <el-card class="section-card" v-if="resumeId">
      <template #header>
        <div class="card-header">
          <span>技能清单</span>
          <el-button type="primary" icon="Plus" size="small" @click="openSkillDialog()">添加</el-button>
        </div>
      </template>
      <div class="tag-list">
        <el-tag
          v-for="skill in skills"
          :key="skill.id"
          closable
          @close="deleteSkill(skill.id)"
          @click="openSkillDialog(skill)"
          class="clickable"
        >
          {{ skill.name }} ({{ skill.level }}%)
        </el-tag>
        <el-empty v-if="!skills.length" description="暂无技能" :image-size="40" />
      </div>
    </el-card>

    <!-- ========== 文本模块编辑区（证书、获奖、语言能力） ========== -->
    <!--
      只有用户在模块配置中选了对应模块，才会显示对应的编辑区
      每个文本模块有一个 textarea 和一个保存按钮
      支持 AI 一键润色
    -->
    <template v-if="resumeId">
      <el-card
        v-for="mod in moduleDataKeys"
        :key="mod.key"
        class="mt-16"
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
          class="mt-8"
          @click="saveModuleData"
          :loading="savingModules"
        >
          保存{{ mod.label }}
        </el-button>
      </el-card>
    </template>

    <!-- ========== 教育经历弹窗 ========== -->
    <!--
      el-dialog：弹窗组件
      - v-model="eduDialog"：控制弹窗显示/隐藏
      - :title：根据编辑/新增模式显示不同标题
      - :width：移动端用95%宽度，桌面端用500px
    -->
    <el-dialog v-model="eduDialog" :title="editingEdu ? '编辑教育经历' : '添加教育经历'" :width="isMobile ? '95%' : '500px'">
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

    <!-- ========== 工作经历弹窗 ========== -->
    <!-- 工作描述支持 AI 润色 -->
    <el-dialog v-model="workDialog" :title="editingWork ? '编辑工作经历' : '添加工作经历'" :width="isMobile ? '95%' : '500px'">
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

    <!-- ========== 项目经历弹窗 ========== -->
    <!-- 项目描述支持 AI 润色 -->
    <el-dialog v-model="projDialog" :title="editingProj ? '编辑项目' : '添加项目'" :width="isMobile ? '95%' : '500px'">
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

    <!-- ========== 技能弹窗 ========== -->
    <!-- 技能熟练度用滑块（el-slider）选择 -->
    <el-dialog v-model="skillDialog" :title="editingSkill ? '编辑技能' : '添加技能'" :width="isMobile ? '95%' : '400px'">
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

    <!-- ========== PDF 导出弹窗 ========== -->
    <!-- 用户选择要包含的模块，然后导出 PDF -->
    <el-dialog v-model="showPdfDialog" title="导出PDF简历" :width="isMobile ? '95%' : '450px'">
      <p class="module-hint">选择要包含的模块（个人信息模块自动包含）：</p>
      <el-checkbox-group v-model="pdfModules">
        <el-checkbox
          v-for="m in availableModules"
          :key="m.key"
          :value="m.key"
          class="module-checkbox"
        >
          {{ m.label }}
        </el-checkbox>
      </el-checkbox-group>
      <div v-if="pdfModules.length === 0" class="error-hint">
        请至少选择1个模块
      </div>
      <template #footer>
        <el-button @click="showPdfDialog = false">取消</el-button>
        <el-button type="primary" @click="exportPdf" :loading="exporting" :disabled="pdfModules.length === 0">
          导出
        </el-button>
      </template>
    </el-dialog>

    <!-- ========== AI 润色弹窗（独立组件） ========== -->
    <!--
      PolishDialog 是一个独立组件，定义在 @/components/PolishDialog.vue
      - v-model：控制弹窗显示/隐藏
      - :text：要润色的原始文本
      - :module-name：模块名称（用于 AI 判断上下文）
      - @accept：用户点击"采纳"时触发，返回润色后的文本
    -->
    <PolishDialog
      v-model="showPolishDialog"
      :text="polishTarget.text"
      :module-name="polishTarget.moduleName"
      @accept="handlePolishAccept"
    />
  </div>
</template>

<script setup>
// ==================== 导入依赖 ====================
import { ref, computed, onMounted, reactive } from 'vue'
// useMobile：自定义组合函数，判断是否为移动端
import { useMobile } from '@/composables/useMobile'
// 各种 API 函数
import { resumeApi, educationApi, workApi, projectApi, skillApi, tagApi } from '@/api'
import { ElMessage } from 'element-plus'
// AI 润色弹窗组件
import PolishDialog from '@/components/PolishDialog.vue'

// ==================== 响应式和基础状态 ====================
// isMobile：移动端检测（控制弹窗宽度）
const { isMobile } = useMobile()
// 简历 ID（null 表示尚未创建）
const resumeId = ref(null)
// 是否为创建模式
const isCreate = ref(true)
// 各种保存/导出的加载状态
const saving = ref(false)
const savingModules = ref(false)
const exporting = ref(false)
// 文件上传相关
const fileList = ref([])
const uploadFile = ref(null)

// ==================== 简历基本信息表单 ====================
const form = ref({ title: '我的简历', summary: '', status: 'draft' })

// ==================== 子模块数据列表 ====================
const educations = ref([])        // 教育经历列表
const workExperiences = ref([])   // 工作经历列表
const projects = ref([])          // 项目经历列表
const skills = ref([])            // 技能列表
const allTags = ref([])           // 所有可用标签（用于选择器）
const selectedTagIds = ref([])    // 已选标签 ID 列表
const selectedModules = ref([])   // 已启用的模块列表
const moduleData = ref({})        // 文本模块数据（证书、获奖、语言）

// ==================== 弹窗控制状态 ====================
// 每个子模块都有：弹窗显示状态 + 正在编辑的项（null 表示新增）
const eduDialog = ref(false)
const workDialog = ref(false)
const projDialog = ref(false)
const skillDialog = ref(false)
const editingEdu = ref(null)      // null=新增, 有值=编辑
const editingWork = ref(null)
const editingProj = ref(null)
const editingSkill = ref(null)
const showPdfDialog = ref(false)  // PDF 导出弹窗
const pdfModules = ref([])        // PDF 要包含的模块

// ==================== 各子模块的表单数据 ====================
const eduForm = ref({ school: '', degree: '学士', major: '', start_date: '', end_date: '', description: '' })
const workForm = ref({ company: '', position: '', start_date: '', end_date: '', description: '' })
const projForm = ref({ name: '', role: '', start_date: '', end_date: '', tech_stack: '', description: '' })
const skillForm = ref({ name: '', level: 50, category: '其他' })

// ==================== AI 润色弹窗状态 ====================
const showPolishDialog = ref(false)
// reactive() 创建响应式对象：包含要润色的文本和模块名
// 当 openPolish() 被调用时更新此对象，PolishDialog 组件会接收到新数据
const polishTarget = reactive({ text: '', moduleName: '', field: null })

// ==================== 静态配置数据 ====================
// 可用模块列表（用于模块选择多选框和 PDF 导出）
const availableModules = [
  { key: 'education', label: '教育经历' },
  { key: 'work_experience', label: '工作经历' },
  { key: 'project', label: '项目经历' },
  { key: 'skill', label: '技能' },
  { key: 'certificate', label: '证书' },
  { key: 'award', label: '获奖' },
  { key: 'language', label: '语言能力' },
]

// ==================== 计算属性 ====================

/**
 * 根据已选模块过滤出需要显示的文本模块
 * 只有用户选了 certificate/award/language 时，对应的编辑区才会显示
 */
const moduleDataKeys = computed(() => {
  const dataModules = [
    { key: 'certificate', label: '证书', placeholder: '请输入持有的证书，每行一个' },
    { key: 'award', label: '获奖', placeholder: '请输入获奖信息，每行一个' },
    { key: 'language', label: '语言能力', placeholder: '请输入语言能力描述' },
  ]
  return dataModules.filter(m => selectedModules.value.includes(m.key))
})

/**
 * 将标签列表按类型分组
 * 用于标签选择器的 el-option-group 分组显示
 *
 * 输入：allTags = [{ id: 1, name: 'Vue', tag_type: 'skill' }, ...]
 * 输出：[{ type: 'skill', label: '技能', tags: [...] }, ...]
 */
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

// ==================== 工具函数 ====================

/**
 * 文件选择变化时的回调
 * el-upload 的 :on-change 会传入文件对象
 * 我们保存 file.raw（原始 File 对象）用于后续上传
 */
function handleFileChange(file) {
  uploadFile.value = file.raw
}

/**
 * 打开 AI 润色弹窗
 * @param {string} text - 要润色的原始文本
 * @param {string} moduleName - 模块名称（如 'summary', 'work_experience', 'project'）
 */
function openPolish(text, moduleName) {
  polishTarget.text = text
  polishTarget.moduleName = moduleName
  showPolishDialog.value = true
}

/**
 * 处理用户在润色弹窗中点击"采纳"
 * 根据 moduleName 将润色结果写回对应的表单字段
 * @param {string} polishedText - AI 润色后的文本
 */
function handlePolishAccept(polishedText) {
  const target = polishTarget.moduleName
  if (target === 'summary') {
    form.value.summary = polishedText
  } else if (target === 'work_experience') {
    workForm.value.description = polishedText
  } else if (target === 'project') {
    projForm.value.description = polishedText
  } else if (moduleData.value.hasOwnProperty(target)) {
    // 文本模块（证书、获奖、语言）
    moduleData.value[target] = polishedText
  }
  ElMessage.success('已采纳润色结果')
}

// ==================== 数据加载函数 ====================

/**
 * 加载所有标签
 * 用于标签选择器（el-select）的数据源
 */
async function loadAllTags() {
  try {
    const data = await tagApi.list({ page_size: 200 })
    allTags.value = data.results || data || []
  } catch { /* 静默失败 */ }
}

/**
 * 加载简历数据
 *
 * 流程：
 * 1. 调用 resumeApi.list() 获取简历列表
 * 2. 如果有简历，取第一条的详情
 * 3. 将详情数据填充到各个表单和列表中
 * 4. 如果没有简历，保持创建模式
 */
async function loadResume() {
  try {
    const list = await resumeApi.list()
    if (list.results?.length) {
      const resume = await resumeApi.detail(list.results[0].id)
      resumeId.value = resume.id
      isCreate.value = false
      // 填充基本信息表单
      form.value = { title: resume.title, summary: resume.summary, status: resume.status }
      // 填充子模块列表
      educations.value = resume.educations || []
      workExperiences.value = resume.work_experiences || []
      projects.value = resume.projects || []
      skills.value = resume.skills || []
      // 填充已选标签
      selectedTagIds.value = (resume.tags_detail || []).map(t => t.id)
      // 填充已启用模块
      selectedModules.value = resume.enabled_modules || []
      // 填充文本模块数据
      moduleData.value = resume.module_data || {}
    }
  } catch { /* 静默失败 */ }
}

// ==================== 保存函数 ====================

/**
 * 保存简历基本信息
 *
 * 流程：
 * 1. 构建 payload（包含标题、简介、状态、标签、模块配置）
 * 2. 创建模式：调用 resumeApi.create()，获取新简历 ID
 *    编辑模式：调用 resumeApi.update()
 * 3. 如果有上传文件，用 FormData 上传并启用 AI 自动归类
 * 4. 上传完成后重新加载简历数据
 */
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

    // 如果选择了文件，上传并触发 AI 自动归类
    if (uploadFile.value && resumeId.value) {
      const fd = new FormData()
      fd.append('file', uploadFile.value)
      fd.append('auto_classify', 'true')  // 告诉后端启用 AI 自动归类
      await resumeApi.uploadFile(resumeId.value, fd)
      ElMessage.success('文件上传成功，AI正在自动归类内容...')
      uploadFile.value = null
      fileList.value = []
      // 重新加载简历（AI 可能已经更新了模块数据）
      await loadResume()
    }
  } catch { /* 静默失败 */ } finally {
    saving.value = false
  }
}

/**
 * 保存文本模块数据（证书、获奖、语言能力）
 * 将已启用模块和模块数据一起发送到后端
 */
async function saveModuleData() {
  savingModules.value = true
  try {
    await resumeApi.updateModules(resumeId.value, {
      enabled_modules: selectedModules.value,
      module_data: moduleData.value,
    })
    ElMessage.success('模块数据已保存')
  } catch { /* 静默失败 */ } finally {
    savingModules.value = false
  }
}

/**
 * 导出 PDF 简历
 *
 * 流程：
 * 1. 验证至少选择了1个模块
 * 2. 调用 resumeApi.exportPdf() 获取 PDF Blob
 * 3. 创建临时 URL 并触发下载
 */
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
  } catch { /* 静默失败 */ } finally {
    exporting.value = false
  }
}

// ==================== 教育经历 CRUD ====================
// CRUD = Create(创建) Read(读取) Update(更新) Delete(删除)

/**
 * 打开教育经历弹窗
 * @param {Object|null} item - 编辑时传入已有数据，新增时传 null
 */
function openEduDialog(item = null) {
  editingEdu.value = item
  // 编辑模式：复制已有数据；新增模式：使用空表单
  eduForm.value = item ? { ...item } : { school: '', degree: '学士', major: '', start_date: '', end_date: '', description: '', resume: resumeId.value }
  eduDialog.value = true
}

/**
 * 保存教育经历（新增或更新）
 * 表单中的 resume 字段关联到简历 ID
 */
async function saveEducation() {
  try {
    eduForm.value.resume = resumeId.value
    if (editingEdu.value) {
      // 编辑模式：调用 update API
      await educationApi.update(editingEdu.value.id, eduForm.value)
    } else {
      // 新增模式：调用 create API
      await educationApi.create(eduForm.value)
    }
    ElMessage.success('保存成功')
    eduDialog.value = false
    // 重新加载简历数据以更新列表
    await loadResume()
  } catch { /* 静默失败 */ }
}

async function deleteEducation(id) {
  await educationApi.delete(id)
  ElMessage.success('删除成功')
  await loadResume()
}

// ==================== 工作经历 CRUD ====================

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
  } catch { /* 静默失败 */ }
}

async function deleteWork(id) {
  await workApi.delete(id)
  ElMessage.success('删除成功')
  await loadResume()
}

// ==================== 项目经历 CRUD ====================

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
  } catch { /* 静默失败 */ }
}

async function deleteProject(id) {
  await projectApi.delete(id)
  ElMessage.success('删除成功')
  await loadResume()
}

// ==================== 技能 CRUD ====================

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
  } catch { /* 静默失败 */ }
}

async function deleteSkill(id) {
  await skillApi.delete(id)
  ElMessage.success('删除成功')
  await loadResume()
}

// ==================== 生命周期钩子 ====================

/**
 * onMounted：页面加载时并发执行两个数据加载任务
 * Promise.all() 并发执行，比顺序执行更快
 * 两个请求互不依赖，可以同时进行
 */
onMounted(async () => {
  await Promise.all([loadAllTags(), loadResume()])
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.edit-form {
  max-width: 700px;
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

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .edit-form :deep(.el-form-item__label) {
    float: none;
    display: block;
    text-align: left;
    padding-bottom: 4px;
  }

  .edit-form :deep(.el-form-item) {
    display: block;
  }

  .edit-form :deep(.el-form-item__content) {
    margin-left: 0 !important;
  }
}

.full-width {
  width: 100%;
}

.section-card {
  margin-top: 16px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.clickable {
  cursor: pointer;
}

.mt-16 {
  margin-top: 16px;
}

.mt-8 {
  margin-top: 8px;
}

.module-hint {
  margin-bottom: 12px;
  color: #666;
}

.module-checkbox {
  display: block;
  margin-bottom: 8px;
}

.error-hint {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 4px;
}
</style>
