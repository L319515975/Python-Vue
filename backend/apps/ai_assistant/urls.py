"""AI Assistant URLs."""
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
