# 服务器发版与部署指南

本文档用于将 `Smart Resume Hub` 发布到正式服务器。

## 一、服务器要求

### 1. 基础环境

- 操作系统：Ubuntu 22.04 LTS 或同类 Linux 发行版
- CPU：2 核起，推荐 4 核
- 内存：2 GB 起，推荐 4 GB
- 磁盘：20 GB 起，推荐 50 GB
- Python：3.10+
- Node.js：18+，推荐 20 LTS
- PostgreSQL：13+，推荐 15+
- Nginx：1.18+
- 证书工具：Certbot（如需 HTTPS）

### 2. 运行依赖

- 后端 Python 依赖见 `backend/requirements.txt`
- 前端依赖见 `frontend/package.json`
- PDF 导出依赖 WeasyPrint 及其系统库
- AI 功能依赖 OpenAI API，未配置时会走本地降级方案

### 3. 环境变量

后端需要准备 `backend/.env`，至少包括：

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com

DB_NAME=resume_db
DB_USER=resume_user
DB_PASSWORD=your-strong-password
DB_HOST=127.0.0.1
DB_PORT=5432

OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

VISITOR_LINK_SECRET=change-me-too
```

## 二、发版步骤

### 1. 拉取代码

```bash
git pull
```

### 2. 后端准备

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

如果是首次部署或需要重建示例数据：

```bash
python manage.py init_data
```

### 3. 前端构建

```bash
cd frontend
npm install
npm run build
```

构建产物输出到 `frontend/dist/`。

### 4. 配置 Nginx

建议将静态前端挂载到站点根目录，API 反代到后端 Gunicorn。

示例：

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    root /var/www/smart-resume;
    index index.html;

    location /api/ {
        proxy_pass http://unix:/run/resume-backend.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/smart-resume-hub/backend/staticfiles/;
    }

    location /media/ {
        alias /opt/smart-resume-hub/backend/media/;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 5. 启动后端

```bash
cd backend
gunicorn config.wsgi:application --bind unix:/run/resume-backend.sock --workers 4 --timeout 120
```

生产环境建议使用 `systemd` 托管 `gunicorn`。

### 6. 发布静态文件

```bash
sudo mkdir -p /var/www/smart-resume
sudo cp -r frontend/dist/* /var/www/smart-resume/
```

### 7. 重载服务

```bash
sudo systemctl reload nginx
sudo systemctl restart resume-backend
```

## 三、上线检查

- 首页能正常打开
- `/api/` 能返回 JSON
- `/admin/` 可登录
- 登录后能创建/编辑简历
- 简历详情页能导出 PDF
- 访客链接可打开，AI 模式和下载权限符合配置
- 管理端可查看 AI 日志、审计日志、访客 AI 日志

## 四、回滚步骤

1. 保留上一版代码和前端构建产物
2. 回退到上一版 git commit
3. 重新执行后端迁移前的检查
4. 重新构建前端并覆盖发布目录
5. 重启 `gunicorn` 和 `nginx`

## 五、补充说明

- 如果只改了前端，可以只重新构建并替换 `frontend/dist/`
- 如果只改了后端接口，前端未变动时不必重新打包前端
- 如果改动了数据库模型，发版前必须确认迁移脚本已经生成并执行
