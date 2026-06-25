"""Resume models - with modular structure, tags, module data, and visitor links."""
import uuid
from django.db import models
from django.conf import settings


class Tag(models.Model):
    """System-level tag for resume categorization."""

    class TagType(models.TextChoices):
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
    is_system = models.BooleanField(default=True, verbose_name='系统级标签')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'
        unique_together = ['name', 'tag_type']
        ordering = ['tag_type', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_tag_type_display()})'


class Resume(models.Model):
    """Resume document linked to a user, with modular structure and visitor sharing."""

    class Status(models.TextChoices):
        DRAFT = 'draft', '草稿'
        PUBLISHED = 'published', '已发布'

    # Built-in fixed modules that are always present
    FIXED_MODULES = ['personal_info', 'contact']
    # Configurable modules (user can enable up to 5)
    CONFIGURABLE_MODULES = [
        'education', 'work_experience', 'project', 'skill',
        'certificate', 'award', 'language',
    ]
    MAX_CONFIGURABLE = 5
    # All available module keys
    MODULE_CHOICES = [(m, m) for m in FIXED_MODULES + CONFIGURABLE_MODULES]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resume',
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
    file = models.FileField(
        upload_to='resumes/',
        blank=True,
        null=True,
        verbose_name='简历文件',
    )
    file_name = models.CharField(max_length=255, blank=True, default='', verbose_name='文件名')

    # Modular structure
    tags = models.ManyToManyField(Tag, blank=True, related_name='resumes', verbose_name='标签')
    enabled_modules = models.JSONField(
        default=list,
        blank=True,
        help_text='用户启用的可配置模块列表，最多5个',
        verbose_name='启用模块',
    )
    module_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='模块数据，键为模块名，值为内容文本',
        verbose_name='模块数据',
    )
    ai_processed = models.BooleanField(default=False, verbose_name='AI已处理')
    ai_classification_result = models.JSONField(
        default=dict,
        blank=True,
        help_text='AI自动归类结果',
        verbose_name='AI归类结果',
    )

    # Visitor link fields
    visitor_enabled = models.BooleanField(
        default=False,
        help_text='是否启用了游客访问链接',
        verbose_name='游客链接启用',
    )
    visitor_token = models.CharField(
        max_length=64,
        blank=True,
        default='',
        help_text='游客访问唯一标识，用于URL路径',
        verbose_name='游客访问Token',
    )
    visitor_expires = models.DateTimeField(
        blank=True,
        null=True,
        help_text='游客链接过期时间',
        verbose_name='游客链接过期时间',
    )
    visitor_allow_download = models.BooleanField(
        default=False,
        help_text='是否允许游客下载PDF',
        verbose_name='允许游客下载',
    )
    public_modules = models.JSONField(
        default=list,
        blank=True,
        help_text='对游客公开的模块列表，为空则公开所有已启用模块',
        verbose_name='公开模块列表',
    )
    # HR visitor mode fields
    visitor_hr_enabled = models.BooleanField(
        default=False,
        help_text='是否启用HR模式（HR可通过链接使用AI助手）',
        verbose_name='HR模式启用',
    )
    visitor_ai_enabled = models.BooleanField(
        default=True,
        help_text='HR游客是否可使用AI功能',
        verbose_name='HR AI功能开关',
    )
    visitor_ai_quota = models.IntegerField(
        default=10,
        help_text='HR游客AI调用总配额',
        verbose_name='HR AI调用配额',
    )
    visitor_ai_used = models.IntegerField(
        default=0,
        help_text='HR游客已使用的AI调用次数',
        verbose_name='HR AI已用次数',
    )

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
        """Return all active modules (fixed + enabled configurable)."""
        return self.FIXED_MODULES + (self.enabled_modules or [])

    def generate_visitor_token(self):
        """Generate a unique visitor access token."""
        self.visitor_token = uuid.uuid4().hex
        return self.visitor_token

    def get_public_modules(self):
        """Return the list of modules visible to visitors."""
        if self.public_modules:
            return self.public_modules
        # Default: all enabled modules minus contact (privacy)
        return [m for m in (self.enabled_modules or []) if m != 'contact']


class AdminAuditLog(models.Model):
    """Records admin operations for security auditing."""

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

    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name='操作管理员',
    )
    action = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        verbose_name='操作类型',
    )
    target_user = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text='被操作的目标用户名',
        verbose_name='目标用户',
    )
    detail = models.TextField(
        blank=True,
        default='',
        help_text='操作详情描述',
        verbose_name='操作详情',
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='IP地址',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        verbose_name = '操作审计日志'
        verbose_name_plural = '操作审计日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.admin_user} - {self.get_action_display()} - {self.target_user}'


class Education(models.Model):
    """Education history."""
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name='educations', verbose_name='简历'
    )
    school = models.CharField(max_length=100, verbose_name='学校')
    degree = models.CharField(max_length=50, verbose_name='学位')
    major = models.CharField(max_length=100, verbose_name='专业')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(blank=True, null=True, verbose_name='结束日期')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    order = models.IntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '教育经历'
        verbose_name_plural = '教育经历'
        ordering = ['-start_date']

    def __str__(self):
        return f'{self.school} - {self.major}'


class WorkExperience(models.Model):
    """Work experience."""
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name='work_experiences', verbose_name='简历'
    )
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
    """Project experience."""
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name='projects', verbose_name='简历'
    )
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
    """Skills with proficiency level."""
    resume = models.ForeignKey(
        Resume, on_delete=models.CASCADE, related_name='skills', verbose_name='简历'
    )
    name = models.CharField(max_length=100, verbose_name='技能名称')
    level = models.IntegerField(
        default=50,
        help_text='熟练度 0-100',
        verbose_name='熟练度',
    )
    category = models.CharField(max_length=50, blank=True, default='其他', verbose_name='分类')
    order = models.IntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '技能'
        verbose_name_plural = '技能'
        ordering = ['category', '-level']

    def __str__(self):
        return f'{self.name} ({self.level}%)'


class HRAiUsageLog(models.Model):
    """Records HR visitor AI usage for auditing and quota tracking."""

    class CallType(models.TextChoices):
        CHAT = 'chat', 'AI咨询'
        POLISH = 'polish', '文本润色'

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name='hr_ai_logs',
        verbose_name='关联简历',
    )
    visitor_token = models.CharField(
        max_length=64,
        help_text='HR游客链接的token标识',
        verbose_name='访客Token',
    )
    call_type = models.CharField(
        max_length=10,
        choices=CallType.choices,
        verbose_name='调用类型',
    )
    query_text = models.TextField(
        blank=True,
        default='',
        verbose_name='查询/润色内容',
    )
    response_text = models.TextField(
        blank=True,
        default='',
        verbose_name='AI回复内容',
    )
    tokens_used = models.IntegerField(default=0, verbose_name='消耗Token数')
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='IP地址',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='调用时间')

    class Meta:
        verbose_name = 'HR AI使用日志'
        verbose_name_plural = 'HR AI使用日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'HR({self.visitor_token[:8]}) {self.get_call_type_display()} - {self.created_at}'