"""简历相关模型 - 包含简历主模型、子模型、标签、审计日志等。

本模块定义了简历系统的核心数据结构：
- Resume（简历主表）：存储简历的基本信息、模块配置、访客链接设置
- Education（教育经历）：简历下的教育记录
- WorkExperience（工作经历）：简历下的工作记录
- Project（项目经历）：简历下的项目记录
- Skill（技能）：简历下的技能记录
- Tag（标签）：用于简历分类的标签系统
- AdminAuditLog（审计日志）：记录管理员的操作
- VisitorAiUsageLog（访客 AI 使用日志）：记录访客使用 AI 功能的情况

模型关系说明：
- Resume 与 User 是一对一关系（一个用户一份简历）
- Education/WorkExperience/Project/Skill 与 Resume 是多对一关系（一份简历多条记录）
- Resume 与 Tag 是多对多关系（一份简历多个标签，一个标签可用于多份简历）
"""
import uuid
from django.db import models
from django.conf import settings


class Tag(models.Model):
    """标签模型 - 用于简历的分类标记。

    标签类型包括：技能、项目、证书、获奖、语言、自定义。
    is_system字段区分系统预设标签和用户自定义标签。
    """

    class TagType(models.TextChoices):
        """标签类型枚举。"""
        SKILL = 'skill', '技能'
        PROJECT = 'project', '项目'
        CERTIFICATE = 'certificate', '证书'
        AWARD = 'award', '获奖'
        LANGUAGE = 'language', '语言'
        CUSTOM = 'custom', '自定义'

    name = models.CharField(max_length=100, verbose_name='标签名称')
    tag_type = models.CharField(
        max_length=20,
        choices=TagType.choices,
        default=TagType.CUSTOM,
        verbose_name='标签类型',
    )
    # 系统标签由管理员创建，用户不可删除
    is_system = models.BooleanField(default=True, verbose_name='系统级标签')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        # unique_together: 同一类型下标签名称不能重复
        unique_together = ['name', 'tag_type']
        ordering = ['tag_type', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_tag_type_display()})'


