# 变更日志

## v2.0.0 (2026-07-12)

### 新增功能

- **管理员"我的简历"模块**：管理员后台"我的简历"排在菜单首位，管理员也可以查看和编辑自己的简历
- **GET/PATCH /api/resumes/my-resume/** 新端点，自动匹配当前登录用户的简历
- **AI 自定义 System Prompt**：访客 AI 模式支持自定义提示词，HR 可通过 AI 准确了解开发者
- **"关于本系统"技术栈展示**：AI 构建简历上下文时自动追加系统技术栈信息

### 功能改进

- **前端路由重构**：管理员菜单按使用频率排序，"我的简历"位居首位
- **微信小程序同步**：小程序端简历详情页优先使用 myResume 接口
- **小程序管理员仪表盘**：新增"我的简历"快捷入口
- **全栈 BOM 清理**：移除所有源码文件中的 BOM 字符，消除潜在构建问题
- **文档体系完善**：新增 ARCHITECTURE.md、AI_FEATURES.md、API.md、CHANGELOG.md

### 数据库变更

- Resume 模型新增 visitor_ai_system_prompt 字段（TextField）

\\ash
# 升级步骤
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate          # 应用 0003 迁移
python manage.py collectstatic --noinput
cd ../frontend
npm install && npm run build
\
## v1.0.0 (2026-06)

初始版本：

- 账号体系（管理员/普通用户 JWT 登录）
- 简历 CRUD + 模块化管理
- 访客分享（HMAC 签名链接）
- 访客 AI 模式（问答 + 润色）
- AI 助手（对话 + 润色 + 文件自动归类）
- PDF 导出（多模板）
- 标签管理
- 操作审计日志
- 微信小程序端
- Vue → 小程序同步脚本
- drf-yasg API 文档
