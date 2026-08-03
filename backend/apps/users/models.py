"""自定义用户模型 - 基于Django内置用户模型扩展。

Django的用户认证系统默认使用 django.contrib.auth.models.AbstractUser，
我们继承它并添加额外字段（角色、手机号、头像等）。

这样做的好处是：
1. 保留Django内置的用户名、密码、邮箱等字段
2. 保留Django内置的权限管理、密码哈希等功能
3. 只添加我们需要的额外字段
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """自定义用户模型。

    继承AbstractUser后，自动拥有以下字段：
    - username（用户名，唯一）
    - password（密码，自动哈希加密）
    - email（邮箱）
    - first_name, last_name（姓名）
    - is_active（是否激活）
    - is_staff（是否可登录管理后台）
    - is_superuser（是否超级管理员）
    - date_joined（注册时间）

    我们额外添加了：role（角色）、phone（手机号）、avatar（头像）
    """

    class Role(models.TextChoices):
        """用户角色枚举。

        TextChoices是Django提供的枚举类，用于定义字段的可选值。
        ADMIN = 'admin' 是存储在数据库中的值
        '管理员' 是显示给用户看的中文名称
        """
        ADMIN = 'admin', '管理员'
        USER = 'user', '普通用户'

    # 角色字段：决定用户是管理员还是普通用户
    # CharField = 字符串字段，max_length=最大长度
    role = models.CharField(
        max_length=10,
        choices=Role.choices,        # 限制只能选择Role中定义的值
        default=Role.USER,           # 默认为普通用户
        verbose_name='角色',
    )

    # 手机号：blank=True 表示可以为空字符串
    phone = models.CharField(max_length=20, blank=True, default='', verbose_name='手机号')

    # 头像：ImageField会将文件保存到 media/avatars/ 目录
    # blank=True(表单可空) + null=True(数据库可NULL)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')

    # auto_now_add=True：创建时自动设置为当前时间，之后不可修改
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    # auto_now=True：每次保存时自动更新为当前时间
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'  # 复数形式，Django管理后台显示用
        ordering = ['-created_at']   # 默认按创建时间倒序排列

    def __str__(self):
        """对象的字符串表示，Django管理后台列表中显示。"""
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_admin_role(self):
        """便捷属性：判断用户是否为管理员角色。

        @property 装饰器让方法可以像属性一样访问：
        user.is_admin_role 而不是 user.is_admin_role()
        """
        return self.role == self.Role.ADMIN