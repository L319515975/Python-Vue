"""
Django项目配置文件 - Smart Resume Management System（智能简历管理系统）。

这是Django项目的核心配置文件，包含：
1. 应用注册（INSTALLED_APPS）
2. 中间件配置（MIDDLEWARE）
3. 数据库配置（DATABASES）
4. 认证和权限配置（REST_FRAMEWORK, SIMPLE_JWT）
5. AI服务配置（OPENAI_*）
6. 跨域配置（CORS）
7. 文件上传限制
8. 国际化和时区

配置项说明：
- 环境变量通过 .env 文件加载（使用 python-dotenv 库）
- 敏感信息（如密钥、API密钥）应通过环境变量设置
- 开发环境使用默认值，生产环境应覆盖这些默认值
"""
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
# .env 文件应放在项目根目录，格式为 KEY=VALUE
load_dotenv()

# 项目根目录（manage.py 所在目录的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent

# Django密钥 - 用于加密Session、Token等
# 【重要】生产环境必须通过环境变量设置一个安全的密钥！
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-this-in-production-!@#$%')

# 调试模式 - 开发环境开启，生产环境必须关闭！
# DEBUG=True会显示详细的错误信息，但会暴露代码细节
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

# 允许访问的主机名 - '*' 表示允许所有（仅开发环境使用）
# 生产环境应设置为实际的域名，如 'example.com,www.example.com'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

# ── 已安装的应用 ──────────────────────────────────────────
# Django会按顺序加载这些应用
INSTALLED_APPS = [
    # Django内置应用
    'django.contrib.admin',         # 管理后台
    'django.contrib.auth',          # 认证系统
    'django.contrib.contenttypes',  # 内容类型框架
    'django.contrib.sessions',      # Session框架
    'django.contrib.messages',      # 消息框架
    'django.contrib.staticfiles',   # 静态文件管理
    # 第三方库
    'rest_framework',               # Django REST Framework（构建REST API）
    'rest_framework_simplejwt',     # JWT认证（Token认证）
    'corsheaders',                  # 跨域资源共享（允许前端跨域请求）
    'django_filters',               # 过滤器（API查询过滤）
    'drf_yasg',                     # API文档自动生成（Swagger）
    # 本地应用（我们自己写的）
    'apps.users',                   # 用户模块
    'apps.resumes',                 # 简历模块
    'apps.ai_assistant',            # AI助手模块
]

# ── 中间件 ──────────────────────────────────────────────
# 中间件是处理请求/响应的"管道"，请求从上到下依次经过每个中间件
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',          # CORS跨域处理（必须在最前面）
    'django.middleware.security.SecurityMiddleware',   # 安全相关（HTTPS重定向等）
    'django.contrib.sessions.middleware.SessionMiddleware',      # Session处理
    'django.middleware.common.CommonMiddleware',       # 通用处理（URL末尾斜杠等）
    'django.middleware.csrf.CsrfViewMiddleware',      # CSRF防护
    'django.contrib.auth.middleware.AuthenticationMiddleware',   # 用户认证
    'django.contrib.messages.middleware.MessageMiddleware',      # 消息处理
    'django.middleware.clickjacking.XFrameOptionsMiddleware',    # 点击劫持防护
]

ROOT_URLCONF = 'config.urls'  # 根URL配置文件

# 模板引擎配置
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # 自定义模板目录
        'APP_DIRS': True,                   # 在应用目录中查找模板
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ── 数据库配置 ──────────────────────────────────────────
# 开发环境使用SQLite（无需安装，文件型数据库）
# 生产环境应切换到PostgreSQL或MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQL配置（生产环境使用，取消注释即可）
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('DB_NAME', 'resume_db'),
#         'USER': os.getenv('DB_USER', 'postgres'),
#         'PASSWORD': os.getenv('DB_PASSWORD', ''),
#         'HOST': os.getenv('DB_HOST', 'localhost'),
#         'PORT': os.getenv('DB_PORT', '5432'),
#     }
# }

# 自定义用户模型 - 告诉Django使用我们的User模型而不是默认的
AUTH_USER_MODEL = 'users.User'

# 密码验证器 - 注册/修改密码时检查密码强度
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── 国际化和时区 ──────────────────────────────────────────
LANGUAGE_CODE = 'zh-hans'      # 中文简体
TIME_ZONE = 'Asia/Shanghai'    # 中国时区
USE_I18N = True                # 启用国际化翻译
USE_TZ = True                  # 启用时区感知（数据库中存储UTC时间）

# ── 静态文件和媒体文件 ──────────────────────────────────────
STATIC_URL = 'static/'         # 静态文件URL前缀
STATIC_ROOT = BASE_DIR / 'staticfiles'  # collectstatic收集到的目录

MEDIA_URL = 'media/'           # 媒体文件URL前缀
MEDIA_ROOT = BASE_DIR / 'media'          # 用户上传文件的存储目录

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'  # 默认主键类型（64位整数）

# ── CORS跨域配置 ──────────────────────────────────────────
# 前端（Vue）运行在 localhost:5173，后端运行在 localhost:8000
# 浏览器的同源策略会阻止跨域请求，需要配置CORS允许
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173'
).split(',')
CORS_ALLOW_CREDENTIALS = True  # 允许携带Cookie（JWT Token在Header中，不需要Cookie）

# ── Django REST Framework配置 ──────────────────────────────
REST_FRAMEWORK = {
    # 认证方式：使用JWT Token认证
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # 默认权限：需要登录才能访问
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # 分页：默认每页20条
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # 过滤后端：支持搜索、过滤、排序
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',  # 日期时间格式
}

# ── JWT配置 ──────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),     # 访问Token有效期：2小时
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # 刷新Token有效期：7天
    'ROTATE_REFRESH_TOKENS': True,                    # 刷新时返回新Token
    'BLACKLIST_AFTER_ROTATION': False,                # 刷新后旧Token不失效
    'AUTH_HEADER_TYPES': ('Bearer',),                 # Token格式：Bearer <token>
    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.serializers.CustomTokenObtainPairSerializer',
}

# ── AI服务配置 ──────────────────────────────────────────
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')           # API密钥（为空则使用本地回退）
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')  # API地址
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo') # 使用的模型

# ── 文件上传限制 ──────────────────────────────────────────
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

RESUME_UPLOAD_PATH = 'resumes/'  # 简历文件存储路径（相对于MEDIA_ROOT）

# ── 访客链接安全配置 ──────────────────────────────────────
VISITOR_LINK_SECRET = os.getenv('VISITOR_LINK_SECRET', SECRET_KEY + '-visitor')
VISITOR_LINK_DEFAULT_EXPIRY_DAYS = 30  # 默认30天有效期