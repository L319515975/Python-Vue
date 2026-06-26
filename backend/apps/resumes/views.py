"""
简历模块的视图层 —— 处理所有与简历相关的 HTTP 请求。

本文件包含：
1. 公开的访客 API（无需登录即可访问）
2. 标签（Tag）的增删改查
3. 简历（Resume）的增删改查，包括文件上传、模块管理、PDF导出
4. 访客链接管理（支持HR模式和AI对话）
5. 子模型（教育经历、工作经历、项目、技能）的增删改查

知识点：
- @api_view：DRF 提供的装饰器，把普通函数变成 API 接口
- @permission_classes：设置接口的权限，AllowAny 表示任何人都能访问
- viewsets.ModelViewSet：DRF 提供的视图集，自动提供 list/create/retrieve/update/destroy 方法
- @action：在 ViewSet 中添加自定义接口方法
"""
import io                                    # 用于内存中的字节流操作（PDF生成）
import logging                               # 日志记录模块，用于记录错误和调试信息
from datetime import timedelta               # 时间差计算，用于设置链接过期时间

from rest_framework import viewsets, status   # DRF 的视图集和状态码
from rest_framework.decorators import action, api_view, permission_classes  # 装饰器工具
from rest_framework.response import Response  # DRF 的响应对象
from rest_framework.permissions import IsAuthenticated, AllowAny  # 权限类
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser  # 文件解析器
from django.http import FileResponse, JsonResponse  # Django 响应：文件下载、JSON
from django.utils import timezone            # Django 时区工具，获取当前时间

# 从本应用的 models.py 导入所有数据模型
from .models import Resume, Education, WorkExperience, Project, Skill, Tag, AdminAuditLog, HRAiUsageLog
# 从本应用的 serializers.py 导入所有序列化器
from .serializers import (
    ResumeListSerializer, ResumeDetailSerializer, ResumeCreateUpdateSerializer,
    EducationSerializer, WorkExperienceSerializer, ProjectSerializer, SkillSerializer,
    TagSerializer, TagCreateSerializer, PdfExportSerializer,
    VisitorLinkSerializer, VisitorLinkUpdateSerializer,
)
# 从访客工具模块导入安全和数据过滤函数
from .visitor_utils import (
    verify_visitor_signature, is_visitor_link_valid, get_visitor_url,
    filter_visitor_data, check_hr_ai_quota, generate_visitor_signature,
)
# 从用户应用导入自定义权限类
from apps.users.permissions import IsAdminRole, IsOwnerOrAdmin

# 创建本模块的日志记录器，用于输出调试和错误信息
logger = logging.getLogger(__name__)


# ========== 辅助函数 ==========

def _log_audit(request, action_type, target_user='', detail=''):
    """
    记录管理员操作审计日志。

    作用：当管理员执行敏感操作（如修改简历、删除标签）时，自动记录"谁在什么时候做了什么"。
    参数说明：
        request      —— 当前的 HTTP 请求对象，包含请求者信息
        action_type  —— 操作类型标识，如 'tag_create'、'resume_update'
        target_user  —— 被操作的目标用户名（可选）
        detail       —— 操作的详细描述（可选）
    """
    try:
        # 获取客户端真实 IP 地址
        # HTTP_X_FORWARDED_FOR：如果请求经过代理/负载均衡器，会包含原始 IP
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        # 取第一个 IP（最左边的是原始客户端 IP）
        ip = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')
        # 创建审计日志记录
        AdminAuditLog.objects.create(
            admin_user=request.user,   # 执行操作的管理员
            action=action_type,        # 操作类型
            target_user=target_user,   # 目标用户
            detail=detail,             # 操作详情
            ip_address=ip,             # 客户端 IP
        )
    except Exception as e:
        # 记录审计日志本身不应影响正常业务，所以捕获异常但不抛出
        logger.warning(f'审计日志创建失败: {e}')


def _get_client_ip(request):
    """
    从请求中提取客户端真实 IP 地址。

    原理：Web 应用通常部署在 Nginx/Apache 反向代理后面，
    直接读取 REMOTE_ADDR 拿到的是代理服务器的 IP，
    真实客户端 IP 存放在 HTTP_X_FORWARDED_FOR 头中。
    """
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')


