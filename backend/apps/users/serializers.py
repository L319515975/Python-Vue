"""用户序列化器 - 处理用户数据的序列化和反序列化。

序列化器的作用（通俗解释）：
- 序列化：把Python对象（如User模型）转换成JSON格式，供API返回给前端
- 反序列化：把前端发来的JSON数据转换成Python对象，保存到数据库

序列化器还负责数据验证：
- 检查必填字段是否提供
- 检查字段格式是否正确（如密码最小长度）
- 检查业务逻辑是否合法（如原密码是否正确）
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """自定义JWT Token序列化器。

    默认的JWT Token只包含用户ID，我们扩展它以包含：
    1. 用户角色（role）- 前端用于判断显示管理员页面还是用户页面
    2. 用户名（username）- 前端用于显示欢迎信息

    JWT Token的工作原理：
    - 用户提交用户名+密码
    - 服务器验证通过后，生成一个加密的字符串（Token）
    - 前端保存Token，每次请求时放在请求头中
    - 服务器解码Token就知道是哪个用户在请求
    """

    @classmethod
    def get_token(cls, user):
        """在Token中添加自定义字段。"""
        token = super().get_token(user)
        token['role'] = user.role        # 添加角色信息
        token['username'] = user.username # 添加用户名
        return token

    def validate(self, attrs):
        """验证并返回登录响应数据。

        attrs 包含用户提交的 {username, password}。
        调用父类的validate会验证密码并生成Token。
        我们在返回数据中额外附带用户的完整信息。
        """
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data  # 附带用户信息
        return data


class UserSerializer(serializers.ModelSerializer):
    """用户完整信息序列化器 - 用于查看用户列表和个人信息。

    ModelSerializer 会根据模型字段自动生成序列化器字段，
    比手动定义每个字段更方便，也更容易维护。

    role_display 是一个"计算字段"，不在数据库中，
    它调用模型的 get_role_display() 方法获取角色的中文名称。
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role', 'role_display',
                  'avatar', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']  # 这些字段不允许修改


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器 - 用于注册新用户。

    password字段设置write_only=True，表示：
    - 反序列化时（接收前端数据）：需要提供password
    - 序列化时（返回给前端）：不包含password（安全考虑）

    create方法中使用set_password而不是直接赋值，
    因为set_password会对密码进行哈希加密，数据库中不会存储明文密码。
    """
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'phone', 'role']

    def create(self, validated_data):
        """创建用户，对密码进行哈希处理。"""
        password = validated_data.pop('password')  # 从数据中取出密码
        user = User(**validated_data)               # 创建用户对象
        user.set_password(password)                 # 哈希加密密码
        user.save()                                 # 保存到数据库
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户更新序列化器 - 用于编辑用户信息。

    密码字段是可选的：如果提供了新密码就更新，没提供就不修改。
    """
    password = serializers.CharField(write_only=True, min_length=6, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'role', 'avatar', 'is_active', 'password']

    def update(self, instance, validated_data):
        """更新用户信息。"""
        password = validated_data.pop('password', None)  # 取出密码（可能为None）
        for attr, value in validated_data.items():
            setattr(instance, attr, value)  # 逐个设置字段值
        if password:
            instance.set_password(password)  # 如果有新密码，哈希后更新
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """密码修改序列化器 - 用于修改当前用户密码。

    注意：这不是ModelSerializer，因为它不直接操作模型，
    只是验证输入数据（旧密码是否正确、新密码格式是否合法）。

    validate_old_password 是一个字段级别的验证方法：
    Django REST Framework会自动调用 validate_<字段名> 方法来验证该字段。
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)

    def validate_old_password(self, value):
        """验证原密码是否正确。"""
        user = self.context['request'].user  # 从context中获取当前用户
        if not user.check_password(value):   # check_password会对比哈希值
            raise serializers.ValidationError('原密码不正确')
        return value