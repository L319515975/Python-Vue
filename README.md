# 智能简历管理系统 (Smart Resume Hub)

基于 Django 4.2 + Vue 3 的三角色权限简历管理系统，集成 AI 智能助手，支持访客免登录访问，包含 HR 访客模式与 AI 配额管控。

## 技术栈

### 后端
- Python 3.10+
- Django 4.2 + Django REST Framework
- JWT 认证 (djangorestframework-simplejwt)
- SQLite (开发) / PostgreSQL (生产)
- WeasyPrint (PDF 导出)
- OpenAI API (AI 助手)

### 前端
- Vue 3 + Vite
- Element Plus (UI 组件)
- Pinia (状态管理)
- Vue Router (路由)
- Marked (Markdown 渲染)

## 功能模块

### 三角色权限体系

| 角色 | 登录方式 | 核心权限 |
|------|----------|----------|
| **管理员** | 账号密码 | 系统配置、用户管理、权限分配、数据监控、所有简历查看/编辑/删除、操作审计、HR AI日志查看 |
| **用户** | 账号密码 | 管理个人简历（CRUD、润色、下载）、生成/管理访客链接、配置 HR 模式与 AI 配额、设置公开模块 |
| **访客** | 免登录 (`/visitor/<token>`) | 查看指定用户的公开简历模块、下载简历（若用户授权） |
| **HR访客** | 免登录 (HR专属链接) | 查看简历、AI智能问答、文本润色（有配额限制）、下载简历（若授权） |

### HR 访客模式

HR 访客模式专为企业招聘方设计，支持免登录访问候选人简历并使用 AI 功能：

- **链接结构**: `/visitor/<token>?role=hr&sig=HMAC(...)&expires=XXX`
- **AI配额**: 用户可自定义 HR 链接的 AI 调用次数（1-100次）
- **签名安全**: HMAC-SHA256 签名包含 role 参数，防止角色篡改
- **审计日志**: 所有 HR AI 调用记录完整保存，管理员可查看
- **配额提示**: 页面实时显示剩余调用次数，超限后灰化 AI 按钮

### 核心功能
1. **简历管理**: 模块化简历结构，支持教育经历、工作经历、项目经历、技能、证书、获奖、语言能力
2. **自定义标签**: 系统级标签库（技能/项目/证书/获奖/语言），管理员可配置
3. **AI 智能助手**:
   - 浮动图标入口，随时可用
   - 自然语言查询简历信息
   - 一键文本润色（带差异对比）
   - 上传文件自动归类到对应模块
   - HR 访客 AI 问答与润色（配额控制）
4. **PDF 导出**: 选择模块生成定制化 PDF 简历
5. **访客分享**: HMAC-SHA256 签名链接，支持普通访客和 HR 访客两种模式
6. **操作审计**: 管理员操作全程记录 + HR AI 使用日志
7. **移动端适配**: 响应式布局，支持手机和平板访问

## 快速开始

### 1. 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py makemigrations users resumes ai_assistant
python manage.py migrate

# 初始化示例数据（含HR访客链接示例）
python manage.py init_data

# 启动后端服务
python manage.py runserver 8000
```

### 2. 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端默认运行在 `http://localhost:5173`，API 代理到 `http://localhost:8000`。

### 3. AI 配置（可选）

在 `backend/.env` 文件中配置 OpenAI API：

```
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
```

未配置 API Key 时，系统会使用本地关键词匹配作为降级方案。

## 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 普通用户 | zhangsan | user123 |

初始化数据后，zhangsan 的简历自动生成 HR 访客分享链接（有效期30天，允许下载，AI配额10次）。

## 项目结构