# ========== 公开的访客 API（无需登录） ==========
# 这些接口面向外部访客（如 HR 查看候选人简历），不需要 JWT 认证

@api_view(['GET'])                # 只接受 GET 请求
@permission_classes([AllowAny])   # 允许任何人访问（无需登录）
def visitor_resume_view(request, token):
    """
    公开接口：通过访客链接查看简历。

    访问流程：
    1. 前端传入 token（简历的唯一访问标识）和签名参数
    2. 后端验证 HMAC 签名，防止链接被篡改
    3. 验证链接是否过期、是否被禁用
    4. 如果是 HR 角色，还需检查 HR 模式是否开启
    5. 返回经过过滤的公开简历数据（隐藏敏感字段）

    URL 示例：/api/resumes/visitor/abc123/?sig=xxx&expires=1234567890&role=hr
    """
    # 从 URL 查询参数中获取签名、过期时间和角色
    sig = request.query_params.get('sig', '')           # HMAC 签名
    expires = int(request.query_params.get('expires', 0))  # 链接过期时间戳（Unix时间戳）
    role = request.query_params.get('role', 'visitor')   # 角色：'visitor' 或 'hr'

    # 第一步：验证 HMAC 签名（防止链接被伪造或篡改）
    if not sig or not verify_visitor_signature(token, expires, sig, role):
        return JsonResponse({'detail': '访问链接无效或已被篡改'}, status=404)

    # 第二步：根据访客 token 查找对应的简历
    # select_related：用 SQL JOIN 一次性查询关联的 user 表（一对一/外键）
    # prefetch_related：用额外查询预加载多对多/一对多关联数据
    # 这样做是为了避免后续访问关联数据时产生 N+1 查询问题
    try:
        resume = Resume.objects.select_related('user').prefetch_related(
            'tags', 'educations', 'work_experiences', 'projects', 'skills'
        ).get(visitor_token=token)
    except Resume.DoesNotExist:
        return JsonResponse({'detail': '访问链接不存在'}, status=404)

    # 第三步：验证链接状态（是否启用、是否过期等）
    validity = is_visitor_link_valid(resume)
    if not validity['valid']:
        return JsonResponse({'detail': validity['reason']}, status=404)

    # 第四步：检查 URL 中的过期时间参数（双重验证）
    if expires and expires < int(timezone.now().timestamp()):
        return JsonResponse({'detail': '访问链接已过期'}, status=404)

    # 第五步：如果是 HR 角色，检查简历是否开启了 HR 模式
    if role == 'hr' and not resume.visitor_hr_enabled:
        return JsonResponse({'detail': '该链接未启用HR模式'}, status=403)

    # 第六步：过滤敏感数据后返回（如隐藏联系方式、身份证等）
    data = filter_visitor_data(resume)
    # ensure_ascii=False 让 JSON 正常显示中文（不转义为 \uXXXX）
    return JsonResponse(data, json_dumps_params={'ensure_ascii': False})


