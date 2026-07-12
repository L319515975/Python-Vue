# 服务器发版与部署指南

本文档用于将 Smart Resume Hub 发布到正式服务器。

> 最后更新：2026-07-12

## 一、服务器要求

### 基础环境

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核 |
| 内存 | 2 GB | 4 GB |
| 磁盘 | 20 GB | 50 GB |
| 操作系统 | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| Python | 3.10+ | 3.12+ |
| Node.js | 18+ | 20 LTS |
| PostgreSQL | 13+ | 16+ |
| Nginx | 1.18+ | 1.24+ |

### 系统依赖

`ash
sudo apt install -y build-essential python3-dev python3-pip python3-venv \\
                    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \\
                    libffi-dev libcairo2 libcairo2-dev
sudo apt install -y certbot python3-certbot-nginx
`

### 环境变量

`env
DJANGO_SECRET_KEY=your-strong-random-secret-key
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
VISITOR_LINK_SECRET=another-strong-random-secret
FRONTEND_URL=https://your-domain.com
`

## 二、发版步骤

### 1. 拉取代码
`ash
cd /opt
git clone <repo-url> smart-resume-hub
cd smart-resume-hub
git checkout master && git pull
`

### 2. 后端准备
`ash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
`

### 3. 数据库
`ash
sudo -u postgres psql -c "CREATE DATABASE resume_db;"
sudo -u postgres psql -c "CREATE USER resume_user WITH PASSWORD 'your-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE resume_db TO resume_user;"
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py init_data
`

### 4. 前端构建
`ash
cd frontend
npm install
npm run build
`

### 5. Nginx + Systemd
见完整配置示例在 docs/ 目录。

### 6. 发布静态文件
`ash
sudo mkdir -p /var/www/smart-resume
sudo cp -r frontend/dist/* /var/www/smart-resume/
`

### 7. 小程序发布
1. 修改 miniprogram/utils/config.js 中 baseUrl
2. 修改 project.config.json 中 appid
3. 开发者工具上传代码
4. 管理后台提交审核发布

## 三、上线检查清单

### 安全
- [ ] DJANGO_DEBUG=False
- [ ] DJANGO_ALLOWED_HOSTS 已配置
- [ ] CORS_ALLOWED_ORIGINS 无通配符
- [ ] SECRET_KEY 已更换
- [ ] VISITOR_LINK_SECRET 已配置
- [ ] HTTPS 已启用

### 功能
- [ ] 首页正常打开
- [ ] API /api/ 返回正确
- [ ] 管理后台可登录
- [ ] 管理员我的简历正常
- [ ] 创建/编辑简历正常
- [ ] PDF 导出正常
- [ ] 访客链接正常
- [ ] 小程序正常

## 四、常规更新流程
`ash
git pull
source backend/venv/bin/activate
pip install -r backend/requirements.txt
python backend/manage.py migrate
cd frontend && npm install && npm run build
sudo cp -r dist/* /var/www/smart-resume/
sudo systemctl restart resume-backend
sudo systemctl reload nginx
`

## 五、回滚
git revert HEAD 或回退到上一版 commit，确认迁移回滚，重新构建前端，重启服务。

## 六、监控
`ash
journalctl -u resume-backend -f
tail -f /var/log/resume-backend/access.log
tail -f /var/log/nginx/access.log
`
