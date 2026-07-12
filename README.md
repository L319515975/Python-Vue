# 智能简历管理系统 (Smart Resume Hub)

Smart Resume Hub 是一个面向管理员、普通用户和访客的智能简历管理平台。提供 **Django 后端**、**Vue 3 Web 前端** 和 **微信小程序端** 三端全覆盖，支持简历编辑、访客分享、PDF 导出、AI 问答/润色、自动归类、操作审计等完整功能链。

## 功能概览

- **账号体系**：管理员与普通用户统一使用 JWT 登录，角色隔离
- **简历管理**：一人一份简历，支持教育、工作、项目、技能、证书、获奖、语言模块自由组合
- **我的简历（管理员）**：管理员后台首页即显示"我的简历"入口，可查看和编辑自己的简历
- **文件处理**：上传 PDF / Word / Markdown 简历文件，AI 自动归类到各模块
- **标签管理**：内置系统标签 + 管理员自定义标签，支持多维度分类
- **PDF 导出**：多模板可选，支持按模块选择导出，WeasyPrint 渲染
- **访客分享**：HMAC-SHA256 签名链接，支持有效期、下载权限、公开模块控制
- **访客 AI 模式**：可配置 AI 问答和文本润色配额，支持自定义 System Prompt
- **AI 助手**：登录用户可进行简历问答、文本润色、对话历史查看
- **日志审计**：管理员操作审计、AI 查询/润色/分类日志、访客 AI 日志全纪录
- **多端同步**：Vue 路由和 API 清单可自动同步到微信小程序端

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Django 4.2、Django REST Framework、SimpleJWT |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |
| AI 能力 | OpenAI API（GPT-3.5/4），未配置 Key 时使用本地关键词降级 |
| PDF 生成 | WeasyPrint + 自定义 HTML 模板 |
| API 文档 | drf-yasg（Swagger / ReDoc） |
| 前端框架 | Vue 3 (Composition API)、Vite、Vue Router、Pinia |
| UI 组件 | Element Plus、@element-plus/icons-vue |
| 小程序 | 微信小程序 + TDesign Mini Program |
| 安全认证 | JWT (SimpleJWT) / HMAC-SHA256 访客签名 |

## 目录结构

`	ext
smart-resume-hub/
├── backend/                  # Django 后端项目
│   ├── config/               # 项目配置（settings, urls, wsgi）
│   ├── apps/
│   │   ├── users/            # 用户模块（认证、角色、审计日志）
│   │   ├── resumes/          # 简历核心模块（CRUD、访客链接、PDF、标签）
│   │   └── ai_assistant/     # AI 助手模块（问答、润色、归类）
│   ├── templates/            # Django 模板
│   ├── media/                # 用户上传文件
│   └── requirements.txt
├── frontend/                 # Vue 3 前端项目
│   ├── src/
│   │   ├── api/              # API 接口封装
│   │   ├── components/       # 公共组件（Layout, AiAssistant, PolishDialog）
│   │   ├── composables/      # 组合式函数（useMobile）
│   │   ├── router/           # 路由配置
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── utils/            # 工具函数（request, download）
│   │   ├── styles/           # 全局样式
│   │   └── views/            # 页面组件
│   └── package.json
├── miniprogram/              # 微信小程序端
│   ├── api/                  # API 接口封装
│   ├── pages/                # 页面（admin/、user/、login/、visitor/）
│   ├── store/                # 状态管理
│   ├── utils/                # 工具函数
│   └── generated/            # 同步脚本生成的快照文件
├── docs/                     # 项目文档
│   ├── DATABASE.md           # 数据库设计
│   ├── SERVER_RELEASE.md     # 服务器发版指南
│   ├── ARCHITECTURE.md       # 系统架构
│   ├── AI_FEATURES.md        # AI 功能说明
│   ├── API.md                # API 接口参考
│   └── CHANGELOG.md          # 变更日志
├── sync-vue-to-miniprogram.cjs  # Vue→小程序同步脚本
├── start.ps1                 # Windows 一键启动脚本
├── launch.bat                # Windows 简易启动脚本
└── README.md
`

## 本地运行

### Windows 一键启动

`powershell
.\start.ps1
`

脚本自动完成：检查环境 → 创建虚拟环境 → 安装依赖 → 数据库迁移 → 初始化示例数据 → 启动后端和前端。

### 手动启动后端

`ash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py init_data      # 创建演示账号和示例数据
python manage.py runserver 127.0.0.1:8000
`

