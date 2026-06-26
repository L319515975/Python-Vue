"""
AI 助手模块的序列化器 —— 定义 AI 功能相关的数据格式。

本文件包含：
1. 日志序列化器（查询日志、润色日志、分类日志）—— 用于后台查看 AI 使用记录
2. 请求/响应序列化器（对话请求、润色请求）—— 用于验证 API 请求参数

知识点：
- Serializer：通用序列化器，不依赖数据库模型，用于验证请求数据
- ModelSerializer：基于数据库模型的序列化器，用于展示数据库记录
- help_text：字段的说明文本，会在 API 文档（Swagger）中显示
"""
from rest_framework import serializers
from .models import QueryLog, PolishLog, ClassificationLog


class QueryLogSerializer(serializers.ModelSerializer):
    """
    AI 对话日志序列化器 —— 展示 AI 问答记录。

    每次用户向 AI 提问，系统都会记录：
    - 谁（username）在什么时间（created_at）问了什么（query）
    - AI 回答了什么（response），识别的意图是什么（intent），消耗了多少 token
    """
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = QueryLog
        fields = ['id', 'user', 'username', 'query', 'response', 'intent',
                  'tokens_used', 'created_at']
        read_only_fields = ['id', 'user', 'response', 'intent', 'tokens_used', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    """
    AI 对话请求序列化器 —— 验证用户发来的对话请求。

    请求格式：{ "query": "我的项目经历有哪些？" }
    """
    query = serializers.CharField(max_length=2000, help_text='用户查询内容')


class ChatResponseSerializer(serializers.Serializer):
    """
    AI 对话响应序列化器 —— 定义返回格式。

    响应格式：{ "response": "您有3个项目...", "intent": "project", "tokens_used": 150 }
    """
    response = serializers.CharField()
    intent = serializers.CharField()
    tokens_used = serializers.IntegerField()


class PolishRequestSerializer(serializers.Serializer):
    """
    文本润色请求序列化器 —— 验证润色请求参数。

    请求格式：{ "text": "负责后端开发", "module_name": "work_experience" }
    module_name 是可选的，用于告诉 AI 这段文字属于哪个模块，以便更精准地润色。
    """
    text = serializers.CharField(max_length=10000, help_text='需要润色的文本内容')
    module_name = serializers.CharField(
        max_length=50, required=False, default='',
        help_text='所属模块名称（如 education, project, skill）',
    )


class PolishResponseSerializer(serializers.Serializer):
    """
    文本润色响应序列化器。

    响应格式：
    {
        "original_text": "负责后端开发",
        "polished_text": "主导后端架构设计与核心功能开发",
        "tokens_used": 80,
        "status": "success"
    }
    """
    original_text = serializers.CharField()
    polished_text = serializers.CharField()
    tokens_used = serializers.IntegerField()
    status = serializers.CharField()


class PolishLogSerializer(serializers.ModelSerializer):
    """
    文本润色日志序列化器 —— 展示润色历史记录。

    记录每次润色的原文、润色结果、所属模块、状态和 token 消耗。
    """
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = PolishLog
        fields = ['id', 'user', 'username', 'original_text', 'polished_text',
                  'module_name', 'status', 'tokens_used', 'created_at']
        read_only_fields = fields  # 所有字段都是只读（日志不可修改）


class ClassificationLogSerializer(serializers.ModelSerializer):
    """
    文件分类日志序列化器 —— 展示 AI 自动分类记录。

    当用户上传简历文件时，AI 会自动解析内容并分类到各模块，
    这个序列化器用于展示分类的结果和状态。
    """
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ClassificationLog
        fields = ['id', 'user', 'username', 'file_name', 'classification_result',
                  'modules_assigned', 'status', 'created_at']
        read_only_fields = fields