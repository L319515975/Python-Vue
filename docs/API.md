# API 接口参考

Smart Resume Hub 全部 API 端点参考。生产环境也可通过 /swagger/ 或 /redoc/ 浏览在线文档。

> 最后更新：2026-07-12

## 基础信息

- **Base URL**: http://localhost:8000/api
- **认证**: JWT Bearer Token（除访客公开接口外均需认证）
- **Content-Type**: pplication/json（文件上传使用 multipart/form-data）
- **分页**: 默认 page_size=20，通过 ?page=&page_size= 控制

## 通用响应格式

### 成功
`json
{
  "count": 42,
  "next": "http://.../?page=3",
  "previous": "http://.../?page=1",
  "results": [...]
}
`

### 错误
`json
{
  "detail": "错误描述"
}
`

## 用户模块

### POST /api/users/login/
登录获取 JWT Token。

`json
// Request
{ "username": "admin", "password": "admin123" }
// Response
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": { "id": 1, "username": "admin", "role": "admin", ... }
}
`

### POST /api/users/token/refresh/
刷新 Access Token。

`json
// Request
{ "refresh": "eyJ..." }
// Response
{ "access": "eyJ..." }
`

### GET /api/users/me/
获取当前登录用户信息。

### PATCH /api/users/me/
更新个人信息。

### POST /api/users/change-password/
修改密码。

`json
// Request
{ "old_password": "old123", "new_password": "new123" }
// Response
{ "detail": "密码修改成功" }
`

### GET /api/users/audit-logs/
管理员审计日志列表。支持过滤：?action=user_create&target_user=zhangsan

### GET /api/users/visitor-ai-logs/
访客 AI 使用日志。支持过滤：?call_type=chat&username=zhangsan

### CRUD /api/users/
管理员管理用户。

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/users/ | 用户列表 |
| POST | /api/users/ | 创建用户 |
| GET | /api/users/{id}/ | 用户详情 |
| PATCH | /api/users/{id}/ | 更新用户 |
| DELETE | /api/users/{id}/ | 删除用户 |

## 简历模块

### GET/PATCH /api/resumes/my-resume/
**v2 新增**。获取或更新当前登录人（含管理员）自己的简历。

- GET 返回当前用户简历详情，不存在则自动创建草稿后返回
- PATCH 部分更新当前用户简历字段

### GET /api/resumes/
简历列表（管理员看全部，普通用户只看自己的）。

支持过滤：?status=published&search=关键词&ordering=-updated_at

### POST /api/resumes/
创建新简历。

### GET /api/resumes/{id}/
简历详情（包含完整嵌套数据：教育/工作/项目/技能）。

### PATCH /api/resumes/{id}/
更新简历字段。

### DELETE /api/resumes/{id}/
删除简历。

### POST /api/resumes/{id}/upload_file/
上传简历文件。支持 PDF / Word / Markdown 格式，自动 AI 分类。

`json
// multipart/form-data
{ "file": (binary), "auto_classify": "true" }
`

### POST /api/resumes/{id}/update-modules/
更新启用模块。

`json
// Request
{ "enabled_modules": ["education", "project", "skill"], "module_data": { "certificate": "CET-6" } }
`

### POST /api/resumes/{id}/export-pdf/
导出 PDF。

`json
// Request
{ "modules": ["education", "work_experience", "project"], "template_key": "default" }
// Response: binary PDF file
`

### POST /api/resumes/{id}/set-tags/
设置标签。

`json
// Request
{ "tag_ids": [1, 3, 5] }
`

### POST /api/resumes/{id}/generate-visitor-link/
生成访客链接。

`json
// Request
{
  "enabled": true,
  "expires_days": 30,
  "allow_download": true,
  "public_modules": ["education", "project"],
  "visitor_ai_mode_enabled": true,
  "ai_enabled": true,
  "ai_quota": 10,
  "ai_system_prompt": "你是一个专业的求职助手..."
}
`

### POST /api/resumes/{id}/disable-visitor-link/
禁用访客链接。

### GET /api/resumes/{id}/visitor-link-info/
查看访客链接配置信息和访问 URL。

### CRUD /api/resumes/tags/
标签管理（管理员可写，已登录用户可读）。

### CRUD /api/resumes/pdf-templates/
PDF 模板管理（管理员可上传和管理）。

### CRUD /api/resumes/educations/
### CRUD /api/resumes/work-experiences/
### CRUD /api/resumes/projects/
### CRUD /api/resumes/skills/

## 访客公开接口（无需登录）

### GET /api/resumes/visitor/{token}/
通过访客链接查看简历。

参数：?sig=xxx&expires=1234567890&role=visitor

### GET /api/resumes/visitor/{token}/download/
下载 PDF（需允许下载）。

### POST /api/resumes/visitor/{token}/ai-chat/
访客 AI 对话（需 AI 模式启用）。

`json
// Request
{ "query": "这个人的项目经历是什么？", "call_type": "chat" }
`

## AI 助手模块

### POST /api/ai/chat/
AI 对话。

`json
// Request
{ "query": "我的教育背景是什么？" }
// Response
{ "response": "您的教育背景...", "intent": "education", "tokens_used": 150 }
`

### POST /api/ai/polish/
文本润色。

`json
// Request
{ "text": "负责后端开发", "module_name": "work_experience" }
// Response
{ "original_text": "...", "polished_text": "主导后端架构设计...", "status": "success" }
`

### GET /api/ai/history/
AI 对话历史。?limit=20

### GET /api/ai/logs/
### GET /api/ai/polish-logs/
### GET /api/ai/classification-logs/
管理员日志查看。
