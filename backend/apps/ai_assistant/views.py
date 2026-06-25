"""AI Assistant views - with polish and classification endpoints."""
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
    """Query log view - admin can see all, users can see own logs."""
    serializer_class = QueryLogSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return QueryLog.objects.select_related('user').all()
        return QueryLog.objects.filter(user=user)

    def get_permissions(self):
        return [IsAuthenticated()]


class PolishLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Polish log view - admin can see all, users can see own logs."""
    serializer_class = PolishLogSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return PolishLog.objects.select_related('user').all()
        return PolishLog.objects.filter(user=user)

    def get_permissions(self):
        return [IsAuthenticated()]


class ClassificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Classification log view - admin only."""
    serializer_class = ClassificationLogSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        return ClassificationLog.objects.select_related('user').all()


class AIAssistantViewSet(viewsets.ViewSet):
    """AI Assistant endpoints: chat, polish, classify."""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='chat')
    def chat(self, request):
        """Send a query to the AI assistant."""
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data['query']
        result = ask_ai(request.user, query)

        # Save query log
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
        """Polish/optimize text content using AI."""
        serializer = PolishRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text = serializer.validated_data['text']
        module_name = serializer.validated_data.get('module_name', '')

        result = polish_text(text, module_name, request.user)

        # Save polish log
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
        """Get current user's chat history."""
        limit = int(request.query_params.get('limit', 20))
        logs = QueryLog.objects.filter(user=request.user)[:limit]
        serializer = QueryLogSerializer(logs, many=True)
        return Response(serializer.data)
