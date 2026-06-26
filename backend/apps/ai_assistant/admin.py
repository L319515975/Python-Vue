"""AI助手Admin配置 - Django管理后台配置。

所有日志模型的字段都设为只读（readonly_fields），
因为日志是系统自动生成的，不应该被手动修改。
"""
from django.contrib import admin
from .models import QueryLog, PolishLog, ClassificationLog


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    """查询日志管理后台。"""
    list_display = ['user', 'query', 'intent', 'tokens_used', 'created_at']
    list_filter = ['intent', 'created_at']
    search_fields = ['user__username', 'query']
    readonly_fields = ['user', 'query', 'response', 'intent', 'tokens_used', 'created_at']


@admin.register(PolishLog)
class PolishLogAdmin(admin.ModelAdmin):
    """润色日志管理后台。"""
    list_display = ['user', 'module_name', 'status', 'tokens_used', 'created_at']
    list_filter = ['status', 'module_name', 'created_at']
    search_fields = ['user__username', 'original_text']
    readonly_fields = ['user', 'original_text', 'polished_text', 'module_name',
                       'status', 'tokens_used', 'created_at']


@admin.register(ClassificationLog)
class ClassificationLogAdmin(admin.ModelAdmin):
    """分类日志管理后台。"""
    list_display = ['user', 'file_name', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'file_name']
    readonly_fields = ['user', 'file_name', 'raw_text', 'classification_result',
                       'modules_assigned', 'status', 'created_at']