class Resume(models.Model):
    """简历主模型 - 存储简历的所有信息。

    这是整个系统的核心模型，包含：
    1. 基本信息：标题、简介、状态
    2. 模块系统：可配置的简历模块（教育、工作、项目、技能等）
    3. 文件管理：支持上传简历文件
    4. AI功能：AI自动分类和处理
    5. 访客链接：支持生成分享链接，访客可通过链接查看简历

    模块系统说明：
    - FIXED_MODULES：固定模块，始终包含（个人信息、联系方式）
    - CONFIGURABLE_MODULES：可配置模块，用户最多选择5个
    - enabled_modules：用户实际启用的可配置模块列表（JSON字段）
    - module_data：各模块的文本数据（JSON字段，如证书、获奖等纯文本内容）
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', '草稿'
        PUBLISHED = 'published', '已发布'

    # 固定模块：始终包含，不可移除
    FIXED_MODULES = ['personal_info', 'contact']
    # 可配置模块：用户可以选择启用哪些
    CONFIGURABLE_MODULES = [
        'education', 'work_experience', 'project', 'skill',
        'certificate', 'award', 'language',
    ]
    MAX_CONFIGURABLE = 5  # 最多可配置模块数
    MODULE_CHOICES = [(m, m) for m in FIXED_MODULES + CONFIGURABLE_MODULES]

    # OneToOneField：一对一关系，每个用户只能有一份简历
    # on_delete=CASCADE：删除用户时，同时删除其简历
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resume',  # 通过 user.resume 访问简历
        verbose_name='用户',
    )
    title = models.CharField(max_length=200, default='我的简历', verbose_name='简历标题')
    summary = models.TextField(blank=True, default='', verbose_name='个人简介')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='状态',
    )
    # FileField：文件上传字段，文件保存到 media/resumes/ 目录
    file = models.FileField(
        upload_to='resumes/',
        blank=True, null=True,
        verbose_name='简历文件',
    )
    file_name = models.CharField(max_length=255, blank=True, default='', verbose_name='文件名')

    # ManyToManyField：多对多关系，一份简历可以有多个标签
    # blank=True：表单中可以不选择标签
    tags = models.ManyToManyField(Tag, blank=True, related_name='resumes', verbose_name='标签')

    # JSONField：存储JSON格式数据，灵活存储结构化信息
    # enabled_modules 存储用户启用的模块列表，如 ['education', 'skill']
    enabled_modules = models.JSONField(
        default=list, blank=True,
        help_text='用户启用的可配置模块列表，最多5个',
        verbose_name='启用模块',
    )
    # module_data 存储各模块的文本内容，如 {'certificate': 'CET-6证书...', 'award': '优秀员工...'}
    module_data = models.JSONField(
        default=dict, blank=True,
        help_text='模块数据，键为模块名，值为内容文本',
        verbose_name='模块数据',
    )

    # AI相关字段
    ai_processed = models.BooleanField(default=False, verbose_name='AI已处理')
    ai_classification_result = models.JSONField(
        default=dict, blank=True,
        help_text='AI自动归类结果',
        verbose_name='AI归类结果',
    )

    # ── 访客链接相关字段 ──────────────────────────────────
    # 访客链接允许用户分享简历给他人查看，无需登录
    visitor_enabled = models.BooleanField(default=False, help_text='是否启用了游客访问链接', verbose_name='游客链接启用')
    visitor_token = models.CharField(max_length=64, blank=True, default='', help_text='游客访问唯一标识，用于URL路径', verbose_name='游客访问Token')
    visitor_expires = models.DateTimeField(blank=True, null=True, help_text='游客链接过期时间', verbose_name='游客链接过期时间')
    visitor_allow_download = models.BooleanField(default=False, help_text='是否允许游客下载PDF', verbose_name='允许游客下载')
    # public_modules：对访客公开的模块列表，为空则公开所有已启用模块
    public_modules = models.JSONField(default=list, blank=True, help_text='对游客公开的模块列表，为空则公开所有已启用模块', verbose_name='公开模块列表')

    # ── AI模式相关字段 ──────────────────────────────────
    # AI模式允许访客通过链接使用AI助手分析简历
    visitor_ai_mode_enabled = models.BooleanField(default=False, help_text='是否启用AI模式（访客可通过链接使用AI助手）', verbose_name='AI模式启用')
    visitor_ai_enabled = models.BooleanField(default=True, help_text='访客是否可使用AI功能', verbose_name='AI功能开关')
    visitor_ai_quota = models.IntegerField(default=10, help_text='访客AI调用总配额', verbose_name='AI调用配额')
    visitor_ai_used = models.IntegerField(default=0, help_text='访客已使用的AI调用次数', verbose_name='AI已用次数')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '简历'
        verbose_name_plural = '简历'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user.username} - {self.title}'

    @property
    def all_modules(self):
        """返回所有活跃模块（固定模块 + 用户启用的模块）。"""
        return self.FIXED_MODULES + (self.enabled_modules or [])

    def generate_visitor_token(self):
        """生成唯一的访客访问Token。

        uuid.uuid4().hex 生成一个32位的随机十六进制字符串，
        用作访客链接的唯一标识，几乎不可能重复。
        """
        self.visitor_token = uuid.uuid4().hex
        return self.visitor_token

    def get_public_modules(self):
        """返回对访客公开的模块列表。

        如果用户指定了公开模块列表，使用用户的选择；
        否则公开所有已启用模块（排除contact联系方式，保护隐私）。
        """
        if self.public_modules:
            return self.public_modules
        return [m for m in (self.enabled_modules or []) if m != 'contact']


class AdminAuditLog(models.Model):
    """管理员操作审计日志 - 记录所有敏感操作用于安全追溯。

    每当管理员执行敏感操作（创建/修改/删除用户、简历、标签等）时，
    系统会自动创建一条审计日志记录，包含：
    - 谁（admin_user）做了什么操作（action）
    - 操作了谁的数据（target_user）
    - 操作详情（detail）
    - 操作时间和IP地址
    """

    class ActionType(models.TextChoices):
        USER_CREATE = 'user_create', '创建用户'
        USER_UPDATE = 'user_update', '修改用户'
        USER_DELETE = 'user_delete', '删除用户'
        RESUME_UPDATE = 'resume_update', '修改简历'
        RESUME_DELETE = 'resume_delete', '删除简历'
        TAG_CREATE = 'tag_create', '创建标签'
        TAG_UPDATE = 'tag_update', '修改标签'
        TAG_DELETE = 'tag_delete', '删除标签'
        ROLE_CHANGE = 'role_change', '角色变更'
        OTHER = 'other', '其他操作'

    # ForeignKey：多对一关系，一个管理员可以有多条审计日志
    # SET_NULL：管理员被删除时，日志中的admin_user设为NULL（保留日志）
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name='audit_logs',
        verbose_name='操作管理员',
    )
    action = models.CharField(max_length=20, choices=ActionType.choices, verbose_name='操作类型')
    target_user = models.CharField(max_length=150, blank=True, default='', help_text='被操作的目标用户名', verbose_name='目标用户')
    detail = models.TextField(blank=True, default='', help_text='操作详情描述', verbose_name='操作详情')
    # GenericIPAddressField：支持IPv4和IPv6地址格式
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP地址')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        verbose_name = '操作审计日志'
        verbose_name_plural = '操作审计日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.admin_user} - {self.get_action_display()} - {self.target_user}'


# ── 简历子模型（教育、工作、项目、技能）──────────────────────────
# 这些模型与Resume是ForeignKey（多对一）关系
# 一份简历可以有多条教育/工作/项目/技能记录

class Education(models.Model):
    """教育经历模型。"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='educations', verbose_name='简历')
    school = models.CharField(max_length=100, verbose_name='学校')
    degree = models.CharField(max_length=50, verbose_name='学位')
    major = models.CharField(max_length=100, verbose_name='专业')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(blank=True, null=True, verbose_name='结束日期')  # null表示"至今"
    description = models.TextField(blank=True, default='', verbose_name='描述')
    order = models.IntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '教育经历'
        verbose_name_plural = '教育经历'
        ordering = ['-start_date']  # 按开始日期倒序（最新的在前）

    def __str__(self):
        return f'{self.school} - {self.major}'


