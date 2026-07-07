"""
AI 助手的核心服务层 —— 负责与 OpenAI API 交互，处理所有 AI 相关的业务逻辑。

本文件是整个 AI 功能的核心，包含：
1. 意图识别（detect_intent）：判断用户想问关于简历的哪个方面
2. 上下文构建（build_resume_context）：从数据库提取简历数据，组装成 AI 能理解的文本
3. AI 对话（ask_ai）：将用户问题和简历上下文发送给 OpenAI 获取回答
4. 文本润色（polish_text）：让 AI 优化简历中的文字表达
5. 文件分类（classify_resume_file）：上传简历文件后，AI 自动解析并分类到各模块
6. 本地降级方案：当 OpenAI API 不可用时，使用关键词匹配作为兜底

架构说明：
- 如果配置了 OPENAI_API_KEY，就调用 OpenAI API 获取智能回答
- 如果没有配置 API_KEY，就使用本地关键词匹配作为降级方案
- 所有函数都设计为：接收 user 或 resume 对象，返回统一格式的字典
"""
import json        # JSON 解析，用于处理 AI 返回的结构化数据
import re          # 正则表达式，用于文本处理
import logging     # 日志记录

from django.conf import settings          # Django 配置，获取 API Key 等
from django.contrib.auth import get_user_model  # 获取用户模型
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from apps.resumes.models import Resume    # 简历模型

logger = logging.getLogger(__name__)
User = get_user_model()


# ========== 意图识别关键词表 ==========
# 当用户提问时，通过匹配这些关键词来判断用户想了解简历的哪个方面
# 例如：用户问"我的学历是什么"，匹配到"学历"关键词，识别为 education 意图
INTENT_KEYWORDS = {
    'education': ['教育', '学历', '学校', '毕业', '学位', '专业', '大学', '硕士', '博士', '本科'],
    'work_experience': ['工作', '经验', '公司', '职位', '岗位', '任职', '就职', '职业'],
    'project': ['项目', '开发', '负责', '参与', '实现', '搭建', '技术栈'],
    'skill': ['技能', '技术', '能力', '擅长', '掌握', '熟悉', '了解'],
    'summary': ['简介', '介绍', '概述', '概况', '自我', '个人信息'],
}

# ========== 文件分类关键词表 ==========
# 用于 AI 自动分类上传的简历文件，比意图识别的关键词更全面
# 包含了简历中常见的标题和段落标记词
MODULE_KEYWORDS = {
    'education': ['教育', '学历', '学校', '毕业', '学位', '专业', '大学', '学院', '硕士', '博士', '本科', '学士', '专科', '高中'],
    'work_experience': ['工作经历', '工作经验', '公司', '职位', '岗位', '任职', '就职', '职业', '在职'],
    'project': ['项目经历', '项目经验', '项目名称', '开发项目', '参与项目', '项目描述', '技术栈'],
    'skill': ['技能', '技术栈', '专业技能', '熟练', '掌握', '熟悉', '了解', '编程语言', '框架', '工具'],
    'certificate': ['证书', '认证', '资格证', '执照', 'CET', '雅思', '托福', 'PMP', 'AWS'],
    'award': ['获奖', '奖励', '荣誉', '奖学金', '竞赛', '比赛', '优秀'],
    'language': ['语言能力', '外语', '英语', '日语', '韩语', '法语', '德语', '中文', '普通话'],
}


def detect_intent(query: str) -> str:
    """
    识别用户查询的意图。

    工作原理：
    1. 将用户输入转为小写
    2. 遍历每个意图的关键词表
    3. 如果用户输入中包含某个关键词，就返回对应的意图
    4. 如果没有匹配到任何关键词，返回 'general'（通用意图）

    例如：
    - "我的学历是本科吗？" → 'education'
    - "我的项目经历有哪些？" → 'project'
    - "帮我看看简历" → 'general'
    """
    query_lower = query.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                return intent
    return 'general'