```
smart-resume-hub/
├── backend/                    # Django 后端
│   ├── apps/
│   │   ├── users/              # 用户管理应用
│   │   │   ├── models.py       # 用户模型
│   │   │   ├── views.py        # 登录、用户CRUD
│   │   │   ├── serializers.py  # 序列化器
│   │   │   ├── permissions.py  # 权限类
│   │   │   └── migrations/
│   │   │       └── 0001_create_user_model.py
│   │   ├── resumes/            # 简历管理应用
│   │   │   ├── models.py       # 简历、标签、教育经历等模型
│   │   │   ├── views.py        # 简历CRUD、访客接口
│   │   │   ├── serializers.py  # 序列化器
│   │   │   ├── visitor_utils.py # 访客链接签名验证
│   │   │   ├── pdf_service.py  # PDF导出服务
│   │   │   └── migrations/
│   │   │       └── 0001_create_resume_models.py
│   │   └── ai_assistant/       # AI助手应用
│   │       ├── models.py       # 查询日志模型
│   │       ├── views.py        # AI聊天、润色接口
│   │       ├── services.py     # OpenAI调用服务
│   │       └── migrations/
│   │           └── 0001_create_ai_models.py
│   ├── config/                 # Django 项目配置
│   │   ├── settings.py         # 主配置文件
│   │   ├── urls.py             # 路由配置
│   │   ├── wsgi.py             # WSGI 入口
│   │   └── asgi.py             # ASGI 入口
│   ├── templates/              # PDF模板
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env                    # 环境变量（从.env.example复制）
│   └── .env.example            # 环境变量模板
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.vue      # 主布局（含移动端响应式）
│   │   │   ├── AiAssistant.vue # 浮动AI助手组件
│   │   │   └── PolishDialog.vue # 润色结果对话框
│   │   ├── views/
│   │   │   ├── Login.vue       # 登录页
│   │   │   ├── VisitorPage.vue # 访客简历页
│   │   │   ├── user/
│   │   │   │   ├── ResumeDetail.vue  # 我的简历
│   │   │   │   └── ResumeEdit.vue    # 编辑简历
│   │   │   └── admin/
│   │   │       ├── Dashboard.vue     # 管理面板
│   │   │       ├── UserManage.vue    # 用户管理
│   │   │       ├── ResumeManage.vue  # 简历管理
│   │   │       ├── TagManage.vue     # 标签管理
│   │   │       ├── AiLogs.vue        # AI日志
│   │   │       └── AuditLog.vue      # 操作审计
│   │   ├── router/index.js     # 路由配置
│   │   ├── stores/user.js      # 用户状态管理
│   │   ├── api/index.js        # API 接口定义
│   │   └── utils/request.js    # Axios 封装
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── README.md
```

## 生产环境部署

### 环境要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核 |
| 内存 | 2 GB | 4 GB |
| 磁盘 | 20 GB | 50 GB |
| OS | Ubuntu 20.04 / CentOS 7 | Ubuntu 22.04 |
| Python | 3.10+ | 3.11+ |
| Node.js | 18+ | 20 LTS |
| PostgreSQL | 13+ | 15+ |
| Nginx | 1.18+ | 1.24+ |

### 1. 环境变量配置

创建 `backend/.env` 文件：

```env
# Django
DJANGO_SECRET_KEY=your-very-long-random-secret-key-at-least-50-chars
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database (PostgreSQL)
DB_NAME=resume_db
DB_USER=resume_user
DB_PASSWORD=your-strong-db-password
DB_HOST=localhost
DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# Visitor Link Security
VISITOR_LINK_SECRET=your-unique-visitor-link-secret-key
```

### 2. PostgreSQL 配置

```bash
# 安装 PostgreSQL
sudo apt install postgresql postgresql-contrib

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE resume_db;
CREATE USER resume_user WITH PASSWORD 'your-strong-db-password';
ALTER ROLE resume_user SET client_encoding TO 'utf8';
ALTER ROLE resume_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE resume_user SET timezone TO 'Asia/Shanghai';
GRANT ALL PRIVILEGES ON DATABASE resume_db TO resume_user;
\q
```

在 `backend/config/settings.py` 中切换数据库配置：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'resume_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

### 3. 后端部署 (Gunicorn)

```bash
cd backend

# 安装依赖
pip install -r requirements.txt
pip install gunicorn

# 数据库迁移
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py init_data  # 仅首次部署

# 测试启动
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# 创建 systemd 服务
sudo tee /etc/systemd/system/resume-backend.service << EOF
[Unit]
Description=Smart Resume Backend
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/smart-resume-hub/backend
Environment="PATH=/opt/smart-resume-hub/backend/venv/bin"
ExecStart=/opt/smart-resume-hub/backend/venv/bin/gunicorn config.wsgi:application --bind unix:/run/resume-backend.sock --workers 4 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable resume-backend
sudo systemctl start resume-backend
```

