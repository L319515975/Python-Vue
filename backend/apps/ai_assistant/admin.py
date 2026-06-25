"""AI Assistant admin - with PolishLog and ClassificationLog."""
from django.contrib import admin
from .models import QueryLog, PolishLog, ClassificationLog


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'query', 'intent', 'tokens_used', 'created_at']
    list_filter = ['intent', 'created_at']
    search_fields = ['user__username', 'query']
    readonly_fields = ['user', 'query', 'response', 'intent', 'tokens_used', 'created_at']


@admin.register(PolishLog)
class PolishLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'module_name', 'status', 'tokens_used', 'created_at']
    list_filter = ['status', 'module_name', 'created_at']
    search_fields = ['user__username', 'original_text']
    readonly_fields = ['user', 'original_text', 'polished_text', 'module_name',
                       'status', 'tokens_used', 'created_at']


@admin.register(ClassificationLog)
class ClassificationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'file_name', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'file_name']
    readonly_fields = ['user', 'file_name', 'raw_text', 'classification_result',
                       'modules_assigned', 'status', 'created_at']
