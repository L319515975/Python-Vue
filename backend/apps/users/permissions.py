"""自定义权限类 - 用于角色级别的访问控制。

Django REST Framework的权限系统工作方式：
1. 每个API请求到达视图之前，都会经过权限检查
2. 如果权限检查失败，返回403 Forbidden错误
3. 权限类需要实现 has_permission（ViewSet级别）或 has_object_permission（对象级别）

权限检查的两个层级：
- ViewSet级别（has_permission）：检查用户是否有权限访问这个API
  例如：只有管理员才能访问用户列表API
- 对象级别（has_object_permission）：检查用户是否有权限操作这个具体对象
  例如：普通用户只能编辑自己的简历，不能编辑别人的
"""
from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """管理员角色权限 - 只允许管理员角色的用户访问。

    使用场景：
    - 用户管理（查看用户列表、删除用户）
    - 标签管理（创建、编辑、删除标签）
    - 审计日志查看
    - AI日志查看

    has_permission 方法在每次请求时被调用，
    返回True表示允许访问，返回False表示拒绝。
    """

    def has_permission(self, request, view):
        # 三重检查：
        # 1. request.user 存在（已通过认证中间件）
        # 2. 用户已登录（is_authenticated）
        # 3. 用户角色是管理员
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsOwnerOrAdmin(BasePermission):
    """对象所有者或管理员权限 - 允许对象的所有者或管理员访问。

    使用场景：
    - 简历编辑：用户只能编辑自己的简历
    - 用户信息修改：用户只能修改自己的信息

    这是一个"对象级别"的权限，只在操作具体对象时检查。
    has_object_permission 会在 get_object() 获取对象后自动调用。
    """

    def has_object_permission(self, request, view, obj):
        # 管理员可以操作任何对象
        if request.user.role == 'admin':
            return True
        # 检查对象是否有user字段（简历、教育经历等都有）
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # 对于User对象本身，直接比较
        return obj == request.user