def build_resume_context(user) -> str:
    """
    从用户的数据库记录中构建简历上下文文本。

    作用：把数据库中的结构化简历数据转换成一段文本，
    这样 AI 就能理解并回答关于简历的问题。

    流程：
    1. 根据 user 查找对应的 Resume 对象
    2. 调用 build_resume_context_from_resume 构建文本
    """
    try:
        # prefetch_related 预加载关联数据，避免 N+1 查询
        resume = Resume.objects.prefetch_related(
            'educations', 'work_experiences', 'projects', 'skills'
        ).get(user=user)
    except Resume.DoesNotExist:
        return '该用户暂无简历信息。'
    return build_resume_context_from_resume(resume)


def generate_system_prompt(intent: str, resume_context: str, owner_label: str = '当前账号') -> str:
    """
    根据用户意图和简历数据生成 AI 的系统提示词（System Prompt）。

    System Prompt 是给 AI 的"角色设定"，告诉 AI：
    - 你是谁（专业简历助手）
    - 你要做什么（分析简历数据）
    - 你怎么回答（专业、结构化、使用列表）

    根据不同意图，还会添加特定的指令：
    - education 意图：重点展示教育经历
    - project 意图：重点展示项目经历和技术栈
    等等。
    """
    # 基础角色设定
    base_prompt = (
        '你是一个专业的简历助手，帮助用户查询和分析简历信息。'
        f'当前回答对象是账号「{owner_label}」的简历。'
        '请只根据提供的简历数据回答，不要编造未提供的信息。'
        '回答应该结构化、清晰，必要时使用列表格式。'
    )

    # 根据意图添加特定指令
    intent_prompts = {
        'education': '用户正在询问教育背景相关信息，请重点提取和展示教育经历部分。',
        'work_experience': '用户正在询问工作经历相关信息，请重点提取和展示工作经历部分。',
        'project': '用户正在询问项目经历相关信息，请重点提取和展示项目经历部分，包括技术栈和具体贡献。',
        'skill': '用户正在询问技能相关信息，请重点提取和展示技能列表，并给出专业评价。',
        'summary': '用户正在询问个人简介，请综合简历信息给出全面的个人概述。',
    }

    intent_note = intent_prompts.get(intent, '请综合分析简历信息来回答用户的问题。')

    return f'{base_prompt}\n\n{intent_note}\n\n以下是从数据库获取的用户简历数据:\n{resume_context}'


def ask_ai(user=None, query: str = '', resume=None, target_user=None) -> dict:
    """
    AI 问答的主入口函数 —— 处理用户的 AI 对话请求。

    参数：
    - user：用户对象（普通用户场景）
    - query：用户的问题文本
    - resume：简历对象（访客 AI 场景，直接传简历避免再查一次数据库）
    - target_user：管理员指定或识别出的目标用户

    返回值：
    - { 'response': 'AI的回答', 'intent': '识别的意图', 'tokens_used': 150 }

    设计思路：
    - 优先传 resume 对象（访客场景），其次传 user 对象（登录用户场景）
    - 如果配置了 OpenAI API Key，调用 OpenAI 获取智能回答
    - 如果没有 API Key，使用本地关键词匹配作为降级方案
    """
    intent = detect_intent(query)
    owner_user = target_user or user
    owner_label = getattr(owner_user, 'username', '当前账号') if owner_user else '当前账号'

    if resume:
        resume_context = build_resume_context_from_resume(resume)
        owner_label = getattr(resume.user, 'username', owner_label)
    elif owner_user:
        resume_context = build_resume_context(owner_user)
    else:
        resume_context = ''

    api_key = settings.OPENAI_API_KEY
    if api_key:
        return _call_openai_api(api_key, intent, resume_context, query, owner_label)
    else:
        return _generate_local_response(intent, resume_context, query, owner_label)


