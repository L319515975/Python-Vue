"""User URLs."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet, CustomTokenObtainPairView, audit_log_list, hr_ai_usage_log_list

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('audit-logs/', audit_log_list, name='audit-log-list'),
    path('hr-ai-logs/', hr_ai_usage_log_list, name='hr-ai-usage-log-list'),
    path('', include(router.urls)),
]

