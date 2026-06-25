"""AI Assistant serializers."""
from rest_framework import serializers
from .models import QueryLog, PolishLog, ClassificationLog


class QueryLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = QueryLog
        fields = ['id', 'user', 'username', 'query', 'response', 'intent',
                  'tokens_used', 'created_at']
        read_only_fields = ['id', 'user', 'response', 'intent', 'tokens_used', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for AI chat requests."""
    query = serializers.CharField(max_length=2000, help_text='用户查询内容')


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for AI chat responses."""
    response = serializers.CharField()
    intent = serializers.CharField()
    tokens_used = serializers.IntegerField()


class PolishRequestSerializer(serializers.Serializer):
    """Serializer for text polish requests."""
    text = serializers.CharField(max_length=10000, help_text='需要润色的文本内容')
    module_name = serializers.CharField(
        max_length=50, required=False, default='',
        help_text='所属模块名称（如 education, project, skill）',
    )


class PolishResponseSerializer(serializers.Serializer):
    """Serializer for text polish responses."""
    original_text = serializers.CharField()
    polished_text = serializers.CharField()
    tokens_used = serializers.IntegerField()
    status = serializers.CharField()


class PolishLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = PolishLog
        fields = ['id', 'user', 'username', 'original_text', 'polished_text',
                  'module_name', 'status', 'tokens_used', 'created_at']
        read_only_fields = fields


class ClassificationLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ClassificationLog
        fields = ['id', 'user', 'username', 'file_name', 'classification_result',
                  'modules_assigned', 'status', 'created_at']
        read_only_fields = fields