def resolve_chat_target(request_user, query: str, target_user_id=None, target_username: str = ''):
    """
    根据请求者、显式目标和问题内容，解析 AI 对话目标账号。

    规则：
    1. 普通用户只能查询自己的简历
    2. 管理员可以显式指定其他用户
    3. 管理员未显式指定时，尝试从问题中识别目标用户名
    """
    if not request_user or not request_user.is_authenticated:
        raise PermissionDenied('请先登录后再使用AI对话功能。')

    explicit_target = target_user_id is not None or bool(target_username)
    if explicit_target:
        if request_user.role != 'admin':
            same_username = target_username.lower() == request_user.username.lower() if target_username else False
            if target_user_id == request_user.id or same_username:
                return request_user
            raise PermissionDenied('只有管理员可以查询其他账号的简历信息。')
        return _get_user_by_identifier(target_user_id, target_username)

    if request_user.role != 'admin':
        return request_user

    inferred_user = _infer_target_user_from_query(query, request_user)
    return inferred_user or request_user


def polish_text(text: str, module_name: str = '', user=None, resume=None) -> dict:
    """
    文本润色的主入口函数 —— 优化简历中的文字表达。

    参数：
    - text：需要润色的原始文本
    - module_name：所属模块名（如 'education'、'work_experience'），帮助 AI 理解上下文
    - user / resume：用于日志记录（可选）

    返回值：
    - { 'original_text': '原文', 'polished_text': '润色后', 'tokens_used': 80, 'status': 'success' }
    """
    if not text or not text.strip():
        return {
            'original_text': text,
            'polished_text': text,
            'tokens_used': 0,
            'status': 'failed',
            'error': '文本内容为空',
        }

    api_key = settings.OPENAI_API_KEY
    if api_key:
        return _call_openai_polish(api_key, text, module_name)

    return _local_polish(text)


# ========== OpenAI API 调用函数 ==========
# 以下函数负责实际与 OpenAI API 通信

