"""Resume views - with tags, PDF export, module management, visitor access, and HR AI chat."""
import io
import logging
from datetime import timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import FileResponse, JsonResponse
from django.utils import timezone

from .models import Resume, Education, WorkExperience, Project, Skill, Tag, AdminAuditLog, HRAiUsageLog
from .serializers import (
    ResumeListSerializer, ResumeDetailSerializer, ResumeCreateUpdateSerializer,
    EducationSerializer, WorkExperienceSerializer, ProjectSerializer, SkillSerializer,
    TagSerializer, TagCreateSerializer, PdfExportSerializer,
    VisitorLinkSerializer, VisitorLinkUpdateSerializer,
)
from .visitor_utils import (
    verify_visitor_signature, is_visitor_link_valid, get_visitor_url,
    filter_visitor_data, check_hr_ai_quota, generate_visitor_signature,
)
from apps.users.permissions import IsAdminRole, IsOwnerOrAdmin

logger = logging.getLogger(__name__)


def _log_audit(request, action_type, target_user='', detail=''):
    """Helper to create admin audit log entries."""
    try:
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')
        AdminAuditLog.objects.create(
            admin_user=request.user,
            action=action_type,
            target_user=target_user,
            detail=detail,
            ip_address=ip,
        )
    except Exception as e:
        logger.warning(f'Audit log creation failed: {e}')


