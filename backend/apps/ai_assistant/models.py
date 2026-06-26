"""AI助手模型 - 记录AI功能的使用日志。

本模块定义了三种AI功能的日志模型：
1. QueryLog（查询日志）：记录用户向AI助手提问的历史
2. PolishLog（润色日志）：记录AI文本润色的历史
3. ClassificationLog（归类日志）：记录AI自动分类简历内容的历史

为什么需要记录日志？
- 监控AI使用量和Token消耗（控制成本）
- 排查AI回答质量问题（调试和改进）
- 安全审计（防止滥用）
- 数据分析（了解用户最常问什么）
"""
from django.db import models
from django.conf import settings


class QueryLog(models.Model):
    """AI查询日志 - 记录用户与AI助手的对话历史。

    每次用户向AI助手提问时，系统会记录：
    - 谁（user）问了什么（query）
    - AI回答了什么（response）
    - AI识别出的意图（intent）
    - 消耗了多少Token（tokens_used）

    意图识别（intent）是AI根据用户问题自动判断的类别：
    - education: 教育背景相关
    - work_experience: 工作经历相关
    - project: 项目经历相关
    - skill: 技能相关
    - summary: 个人简介相关
    - general: 综合查询
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='query_logs',
        verbose_name='用户',
    )
    query = models.TextField(verbose_name='查询内容')
    response = models.TextField(blank=True, default='', verbose_name='回复结果')
    intent = models.CharField(max_length=50, blank=True, default='', verbose_name='识别意图')
    tokens_used = models.IntegerField(default=0, verbose_name='消耗Token数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='查询时间')

    class Meta:
        verbose_name = '查询日志'
        verbose_name_plural = '查询日志'
        ordering = ['-created_at']  # 最新的查询排在前面

    def __str__(self):
        return f'{self.user.username}: {self.query[:50]}'


class PolishLog(models.Model):
    """AI润色日志 - 记录文本润色功能的使用历史。

    润色功能用于优化简历中的文本表达，使其更专业、更精练。
    记录原始文本和润色后的结果，方便对比和回溯。
    """

    class Status(models.TextChoices):
        SUCCESS = 'success', '成功'
        FAILED = 'failed', '失败'
        TIMEOUT = 'timeout', '超时'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='polish_logs',
        verbose_name='用户',
    )
    original_text = models.TextField(verbose_name='原始文本')
    polished_text = models.TextField(blank=True, default='', verbose_name='润色结果')
    # module_name 记录润色的是哪个模块的内容（如 summary, work_experience 等）
    module_name = models.CharField(max_length=50, blank=True, default='', verbose_name='所属模块')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUCCESS, verbose_name='状态')
    tokens_used = models.IntegerField(default=0, verbose_name='消耗Token数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='处理时间')

    class Meta:
        verbose_name = '润色日志'
        verbose_name_plural = '润色日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} 润色: {self.original_text[:30]}...'


class ClassificationLog(models.Model):
    """AI归类日志 - 记录简历文件自动分类的历史。

    当用户上传简历文件（PDF/Word/Markdown）时，
    AI会自动解析文件内容并将其归类到不同的模块中（教育、工作、项目、技能等）。
    这个日志记录了分类的过程和结果。
    """

    class Status(models.TextChoices):
        SUCCESS = 'success', '成功'
        FAILED = 'failed', '失败'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='classification_logs',
        verbose_name='用户',
    )
    file_name = models.CharField(max_length=255, verbose_name='文件名')
    raw_text = models.TextField(blank=True, default='', verbose_name='原始文本')
    # classification_result 存储AI的分类结果，如 {'education': '...', 'skill': '...'}
    classification_result = models.JSONField(default=dict, blank=True, verbose_name='归类结果')
    # modules_assigned 存储分配到的模块列表，如 ['education', 'skill']
    modules_assigned = models.JSONField(default=list, blank=True, verbose_name='分配模块')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUCCESS, verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='处理时间')

    class Meta:
        verbose_name = '归类日志'
        verbose_name_plural = '归类日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} 归类: {self.file_name}'