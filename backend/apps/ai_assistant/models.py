"""AI Assistant models - with polish and classification logs."""
from django.db import models
from django.conf import settings


class QueryLog(models.Model):
    """Records AI assistant interaction history."""

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
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.query[:50]}'


class PolishLog(models.Model):
    """Records AI polish (text optimization) history."""

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
    module_name = models.CharField(max_length=50, blank=True, default='', verbose_name='所属模块')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SUCCESS,
        verbose_name='状态',
    )
    tokens_used = models.IntegerField(default=0, verbose_name='消耗Token数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='处理时间')

    class Meta:
        verbose_name = '润色日志'
        verbose_name_plural = '润色日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} 润色: {self.original_text[:30]}...'


class ClassificationLog(models.Model):
    """Records AI auto-classification history."""

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
    classification_result = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='归类结果',
    )
    modules_assigned = models.JSONField(
        default=list,
        blank=True,
        verbose_name='分配模块',
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.SUCCESS,
        verbose_name='状态',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='处理时间')

    class Meta:
        verbose_name = '归类日志'
        verbose_name_plural = '归类日志'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} 归类: {self.file_name}'

