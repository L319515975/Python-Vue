# 系统架构

本文档描述 Smart Resume Hub 的整体架构设计。

## 三端架构

\+---------------------+       +---------------------+       +-------------------+
|                     |       |                     |       |                   |
|  Vue 3 Web Frontend | HTTP  |   Django Backend    |       |  微信小程序       |
|  (Element Plus)     |------>|   (DRF + JWT)       |       |  (TDesign)        |
|                     |       |                     |       |                   |
|  - Login            |       |  apps/users/        |       |  - Login          |
|  - Admin Dashboard  |       |  apps/resumes/      |       |  - Admin Dashboard|
|  - Resume Detail    |       |  apps/ai_assistant/  |       |  - Resume Detail  |
|  - Resume Edit      |       |                     |       |  - Resume Edit    |
|  - Visitor Page     |       |  SQLite/PostgreSQL  |       |  - Visitor Page   |
|  - AI Assistant     |       |  OpenAI API         |       |  - AI Assistant   |
+---------------------+       +---------------------+       +-------------------+

## 模块边界

### apps/users — 用户与认证

| 模型 | 说明 |
|------|------|
| User | 自定义用户模型，继承 AbstractUser，增加 role/phone/avatar |
| AdminAuditLog | 管理员操作审计日志 |

关键视图：UserViewSet（CRUD + me + change-password）、CustomTokenObtainPairView

权限体系：
- IsAdminRole — 仅管理员角色可访问
- IsOwnerOrAdmin — 对象所有者或管理员可访问
- AllowAny / IsAuthenticated — DRF 内置权限

### apps/resumes — 简历核心

| 模型 | 说明 |
|------|------|
| Resume | 简历主表，模块化设计，含访客链接和 AI 配置 |
| ResumePdfTemplate | PDF 导出模板 |
| Tag | 简历标签（系统级 + 自定义） |
| Education / WorkExperience / Project / Skill | 简历子模块 |
| VisitorAiUsageLog | 访客 AI 调用日志 |

关键端点：
- GET /api/resumes/my-resume/ — 当前用户简历（含管理员）
- POST /api/resumes/{id}/generate-visitor-link/ — 生成 HMAC 签名访客链接
- POST /api/resumes/visitor/{token}/ai-chat/ — 访客 AI 对话

访客链接安全机制：
1. 服务器用 VISITOR_LINK_SECRET 对 	oken:expires:role 生成 HMAC-SHA256 签名
2. 前端 URL 中携带 sig、expires、
ole 参数
3. 后端收到请求后重新计算签名比对，防止篡改

### apps/ai_assistant — AI 功能

| 模型 | 说明 |
|------|------|
| QueryLog | AI 问答日志 |
| PolishLog | AI 润色日志 |
| ClassificationLog | AI 文件分类日志 |

核心服务函数：
- sk_ai() — AI 问答主入口，支持 resume 对象直接传入（访客场景）
- polish_text() — 文本润色
- classify_resume_file() — 文件自动分类
- uild_resume_context_from_resume() — 构建简历上下文文本
- generate_system_prompt() — 生成 AI System Prompt，支持自定义

降级策略：未配置 OPENAI_API_KEY 时，使用关键词匹配作为本地降级方案。

## 数据流

### 访客分享流程
\用户点击"生成访客链接"
  → POST /api/resumes/{id}/generate-visitor-link/
  → 生成 visitor_token（uuid4 hex）
  → 生成 HMAC 签名 sig
  → 返回完整 URL：/visitor/{token}?expires=...&sig=...&role=...

访客打开链接
  → 前端解析 URL 参数
  → GET /api/resumes/visitor/{token}/?sig=...&expires=...&role=...
  → 后端验证 HMAC 签名
  → 验证链接有效期和简历发布状态
  → 过滤敏感字段后返回公开数据
  → 前端 VisitorPage 渲染简历
\
### AI 对话流程
\用户提出问题
  → POST /api/ai/chat/ { query: "..." }
  → detect_intent(query) 识别意图
  → build_resume_context(user) 构建简历上下文
  → 若有 OPENAI_API_KEY → 调用 OpenAI API
    → generate_system_prompt(intent, context, custom_prompt)
    → 返回结构化回答
  → 若无 API Key → 本地关键词匹配降级
  → 记录 QueryLog
  → 返回 { response, intent, tokens_used }
\