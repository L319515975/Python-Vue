# 数据库设计

本文档描述智能简历管理系统的完整数据库结构与表间关系。

> 最后更新：2026-07-12

## ER 关系图

`mermaid
erDiagram
    User {
        BigAutoField id PK
        CharField username
        CharField email
        CharField password
        CharField role "admin / user"
        CharField phone
        ImageField avatar
        DateTimeField created_at
        DateTimeField updated_at
    }

    Resume {
        BigAutoField id PK
        BigAutoField user_id FK "OneToOne"
        CharField title
        TextField summary
        CharField status "draft / published"
        FileField file
        CharField file_name
        JSONField enabled_modules
        JSONField module_data
        BooleanField ai_processed
        JSONField ai_classification_result
        BooleanField visitor_enabled
        CharField visitor_token
        DateTimeField visitor_expires
        BooleanField visitor_allow_download
        JSONField public_modules
        BooleanField visitor_ai_mode_enabled
        BooleanField visitor_ai_enabled
        IntegerField visitor_ai_quota
        IntegerField visitor_ai_used
        TextField visitor_ai_system_prompt "v2 added"
        DateTimeField created_at
        DateTimeField updated_at
    }

    ResumePdfTemplate {
        BigAutoField id PK
        CharField name
        CharField description
        FileField template_file
        BooleanField is_active
        DateTimeField created_at
        DateTimeField updated_at
    }

    Tag {
        BigAutoField id PK
        CharField name
        CharField tag_type "skill / project / certificate / award / language / custom"
        BooleanField is_system
        DateTimeField created_at
    }

    Education {
        BigAutoField id PK
        BigAutoField resume_id FK
        CharField school
        CharField degree
        CharField major
        DateField start_date
        DateField end_date
        TextField description
        IntegerField order
    }

    WorkExperience {
        BigAutoField id PK
        BigAutoField resume_id FK
        CharField company
        CharField position
        DateField start_date
        DateField end_date
        TextField description
        IntegerField order
    }

    Project {
        BigAutoField id PK
        BigAutoField resume_id FK
        CharField name
        CharField role
        DateField start_date
        DateField end_date
        TextField description
        CharField tech_stack
        IntegerField order
    }

    Skill {
        BigAutoField id PK
        BigAutoField resume_id FK
        CharField name
        IntegerField level "0-100"
        CharField category
        IntegerField order
    }

    AdminAuditLog {
        BigAutoField id PK
        BigAutoField admin_user_id FK
        CharField action
        CharField target_user
        TextField detail
        GenericIPAddressField ip_address
        DateTimeField created_at
    }

    VisitorAiUsageLog {
        BigAutoField id PK
        BigAutoField resume_id FK
        CharField visitor_token
        CharField call_type "chat / polish"
        TextField query_text
        TextField response_text
        IntegerField tokens_used
        GenericIPAddressField ip_address
        DateTimeField created_at
    }

    QueryLog {
        BigAutoField id PK
        BigAutoField user_id FK
        TextField query
        TextField response
        CharField intent
        IntegerField tokens_used
        DateTimeField created_at
    }

    PolishLog {
        BigAutoField id PK
        BigAutoField user_id FK
        TextField original_text
        TextField polished_text
        CharField module_name
        CharField status "success / failed / timeout"
        IntegerField tokens_used
        DateTimeField created_at
    }

    ClassificationLog {
        BigAutoField id PK
        BigAutoField user_id FK
        CharField file_name
        TextField raw_text
        JSONField classification_result
        JSONField modules_assigned
        CharField status "success / failed"
        DateTimeField created_at
    }

    User ||--o| Resume : "OneToOne 拥有简历"
    User ||--o{ AdminAuditLog : "一对多 管理员操作"
    User ||--o{ QueryLog : "一对多 AI查询"
    User ||--o{ PolishLog : "一对多 AI润色"
    User ||--o{ ClassificationLog : "一对多 AI归类"
    Resume ||--o{ Education : "一对多 教育经历"
    Resume ||--o{ WorkExperience : "一对多 工作经历"
    Resume ||--o{ Project : "一对多 项目经历"
    Resume ||--o{ Skill : "一对多 技能"
    Resume ||--o{ VisitorAiUsageLog : "一对多 访客AI记录"
    Resume }o--o{ Tag : "多对多 标签"
`

