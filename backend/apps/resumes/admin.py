"""简历模块Admin配置 - Django管理后台的显示配置。

Django Admin是Django自带的后台管理界面，访问 /admin/ 即可进入。
通过admin.site.register()或@admin.register装饰器，可以配置：
- list_display: 列表页显示哪些列
- list_filter: 右侧过滤器
- search_fields: 搜索框搜索哪些字段
- readonly_fields: 哪些字段只读
- fieldsets: 编辑页的字段分组
"""
from django.contrib import admin
from .models import Resume, Education, WorkExperience, Project, Skill, Tag, AdminAuditLog, VisitorAiUsageLog


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """标签管理后台配置。"""
    list_display = ['name', 'tag_type', 'is_system', 'created_at']
    list_filter = ['tag_type', 'is_system']
    search_fields = ['name']


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    """简历管理后台配置 - 使用fieldsets分组显示字段。"""
    list_display = ['user', 'title', 'status', 'visitor_enabled', 'ai_processed', 'updated_at']
    list_filter = ['status', 'visitor_enabled', 'ai_processed']
    search_fields = ['user__username', 'title']
    filter_horizontal = ['tags']  # 多对多字段使用水平过滤器选择
    # fieldsets 将编辑页的字段分成多个组，更清晰
    fieldsets = (
        ('基本信息', {'fields': ('user', 'title', 'summary', 'status')}),
        ('文件', {'fields': ('file', 'file_name')}),
        ('模块', {'fields': ('tags', 'enabled_modules', 'module_data')}),
        ('AI', {'fields': ('ai_processed', 'ai_classification_result')}),
        ('游客链接', {'fields': ('visitor_enabled', 'visitor_token', 'visitor_expires', 'visitor_allow_download', 'public_modules')}),
        ('AI模式', {'fields': ('visitor_ai_mode_enabled', 'visitor_ai_enabled', 'visitor_ai_quota', 'visitor_ai_used')}),
    )


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ['resume', 'school', 'degree', 'major', 'start_date']
    search_fields = ['school', 'major']


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ['resume', 'company', 'position', 'start_date']
    search_fields = ['company', 'position']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['resume', 'name', 'role', 'tech_stack']
    search_fields = ['name', 'tech_stack']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['resume', 'name', 'level', 'category']
    list_filter = ['category']
    search_fields = ['name']


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    """审计日志管理后台 - 所有字段设为只读，不可修改。"""
    list_display = ['admin_user', 'action', 'target_user', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['admin_user__username', 'target_user', 'detail']
    readonly_fields = ['admin_user', 'action', 'target_user', 'detail', 'ip_address', 'created_at']


@admin.register(VisitorAiUsageLog)
class VisitorAiUsageLogAdmin(admin.ModelAdmin):
    """访客 AI 使用日志管理后台 - 所有字段只读。"""
    list_display = ['visitor_token', 'call_type', 'tokens_used', 'ip_address', 'created_at']
    list_filter = ['call_type', 'created_at']
    search_fields = ['visitor_token', 'query_text']
    readonly_fields = ['resume', 'visitor_token', 'call_type', 'query_text', 'response_text', 'tokens_used', 'ip_address', 'created_at']