def _call_openai_polish(api_key: str, text: str, module_name: str) -> dict:
    """
    调用 OpenAI API 进行文本润色。

    流程：
    1. 创建 OpenAI 客户端
    2. 构建系统提示词（告诉 AI 你是润色专家，给出润色规则）
    3. 发送请求到 OpenAI
    4. 解析返回的润色结果
    5. 如果出错，返回原文并标记失败

    参数说明：
    - temperature=0.7：控制 AI 回答的随机性，0.7 是比较适中的值
      值越小回答越确定，值越大回答越多样
    - max_tokens=2000：限制 AI 回答的最大 token 数（防止过长）
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=settings.OPENAI_BASE_URL)

        # 如果指定了模块名，添加上下文提示
        context_hint = f'（此内容属于简历的"{module_name}"模块）' if module_name else ''
        system_prompt = (
            '你是一位专业的简历润色专家。请对用户提供的简历文本进行润色优化，要求：\n'
            '1. 保持原始信息的完整性和准确性\n'
            '2. 使用更专业、精练的表达方式\n'
            '3. 突出关键成果和数据\n'
            '4. 语言简洁有力，避免冗余\n'
            '5. 仅返回润色后的文本，不要添加解释\n'
            f'{context_hint}'
        )

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},   # AI 的角色设定
                {'role': 'user', 'content': text},              # 用户的输入
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        polished = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens if response.usage else 0

        return {
            'original_text': text,
            'polished_text': polished,
            'tokens_used': tokens,
            'status': 'success',
        }

    except Exception as e:
        logger.error(f'OpenAI 润色调用失败: {e}')
        return {
            'original_text': text,
            'polished_text': text,
            'tokens_used': 0,
            'status': 'failed',
            'error': str(e),
        }


def _local_polish(text: str) -> dict:
    """
    本地文本润色降级方案 —— 在没有 OpenAI API 时使用。

    只做简单的文本清理：
    1. 去除多余的空行（3行以上合并为2行）
    2. 去除多余的空格
    3. 去除常见口语化词汇（"然后"、"就是"、"那个"等）
    """
    polished = text.strip()
    # 去除连续3个以上的空行，替换为2个空行
    polished = re.sub(r'\n{3,}', '\n\n', polished)
    # 去除连续多个空格，替换为1个
    polished = re.sub(r' {2,}', ' ', polished)
    # 去除口语化词汇
    fillers = ['然后', '就是', '那个', '基本上', '大概', '差不多']
    for filler in fillers:
        polished = polished.replace(filler, '')

    return {
        'original_text': text,
        'polished_text': polished,
        'tokens_used': 0,
        'status': 'success',
    }


# ========== 文件自动分类功能 ==========

def classify_resume_file(resume) -> dict:
    """
    解析上传的简历文件并自动分类到各模块。

    流程：
    1. 读取上传的文件内容（支持 PDF、Word、Markdown、纯文本）
    2. 如果有 OpenAI API Key，调用 AI 进行智能分类
    3. 如果没有 API Key，使用本地关键词匹配作为降级方案

    返回值：
    - { 'success': True, 'classification': {'education': '...', 'project': '...'}, 'modules_assigned': [...] }
    """
    file_path = None
    if resume.file:
        file_path = resume.file.path   # 获取文件在服务器上的路径
    else:
        return {'success': False, 'error': '没有上传文件'}

    # 从文件中提取文本内容
    raw_text = _extract_text_from_file(file_path)
    if not raw_text:
        return {'success': False, 'error': '无法解析文件内容'}

    # 尝试 AI 分类
    api_key = settings.OPENAI_API_KEY
    if api_key:
        return _call_openai_classify(api_key, raw_text, resume)

    # 本地降级方案：基于关键词匹配
    return _local_classify(raw_text, resume)


def _extract_text_from_file(file_path: str) -> str:
    """
    从上传的文件中提取纯文本内容。

    支持的格式：
    - .txt / .md：直接读取文本
    - .pdf：使用 PyMuPDF（fitz）库解析
    - .doc / .docx：使用 python-docx 库解析
    - 其他格式：尝试以 UTF-8 文本读取
    """
    try:
        if file_path.endswith('.txt') or file_path.endswith('.md'):
            # 纯文本和 Markdown 文件：直接读取
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_path.endswith('.pdf'):
            # PDF 文件：使用 PyMuPDF 解析
            try:
                import fitz  # PyMuPDF 库
                doc = fitz.open(file_path)
                text = ''
                for page in doc:
                    text += page.get_text()  # 提取每一页的文本
                return text
            except ImportError:
                logger.warning('PyMuPDF 未安装，尝试基本读取')
                with open(file_path, 'rb') as f:
                    return f.read().decode('utf-8', errors='ignore')
        elif file_path.endswith('.doc') or file_path.endswith('.docx'):
            # Word 文件：使用 python-docx 解析
            try:
                import docx
                doc = docx.Document(file_path)
                return '\n'.join([p.text for p in doc.paragraphs])
            except ImportError:
                logger.warning('python-docx 未安装')
                return ''
        else:
            # 其他格式：尝试文本读取
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        logger.error(f'文件提取失败: {e}')
        return ''


def _call_openai_classify(api_key: str, raw_text: str, resume) -> dict:
    """
    调用 OpenAI API 进行简历内容分类。

    工作原理：
    1. 告诉 AI 可用的模块列表（教育经历、工作经历、项目等）
    2. 让 AI 以 JSON 格式返回分类结果
    3. 解析 JSON，更新简历的 module_data 和 enabled_modules
    4. 记录分类日志

    为什么 temperature=0.3？
    分类任务需要确定性结果，低 temperature 让 AI 的回答更稳定可靠。
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=settings.OPENAI_BASE_URL)

        modules_list = ', '.join(Resume.CONFIGURABLE_MODULES)
        system_prompt = (
            '你是一个简历内容分析专家。请分析以下简历文本，将内容归类到以下模块中:\n'
            f'可用模块: {modules_list}\n\n'
            '请以JSON格式返回结果，格式如下:\n'
            '{\n'
            '  "education": "教育经历相关文本",\n'
            '  "work_experience": "工作经历相关文本",\n'
            '  "project": "项目经历相关文本",\n'
            '  "skill": "技能相关文本",\n'
            '  "certificate": "证书相关文本",\n'
            '  "award": "获奖相关文本",\n'
            '  "language": "语言能力相关文本"\n'
            '}\n'
            '只包含有内容的模块，没有对应内容的模块不要包含在结果中。'
            '仅返回JSON，不要添加其他说明。'
        )

        # 截断过长文本，避免超过 token 限制
        truncated = raw_text[:4000]

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': truncated},
            ],
            temperature=0.3,
            max_tokens=3000,
        )

        result_text = response.choices[0].message.content.strip()

        # 处理 AI 返回的 markdown 代码块格式（如 ```json ... ```）
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', result_text)
        if json_match:
            result_text = json_match.group(1).strip()

        classification = json.loads(result_text)
        # 过滤出有效的模块名
        modules_assigned = [k for k in classification.keys() if k in Resume.CONFIGURABLE_MODULES]

        # 更新简历的模块数据
        if classification:
            current_data = resume.module_data or {}
            for key, value in classification.items():
                if key in Resume.CONFIGURABLE_MODULES and value:
                    current_data[key] = value
            resume.module_data = current_data
            # 合并已启用模块和新分类的模块
            existing_enabled = set(resume.enabled_modules or [])
            new_modules = set(modules_assigned) | existing_enabled
            # 限制最大模块数
            resume.enabled_modules = list(new_modules)[:Resume.MAX_CONFIGURABLE]
            resume.save()

        # 记录分类日志
        from apps.ai_assistant.models import ClassificationLog
        ClassificationLog.objects.create(
            user=resume.user,
            file_name=resume.file_name or 'unknown',
            raw_text=raw_text[:5000],
            classification_result=classification,
            modules_assigned=modules_assigned,
            status='success',
        )

        return {
            'success': True,
            'classification': classification,
            'modules_assigned': modules_assigned,
        }

    except json.JSONDecodeError as e:
        logger.error(f'AI 分类 JSON 解析失败: {e}')
        return _local_classify(raw_text, resume)
    except Exception as e:
        logger.error(f'OpenAI 分类调用失败: {e}')
        return _local_classify(raw_text, resume)