class WorkExperience(models.Model):
    """工作经历模型。"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='work_experiences', verbose_name='简历')
    company = models.CharField(max_length=100, verbose_name='公司')
    position = models.CharField(max_length=100, verbose_name='职位')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(blank=True, null=True, verbose_name='结束日期')
    description = models.TextField(blank=True, default='', verbose_name='工作描述')
    order = models.IntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '工作经历'
        verbose_name_plural = '工作经历'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.company} - {self.position}'


class Project(models.Model):
    """项目经历模型。"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='projects', verbose_name='简历')
    name = models.CharField(max_length=200, verbose_name='项目名称')
    role = models.CharField(max_length=100, blank=True, default='', verbose_name='担任角色')
    start_date = models.DateField(blank=True, null=True, verbose_name='开始日期')
    end_date = models.DateField(blank=True, null=True, verbose_name='结束日期')
    description = models.TextField(blank=True, default='', verbose_name='项目描述')
    tech_stack = models.CharField(max_length=500, blank=True, default='', verbose_name='技术栈')
    order = models.IntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '项目经历'
        verbose_name_plural = '项目经历'
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class Skill(models.Model):
    """技能模型 - 带熟练度百分比。"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='skills', verbose_name='简历')
    name = models.CharField(max_length=100, verbose_name='技能名称')
    level = models.IntegerField(default=50, help_text='熟练度 0-100', verbose_name='熟练度')
    category = models.CharField(max_length=50, blank=True, default='其他', verbose_name='分类')
    order = models.IntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '技能'
        verbose_name_plural = '技能'
        ordering = ['category', '-level']  # 先按分类排序，再按熟练度倒序

    def __str__(self):
        return f'{self.name} ({self.level}%)'


class VisitorAiUsageLog(models.Model):
    """访客 AI 使用日志 - 记录访客通过链接使用 AI 功能的情况。

    用于：
    1. 监控AI使用量和Token消耗
    2. 追踪哪些访客在使用AI功能
    3. 配额管理（防止滥用）
    4. 安全审计
    """

    class CallType(models.TextChoices):
        CHAT = 'chat', 'AI咨询'
        POLISH = 'polish', '文本润色'

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='visitor_ai_logs', verbose_name='关联简历')
    visitor_token = models.CharField(max_length=64, help_text='访客链接的token标识', verbose_name='访客Token')
    call_type = models.CharField(max_length=10, choices=CallType.choices, verbose_name='调用类型')
    query_text = models.TextField(blank=True, default='', verbose_name='查询/润色内容')
    response_text = models.TextField(blank=True, default='', verbose_name='AI回复内容')
    tokens_used = models.IntegerField(default=0, verbose_name='消耗Token数')
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP地址')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='调用时间')

    class Meta:
        verbose_name = '访客 AI 使用日志'
        verbose_name_plural = '访客 AI 使用日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'AI({self.visitor_token[:8]}) {self.get_call_type_display()} - {self.created_at}'