## 表关系说明

| 关系 | 类型 | 说明 |
|------|------|------|
| User → Resume | 一对一 | 一个用户对应一份简历，通过 user_id 关联 |
| Resume → Education | 一对多 | 一份简历包含多条教育经历 |
| Resume → WorkExperience | 一对多 | 一份简历包含多条工作经历 |
| Resume → Project | 一对多 | 一份简历包含多条项目经历 |
| Resume → Skill | 一对多 | 一份简历包含多项技能 |
| Resume ↔ Tag | 多对多 | 简历与标签多对多关联，Django 自动创建中间表 |
| Resume → VisitorAiUsageLog | 一对多 | 访客 AI 调用记录归属到对应简历 |
| Resume → ResumePdfTemplate | 无外键 | 模板是独立配置，各简历导出时按模板名引用 |
| User → AdminAuditLog | 一对多 | 审计日志记录操作管理员身份 |
| User → QueryLog | 一对多 | AI 查询日志关联到发起查询的用户 |
| User → PolishLog | 一对多 | AI 润色日志关联到发起润色的用户 |
| User → ClassificationLog | 一对多 | AI 归类日志关联到上传文件的用户 |

## 核心模型详解

### Resume（简历主表）

简历是整个系统的核心模型，采用**模块化设计**：

- **固定模块**：personal_info（个人信息）、contact（联系方式），始终启用
- **可配置模块**：education、work_experience、project、skill、certificate、ward、language，用户最多选 5 个
- **模块数据**：结构化数据（教育/工作/项目/技能）存储在子表中；纯文本模块（证书/获奖/语言）存储在 module_data（JSONField）中

**访客链接字段组**控制简历的外部分享行为：
- isitor_enabled / isitor_token / isitor_expires — 链接开关与有效期
- isitor_allow_download / public_modules — 下载与可见范围
- isitor_ai_mode_enabled / isitor_ai_enabled / isitor_ai_quota / isitor_ai_used — AI 模式配额
- isitor_ai_system_prompt — 自定义 AI 提示词（v2 新增），让 HR 等访客通过 AI 准确了解开发者

### ResumePdfTemplate（PDF 模板）

独立于简历的模板配置，支持上传自定义 HTML 模板文件：

| 字段 | 类型 | 说明 |
|------|------|------|
| name | CharField(120) | 模板名称 |
| description | CharField(255) | 模板描述 |
| template_file | FileField | HTML 模板文件，上传到 esume_templates/ |
| is_active | BooleanField | 是否启用 |
| created_at / updated_at | DateTimeField | 时间戳 |

	emplate_key 为 default 和 modern 两个内置模板，自定义模板的 key 格式为 custom:{id}。

### 审计与日志

系统包含 **5 种日志**，覆盖所有敏感操作和 AI 调用：

| 日志表 | 记录内容 | 访问权限 |
|--------|----------|----------|
| AdminAuditLog | 管理员对用户/简历/标签的增删改操作 | 仅管理员 |
| QueryLog | 用户向 AI 助手提问的记录 | 本人/管理员 |
| PolishLog | AI 文本润色的原文与结果 | 本人/管理员 |
| ClassificationLog | AI 自动分类简历文件的结果 | 仅管理员 |
| VisitorAiUsageLog | 访客通过链接使用 AI 的记录 | 仅管理员 |

## 所属应用

| 应用 | 包含模型 |
|------|----------|
| pps.users | User, AdminAuditLog |
| pps.resumes | Resume, ResumePdfTemplate, Tag, Education, WorkExperience, Project, Skill, VisitorAiUsageLog |
| pps.ai_assistant | QueryLog, PolishLog, ClassificationLog |

## 迁移历史

| 迁移文件 | 变更内容 |
|----------|----------|
|  001_initial.py | 初始建表：User、Resume、Tag、子模型 |
|  002_resumepdftemplate.py | 新增 ResumePdfTemplate 模型 |
|  003_resume_visitor_ai_system_prompt.py | Resume 新增 isitor_ai_system_prompt 字段 |