def _local_classify(raw_text: str, resume) -> dict:
    """
    本地关键词分类降级方案 —— 在没有 OpenAI API 时使用。

    工作原理：
    1. 遍历每个模块的关键词表
    2. 统计每个模块匹配到的关键词数量
    3. 如果某个模块匹配到 2 个以上关键词，认为该模块有内容
    4. 尝试从原文中提取该模块的相关段落
    5. 更新简历的 module_data 和 enabled_modules

    注意：这种方案不如 AI 分类准确，但能提供基本的分类能力。
    """
    classification = {}
    modules_assigned = []

    text_lower = raw_text.lower()

    for module, keywords in MODULE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in text_lower:
                score += 1

        # 至少匹配 2 个关键词才算有效
        if score >= 2:
            # 尝试从原文中提取该模块的段落
            section_text = _extract_section(raw_text, module)
            if section_text:
                classification[module] = section_text
                modules_assigned.append(module)

    # 更新简历数据
    if classification:
        current_data = resume.module_data or {}
        for key, value in classification.items():
            if key in Resume.CONFIGURABLE_MODULES and value:
                current_data[key] = value
        resume.module_data = current_data
        existing_enabled = set(resume.enabled_modules or [])
        new_modules = set(modules_assigned) | existing_enabled
        resume.enabled_modules = list(new_modules)[:Resume.MAX_CONFIGURABLE]
        resume.save()

    # 记录分类日志
    try:
        from apps.ai_assistant.models import ClassificationLog
        ClassificationLog.objects.create(
            user=resume.user,
            file_name=resume.file_name or 'unknown',
            raw_text=raw_text[:5000],
            classification_result=classification,
            modules_assigned=modules_assigned,
            status='success' if classification else 'failed',
        )
    except Exception:
        pass

    return {
        'success': bool(classification),
        'classification': classification,
        'modules_assigned': modules_assigned,
    }


