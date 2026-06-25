"""Resume admin - with Tag and AdminAuditLog."""
from django.contrib import admin
from .models import Resume, Education, WorkExperience, Project, Skill, Tag, AdminAuditLog, HRAiUsageLog


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'tag_type', 'is_system', 'created_at']
    list_filter = ['tag_type', 'is_system']
    search_fields = ['name']


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'status', 'visitor_enabled', 'ai_processed', 'updated_at']
    list_filter = ['status', 'visitor_enabled', 'ai_processed']
    search_fields = ['user__username', 'title']
    filter_horizontal = ['tags']
    fieldsets = (
        ('基本信息', {'fields': ('user', 'title', 'summary', 'status')}),
        ('文件', {'fields': ('file', 'file_name')}),
        ('模块', {'fields': ('tags', 'enabled_modules', 'module_data')}),
        ('AI', {'fields': ('ai_processed', 'ai_classification_result')}),
        ('游客链接', {'fields': ('visitor_enabled', 'visitor_token', 'visitor_expires',
                               'visitor_allow_download', 'public_modules')}),
        ('HR模式', {'fields': ('visitor_hr_enabled', 'visitor_ai_enabled',
                               'visitor_ai_quota', 'visitor_ai_used')}),
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
    list_display = ['admin_user', 'action', 'target_user', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['admin_user__username', 'target_user', 'detail']
    readonly_fields = ['admin_user', 'action', 'target_user', 'detail', 'ip_address', 'created_at']

@admin.register(HRAiUsageLog)
class HRAiUsageLogAdmin(admin.ModelAdmin):
    list_display = ['visitor_token', 'call_type', 'tokens_used', 'ip_address', 'created_at']
    list_filter = ['call_type', 'created_at']
    search_fields = ['visitor_token', 'query_text']
    readonly_fields = ['resume', 'visitor_token', 'call_type', 'query_text', 'response_text', 'tokens_used', 'ip_address', 'created_at']