### 手动启动前端

`ash
cd frontend
npm install
npm run dev
`

前端默认地址：**http://localhost:5173**

### 微信小程序

1. 用微信开发者工具打开 miniprogram/ 目录
2. 确保 miniprogram/utils/config.js 中的 aseUrl 指向正确的后端地址
3. 编译运行即可

### 多端同步

`ash
# 手动同步 Vue 路由和 API 到小程序
node sync-vue-to-miniprogram.cjs

# 监听模式（文件变动时自动同步）
node sync-vue-to-miniprogram.cjs --watch
`

同步脚本会维护 miniprogram/app.json 页面清单，并生成 miniprogram/generated/ 下的同步快照文件。

## 访问入口

| 入口 | 地址 |
|------|------|
| Vue 前端 | http://localhost:5173 |
| Django 后端首页 | http://localhost:8000/ |
| API 入口 | http://localhost:8000/api/ |
| Django Admin | http://localhost:8000/admin/ |
| Swagger | http://localhost:8000/swagger/ |
| ReDoc | http://localhost:8000/redoc/ |

## 默认账号

运行 init_data 后：

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 普通用户 | zhangsan | user123 |

init_data 还会创建示例简历、系统标签和访客分享链接。

## 配置项

后端配置文件位于 ackend/.env，关键变量：

`env
# Django 基础配置
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://localhost:5173

# PostgreSQL 配置（生产环境使用，开发默认用 SQLite）
DB_NAME=resume_db
DB_USER=resume_user
DB_PASSWORD=your-password
DB_HOST=127.0.0.1
DB_PORT=5432

# OpenAI API 配置
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 访客链接安全密钥
VISITOR_LINK_SECRET=your-visitor-secret
FRONTEND_URL=http://localhost:5173
`

## API 概览

详见 [docs/API.md](docs/API.md)。

### 用户模块 /api/users/

| 端点 | 方法 | 说明 |
|------|------|------|
| login/ | POST | 登录获取 JWT |
| 	oken/refresh/ | POST | 刷新 Token |
| me/ | GET/PATCH | 当前用户信息 |
| change-password/ | POST | 修改密码 |
| udit-logs/ | GET | 操作审计日志（管理员） |
| isitor-ai-logs/ | GET | 访客 AI 日志（管理员） |
| CRUD | GET/POST/PATCH/DELETE | 用户管理（管理员） |

### 简历模块 /api/resumes/

| 端点 | 方法 | 说明 |
|------|------|------|
| my-resume/ | GET/PATCH | 当前登录人简历（含管理员） |
| CRUD | GET/POST/PATCH/DELETE | 简历管理 |
| {id}/upload_file/ | POST | 上传简历文件 |
| {id}/update-modules/ | POST | 更新启用模块 |
| {id}/export-pdf/ | POST | 导出 PDF |
| {id}/set-tags/ | POST | 设置标签 |
| {id}/generate-visitor-link/ | POST | 生成访客链接 |
| {id}/disable-visitor-link/ | POST | 禁用访客链接 |
| {id}/visitor-link-info/ | GET | 访客链接信息 |
| 	ags/ | CRUD | 标签管理 |
| pdf-templates/ | CRUD | PDF 模板管理 |
| educations/ | CRUD | 教育经历 |
| work-experiences/ | CRUD | 工作经历 |
| projects/ | CRUD | 项目经历 |
| skills/ | CRUD | 技能 |

### 访客公开接口 /api/resumes/visitor/<token>/

| 端点 | 方法 | 说明 |
|------|------|------|
| / | GET | 查看公开简历 |
| /download/ | GET | 下载 PDF |
| /ai-chat/ | POST | AI 对话 |

### AI 模块 /api/ai/

| 端点 | 方法 | 说明 |
|------|------|------|
| chat/ | POST | AI 对话 |
| polish/ | POST | 文本润色 |
| history/ | GET | 对话历史 |
| logs/ | GET | 查询日志（管理员） |
| polish-logs/ | GET | 润色日志（管理员） |
| classification-logs/ | GET | 分类日志（管理员） |

## 扩展阅读

- [数据库设计](docs/DATABASE.md)
- [服务器发版指南](docs/SERVER_RELEASE.md)
- [系统架构](docs/ARCHITECTURE.md)
- [AI 功能说明](docs/AI_FEATURES.md)
- [API 接口参考](docs/API.md)
- [变更日志](docs/CHANGELOG.md)

## 许可证

MIT License