def _extract_section(text: str, module: str) -> str:
    """
    从简历原文中提取特定模块的段落。

    工作原理：
    1. 逐行扫描文本
    2. 当发现包含模块关键词的行时，开始捕获内容
    3. 当遇到其他模块的关键词时，停止捕获
    4. 返回捕获到的段落文本

    这是一种简单的"基于标题的段落提取"方法。
    """
    lines = text.split('\n')
    keywords = MODULE_KEYWORDS.get(module, [])
    section_lines = []
    capturing = False  # 是否正在捕获段落

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            if capturing:
                section_lines.append('')  # 保留段落内的空行
            continue

        # 检查这行是否包含当前模块的关键词（段落开始标记）
        if any(kw in line_stripped.lower() for kw in keywords):
            capturing = True
            section_lines.append(line_stripped)
            continue

        if capturing:
            # 检查是否遇到了其他模块的关键词（段落结束标记）
            is_new_section = False
            for other_module, other_kws in MODULE_KEYWORDS.items():
                if other_module != module:
                    if any(kw in line_stripped.lower() for kw in other_kws):
                        is_new_section = True
                        break
            if is_new_section:
                break  # 遇到新段落标题，停止捕获
            section_lines.append(line_stripped)

    return '\n'.join(section_lines).strip() if section_lines else ''


# ========== OpenAI 对话调用 ==========

