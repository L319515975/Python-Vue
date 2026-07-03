"""简历模块URL配置。

URL路由说明：
- /api/resumes/                          → 简历CRUD（ViewSet自动生成）
- /api/resumes/{id}/upload_file/         → 上传简历文件
- /api/resumes/{id}/update-modules/      → 更新启用模块
- /api/resumes/{id}/export-pdf/          → 导出PDF
- /api/resumes/{id}/set-tags/            → 设置标签
- /api/resumes/{id}/generate-visitor-link/ → 生成访客链接
- /api/resumes/{id}/disable-visitor-link/  → 禁用访客链接
- /api/resumes/{id}/visitor-link-info/     → 获取访客链接信息
- /api/resumes/tags/                     → 标签CRUD
- /api/resumes/educations/               → 教育经历CRUD
- /api/resumes/work-experiences/         → 工作经历CRUD
- /api/resumes/projects/                 → 项目经历CRUD
- /api/resumes/skills/                   → 技能CRUD
- /api/resumes/visitor/{token}/          → 访客查看简历（无需登录）
- /api/resumes/visitor/{token}/download/ → 访客下载PDF
- /api/resumes/visitor/{token}/ai-chat/  → 访客AI对话
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ResumeViewSet, EducationViewSet, WorkExperienceViewSet,
    ProjectViewSet, SkillViewSet, TagViewSet,
    visitor_resume_view, visitor_download_pdf, visitor_ai_chat,
)

# 为ViewSet自动注册URL路由
router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'', ResumeViewSet, basename='resume')
router.register(r'educations', EducationViewSet, basename='education')
router.register(r'work-experiences', WorkExperienceViewSet, basename='work-experience')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'skills', SkillViewSet, basename='skill')

urlpatterns = [
    # 访客相关路由（使用函数视图，无需登录认证）
    # 注意：这些路由必须放在 router.urls 之前，否则会被ViewSet捕获
    path('visitor/<str:token>/', visitor_resume_view, name='visitor-resume'),
    path('visitor/<str:token>/download/', visitor_download_pdf, name='visitor-download'),
    path('visitor/<str:token>/ai-chat/', visitor_ai_chat, name='visitor-ai-chat'),
    # 引入ViewSet自动生成的所有路由
    path('', include(router.urls)),
]
