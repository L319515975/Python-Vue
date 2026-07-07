# 智能简历管理系统 (Smart Resume Hub)

Smart Resume Hub 是一个面向管理员、普通用户和访客的智能简历管理平台。它同时提供 Django 后端、Vue 3 Web 前端和微信小程序端，支持简历编辑、访客分享、PDF 导出、AI 问答/润色、自动归类和操作审计。

## 功能概览

- 账号体系：管理员、普通用户，统一使用 JWT 登录
- 简历管理：一人一份简历，支持教育、工作、项目、技能、证书、获奖、语言等模块
- 文件处理：支持上传 PDF / Word / Markdown 简历文件，并进行自动归类
- 标签管理：内置系统标签，也支持管理员维护自定义标签
- PDF 导出：按模块和模板导出简历 PDF
- 访客分享：HMAC-SHA256 签名链接，支持有效期、下载权限、公开模块控制
- 访客 AI 模式：可配置 AI 问答和文本润色配额，超限后自动限制
- AI 助手：登录用户可进行简历问答、文本润色、对话历史查看
- 日志审计：管理员操作审计、AI 查询日志、润色日志、分类日志、访客 AI 日志
- 多端同步：Vue 路由和 API 清单可同步到微信小程序端

## 发版文档

服务器发版步骤和上线要求见 [docs/SERVER_RELEASE.md](docs/SERVER_RELEASE.md)。

## 技术栈

- 后端：Django 4.2、Django REST Framework、SimpleJWT、django-filter、drf-yasg
- AI：OpenAI API，未配置 Key 时使用本地关键词降级方案
- PDF：WeasyPrint
- 前端：Vue 3、Vite、Vue Router、Pinia、Element Plus、Axios、Marked
- 小程序：微信小程序 + TDesign Mini Program
- 数据库：SQLite（开发默认）/ PostgreSQL（生产）

## 目录结构

```text
smart-resume-hub/
├── backend/              # Django 后端
├── frontend/             # Vue 3 前端
├── miniprogram/          # 微信小程序端
├── docs/                 # 数据库与设计文档
├── sync-vue-to-miniprogram.cjs
├── start.ps1             # Windows 一键启动脚本
├── launch.bat            # Windows 简易启动脚本
└── README.md
```

## 本地运行

### Windows 一键启动

```powershell
.\start.ps1
```

这个脚本会自动检查 Python/Node 环境、创建虚拟环境、安装依赖、初始化示例数据，并启动后端和前端。
如果你已经配好环境，也可以直接运行 `launch.bat` 快速拉起两个开发进程。

### 手动启动后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py init_data
python manage.py runserver 127.0.0.1:8000
```

### 手动启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：`http://localhost:5173`

### 微信小程序同步

```bash
node sync-vue-to-miniprogram.cjs
node sync-vue-to-miniprogram.cjs --watch
```

同步脚本会维护 `miniprogram/app.json` 页面清单，并生成 `miniprogram/generated/` 下的同步清单文件。

## 访问入口

- 后端首页：`http://localhost:8000/`
- API 入口：`http://localhost:8000/api/`
- Django 管理后台：`http://localhost:8000/admin/`
- Swagger：`http://localhost:8000/swagger/`
- ReDoc：`http://localhost:8000/redoc/`

## 默认账号

初始化示例数据后可直接登录：

- 管理员：`admin / admin123`
- 普通用户：`zhangsan / user123`

`init_data` 还会创建示例简历、系统标签和访客分享链接。

## 配置项

后端配置文件位于 `backend/.env`，常用变量如下：

```env
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://localhost:5173

OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

VISITOR_LINK_SECRET=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
```

## API 概览

- `/api/users/`
  - `login/`
  - `token/refresh/`
  - `me/`
  - `change-password/`
  - `audit-logs/`
  - `visitor-ai-logs/`
- `/api/resumes/`
  - CRUD
  - `upload_file/`
  - `update-modules/`
  - `export-pdf/`
  - `set-tags/`
  - `generate-visitor-link/`
  - `disable-visitor-link/`
  - `visitor-link-info/`
  - `pdf-templates/`
- `/api/resumes/visitor/<token>/`
  - 简历公开查看
  - PDF 下载
  - 访客 AI 对话
- `/api/ai/`
  - `chat/`
  - `polish/`
  - `history/`
  - `logs/`
  - `polish-logs/`
  - `classification-logs/`

完整数据库说明请见 [docs/DATABASE.md](docs/DATABASE.md)。

## 许可证

MIT License