def _get_client_ip(request):
    """Extract client IP from request."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


# -- Public Visitor API (no auth required) ----------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def visitor_resume_view(request, token):
    """
    Public API: view a resume via visitor link.
    Validates signature and expiry, returns filtered public data.
    If role=hr in query params, validates HR-specific signature.
    """
    sig = request.query_params.get('sig', '')
    expires = int(request.query_params.get('expires', 0))
    role = request.query_params.get('role', 'visitor')

    # Verify HMAC signature (role-aware)
    if not sig or not verify_visitor_signature(token, expires, sig, role):
        return JsonResponse({'detail': '\u8bbf\u95ee\u94fe\u63a5\u65e0\u6548\u6216\u5df2\u88ab\u7be1\u6539'}, status=404)

    # Find resume by visitor token
    try:
        resume = Resume.objects.select_related('user').prefetch_related(
            'tags', 'educations', 'work_experiences', 'projects', 'skills'
        ).get(visitor_token=token)
    except Resume.DoesNotExist:
        return JsonResponse({'detail': '\u8bbf\u95ee\u94fe\u63a5\u4e0d\u5b58\u5728'}, status=404)

    # Validate link status
    validity = is_visitor_link_valid(resume)
    if not validity['valid']:
        return JsonResponse({'detail': validity['reason']}, status=404)

    # Check URL expiry parameter
    if expires and expires < int(timezone.now().timestamp()):
        return JsonResponse({'detail': '\u8bbf\u95ee\u94fe\u63a5\u5df2\u8fc7\u671f'}, status=404)

    # Validate HR role - ensure HR mode is actually enabled on the resume
    if role == 'hr' and not resume.visitor_hr_enabled:
        return JsonResponse({'detail': '\u8be5\u94fe\u63a5\u672a\u542f\u7528HR\u6a21\u5f0f'}, status=403)

    # Return filtered public data with HR metadata
    data = filter_visitor_data(resume)
    return JsonResponse(data, json_dumps_params={'ensure_ascii': False})


@api_view(['GET'])
@permission_classes([AllowAny])
def visitor_download_pdf(request, token):
    """
    Public API: download resume PDF via visitor link (if allowed).
    """
    sig = request.query_params.get('sig', '')
    expires = int(request.query_params.get('expires', 0))
    role = request.query_params.get('role', 'visitor')

    if not sig or not verify_visitor_signature(token, expires, sig, role):
        return JsonResponse({'detail': '\u8bbf\u95ee\u94fe\u63a5\u65e0\u6548'}, status=404)

    try:
        resume = Resume.objects.select_related('user').get(visitor_token=token)
    except Resume.DoesNotExist:
        return JsonResponse({'detail': '\u8bbf\u95ee\u94fe\u63a5\u4e0d\u5b58\u5728'}, status=404)

    validity = is_visitor_link_valid(resume)
    if not validity['valid']:
        return JsonResponse({'detail': validity['reason']}, status=404)

    if not resume.visitor_allow_download:
        return JsonResponse({'detail': '\u8be5\u7b80\u5386\u672a\u6388\u6743\u6e38\u5ba2\u4e0b\u8f7d'}, status=403)

    # Generate PDF with public modules
    try:
        from .pdf_service import generate_resume_pdf
        public_modules = resume.get_public_modules()
        pdf_buffer = generate_resume_pdf(resume, public_modules)
        filename = f'{resume.user.username}_resume.pdf'
        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=filename,
            content_type='application/pdf',
        )
    except ImportError:
        return JsonResponse({'detail': 'PDF\u751f\u6210\u670d\u52a1\u4e0d\u53ef\u7528'}, status=501)
    except Exception as e:
        logger.error(f'Visitor PDF download failed: {e}')
        return JsonResponse({'detail': 'PDF\u751f\u6210\u5931\u8d25'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def visitor_ai_chat(request, token):
    """
    Public API: HR visitor AI chat endpoint.
    Validates signature with role=hr, checks AI quota, calls AI service.
    """
    sig = request.query_params.get('sig', '')
    expires = int(request.query_params.get('expires', 0))
    role = request.query_params.get('role', 'visitor')

    # Must be HR role
    if role != 'hr':
        return JsonResponse({'detail': '\u666e\u901a\u6e38\u5ba2\u65e0\u6743\u4f7f\u7528AI\u529f\u80fd'}, status=403)

    # Verify HR signature
    if not sig or not verify_visitor_signature(token, expires, sig, 'hr'):
        return JsonResponse({'detail': '\u8bbf\u95ee\u94fe\u63a5\u65e0\u6548\u6216\u5df2\u88ab\u7be1\u6539'}, status=404)

    # Find resume
    try:
        resume = Resume.objects.select_related('user').prefetch_related(
            'tags', 'educations', 'work_experiences', 'projects', 'skills'
        ).get(visitor_token=token)
    except Resume.DoesNotExist:
        return JsonResponse({'detail': '\u8bbf\u95ee\u94fe\u63a5\u4e0d\u5b58\u5728'}, status=404)

    # Validate link
    validity = is_visitor_link_valid(resume)
    if not validity['valid']:
        return JsonResponse({'detail': validity['reason']}, status=404)

    if expires and expires < int(timezone.now().timestamp()):
        return JsonResponse({'detail': '\u8bbf\u95ee\u94fe\u63a5\u5df2\u8fc7\u671f'}, status=404)

    # Check HR mode enabled
    if not resume.visitor_hr_enabled:
        return JsonResponse({'detail': '\u8be5\u94fe\u63a5\u672a\u542f\u7528HR\u6a21\u5f0f'}, status=403)

    # Check AI quota
    quota_info = check_hr_ai_quota(resume)
    if not quota_info['available']:
        return JsonResponse({
            'detail': quota_info['reason'],
            'quota_exhausted': True,
            'remaining': 0,
            'total': quota_info['total'],
        }, status=429)

    # Get query text
    query = request.data.get('query', '').strip()
    if not query:
        return JsonResponse({'detail': '\u67e5\u8be2\u5185\u5bb9\u4e3a\u7a7a'}, status=400)

    call_type = request.data.get('call_type', 'chat')
    module_name = request.data.get('module_name', '')

    try:
        from apps.ai_assistant.services import ask_ai_for_visitor, polish_text_for_visitor

        if call_type == 'polish':
            result = polish_text_for_visitor(resume, query, module_name)
        else:
            result = ask_ai_for_visitor(resume, query)

        # Increment quota
        resume.visitor_ai_used += 1
        resume.save(update_fields=['visitor_ai_used'])

        # Log usage
        ip = _get_client_ip(request)
        HRAiUsageLog.objects.create(
            resume=resume,
            visitor_token=token,
            call_type=call_type,
            query_text=query[:2000],
            response_text=result.get('response', result.get('polished_text', ''))[:5000],
            tokens_used=result.get('tokens_used', 0),
            ip_address=ip,
        )

        remaining = max(0, resume.visitor_ai_quota - resume.visitor_ai_used)

        response_data = {
            'remaining': remaining,
            'total': resume.visitor_ai_quota,
            'tokens_used': result.get('tokens_used', 0),
        }

        if call_type == 'polish':
            response_data['original_text'] = result.get('original_text', query)
            response_data['polished_text'] = result.get('polished_text', '')
            response_data['status'] = result.get('status', 'success')
        else:
            response_data['response'] = result.get('response', '')
            response_data['intent'] = result.get('intent', 'general')

        return JsonResponse(response_data, json_dumps_params={'ensure_ascii': False})

    except Exception as e:
        logger.error(f'HR AI chat failed: {e}')
        return JsonResponse({'detail': f'AI\u670d\u52a1\u8c03\u7528\u5931\u8d25: {str(e)}'}, status=500)


# -- Tag ViewSet -------------------------------------------------------

class TagViewSet(viewsets.ModelViewSet):
    """Tag CRUD ViewSet - admin CRUD, user read-only."""
    queryset = Tag.objects.all()
    filterset_fields = ['tag_type', 'is_system']
    search_fields = ['name']
    ordering_fields = ['name', 'tag_type', 'created_at']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return TagCreateSerializer
        return TagSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAdminRole()]

    def perform_create(self, serializer):
        serializer.save()
        _log_audit(request=self.request, action_type='tag_create',
                   detail=f'\u521b\u5efa\u6807\u7b7e: {serializer.instance.name}')

    def perform_update(self, serializer):
        serializer.save()
        _log_audit(request=self.request, action_type='tag_update',
                   detail=f'\u4fee\u6539\u6807\u7b7e: {serializer.instance.name}')

    def perform_destroy(self, instance):
        name = instance.name
        instance.delete()
        _log_audit(request=self.request, action_type='tag_delete',
                   detail=f'\u5220\u9664\u6807\u7b7e: {name}')


# -- Resume ViewSet ----------------------------------------------------

class ResumeViewSet(viewsets.ModelViewSet):
    """
    Resume CRUD ViewSet.
    - Admin: can see all resumes
    - Normal user: can only see/edit own resume
    Includes visitor link management with HR mode support.
    """
    filterset_fields = ['status', 'ai_processed']
    search_fields = ['title', 'summary']
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Resume.objects.select_related('user').prefetch_related('tags').all()
        return Resume.objects.select_related('user').prefetch_related('tags').filter(user=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ResumeListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ResumeCreateUpdateSerializer
        return ResumeDetailSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        if self.request.user.role == 'admin':
            _log_audit(request=self.request, action_type='resume_update',
                       target_user=instance.user.username,
                       detail=f'\u7ba1\u7406\u5458\u4fee\u6539\u7b80\u5386: {instance.title}')

    def perform_destroy(self, instance):
        if self.request.user.role == 'admin':
            _log_audit(request=self.request, action_type='resume_delete',
                       target_user=instance.user.username,
                       detail=f'\u7ba1\u7406\u5458\u5220\u9664\u7b80\u5386: {instance.title}')
        instance.delete()

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser])
    def upload_file(self, request, pk=None):
        """Upload resume file (Word/PDF/Markdown) with auto-classification."""
        resume = self.get_object()
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': '\u8bf7\u4e0a\u4f20\u6587\u4ef6'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/markdown',
            'text/plain',
        ]
        if file.content_type not in allowed_types and not file.name.endswith(('.md', '.pdf', '.doc', '.docx')):
            return Response(
                {'detail': '\u4ec5\u652f\u6301 PDF\u3001Word\u3001Markdown \u683c\u5f0f'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resume.file = file
        resume.file_name = file.name
        resume.save()

        auto_classify = request.data.get('auto_classify', 'true').lower() in ('true', '1', 'yes')
        if auto_classify:
            try:
                from apps.ai_assistant.services import classify_resume_file
                result = classify_resume_file(resume)
                if result.get('success'):
                    resume.ai_processed = True
                    resume.ai_classification_result = result.get('classification', {})
                    resume.save()
            except Exception as e:
                logger.warning(f'Auto-classification failed: {e}')

        return Response(ResumeDetailSerializer(resume).data)

    @action(detail=True, methods=['post'], url_path='update-modules')
    def update_modules(self, request, pk=None):
        """Update enabled modules for a resume."""
        resume = self.get_object()
        enabled = request.data.get('enabled_modules', [])
        module_data = request.data.get('module_data', None)

        if not isinstance(enabled, list):
            return Response({'detail': 'enabled_modules error'}, status=status.HTTP_400_BAD_REQUEST)
        if len(enabled) > Resume.MAX_CONFIGURABLE:
            return Response(
                {'detail': f'max {Resume.MAX_CONFIGURABLE} modules'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resume.enabled_modules = enabled
        if module_data is not None:
            resume.module_data = module_data
        resume.save()
        return Response(ResumeDetailSerializer(resume).data)

    @action(detail=True, methods=['post'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """Export resume as PDF with selected modules."""
        resume = self.get_object()
        serializer = PdfExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected_modules = serializer.validated_data['modules']

        try:
            from .pdf_service import generate_resume_pdf
            pdf_buffer = generate_resume_pdf(resume, selected_modules)
            filename = f'{resume.user.username}_resume.pdf'
            return FileResponse(
                pdf_buffer, as_attachment=True, filename=filename,
                content_type='application/pdf',
            )
        except ImportError:
            return Response(
                {'detail': 'PDF dependency missing'},
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )
        except Exception as e:
            logger.error(f'PDF generation failed: {e}')
            return Response({'detail': f'PDF failed: {str(e)}'}, status=500)

    @action(detail=True, methods=['post'], url_path='set-tags')
    def set_tags(self, request, pk=None):
        """Set tags for a resume."""
        resume = self.get_object()
        tag_ids = request.data.get('tag_ids', [])
        tags = Tag.objects.filter(id__in=tag_ids)
        resume.tags.set(tags)
        return Response(ResumeDetailSerializer(resume).data)

    # -- Visitor Link Management (with HR mode) ------------------------

    @action(detail=True, methods=['post'], url_path='generate-visitor-link')
    def generate_visitor_link(self, request, pk=None):
        """
        Generate or regenerate a visitor access link.
        Body params: enabled, expires_days, allow_download, public_modules,
                     hr_enabled, ai_enabled, ai_quota
        """
        resume = self.get_object()
        serializer = VisitorLinkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        resume.generate_visitor_token()
        resume.visitor_enabled = data.get('enabled', True)
        resume.visitor_allow_download = data.get('allow_download', False)

        if 'public_modules' in data:
            resume.public_modules = data['public_modules']

        # HR mode settings
        resume.visitor_hr_enabled = data.get('hr_enabled', False)
        resume.visitor_ai_enabled = data.get('ai_enabled', True)
        resume.visitor_ai_quota = data.get('ai_quota', 10)
        # Reset used count when regenerating
        resume.visitor_ai_used = 0

        expires_days = data.get('expires_days', 30)
        resume.visitor_expires = timezone.now() + timedelta(days=expires_days)
        resume.save()

        return Response(VisitorLinkSerializer(resume, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='disable-visitor-link')
    def disable_visitor_link(self, request, pk=None):
        """Disable the visitor access link."""
        resume = self.get_object()
        resume.visitor_enabled = False
        resume.visitor_hr_enabled = False
        resume.save()
        return Response(VisitorLinkSerializer(resume, context={'request': request}).data)

    @action(detail=True, methods=['get'], url_path='visitor-link-info')
    def visitor_link_info(self, request, pk=None):
        """Get current visitor link settings and URL."""
        resume = self.get_object()
        return Response(VisitorLinkSerializer(resume, context={'request': request}).data)


# -- CRUD ViewSets for sub-models -------------------------------------

class EducationViewSet(viewsets.ModelViewSet):
    """Education CRUD."""
    serializer_class = EducationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Education.objects.all()
        return Education.objects.filter(resume__user=user)

    def get_permissions(self):
        return [IsAuthenticated()]


class WorkExperienceViewSet(viewsets.ModelViewSet):
    """Work experience CRUD."""
    serializer_class = WorkExperienceSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return WorkExperience.objects.all()
        return WorkExperience.objects.filter(resume__user=user)

    def get_permissions(self):
        return [IsAuthenticated()]


class ProjectViewSet(viewsets.ModelViewSet):
    """Project CRUD."""
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Project.objects.all()
        return Project.objects.filter(resume__user=user)

    def get_permissions(self):
        return [IsAuthenticated()]


class SkillViewSet(viewsets.ModelViewSet):
    """Skill CRUD."""
    serializer_class = SkillSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Skill.objects.all()
        return Skill.objects.filter(resume__user=user)

    def get_permissions(self):
        return [IsAuthenticated()]

