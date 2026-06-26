"""
简历模块的序列化器 —— 将模型实例转换为 JSON（序列化），以及将 JSON 转换为模型实例（反序列化）。

本文件包含：
1. 标签序列化器（TagSerializer / TagCreateSerializer）
2. 子模型序列化器（教育、工作经历、项目、技能）
3. 访客链接序列化器（VisitorLinkSerializer / VisitorLinkUpdateSerializer）
4. 简历序列化器（列表版/详情版/创建更新版）
5. PDF 导出请求序列化器（PdfExportSerializer）

知识点：
- ModelSerializer：DRF 提供的序列化器，自动根据 Django 模型生成字段
- Serializer：手动定义字段的序列化器，适用于非模型数据
- read_only_fields：只读字段，只在输出时包含，不接受输入
- SerializerMethodField：自定义方法字段，通过 get_<字段名> 方法生成值
- PrimaryKeyRelatedField：以外键 ID 的形式表示关联对象
"""
from rest_framework import serializers
from .models import Resume, Education, WorkExperience, Project, Skill, Tag


class TagSerializer(serializers.ModelSerializer):
    """
    标签序列化器 —— 用于展示标签信息。

    字段说明：
    - id：标签的唯一标识（自动生成）
    - name：标签名称，如 'Python'、'985院校'
    - tag_type：标签类型，如 'skill'、'education'
    - is_system：是否为系统预设标签（管理员创建的标签）
    - created_at：创建时间
    """
    class Meta:
        model = Tag
        fields = ['id', 'name', 'tag_type', 'is_system', 'created_at']
        read_only_fields = ['id', 'is_system', 'created_at']


class TagCreateSerializer(serializers.ModelSerializer):
    """
    标签创建序列化器 —— 用于管理员创建标签。

    与 TagSerializer 的区别：
    - 创建时自动设置 is_system=True（表示这是系统标签）
    - 不包含 is_system 和 created_at 的输入字段
    """
    class Meta:
        model = Tag
        fields = ['id', 'name', 'tag_type']
        read_only_fields = ['id']

    def create(self, validated_data):
        """
        重写 create 方法，在保存前自动设置 is_system=True。

        validated_data 是经过验证后的数据字典。
        """
        validated_data['is_system'] = True
        return super().create(validated_data)


class EducationSerializer(serializers.ModelSerializer):
    """
    教育经历序列化器。

    包含字段：学校、学位、专业、起止时间、描述等（由 models.py 定义）。
    fields = '__all__' 表示包含模型的所有字段。
    """
    class Meta:
        model = Education
        fields = '__all__'            # 包含所有字段
        read_only_fields = ['id']    # id 只读


class WorkExperienceSerializer(serializers.ModelSerializer):
    """工作经历序列化器。"""
    class Meta:
        model = WorkExperience
        fields = '__all__'
        read_only_fields = ['id']


class ProjectSerializer(serializers.ModelSerializer):
    """项目经历序列化器。"""
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id']


class SkillSerializer(serializers.ModelSerializer):
    """技能序列化器。"""
    class Meta:
        model = Skill
        fields = '__all__'
        read_only_fields = ['id']


