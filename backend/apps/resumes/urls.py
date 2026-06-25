"""Resume URLs - with tags, visitor access, and HR AI chat."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ResumeViewSet, EducationViewSet, WorkExperienceViewSet,
    ProjectViewSet, SkillViewSet, TagViewSet,
    visitor_resume_view, visitor_download_pdf, visitor_ai_chat,
)

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'', ResumeViewSet, basename='resume')
router.register(r'educations', EducationViewSet, basename='education')
router.register(r'work-experiences', WorkExperienceViewSet, basename='work-experience')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'skills', SkillViewSet, basename='skill')

urlpatterns = [
    path('visitor/<str:token>/', visitor_resume_view, name='visitor-resume'),
    path('visitor/<str:token>/download/', visitor_download_pdf, name='visitor-download'),
    path('visitor/<str:token>/ai-chat/', visitor_ai_chat, name='visitor-ai-chat'),
    path('', include(router.urls)),
]
