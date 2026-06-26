"""用户视图模块 - 处理用户相关的API请求。

本模块包含：
1. 用户登录（JWT Token获取）
2. 用户管理CRUD（管理员可管理所有用户，普通用户只能管理自己）
3. 操作审计日志查询（管理员专用）
4. HR AI使用日志查询（管理员专用）

Django REST Framework中的ViewSet概念：
- ViewSet将多个相关的HTTP请求处理函数组合在一个类中
- 比如UserViewSet处理 /api/users/ 的 GET(列表)、POST(创建)、PUT(更新)、DELETE(删除) 等请求
- 通过 router 自动注册URL路由，不需要手动写url配置
"""
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model

from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    CustomTokenObtainPairSerializer, ChangePasswordSerializer,
)
from .permissions import IsAdminRole, IsOwnerOrAdmin

# get_user_model() 返回当前项目配置的用户模型（AUTH_USER_MODEL）
# 这样做的好处是：如果以后更换用户模型，不需要修改这里的代码
User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """自定义登录视图 - 在JWT Token中包含用户角色和基本信息。

    当用户提交用户名和密码登录时：
    1. 验证用户名密码是否正确
    2. 生成 access_token（访问令牌，2小时有效）
    3. 生成 refresh_token（刷新令牌，7天有效）
    4. 在token中附带用户角色信息，前端可以解码token获取角色
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    用户管理ViewSet - 提供用户的增删改查API。

    权限规则：
    - 管理员：可以查看、创建、编辑、删除所有用户
    - 普通用户：只能查看和编辑自己的信息
    - 未登录用户：可以注册新账号（但只能注册为普通用户）

    API端点：
    - GET    /api/users/          → 获取用户列表（仅管理员）
    - POST   /api/users/          → 创建新用户
    - GET    /api/users/{id}/     → 获取指定用户详情
    - PUT    /api/users/{id}/     → 更新指定用户（全部字段）
    - PATCH  /api/users/{id}/     → 更新指定用户（部分字段）
    - DELETE /api/users/{id}/     → 删除指定用户（仅管理员）
    - GET    /api/users/me/       → 获取当前登录用户信息
    - PATCH  /api/users/me/       → 更新当前登录用户信息
    - POST   /api/users/change-password/ → 修改密码
    """
    queryset = User.objects.all()
    # 支持按角色和激活状态过滤
    filterset_fields = ['role', 'is_active']
    # 支持按用户名、邮箱、手机号搜索
    search_fields = ['username', 'email', 'phone']
    # 支持按创建时间和用户名排序
    ordering_fields = ['created_at', 'username']

    def get_serializer_class(self):
        """根据不同操作选择不同的序列化器。

        序列化器的作用：将Python对象转换为JSON，或将JSON转换为Python对象。
        不同操作需要不同的字段：创建时需要密码，更新时密码可选，查看时不含密码。
        """
        if self.action == 'create':
            return UserCreateSerializer      # 创建用户：需要密码字段
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer      # 更新用户：密码可选
        return UserSerializer                # 查看用户：包含所有只读字段

    def get_permissions(self):
        """根据不同操作设置不同的权限。

        权限检查顺序：先检查ViewSet级别的权限，再检查对象级别的权限。
        AllowAny = 任何人可访问
        IsAuthenticated = 必须登录
        IsAdminRole = 必须是管理员角色
        """
        if self.action == 'create':
            # 【安全修复】创建用户时：
            # - 如果是已登录的管理员，允许创建任意角色的用户
            # - 如果是未登录用户（注册），只允许创建普通用户
            # 这里先返回AllowAny，在perform_create中限制角色
            return [AllowAny()]
        if self.action in ('list', 'destroy'):
            return [IsAdminRole()]           # 列表和删除仅管理员
        return [IsAuthenticated()]           # 其他操作需要登录

    def get_queryset(self):
        """根据用户角色过滤查询集。

        管理员可以看到所有用户，普通用户只能看到自己。
        这是数据层面的权限隔离，即使API返回200，普通用户也看不到别人的数据。
        """
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()        # 管理员：返回所有用户
        return User.objects.filter(id=user.id)  # 普通用户：只返回自己

    def perform_create(self, serializer):
        """创建用户时的安全检查。

        【安全修复】防止未登录用户创建管理员账号。
        - 如果请求来自已登录的管理员 → 允许创建任意角色
        - 如果请求来自未登录用户 → 强制角色为普通用户
        """
        request = self.request
        if request.user.is_authenticated and request.user.role == 'admin':
            # 管理员创建用户：使用请求中指定的角色
            serializer.save()
        else:
            # 未登录用户注册：强制为普通用户角色
            serializer.save(role='user')

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        """获取或更新当前登录用户的个人信息。

        这是一个自定义action，URL为 /api/users/me/
        GET  → 返回当前用户的完整信息
        PATCH → 更新当前用户的部分信息
        """
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        # PATCH请求：partial=True 表示只更新传入的字段
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """修改当前用户密码。

        需要提供原密码和新密码，系统会先验证原密码是否正确。
        context={'request': request} 将请求对象传递给序列化器，
        序列化器需要用它来获取当前用户以验证原密码。
        """
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        # set_password 会对密码进行哈希加密后存储
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': '密码修改成功'})


