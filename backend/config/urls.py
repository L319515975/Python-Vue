"""
项目的 URL 路由配置 —— 所有 HTTP 请求的入口。

URL 路由就像一个"分发中心"，根据请求的 URL 地址，
把请求转发到对应的处理函数（视图）。

URL 结构：
- /admin/               → Django 自带的管理后台
- /api/users/           → 用户相关接口（登录、注册、用户管理）
- /api/resumes/         → 简历相关接口（简历 CRUD、标签、访客等）
- /api/ai/              → AI 助手相关接口（对话、润色、分类）
- /swagger/             → API 接口文档（Swagger UI）
- /redoc/               → API 接口文档（ReDoc UI）

知识点：
- include()：将 URL 分发到各应用的 urls.py 中（分而治之）
- drf_yasg：自动生成 API 文档的工具，根据代码中的序列化器和视图自动生成文档
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view   # Swagger 文档视图
from drf_yasg import openapi                 # OpenAPI 规范工具

# API 文档配置 —— 定义文档的基本信息
schema_view = get_schema_view(
    openapi.Info(
        title="Smart Resume Hub API",           # API 文档标题
        default_version='v1',                    # API 版本号
        description="智能简历管理系统 API 接口文档",  # 文档描述
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="1943201663@qq.com"),  # 联系方式
        license=openapi.License(name="MIT License"),          # 许可证
    ),
    public=True,                             # 文档对外公开
    permission_classes=(permissions.AllowAny,),  # 任何人都能查看文档
)

# URL 路由列表 —— 定义 URL 到视图的映射关系
urlpatterns = [
    # Django 管理后台（超级管理员使用）
    path('admin/', admin.site.urls),

    # 用户相关接口：登录、注册、个人信息、用户管理等
    path('api/users/', include('apps.users.urls')),

    # 简历相关接口：简历 CRUD、标签管理、文件上传、访客链接等
    path('api/resumes/', include('apps.resumes.urls')),

    # AI 助手接口：智能问答、文本润色、日志查看等
    path('api/ai/', include('apps.ai_assistant.urls')),

    # API 文档（Swagger 格式，支持在线测试接口）
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # API 文档（ReDoc 格式，更适合阅读）
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# 开发模式下，为上传的文件提供访问服务
# MEDIA_URL = '/media/'，MEDIA_ROOT 是文件上传的存储目录
# 这行代码让 Django 能够响应 /media/xxx 的请求，返回上传的文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)