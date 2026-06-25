"""Resume serializers - with tags, module data, PDF export, visitor link, and HR mode."""
from rest_framework import serializers
from .models import Resume, Education, WorkExperience, Project, Skill, Tag


class TagSerializer(serializers.ModelSerializer):
    """Tag serializer."""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'tag_type', 'is_system', 'created_at']
        read_only_fields = ['id', 'is_system', 'created_at']


class TagCreateSerializer(serializers.ModelSerializer):
    """Tag creation serializer (admin only)."""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'tag_type']
        read_only_fields = ['id']

    def create(self, validated_data):
        validated_data['is_system'] = True
        return super().create(validated_data)


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = '__all__'
        read_only_fields = ['id']


class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = '__all__'
        read_only_fields = ['id']


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id']


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'
        read_only_fields = ['id']


class VisitorLinkSerializer(serializers.ModelSerializer):
    """Serializer for visitor link info (including HR mode fields)."""
    visitor_url = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = [
            'visitor_enabled', 'visitor_token', 'visitor_expires',
            'visitor_allow_download', 'public_modules', 'visitor_url',
            # HR fields
            'visitor_hr_enabled', 'visitor_ai_enabled',
            'visitor_ai_quota', 'visitor_ai_used',
        ]
        read_only_fields = ['visitor_token', 'visitor_ai_used']

    def get_visitor_url(self, obj):
        if not obj.visitor_enabled or not obj.visitor_token:
            return ''
        from .visitor_utils import get_visitor_url
        request = self.context.get('request')
        return get_visitor_url(obj, request)


class ResumeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
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
    """Full serializer with nested related data and visitor link info."""
    username = serializers.CharField(source='user.username', read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    work_experiences = WorkExperienceSerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    tags_detail = TagSerializer(source='tags', many=True, read_only=True)
    all_modules = serializers.ListField(read_only=True)
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
        if not obj.visitor_enabled or not obj.visitor_token:
            return ''
        from .visitor_utils import get_visitor_url
        request = self.context.get('request')
        return get_visitor_url(obj, request)


class ResumeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating resume."""
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
        if value and len(value) > Resume.MAX_CONFIGURABLE:
            raise serializers.ValidationError(
                f'max {Resume.MAX_CONFIGURABLE} modules'
            )
        return value

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        validated_data['user'] = self.context['request'].user
        resume = super().create(validated_data)
        if tags:
            resume.tags.set(tags)
        return resume

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        resume = super().update(instance, validated_data)
        if tags is not None:
            resume.tags.set(tags)
        return resume


class PdfExportSerializer(serializers.Serializer):
    """Serializer for PDF export request."""
    modules = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        max_length=5,
    )

    def validate_modules(self, value):
        valid = set(Resume.CONFIGURABLE_MODULES)
        for m in value:
            if m not in valid:
                raise serializers.ValidationError(f'invalid module: {m}')
        return value


class VisitorLinkUpdateSerializer(serializers.Serializer):
    """Serializer for updating visitor link settings (including HR mode)."""
    enabled = serializers.BooleanField(required=False)
    expires_days = serializers.IntegerField(required=False, min_value=1, max_value=365)
    allow_download = serializers.BooleanField(required=False)
    public_modules = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    # HR mode fields
    hr_enabled = serializers.BooleanField(required=False, default=False)
    ai_enabled = serializers.BooleanField(required=False, default=True)
    ai_quota = serializers.IntegerField(required=False, min_value=1, max_value=100, default=10)

    def validate_public_modules(self, value):
        valid = set(Resume.CONFIGURABLE_MODULES)
        for m in value:
            if m not in valid:
                raise serializers.ValidationError(f'invalid module: {m}')
        return value
