"""AI助手视图模块 - 处理AI功能的API请求。

本模块提供三个AI功能的API：
1. AI对话（chat）：用户向AI助手提问，AI根据简历内容回答
2. 文本润色（polish）：用户提交文本，AI优化表达使其更专业
3. 文件分类（classify）：上传简历文件后AI自动将内容归类到不同模块

还有三个只读的日志查看ViewSet：
- QueryLogViewSet：查看AI对话日志
- PolishLogViewSet：查看润色日志
- ClassificationLogViewSet：查看分类日志（仅管理员）
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import QueryLog, PolishLog, ClassificationLog
from .serializers import (
    QueryLogSerializer, ChatRequestSerializer,
    PolishRequestSerializer, PolishResponseSerializer,
    PolishLogSerializer, ClassificationLogSerializer,
)
from .services import ask_ai, polish_text, classify_resume_file
from apps.users.permissions import IsAdminRole


class QueryLogViewSet(viewsets.ReadOnlyModelViewSet):
    """查询日志ViewSet - 只读，管理员可看所有，普通用户只能看自己的。

    ReadOnlyModelViewSet 只提供 list（列表）和 retrieve（详情）操作，
    不提供 create、update、delete 操作（日志不允许修改）。
    """
    serializer_class = QueryLogSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return QueryLog.objects.select_related('user').all()
        return QueryLog.objects.filter(user=user)

    def get_permissions(self):
        return [IsAuthenticated()]


class PolishLogViewSet(viewsets.ReadOnlyModelViewSet):
    """润色日志ViewSet - 只读，管理员可看所有，普通用户只能看自己的。"""
    serializer_class = PolishLogSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return PolishLog.objects.select_related('user').all()
        return PolishLog.objects.filter(user=user)

    def get_permissions(self):
        return [IsAuthenticated()]


class ClassificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """分类日志ViewSet - 只读，仅管理员可查看。"""
    serializer_class = ClassificationLogSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        return ClassificationLog.objects.select_related('user').all()


class AIAssistantViewSet(viewsets.ViewSet):
    """AI助手ViewSet - 提供对话、润色、分类三个功能接口。

    这个ViewSet不基于Model，而是自定义action处理AI请求。
    每个action对应一个独立的AI功能。
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='chat')
    def chat(self, request):
        """AI对话接口 - 用户发送问题，AI根据简历内容回答。

        请求体：{ "query": "我的教育背景是什么？" }
        返回：{ "response": "AI的回答...", "intent": "education", "tokens_used": 150 }

        处理流程：
        1. 验证请求数据
        2. 调用AI服务获取回答
        3. 保存查询日志
        4. 返回结果给前端
        """
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data['query']
        result = ask_ai(request.user, query)

        # 保存查询日志（异步场景下可以用Celery异步保存）
        QueryLog.objects.create(
            user=request.user,
            query=query,
            response=result['response'],
            intent=result['intent'],
            tokens_used=result['tokens_used'],
        )

        return Response({
            'response': result['response'],
            'intent': result['intent'],
            'tokens_used': result['tokens_used'],
        })

    @action(detail=False, methods=['post'], url_path='polish')
    def polish(self, request):
        """文本润色接口 - 用户提交文本，AI优化表达。

        请求体：{ "text": "原始文本...", "module_name": "summary" }
        返回：{ "original_text": "...", "polished_text": "优化后...", "tokens_used": 100, "status": "success" }
        """
        serializer = PolishRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text = serializer.validated_data['text']
        module_name = serializer.validated_data.get('module_name', '')

        result = polish_text(text, module_name, request.user)

        # 保存润色日志
        PolishLog.objects.create(
            user=request.user,
            original_text=result['original_text'],
            polished_text=result.get('polished_text', ''),
            module_name=module_name,
            status=result['status'],
            tokens_used=result.get('tokens_used', 0),
        )

        return Response({
            'original_text': result['original_text'],
            'polished_text': result.get('polished_text', ''),
            'tokens_used': result.get('tokens_used', 0),
            'status': result['status'],
        })

    @action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        """获取当前用户的AI对话历史。

        查询参数：limit（返回条数，默认20）
        """
        limit = int(request.query_params.get('limit', 20))
        logs = QueryLog.objects.filter(user=request.user)[:limit]
        serializer = QueryLogSerializer(logs, many=True)
        return Response(serializer.data)