# ── 管理员操作审计日志 API ──────────────────────────────────────────
# 以下函数处理管理员操作日志的查询
# 审计日志用于记录管理员的所有敏感操作，便于安全审计和追溯

from rest_framework.decorators import api_view, permission_classes as pc
from rest_framework.pagination import PageNumberPagination
from apps.resumes.models import AdminAuditLog


class AuditLogPagination(PageNumberPagination):
    """审计日志专用分页器。

    PageNumberPagination 是按页码分页的方式：
    - 请求 ?page=1&page_size=20 获取第1页的20条数据
    - 返回 { count: 总数, results: 当前页数据 }
    """
    page_size = 20              # 默认每页20条
    page_size_query_param = 'page_size'  # 允许前端自定义每页数量
    max_page_size = 100         # 最大每页100条，防止一次请求太多数据


@api_view(['GET'])  # 只允许GET请求
@pc([IsAdminRole])  # 仅管理员可访问
def audit_log_list(request):
    """管理员操作审计日志列表API。

    支持的查询参数：
    - action: 按操作类型过滤（如 user_create, tag_delete 等）
    - target_user: 按目标用户名过滤（模糊匹配）
    - admin_user: 按操作管理员用户名过滤（模糊匹配）
    - page: 页码
    - page_size: 每页数量

    select_related('admin_user') 用于优化查询性能：
    它会用SQL JOIN一次性查询关联的用户表，避免N+1查询问题。
    """
    logs = AdminAuditLog.objects.select_related('admin_user').all()

    # 按操作类型过滤
    action_type = request.query_params.get('action')
    if action_type:
        logs = logs.filter(action=action_type)

    # 按目标用户过滤（icontains 表示不区分大小写的模糊匹配）
    target = request.query_params.get('target_user')
    if target:
        logs = logs.filter(target_user__icontains=target)

    # 按操作管理员过滤
    admin_user = request.query_params.get('admin_user')
    if admin_user:
        logs = logs.filter(admin_user__username__icontains=admin_user)

    # 分页处理
    paginator = AuditLogPagination()
    page = paginator.paginate_queryset(logs, request)

    # 手动构建返回数据（将模型对象转为字典）
    data = []
    for log in page:
        data.append({
            'id': log.id,
            'admin_user': log.admin_user.username if log.admin_user else None,
            'action': log.action,
            'action_display': log.get_action_display(),  # 获取操作类型的中文显示名
            'target_user': log.target_user,
            'detail': log.detail,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat() if log.created_at else None,
        })

    return paginator.get_paginated_response(data)


# ── HR AI使用日志 API（管理员专用）──────────────────────────────────
# 记录HR通过访客链接使用AI功能的情况，用于监控AI使用量和成本

@api_view(['GET'])
@pc([IsAdminRole])
def hr_ai_usage_log_list(request):
    """HR AI使用日志列表API。

    支持的查询参数：
    - call_type: 按调用类型过滤（chat=AI咨询, polish=文本润色）
    - visitor_token: 按访客Token过滤
    - username: 按简历所属用户名过滤

    这个API帮助管理员监控：
    - 哪些HR在使用AI功能
    - AI调用消耗了多少Token
    - 是否存在滥用情况
    """
    from apps.resumes.models import HRAiUsageLog
    logs = HRAiUsageLog.objects.select_related('resume', 'resume__user').all()

    # 按调用类型过滤
    call_type = request.query_params.get('call_type')
    if call_type:
        logs = logs.filter(call_type=call_type)

    # 按访客Token过滤
    visitor_token = request.query_params.get('visitor_token')
    if visitor_token:
        logs = logs.filter(visitor_token__icontains=visitor_token)

    # 按简历所属用户过滤（跨表查询：resume__user__username）
    username = request.query_params.get('username')
    if username:
        logs = logs.filter(resume__user__username__icontains=username)

    paginator = AuditLogPagination()
    page = paginator.paginate_queryset(logs, request)

    data = []
    for log in page:
        data.append({
            'id': log.id,
            'username': log.resume.user.username if log.resume else None,
            'visitor_token': log.visitor_token[:16] + '...' if len(log.visitor_token) > 16 else log.visitor_token,
            'call_type': log.call_type,
            'call_type_display': log.get_call_type_display(),
            'query_text': log.query_text[:200] if log.query_text else '',
            'tokens_used': log.tokens_used,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat() if log.created_at else None,
        })

    return paginator.get_paginated_response(data)