def _call_openai_api(api_key: str, intent: str, resume_context: str, query: str, owner_label: str) -> dict:
    """
    调用 OpenAI API 进行简历问答。

    流程：
    1. 根据意图和简历数据生成系统提示词
    2. 发送对话请求到 OpenAI
    3. 解析返回结果

    如果调用失败，自动降级到本地响应。
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=settings.OPENAI_BASE_URL)
        system_prompt = generate_system_prompt(intent, resume_context, owner_label)

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},   # AI 的角色设定
                {'role': 'user', 'content': query},              # 用户的问题
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        answer = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0

        return {'response': answer, 'intent': intent, 'tokens_used': tokens}

    except Exception as e:
        logger.error(f'OpenAI API 调用失败: {e}')
        return _generate_local_response(intent, resume_context, query, owner_label)


def _generate_local_response(intent: str, resume_context: str, query: str, owner_label: str) -> dict:
    """
    本地响应降级方案 —— 在没有 OpenAI API 时使用。

    工作原理：
    1. 根据意图从简历上下文中提取相关的段落
    2. 将提取的内容拼接成回答
    3. 如果没有找到相关内容，提示用户完善简历

    这是一种"智能搜索+拼接"的方法，虽然不如 AI 回答自然，
    但能提供基本的信息提取功能。
    """
    section_map = {
        'education': ('教育经历', '以下是账号「{owner_label}」的教育背景信息'),
        'work_experience': ('工作经历', '以下是账号「{owner_label}」的工作经历信息'),
        'project': ('项目经历', '以下是账号「{owner_label}」的项目经历信息'),
        'skill': ('技能列表', '以下是账号「{owner_label}」的技能信息'),
        'summary': ('个人简介', '以下是账号「{owner_label}」的个人概述'),
    }

    if intent in section_map:
        section_key, intro = section_map[intent]
        lines = resume_context.split('\n')
        relevant = []
        capture = False
        for line in lines:
            if section_key in line:
                capture = True
                relevant.append(line)
                continue
            if capture:
                # 检查是否遇到了其他段落的标题
                if line.strip() and not line.startswith(' ') and not line.startswith('  '):
                    if any(k in line for k in ['教育经历', '工作经历', '项目经历', '技能列表', '简历标题']):
                        break
                relevant.append(line)

        if relevant:
            answer = f'{intro.format(owner_label=owner_label)}:\n\n' + '\n'.join(relevant)
        else:
            answer = f'抱歉，账号「{owner_label}」暂未找到与"{section_key}"相关的信息。请确认简历内容已完善。'
    else:
        if resume_context == '该用户暂无简历信息。':
            answer = f'抱歉，账号「{owner_label}」还没有填写简历信息。请先完善简历，然后再提问。'
        else:
            answer = f'以下是账号「{owner_label}」的简历概况:\n\n{resume_context}\n\n如需了解某个方面的详细信息，请具体提问。'

    return {'response': answer, 'intent': intent, 'tokens_used': 0}


def _normalize_lookup_text(text: str) -> str:
    return re.sub(r'\s+', '', (text or '').lower())


def _get_user_by_identifier(user_id=None, username: str = ''):
    query = User.objects.all()
    if user_id is not None:
        user = query.filter(id=user_id).first()
    else:
        user = query.filter(username__iexact=username).first()
    if not user:
        raise NotFound('未找到目标用户。')
    return user


def _infer_target_user_from_query(query: str, request_user):
    """
    从问题文本中识别目标用户。

    仅在管理员未显式指定目标时使用。
    """
    normalized_query = _normalize_lookup_text(query)
    if not normalized_query:
        return None

    candidates = User.objects.exclude(id=request_user.id).only(
        'id', 'username', 'first_name', 'last_name', 'email'
    )
    matched = []
    for candidate in candidates:
        aliases = {
            candidate.username,
            candidate.first_name,
            candidate.last_name,
            candidate.get_full_name(),
            candidate.email,
        }
        for alias in aliases:
            alias_text = _normalize_lookup_text(alias)
            if alias_text and alias_text in normalized_query:
                matched.append(candidate)
                break

    if len(matched) > 1:
        raise ValidationError('检测到多个可能的目标用户，请通过 target_user_id 或 target_username 明确指定。')
    if matched:
        return matched[0]
    return None


def build_resume_context_from_resume(resume) -> str:
    """
    直接从 Resume 对象构建简历上下文文本（用于访客 AI 场景）。

    与 build_resume_context(user) 的区别：
    - 这个函数直接接收 Resume 对象，不需要先查数据库
    - 在访客 AI 场景中使用（已经持有 Resume 对象时避免重复查询）

    构建的内容包括：
    1. 简历标题和摘要
    2. 自定义模块数据（module_data）
    3. 教育经历列表
    4. 工作经历列表
    5. 项目经历列表
    6. 技能列表
    7. 标签列表

    输出格式为纯文本，方便 AI 理解。
    """
    parts = [f'简历标题: {resume.title}']
    if resume.summary:
        parts.append(f'个人简介: {resume.summary}')

    # 自定义模块数据（用户通过编辑器填写的内容）
    if resume.module_data:
        for module_key, content in resume.module_data.items():
            if content:
                parts.append(f'\n{module_key}: {content}')

    # 教育经历
    educations = resume.educations.all()
    if educations.exists():
        parts.append('\n教育经历:')
        for edu in educations:
            end = edu.end_date.strftime('%Y-%m') if edu.end_date else '至今'
            parts.append(f'  - {edu.school} | {edu.degree} | {edu.major} ({edu.start_date.strftime("%Y-%m")} ~ {end})')
            if edu.description:
                parts.append(f'    描述: {edu.description}')

    # 工作经历
    works = resume.work_experiences.all()
    if works.exists():
        parts.append('\n工作经历:')
        for w in works:
            end = w.end_date.strftime('%Y-%m') if w.end_date else '至今'
            parts.append(f'  - {w.company} | {w.position} ({w.start_date.strftime("%Y-%m")} ~ {end})')
            if w.description:
                parts.append(f'    描述: {w.description}')

    # 项目经历
    projects = resume.projects.all()
    if projects.exists():
        parts.append('\n项目经历:')
        for p in projects:
            date_range = ''
            if p.start_date:
                end = p.end_date.strftime('%Y-%m') if p.end_date else '至今'
                date_range = f' ({p.start_date.strftime("%Y-%m")} ~ {end})'
            parts.append(f'  - {p.name}{date_range}')
            if p.role:
                parts.append(f'    角色: {p.role}')
            if p.tech_stack:
                parts.append(f'    技术栈: {p.tech_stack}')
            if p.description:
                parts.append(f'    描述: {p.description}')

    # 技能列表
    skills = resume.skills.all()
    if skills.exists():
        parts.append('\n技能列表:')
        for s in skills:
            parts.append(f'  - {s.name} (熟练度: {s.level}%) [{s.category}]')

    # 标签
    tags = resume.tags.all()
    if tags.exists():
        parts.append('\n标签: ' + ', '.join([t.name for t in tags]))

    return '\n'.join(parts)