### 4. 前端构建

```bash
cd frontend

# 安装依赖
npm install

# 生产构建
npm run build

# 构建产物在 frontend/dist/ 目录
sudo cp -r dist /var/www/smart-resume
```

### 5. Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 前端静态文件
    root /var/www/smart-resume;
    index index.html;

    # API 请求代理到后端
    location /api/ {
        proxy_pass http://unix:/run/resume-backend.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        client_max_body_size 10M;
    }

    # 静态文件 (Django admin, PDF模板等)
    location /static/ {
        alias /opt/smart-resume-hub/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 媒体文件 (用户上传)
    location /media/ {
        alias /opt/smart-resume-hub/backend/media/;
        expires 7d;
    }

    # Vue Router history 模式
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/resume /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. HTTPS (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
sudo certbot renew --dry-run
```

### 7. 定时任务

```bash
# 添加 crontab
crontab -e

# 每天凌晨3点清理过期访客链接
0 3 * * * cd /opt/smart-resume-hub/backend && /opt/smart-resume-hub/backend/venv/bin/python manage.py shell -c "
from apps.resumes.models import Resume
from django.utils import timezone
expired = Resume.objects.filter(visitor_enabled=True, visitor_expires__lt=timezone.now())
expired.update(visitor_enabled=False, visitor_token='')
print(f'Disabled {expired.count()} expired visitor links')
"

# 每周日凌晨2点备份数据库
0 2 * * 0 pg_dump -U resume_user resume_db | gzip > /backups/resume_db_$(date +\%Y\%m\%d).sql.gz
```

### 8. 日志配置

在 `backend/config/settings.py` 中添加生产日志配置：

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/smart-resume/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'WARNING',
    },
}
```

## API 接口

### 用户认证
- `POST /api/users/login/` - 登录获取 JWT
- `POST /api/users/token/refresh/` - 刷新 Token
- `GET /api/users/me/` - 获取当前用户信息

### 简历管理
- `GET/POST /api/resumes/` - 简历列表/创建
- `GET/PUT/PATCH/DELETE /api/resumes/{id}/` - 简历详情/修改/删除
- `POST /api/resumes/{id}/upload_file/` - 上传简历文件（自动归类）
- `POST /api/resumes/{id}/export-pdf/` - 导出 PDF

### 访客链接管理
- `POST /api/resumes/{id}/generate-visitor-link/` - 生成/更新访客链接（支持 HR 模式参数: hr_enabled, ai_enabled, ai_quota）
- `POST /api/resumes/{id}/disable-visitor-link/` - 禁用访客链接
- `GET /api/resumes/{id}/visitor-link-info/` - 获取链接设置

### 访客公开接口（无需认证）
- `GET /api/resumes/visitor/<token>/?sig=...&expires=...&role=hr` - 查看公开简历（HR模式含AI元数据）
- `GET /api/resumes/visitor/<token>/download/?sig=...&expires=...` - 下载 PDF
- `POST /api/resumes/visitor/<token>/ai-chat/?sig=...&expires=...&role=hr` - HR AI 咨询/润色（配额控制）

### AI 助手
- `POST /api/ai/chat/` - AI 查询（已登录用户）
- `POST /api/ai/polish/` - 文本润色（已登录用户）

### 审计日志（管理员）
- `GET /api/users/audit-logs/` - 操作审计日志
- `GET /api/users/hr-ai-logs/` - HR AI 使用日志

## 访客链接安全机制

访客链接使用 HMAC-SHA256 签名防篡改：

1. 用户在"我的简历"页面生成访客链接，可配置 HR 模式、有效期、公开模块、下载权限、AI 配额
2. 后端生成唯一 token，拼接过期时间戳和 role 参数后用 HMAC-SHA256 签名
3. 访客访问时，后端验证签名完整性、链接有效期、简历发布状态、role 参数
4. HR 模式下检查 AI 配额，每次调用递增已用计数并记录审计日志
5. 仅返回用户选定的公开模块数据，隐藏联系方式等敏感信息

## 许可证

MIT License