"""
项目级 URL 配置。

这里负责把“访问哪个地址”映射到“执行哪个视图”。
你可以把它理解成总路由表：
- `/` 显示一个简单首页
- `/admin/` 进入 Django 后台
- `/api/` 返回 API 入口说明
- `/api/users/` 用户相关接口
- `/api/resumes/` 简历相关接口
- `/api/ai/` AI 相关接口
- `/swagger/` 和 `/redoc/` 提供接口文档
"""

from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view


def home_page(request):
    """
    根路径首页。

    这样访问 `http://localhost:8000/` 时不会看到 404，
    而是看到一个简单的入口页，方便新手确认服务已启动。
    """
    html = """
    <html>
      <head>
        <meta charset="utf-8">
        <title>智能简历系统</title>
        <style>
          body { font-family: Arial, "Microsoft YaHei", sans-serif; padding: 40px; background: #f7f8fa; }
          .card { max-width: 720px; background: #fff; border-radius: 16px; padding: 28px; box-shadow: 0 10px 30px rgba(0,0,0,.08); }
          h1 { margin-top: 0; }
          a { color: #1677ff; text-decoration: none; }
          ul { line-height: 1.9; }
        </style>
      </head>
      <body>
        <div class="card">
          <h1>智能简历管理系统</h1>
          <p>后端服务已启动。你可以从下面入口继续使用：</p>
          <ul>
            <li><a href="/admin/">Django 管理后台</a></li>
            <li><a href="/api/">API 入口</a></li>
            <li><a href="/swagger/">Swagger 文档</a></li>
            <li><a href="/redoc/">ReDoc 文档</a></li>
          </ul>
        </div>
      </body>
    </html>
    """
    return HttpResponse(html)


def api_index(request):
    """
    API 入口说明。

    访问 `/api/` 时返回 JSON，避免浏览器直接看到 404。
    """
    return JsonResponse(
        {
            "message": "Smart Resume Hub API",
            "version": "v1",
            "endpoints": {
                "users": "/api/users/",
                "resumes": "/api/resumes/",
                "ai": "/api/ai/",
                "swagger": "/swagger/",
                "redoc": "/redoc/",
            },
        }
    )


schema_view = get_schema_view(
    openapi.Info(
        title="Smart Resume Hub API",
        default_version="v1",
        description="智能简历管理系统 API 文档",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="1943201663@qq.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path("", home_page),
    path("admin/", admin.site.urls),
    path("api/", api_index),
    path("api/users/", include("apps.users.urls")),
    path("api/resumes/", include("apps.resumes.urls")),
    path("api/ai/", include("apps.ai_assistant.urls")),
    path("swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
