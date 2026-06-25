# 智能简历管理系统 (Smart Resume Management System)

基于 Django + Vue3 的三角色权限简历管理系统，集成 AI 智能助手，支持游客免登录访问，包含 HR 游客模式与 AI 配额管控。

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
|------|----------|------|
| **管理员** | 账号密码 | 系统配置、用户管理、权限分配、数据监控、所有简历查看/编辑/删除、操作审计、HR AI日志查看 |
| **用户** | 账号密码 | 管理个人简历（CRUD、润色、下载）、生成/管理游客链接、配置 HR 模式与 AI 配额、设置公开模块 |
| **游客** | 免登录 (`/visitor/<token>`) | 查看指定用户的公开简历模块、下载简历（若用户授权） |
| **HR游客** | 免登录 (HR专属链接) | 查看简历、AI智能问答、文本润色（有配额限制）、下载简历（若授权） |

### HR 游客模式

HR 游客模式专为企业招聘方设计，支持免登录访问候选人简历并使用 AI 功能：

- **链接结构**: `/visitor/<token>?role=hr&sig=HMAC(...)&expires=XXX&quota=10`
- **AI配额**: 用户可自定义 HR 链接的 AI 调用次数（1-100次）
- **签名安全**: HMAC-SHA256 签名包含 role 参数，防止角色篡改
- **审计日志**: 所有 HR AI 调用记录完整保存，管理员可查看
- **配额提示**: 页面实时显示剩余调用次数，超限后灰化 AI 按钮

### 核心功能
1. **简历管理**: 模块化简历结构，支持教育经历、工作经历、项目经历、技能、证书、获奖、语言能力
2. **自定义标签**: 系统级标签库（技能/项目/证书/获奖/语言），管理员可配置
3. **AI 智能助手**:
   - 自然语言查询简历信息
   - 一键文本润色（带差异对比）
   - 上传文件自动归类到对应模块
   - HR 游客 AI 问答与润色（配额控制）
4. **PDF 导出**: 选择模块生成定制化 PDF 简历
5. **游客分享**: HMAC-SHA256 签名链接，支持普通游客和 HR 游客两种模式
6. **操作审计**: 管理员操作全程记录 + HR AI 使用日志

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

# 初始化示例数据（含HR游客链接示例）
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

在 `backend/.env` 文件中配置 OpenAI API:

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

初始化数据后，zhangsan 的简历自动生成 HR 游客分享链接（有效期30天，允许下载，AI配额10次）。

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

### 游客链接管理
- `POST /api/resumes/{id}/generate-visitor-link/` - 生成/更新游客链接（支持 HR 模式参数: hr_enabled, ai_enabled, ai_quota）
- `POST /api/resumes/{id}/disable-visitor-link/` - 禁用游客链接
- `GET /api/resumes/{id}/visitor-link-info/` - 获取链接设置

### 游客公开接口（无需认证）
- `GET /api/resumes/visitor/<token>/?sig=...&expires=...&role=hr` - 查看公开简历（HR模式含AI元数据）
- `GET /api/resumes/visitor/<token>/download/?sig=...&expires=...` - 下载 PDF
- `POST /api/resumes/visitor/<token>/ai-chat/?sig=...&expires=...&role=hr` - HR AI 咨询/润色（配额控制）

### AI 助手
- `POST /api/ai/chat/` - AI 查询（已登录用户）
- `POST /api/ai/polish/` - 文本润色（已登录用户）

### 审计日志（管理员）
- `GET /api/users/audit-logs/` - 操作审计日志
- `GET /api/users/hr-ai-logs/` - HR AI 使用日志

## 游客链接安全机制

游客链接使用 HMAC-SHA256 签名防篡改：

1. 用户在“我的简历”页面生成游客链接，可配置 HR 模式、有效期、公开模块、下载权限、AI 配额
2. 后端生成唯一 token，拼接过期时间戳和 role 参数后用 HMAC-SHA256 签名
3. 游客访问时，后端验证签名完整性、链接有效期、简历发布状态、role 参数
4. HR 模式下检查 AI 配额，每次调用递增已用计数并记录审计日志
5. 仅返回用户选定的公开模块数据，隐藏联系方式等敏感信息