class VisitorLinkSerializer(serializers.ModelSerializer):
    """
    访客链接信息序列化器 —— 用于展示访客链接配置。

    包含两部分字段：
    1. 基础访客字段：是否启用、token、过期时间、允许下载等
    2. HR 模式字段：HR 模式开关、AI 功能开关、AI 配额

    visitor_url 是通过 SerializerMethodField 动态生成的完整访问链接。
    """
    visitor_url = serializers.SerializerMethodField()  # 自定义方法字段

    class Meta:
        model = Resume
        fields = [
            'visitor_enabled',          # 是否启用访客链接
            'visitor_token',            # 访客 token（唯一标识）
            'visitor_expires',          # 链接过期时间
            'visitor_allow_download',   # 是否允许下载
            'public_modules',           # 公开的模块列表
            'visitor_url',              # 完整的访客访问 URL（动态生成）
            # HR 模式字段
            'visitor_hr_enabled',       # 是否启用 HR 模式
            'visitor_ai_enabled',       # 是否允许 HR 使用 AI
            'visitor_ai_quota',         # HR 的 AI 使用配额
            'visitor_ai_used',          # HR 已使用的 AI 次数
        ]
        read_only_fields = ['visitor_token', 'visitor_ai_used']

    def get_visitor_url(self, obj):
        """
        动态生成完整的访客访问 URL。

        原理：根据当前请求的域名和简历的 visitor_token，
        拼接出完整的前端页面 URL（如 http://example.com/visitor/abc123）。
        """
        if not obj.visitor_enabled or not obj.visitor_token:
            return ''
        from .visitor_utils import get_visitor_url
        request = self.context.get('request')  # 从上下文获取当前请求对象
        return get_visitor_url(obj, request)


class ResumeListSerializer(serializers.ModelSerializer):
    """
    简历列表序列化器 —— 轻量版，用于列表展示。

    与详情版的区别：
    - 不包含嵌套的教育/工作/项目/技能数据（减少数据量）
    - 使用计数字段代替完整列表（如 educations_count）

    知识点：source='user.username' 表示从关联的 user 对象取 username 字段。
    """
    username = serializers.CharField(source='user.username', read_only=True)
    educations_count = serializers.IntegerField(source='educations.count', read_only=True)
    work_experiences_count = serializers.IntegerField(source='work_experiences.count', read_only=True)
    projects_count = serializers.IntegerField(source='projects.count', read_only=True)
    skills_count = serializers.IntegerField(source='skills.count', read_only=True)
    tags_detail = TagSerializer(source='tags', many=True, read_only=True)

    class Meta:
        model = Resume
        fields = ['id', 'user', 'username', 'title', 'summary', 'status',
                  'file', 'file_name', 'enabled_modules', 'ai_processed',
                  'visitor_enabled', 'visitor_expires',
                  'tags_detail', 'educations_count', 'work_experiences_count',
                  'projects_count', 'skills_count', 'created_at', 'updated_at']