@api_view(['GET'])
@permission_classes([AllowAny])
def visitor_download_pdf(request, token):
    """
    公开接口：通过访客链接下载简历 PDF。

    流程与 visitor_resume_view 类似，额外检查简历是否允许下载。
    """
    sig = request.query_params.get('sig', '')
    expires = int(request.query_params.get('expires', 0))
    role = request.query_params.get('role', 'visitor')

    if not sig or not verify_visitor_signature(token, expires, sig, role):
        return JsonResponse({'detail': '访问链接无效'}, status=404)

    try:
        resume = Resume.objects.select_related('user').get(visitor_token=token)
    except Resume.DoesNotExist:
        return JsonResponse({'detail': '访问链接不存在'}, status=404)

    validity = is_visitor_link_valid(resume)
    if not validity['valid']:
        return JsonResponse({'detail': validity['reason']}, status=404)

    # 检查简历是否允许访客下载 PDF
    if not resume.visitor_allow_download:
        return JsonResponse({'detail': '该简历未授权游客下载'}, status=403)

    try:
        # 动态导入 PDF 生成服务（避免循环导入）
        from .pdf_service import generate_resume_pdf
        # 获取简历的公开模块列表
        public_modules = resume.get_public_modules()
        # 生成 PDF 文件（返回内存中的字节流）
        pdf_buffer = generate_resume_pdf(resume, public_modules)
        filename = f'{resume.user.username}_resume.pdf'
        # FileResponse 会自动处理文件流的传输
        return FileResponse(
            pdf_buffer,
            as_attachment=True,    # 告诉浏览器这是下载而不是预览
            filename=filename,     # 下载时的文件名
            content_type='application/pdf',
        )
    except ImportError:
        return JsonResponse({'detail': 'PDF生成服务不可用'}, status=501)
    except Exception as e:
        logger.error(f'访客 PDF 下载失败: {e}')
        return JsonResponse({'detail': 'PDF生成失败'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def visitor_ai_chat(request, token):
    """
    公开接口：HR 访客 AI 对话。

    仅限 HR 角色使用，支持两种模式：
    - chat：基于简历内容的问答（如"这个人的项目经历是什么？"）
    - polish：文本润色（如优化一段简历描述）

    流程：
    1. 验证签名和 HR 角色
    2. 检查 AI 配额（每个访客链接有使用次数限制）
    3. 调用 AI 服务获取结果
    4. 更新已用配额并记录使用日志
    """
    sig = request.query_params.get('sig', '')
    expires = int(request.query_params.get('expires', 0))
    role = request.query_params.get('role', 'visitor')

    # 只允许 HR 角色使用 AI 功能
    if role != 'hr':
        return JsonResponse({'detail': '普通游客无权使用AI功能'}, status=403)

    if not sig or not verify_visitor_signature(token, expires, sig, 'hr'):
        return JsonResponse({'detail': '访问链接无效或已被篡改'}, status=404)

    try:
        resume = Resume.objects.select_related('user').prefetch_related(
            'tags', 'educations', 'work_experiences', 'projects', 'skills'
        ).get(visitor_token=token)
    except Resume.DoesNotExist:
        return JsonResponse({'detail': '访问链接不存在'}, status=404)

    validity = is_visitor_link_valid(resume)
    if not validity['valid']:
        return JsonResponse({'detail': validity['reason']}, status=404)

    if expires and expires < int(timezone.now().timestamp()):
        return JsonResponse({'detail': '访问链接已过期'}, status=404)

    if not resume.visitor_hr_enabled:
        return JsonResponse({'detail': '该链接未启用HR模式'}, status=403)

    # 检查 AI 使用配额（防止滥用）
    quota_info = check_hr_ai_quota(resume)
    if not quota_info['available']:
        return JsonResponse({
            'detail': quota_info['reason'],    # 配额用尽的原因
            'quota_exhausted': True,           # 标记配额已用完
            'remaining': 0,                    # 剩余次数
            'total': quota_info['total'],      # 总配额
        }, status=429)  # 429 = Too Many Requests（请求过多）

    # 获取用户的查询内容
    query = request.data.get('query', '').strip()
    if not query:
        return JsonResponse({'detail': '查询内容为空'}, status=400)

    call_type = request.data.get('call_type', 'chat')      # 调用类型：chat 或 polish
    module_name = request.data.get('module_name', '')       # 模块名（润色时指定）

    try:
        from apps.ai_assistant.services import ask_ai, polish_text

        # 根据调用类型选择不同的 AI 服务
        if call_type == 'polish':
            result = polish_text(query, module_name, resume=resume)
        else:
            result = ask_ai(resume=resume, query=query)

        # 递增已用 AI 次数
        resume.visitor_ai_used += 1
        resume.save(update_fields=['visitor_ai_used'])  # 只更新这一个字段，提高效率

        # 记录 HR AI 使用日志（用于统计和审计）
        ip = _get_client_ip(request)
        HRAiUsageLog.objects.create(
            resume=resume,
            visitor_token=token,
            call_type=call_type,
            query_text=query[:2000],                    # 截断防止超长文本
            response_text=result.get('response', result.get('polished_text', ''))[:5000],
            tokens_used=result.get('tokens_used', 0),
            ip_address=ip,
        )

        # 计算剩余 AI 使用次数
        remaining = max(0, resume.visitor_ai_quota - resume.visitor_ai_used)

        response_data = {
            'remaining': remaining,                    # 剩余次数
            'total': resume.visitor_ai_quota,          # 总配额
            'tokens_used': result.get('tokens_used', 0),  # 消耗的 token 数
        }

        # 根据调用类型返回不同格式的响应
        if call_type == 'polish':
            response_data['original_text'] = result.get('original_text', query)
            response_data['polished_text'] = result.get('polished_text', '')
            response_data['status'] = result.get('status', 'success')
        else:
            response_data['response'] = result.get('response', '')
            response_data['intent'] = result.get('intent', 'general')

        return JsonResponse(response_data, json_dumps_params={'ensure_ascii': False})

    except Exception as e:
        logger.error(f'HR AI 对话失败: {e}')
        return JsonResponse({'detail': f'AI服务调用失败: {str(e)}'}, status=500)


# ========== 标签（Tag）视图集 ==========
# 管理员可以增删改查标签，普通用户只能查看标签列表

class TagViewSet(viewsets.ModelViewSet):
    """
    标签的增删改查视图集。

    权限规则：
    - list（列表）和 retrieve（详情）：已登录用户即可
    - create（创建）、update（更新）、destroy（删除）：仅管理员

    标签示例：'Python'、'3年经验'、'985院校' 等。
    标签用于给简历打标记，方便搜索和筛选。
    """
    queryset = Tag.objects.all()               # 查询所有标签
    filterset_fields = ['tag_type', 'is_system']  # 支持按标签类型和是否系统标签筛选
    search_fields = ['name']                      # 支持按名称搜索
    ordering_fields = ['name', 'tag_type', 'created_at']  # 支持排序的字段

    def get_serializer_class(self):
        """根据操作类型选择不同的序列化器。"""
        if self.action in ('create', 'update', 'partial_update'):
            return TagCreateSerializer   # 创建/更新时使用创建专用序列化器
        return TagSerializer             # 其他操作使用通用序列化器

    def get_permissions(self):
        """
        根据操作类型设置不同的权限。

        原理：DRF 会在调用视图方法前先执行 get_permissions()，
        返回的权限对象列表中的每个对象都会调用 has_permission() 检查。
        """
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]   # 查看操作：已登录即可
        return [IsAdminRole()]           # 写入操作：需要管理员角色

    def perform_create(self, serializer):
        """
        创建标签时自动记录审计日志。

        perform_create 是 DRF 的钩子方法，在 serializer.save() 时自动调用。
        """
        serializer.save()
        _log_audit(request=self.request, action_type='tag_create',
                   detail=f'创建标签: {serializer.instance.name}')

    def perform_update(self, serializer):
        """更新标签时自动记录审计日志。"""
        serializer.save()
        _log_audit(request=self.request, action_type='tag_update',
                   detail=f'修改标签: {serializer.instance.name}')

    def perform_destroy(self, instance):
        """删除标签时自动记录审计日志。"""
        name = instance.name
        instance.delete()
        _log_audit(request=self.request, action_type='tag_delete',
                   detail=f'删除标签: {name}')


# ========== 简历（Resume）视图集 ==========
# 这是整个系统的核心视图，处理简历的 CRUD、文件上传、模块管理、访客链接等

class ResumeViewSet(viewsets.ModelViewSet):
    """
    简历的增删改查视图集。

    权限规则：
    - 管理员：可以查看和操作所有用户的简历
    - 普通用户：只能查看和操作自己的简历

    包含的自定义接口（通过 @action 装饰器实现）：
    - upload_file：上传简历文件并自动分类
    - update_modules：更新简历的启用模块
    - export_pdf：导出简历为 PDF
    - set_tags：设置简历标签
    - generate_visitor_link：生成访客链接
    - disable_visitor_link：禁用访客链接
    - visitor_link_info：查看访客链接信息
    """
    filterset_fields = ['status', 'ai_processed']      # 支持按状态和AI处理状态筛选
    search_fields = ['title', 'summary']                # 支持按标题和摘要搜索
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # 支持文件上传和JSON

    def get_queryset(self):
        """
        根据用户角色返回不同的查询集。

        原理：admin 看所有简历，普通用户只看自己的。
        select_related 和 prefetch_related 用于优化数据库查询性能。
        """
        user = self.request.user
        if user.role == 'admin':
            return Resume.objects.select_related('user').prefetch_related('tags').all()
        return Resume.objects.select_related('user').prefetch_related('tags').filter(user=user)

    def get_serializer_class(self):
        """根据操作类型选择序列化器：列表用轻量版，详情用完整版。"""
        if self.action == 'list':
            return ResumeListSerializer            # 列表：只返回基本信息，不含嵌套数据
        if self.action in ('create', 'update', 'partial_update'):
            return ResumeCreateUpdateSerializer    # 创建/更新：接受写入字段
        return ResumeDetailSerializer              # 详情：返回完整嵌套数据

    def get_permissions(self):
        """所有简历操作都需要登录。"""
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """创建简历时自动关联当前登录用户。"""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """更新简历时，如果是管理员操作则记录审计日志。"""
        instance = serializer.save()
        if self.request.user.role == 'admin':
            _log_audit(request=self.request, action_type='resume_update',
                       target_user=instance.user.username,
                       detail=f'管理员修改简历: {instance.title}')

    def perform_destroy(self, instance):
        """删除简历时，如果是管理员操作则记录审计日志。"""
        if self.request.user.role == 'admin':
            _log_audit(request=self.request, action_type='resume_delete',
                       target_user=instance.user.username,
                       detail=f'管理员删除简历: {instance.title}')
        instance.delete()

    # ---------- 自定义接口 ----------

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser])
    def upload_file(self, request, pk=None):
        """
        上传简历文件（Word/PDF/Markdown/纯文本），支持自动 AI 分类。

        流程：
        1. 验证文件格式
        2. 保存文件到简历记录
        3. 如果开启自动分类，调用 AI 服务解析文件内容并归类到各模块

        detail=True 表示这是针对单个简历的操作，URL 中包含 pk（主键）
        """
        resume = self.get_object()  # 获取当前操作的简历实例
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': '请上传文件'}, status=status.HTTP_400_BAD_REQUEST)

        # 允许的文件 MIME 类型
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/markdown',
            'text/plain',
        ]
        # 同时检查 MIME 类型和文件扩展名（兼容性更好）
        if file.content_type not in allowed_types and not file.name.endswith(('.md', '.pdf', '.doc', '.docx')):
            return Response(
                {'detail': '仅支持 PDF、Word、Markdown 格式'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 保存上传的文件
        resume.file = file
        resume.file_name = file.name
        resume.save()

        # 自动 AI 分类（默认开启）
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
                logger.warning(f'自动分类失败: {e}')

        return Response(ResumeDetailSerializer(resume).data)

    @action(detail=True, methods=['post'], url_path='update-modules')
    def update_modules(self, request, pk=None):
        """
        更新简历的启用模块。

        简历由多个模块组成（教育经历、工作经历、项目、技能等），
        用户可以选择启用哪些模块，以及调整模块数据。

        请求体示例：
        {
            "enabled_modules": ["education", "work_experience", "project"],
            "module_data": {"summary": "我是..."}
        }
        """
        resume = self.get_object()
        enabled = request.data.get('enabled_modules', [])    # 要启用的模块列表
        module_data = request.data.get('module_data', None)  # 模块数据（可选）

        if not isinstance(enabled, list):
            return Response({'detail': 'enabled_modules 格式错误'}, status=status.HTTP_400_BAD_REQUEST)
        # 限制最多启用的模块数量
        if len(enabled) > Resume.MAX_CONFIGURABLE:
            return Response(
                {'detail': f'最多 {Resume.MAX_CONFIGURABLE} 个模块'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resume.enabled_modules = enabled
        if module_data is not None:
            resume.module_data = module_data
        resume.save()
        return Response(ResumeDetailSerializer(resume).data)

    @action(detail=True, methods=['post'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """
        导出简历为 PDF 文件。

        请求体示例：{ "modules": ["education", "work_experience", "project"] }
        """
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
            return Response({'detail': 'PDF依赖缺失'}, status=status.HTTP_501_NOT_IMPLEMENTED)
        except Exception as e:
            logger.error(f'PDF 生成失败: {e}')
            return Response({'detail': f'PDF 生成失败: {str(e)}'}, status=500)

    @action(detail=True, methods=['post'], url_path='set-tags')
    def set_tags(self, request, pk=None):
        """
        为简历设置标签（整体替换，不是追加）。

        请求体示例：{ "tag_ids": [1, 3, 5] }
        """
        resume = self.get_object()
        tag_ids = request.data.get('tag_ids', [])
        tags = Tag.objects.filter(id__in=tag_ids)
        resume.tags.set(tags)  # set() 方法会先清除旧的再设置新的
        return Response(ResumeDetailSerializer(resume).data)

    # ========== 访客链接管理（支持HR模式） ==========

    @action(detail=True, methods=['post'], url_path='generate-visitor-link')
    def generate_visitor_link(self, request, pk=None):
        """
        生成或重新生成访客访问链接。

        支持的参数：
        - enabled：是否启用链接
        - expires_days：链接有效期（天）
        - allow_download：是否允许下载 PDF
        - public_modules：公开哪些模块给访客
        - hr_enabled：是否启用 HR 模式
        - ai_enabled：是否允许 HR 使用 AI 功能
        - ai_quota：HR 的 AI 使用配额（次数）
        """
        resume = self.get_object()
        serializer = VisitorLinkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        resume.generate_visitor_token()  # 生成新的随机 token
        resume.visitor_enabled = data.get('enabled', True)
        resume.visitor_allow_download = data.get('allow_download', False)

        if 'public_modules' in data:
            resume.public_modules = data['public_modules']

        # HR 模式设置
        resume.visitor_hr_enabled = data.get('hr_enabled', False)
        resume.visitor_ai_enabled = data.get('ai_enabled', True)
        resume.visitor_ai_quota = data.get('ai_quota', 10)
        resume.visitor_ai_used = 0  # 重新生成时重置已用次数

        # 计算过期时间
        expires_days = data.get('expires_days', 30)
        resume.visitor_expires = timezone.now() + timedelta(days=expires_days)
        resume.save()

        return Response(VisitorLinkSerializer(resume, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='disable-visitor-link')
    def disable_visitor_link(self, request, pk=None):
        """禁用访客链接（同时禁用 HR 模式）。"""
        resume = self.get_object()
        resume.visitor_enabled = False
        resume.visitor_hr_enabled = False
        resume.save()
        return Response(VisitorLinkSerializer(resume, context={'request': request}).data)

    @action(detail=True, methods=['get'], url_path='visitor-link-info')
    def visitor_link_info(self, request, pk=None):
        """查看当前访客链接的配置信息和 URL。"""
        resume = self.get_object()
        return Response(VisitorLinkSerializer(resume, context={'request': request}).data)


# ========== 子模型 CRUD 视图集 ==========
# 教育经历、工作经历、项目、技能都是简历的子模型（通过外键关联）
# 它们的视图集结构几乎相同，区别只在于使用的模型和序列化器

class EducationViewSet(viewsets.ModelViewSet):
    """
    教育经历的增删改查。

    queryset 通过 get_queryset() 动态生成，
    确保普通用户只能操作自己的教育经历记录。
    """
    serializer_class = EducationSerializer

    def get_queryset(self):
        user = self.request.user
        base = Education.objects.select_related('resume', 'resume__user')
        if user.role == 'admin':
            return base.all()                # 管理员：查看所有
        return base.filter(resume__user=user)  # 普通用户：只看自己的

    def get_permissions(self):
        return [IsAuthenticated()]


class WorkExperienceViewSet(viewsets.ModelViewSet):
    """工作经历的增删改查。"""
    serializer_class = WorkExperienceSerializer

    def get_queryset(self):
        user = self.request.user
        base = WorkExperience.objects.select_related('resume', 'resume__user')
        if user.role == 'admin':
            return base.all()
        return base.filter(resume__user=user)

    def get_permissions(self):
        return [IsAuthenticated()]


class ProjectViewSet(viewsets.ModelViewSet):
    """项目经历的增删改查。"""
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user = self.request.user
        base = Project.objects.select_related('resume', 'resume__user')
        if user.role == 'admin':
            return base.all()
        return base.filter(resume__user=user)

    def get_permissions(self):
        return [IsAuthenticated()]


class SkillViewSet(viewsets.ModelViewSet):
    """技能的增删改查。"""
    serializer_class = SkillSerializer

    def get_queryset(self):
        user = self.request.user
        base = Skill.objects.select_related('resume', 'resume__user')
        if user.role == 'admin':
            return base.all()
        return base.filter(resume__user=user)

    def get_permissions(self):
        return [IsAuthenticated()]