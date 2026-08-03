# AI 功能说明

本文档详细描述 Smart Resume Hub 中所有 AI 相关功能的设计与使用。

> 最后更新：2026-07-12

## 功能概览

| 功能 | 适用场景 | 触发方式 |
|------|----------|----------|
| AI 问答 | 用户向 AI 询问简历内容 | /api/ai/chat/ |
| 文本润色 | 优化简历中的文字表达 | /api/ai/polish/ |
| 文件自动归类 | 上传简历文件后自动拆分到各模块 | /api/resumes/{id}/upload_file/ |
| 访客 AI 对话 | 访客通过分享链接与 AI 交流 | /api/resumes/visitor/{token}/ai-chat/ |
| 意图识别 | 自动判断用户问题属于哪个模块 | ask_ai() 内部调用 |

## 架构设计

### 服务层（services.py）
所有 AI 逻辑集中在 pps/ai_assistant/services.py，核心函数：

`
ask_ai(user, query, resume, target_user)
  ├── detect_intent(query) → intent
  ├── build_resume_context(user_or_resume) → context_text
  ├── generate_system_prompt(intent, context, custom_prompt)
  ├── API Key 存在? → _call_openai_api() → OpenAI
  └── 无 Key → _generate_local_response() → 关键词降级
`

### 降级策略
未配置 OPENAI_API_KEY 时，系统自动使用本地关键词匹配：

- **意图识别**：扫描用户问题中的关键词（教育/工作/项目/技能等），返回匹配的意图
- **本地回答**：根据意图从简历上下文中提取相关段落拼接成回答
- **本地润色**：去除多余空行、空格和口语化词汇
- **本地分类**：统计各模块关键词命中数量，命中 2+ 个即认为该模块有内容

## 自定义 System Prompt 功能

### 业务背景
本系统作为求职者（开发者本人）的求职作品展示给 HR。管理员可以在访客 AI 模式中配置自定义 System Prompt，例如：

> 你是一个专业的求职助手，关于候选人（开发者）的信息如下：
> 他是一名全栈工程师，精通 Django、Vue 3、微信小程序开发...
> 请根据以下简历数据回答 HR 的问题。

### 配置方式
1. 在简历详情页的"访客链接"区域，启用 AI 模式
2. 在"AI 自定义提示词"文本框中输入提示内容
3. 保存后，HR 通过访客 AI 模式提问时，系统会将自定义提示词附加到默认 System Prompt 之前

### 实现原理
`
generate_system_prompt(intent, context, custom_prompt):
  base = base_prompt + intent_note + resume_context
  if custom_prompt:
    base = custom_prompt + '\n\n---\n\n' + base
  return base
`

## 访客 AI 模式

### 流程
`
HR 打开分享链接
  → 前端识别 role=ai 参数
  → 加载简历公开数据 + AI 模式元数据
  → HR 输入问题
  → POST /api/resumes/visitor/{token}/ai-chat/?sig=...&role=ai
  → 后端验证 HMAC 签名 + AI 配额
  → 调用 ask_ai(resume=resume, query=query) 获取回答
  → 更新已用配额（visitor_ai_used += 1）
  → 记录 VisitorAiUsageLog
  → 返回回答 + 剩余配额信息
`

### 配额控制
- isitor_ai_quota：总配额（默认 10 次），管理员可单独设置
- isitor_ai_used：已使用次数
- 超出配额返回 429 Too Many Requests
- 重新生成访客链接时重置已用次数

## "关于本系统"技术栈展示

AI 助手在构建简历上下文时，会自动在末尾追加系统技术栈信息：

`
【关于本系统】
本简历由我独立开发的「智能简历管理系统」(Smart Resume Hub) 自动生成。
系统技术栈:
  - 后端框架: Django + Django REST Framework
  - 前端框架: Vue 3 (Composition API + Pinia)
  - 移动端: 微信小程序 (WeChat Mini Program)
  - AI能力: OpenAI GPT 集成 (简历分析/润色/智能问答)
  - 数据库: SQLite (开发) / PostgreSQL (生产)
  - PDF生成: WeasyPrint / 自定义HTML模板
  - 认证: JWT (SimpleJWT) / HMAC访客签名
该系统完整涵盖简历编辑、AI辅助、访客分享、PDF导出、标签管理等模块。
`

**效果**：当 HR 问"这个系统是你自己做的吗？"时，AI 可以直接根据这些信息回答。

## 三种 AI 日志

| 日志类型 | 记录内容 | 查看权限 |
|----------|----------|----------|
| QueryLog | 用户提问、AI 回答、意图、Token 消耗 | 本人/管理员 |
| PolishLog | 润色原文、润色结果、状态、模块名 | 本人/管理员 |
| ClassificationLog | 文件名、归类结果、分配模块 | 仅管理员 |

## 配置项

`env
# apps/ai_assistant/settings.py（通过 Django settings 引用）
OPENAI_API_KEY=sk-...          # API 密钥，为空时使用本地降级
OPENAI_BASE_URL=https://api.openai.com/v1  # API 地址
OPENAI_MODEL=gpt-3.5-turbo     # 使用的模型

# Resume 模型上的字段
visitor_ai_mode_enabled         # 访客 AI 模式开关
visitor_ai_enabled              # AI 功能开关
visitor_ai_quota                # AI 调用配额
visitor_ai_used                 # 已用次数
visitor_ai_system_prompt        # 自定义 System Prompt
`