class ResumeDetailSerializer(serializers.ModelSerializer):
    """
    简历详情序列化器 —— 完整版，包含所有嵌套数据。

    嵌套序列化器（many=True 表示一对多关系）：
    - educations：教育经历列表
    - work_experiences：工作经历列表
    - projects：项目经历列表
    - skills：技能列表
    - tags_detail：标签列表

    知识点：嵌套序列化器默认是只读的，写入需要使用 PrimaryKeyRelatedField。
    """
    username = serializers.CharField(source='user.username', read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    work_experiences = WorkExperienceSerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    tags_detail = TagSerializer(source='tags', many=True, read_only=True)
    all_modules = serializers.ListField(read_only=True)  # 所有可用模块列表
    visitor_url = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = ['id', 'user', 'username', 'title', 'summary', 'status',
                  'file', 'file_name', 'enabled_modules', 'module_data',
                  'ai_processed', 'ai_classification_result',
                  'tags_detail', 'all_modules',
                  'educations', 'work_experiences', 'projects', 'skills',
                  'visitor_enabled', 'visitor_token', 'visitor_expires',
                  'visitor_allow_download', 'public_modules', 'visitor_url',
                  'visitor_hr_enabled', 'visitor_ai_enabled',
                  'visitor_ai_quota', 'visitor_ai_used',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'ai_processed', 'ai_classification_result',
                            'visitor_token', 'visitor_ai_used',
                            'created_at', 'updated_at']

    def get_visitor_url(self, obj):
        """动态生成访客 URL。"""
        if not obj.visitor_enabled or not obj.visitor_token:
            return ''
        from .visitor_utils import get_visitor_url
        request = self.context.get('request')
        return get_visitor_url(obj, request)


class ResumeCreateUpdateSerializer(serializers.ModelSerializer):
    """
    简历创建/更新序列化器 —— 处理写入操作。

    特点：
    - tags 使用 PrimaryKeyRelatedField，前端传标签 ID 数组
    - 创建时自动关联当前登录用户
    - validate_enabled_modules 限制最大模块数量

    知识点：create() 和 update() 方法控制数据如何保存到数据库。
    """
    # PrimaryKeyRelatedField：前端传标签的 ID 列表，如 [1, 3, 5]
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )

    class Meta:
        model = Resume
        fields = ['id', 'title', 'summary', 'status', 'file', 'file_name',
                  'enabled_modules', 'module_data', 'tags',
                  'visitor_enabled', 'visitor_expires', 'visitor_allow_download',
                  'public_modules',
                  'visitor_hr_enabled', 'visitor_ai_enabled',
                  'visitor_ai_quota']
        read_only_fields = ['id']

    def validate_enabled_modules(self, value):
        """
        验证 enabled_modules 字段，确保不超过最大数量限制。

        这是 DRF 的字段级验证方法，格式为 validate_<字段名>。
        如果验证失败，抛出 ValidationError。
        """
        if value and len(value) > Resume.MAX_CONFIGURABLE:
            raise serializers.ValidationError(
                f'最多 {Resume.MAX_CONFIGURABLE} 个模块'
            )
        return value

    def create(self, validated_data):
        """
        创建简历时：
        1. 先弹出 tags 数据（多对多字段需要单独处理）
        2. 自动关联当前登录用户
        3. 创建简历后设置标签

        为什么 tags 要单独处理？
        因为多对多关系需要先创建主对象，再通过 .set() 方法建立关联。
        """
        tags = validated_data.pop('tags', [])
        validated_data['user'] = self.context['request'].user
        resume = super().create(validated_data)
        if tags:
            resume.tags.set(tags)
        return resume

    def update(self, instance, validated_data):
        """
        更新简历时：
        1. 弹出 tags 数据
        2. 更新其他字段
        3. 如果传了 tags（不是 None），则更新标签关系

        注意：tags=None 表示不修改标签，tags=[] 表示清空所有标签。
        """
        tags = validated_data.pop('tags', None)
        resume = super().update(instance, validated_data)
        if tags is not None:
            resume.tags.set(tags)
        return resume


class PdfExportSerializer(serializers.Serializer):
    """
    PDF 导出请求序列化器 —— 验证导出参数。

    这是一个普通的 Serializer（不是 ModelSerializer），
    因为它不对应任何数据库模型，只是验证请求参数。

    请求示例：{ "modules": ["education", "work_experience"] }
    """
    modules = serializers.ListField(
        child=serializers.CharField(),   # 列表中的每个元素都是字符串
        min_length=1,                    # 至少选择 1 个模块
        max_length=5,                    # 最多 5 个模块
    )

    def validate_modules(self, value):
        """验证模块名称是否合法。"""
        valid = set(Resume.CONFIGURABLE_MODULES)
        for m in value:
            if m not in valid:
                raise serializers.ValidationError(f'无效模块: {m}')
        return value


class VisitorLinkUpdateSerializer(serializers.Serializer):
    """
    访客链接更新请求序列化器 —— 验证链接配置参数。

    包含基础访客设置和 HR 模式设置。
    所有字段都是可选的（required=False），只更新传入的字段。
    """
    enabled = serializers.BooleanField(required=False)
    expires_days = serializers.IntegerField(required=False, min_value=1, max_value=365)
    allow_download = serializers.BooleanField(required=False)
    public_modules = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    # HR 模式字段
    hr_enabled = serializers.BooleanField(required=False, default=False)
    ai_enabled = serializers.BooleanField(required=False, default=True)
    ai_quota = serializers.IntegerField(required=False, min_value=1, max_value=100, default=10)

    def validate_public_modules(self, value):
        """验证公开模块名称是否合法。"""
        valid = set(Resume.CONFIGURABLE_MODULES)
        for m in value:
            if m not in valid:
                raise serializers.ValidationError(f'无效模块: {m}')
        return value