"""用户模块URL配置。

Django的URL路由工作方式：
1. 请求到达时，Django从上到下匹配URL模式
2. 找到匹配的模式后，调用对应的视图函数或ViewSet
3. path() 定义一个URL路由规则

URL结构说明：
- /api/users/login/          → 用户登录，获取JWT Token
- /api/users/token/refresh/  → 刷新Token（Token过期后获取新Token）
- /api/users/audit-logs/     → 操作审计日志（管理员）
- /api/users/visitor-ai-logs/ → 访客 AI 使用日志（管理员）
- /api/users/                → 用户列表/创建（ViewSet自动生成）
- /api/users/{id}/           → 用户详情/更新/删除（ViewSet自动生成）
- /api/users/me/             → 当前用户信息（自定义action）
- /api/users/change-password/ → 修改密码（自定义action）
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet, CustomTokenObtainPairView, audit_log_list, visitor_ai_usage_log_list

# DefaultRouter 会自动为ViewSet生成URL路由
# 例如：UserViewSet 会自动生成 /users/ 和 /users/{pk}/ 两个路由
router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    # 登录和Token相关路由（放在ViewSet路由之前，避免被ViewSet捕获）
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 审计日志路由（使用独立的函数视图，不是ViewSet）
    path('audit-logs/', audit_log_list, name='audit-log-list'),
    path('visitor-ai-logs/', visitor_ai_usage_log_list, name='visitor-ai-usage-log-list'),

    # include(router.urls) 引入ViewSet自动生成的所有路由
    path('', include(router.urls)),
]
