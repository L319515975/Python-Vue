"""User views and ViewSets."""
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

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view with extended user info."""
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    User management ViewSet.
    - Admin: full CRUD on all users
    - Normal user: can only view/edit own profile
    """
    queryset = User.objects.all()
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'email', 'phone']
    ordering_fields = ['created_at', 'username']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action in ('list', 'destroy'):
            return [IsAdminRole()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        return User.objects.filter(id=user.id)

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        """Get or update current user's profile."""
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """Change current user's password."""
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': '密码修改成功'})

# ── Admin Audit Log API ──────────────────────────────────────────────

from rest_framework.decorators import api_view, permission_classes as pc
from rest_framework.pagination import PageNumberPagination
from apps.resumes.models import AdminAuditLog


class AuditLogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@pc([IsAdminRole])
def audit_log_list(request):
    """List admin audit logs with pagination and filtering."""
    logs = AdminAuditLog.objects.select_related('admin_user').all()

    # Filtering
    action_type = request.query_params.get('action')
    if action_type:
        logs = logs.filter(action=action_type)

    target = request.query_params.get('target_user')
    if target:
        logs = logs.filter(target_user__icontains=target)

    admin_user = request.query_params.get('admin_user')
    if admin_user:
        logs = logs.filter(admin_user__username__icontains=admin_user)

    paginator = AuditLogPagination()
    page = paginator.paginate_queryset(logs, request)

    data = []
    for log in page:
        data.append({
            'id': log.id,
            'admin_user': log.admin_user.username if log.admin_user else None,
            'action': log.action,
            'action_display': log.get_action_display(),
            'target_user': log.target_user,
            'detail': log.detail,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat() if log.created_at else None,
        })

    return paginator.get_paginated_response(data)


# -- HR AI Usage Log API (admin only) --------------------------------

@api_view(['GET'])
@pc([IsAdminRole])
def hr_ai_usage_log_list(request):
    """List HR AI usage logs with pagination and filtering."""
    from apps.resumes.models import HRAiUsageLog
    logs = HRAiUsageLog.objects.select_related('resume', 'resume__user').all()

    # Filtering
    call_type = request.query_params.get('call_type')
    if call_type:
        logs = logs.filter(call_type=call_type)

    visitor_token = request.query_params.get('visitor_token')
    if visitor_token:
        logs = logs.filter(visitor_token__icontains=visitor_token)

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
