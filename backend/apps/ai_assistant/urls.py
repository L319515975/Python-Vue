"""AI助手模块URL配置。

URL路由说明：
- /api/ai/logs/                → 查询日志列表（ViewSet自动生成）
- /api/ai/logs/{id}/          → 查询日志详情
- /api/ai/polish-logs/        → 润色日志列表
- /api/ai/classification-logs/ → 分类日志列表
- /api/ai/chat/               → AI对话（自定义action）
- /api/ai/polish/             → 文本润色（自定义action）
- /api/ai/history/            → 对话历史（自定义action）
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QueryLogViewSet, AIAssistantViewSet, PolishLogViewSet, ClassificationLogViewSet

router = DefaultRouter()
router.register(r'logs', QueryLogViewSet, basename='query-log')
router.register(r'polish-logs', PolishLogViewSet, basename='polish-log')
router.register(r'classification-logs', ClassificationLogViewSet, basename='classification-log')
router.register(r'', AIAssistantViewSet, basename='ai-assistant')

urlpatterns = [
    path('', include(router.urls)),
]