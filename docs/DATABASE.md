# 数据库设计

本文档描述智能简历管理系统的完整数据库结构与表间关系。

## ER 关系图

```mermaid
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

    User ||--o| Resume : "拥有简历"
    User ||--o{ AdminAuditLog : "管理员操作"
    User ||--o{ QueryLog : "AI查询"
    User ||--o{ PolishLog : "AI润色"
    User ||--o{ ClassificationLog : "AI归类"
    Resume ||--o{ Education : "教育经历"
    Resume ||--o{ WorkExperience : "工作经历"
    Resume ||--o{ Project : "项目经历"
    Resume ||--o{ Skill : "技能"
    Resume ||--o{ VisitorAiUsageLog : "访客AI记录"
    Resume }o--o{ Tag : "标签(M2M)"
```

## 表关系说明

| 关系 | 类型 | 说明 |
|------|------|------|
| User → Resume | 一对一 | 一个用户对应一份简历 |
| Resume → Education | 一对多 | 一份简历包含多条教育经历 |
| Resume → WorkExperience | 一对多 | 一份简历包含多条工作经历 |
| Resume → Project | 一对多 | 一份简历包含多条项目经历 |
| Resume → Skill | 一对多 | 一份简历包含多项技能 |
| Resume ↔ Tag | 多对多 | 简历与标签互相绑定，通过中间表关联 |
| Resume → VisitorAiUsageLog | 一对多 | 访客的AI调用记录归属到对应简历 |
| User → AdminAuditLog | 一对多 | 审计日志记录操作管理员身份 |
| User → QueryLog | 一对多 | AI查询日志关联到发起查询的用户 |
| User → PolishLog | 一对多 | AI润色日志关联到发起润色的用户 |
| User → ClassificationLog | 一对多 | AI归类日志关联到上传文件的用户 |

## 所属应用

| 应用 | 表 |
|------|----|
| `apps.users` | User, AdminAuditLog |
| `apps.resumes` | Resume, Tag, Education, WorkExperience, Project, Skill, VisitorAiUsageLog |
| `apps.ai_assistant` | QueryLog, PolishLog, ClassificationLog |
