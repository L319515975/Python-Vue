"""AI Assistant service - handles OpenAI API integration, text polishing, and file classification."""
import json
import re
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.resumes.models import Resume

logger = logging.getLogger(__name__)
User = get_user_model()

# Intent keywords mapping
INTENT_KEYWORDS = {
    'education': ['教育', '学历', '学校', '毕业', '学位', '专业', '大学', '硕士', '博士', '本科'],
    'work_experience': ['工作', '经验', '公司', '职位', '岗位', '任职', '就职', '职业'],
    'project': ['项目', '开发', '负责', '参与', '实现', '搭建', '技术栈'],
    'skill': ['技能', '技术', '能力', '擅长', '掌握', '熟悉', '了解'],
    'summary': ['简介', '介绍', '概述', '概况', '自我', '个人信息'],
}

# Module classification keywords for auto-classification
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
    """Detect user query intent from keywords."""
    query_lower = query.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                return intent
    return 'general'


def build_resume_context(user) -> str:
    """Build resume context string from user's database records."""
    try:
        resume = Resume.objects.prefetch_related(
            'educations', 'work_experiences', 'projects', 'skills'
        ).get(user=user)
    except Resume.DoesNotExist:
        return '该用户暂无简历信息。'

    parts = [f'简历标题: {resume.title}']
    if resume.summary:
        parts.append(f'个人简介: {resume.summary}')

    # Module data (certificate, award, language, etc.)
    if resume.module_data:
        for module_key, content in resume.module_data.items():
            if content:
                parts.append(f'\n{module_key}: {content}')

    # Education
    educations = resume.educations.all()
    if educations.exists():
        parts.append('\n教育经历:')
        for edu in educations:
            end = edu.end_date.strftime('%Y-%m') if edu.end_date else '至今'
            parts.append(f'  - {edu.school} | {edu.degree} | {edu.major} ({edu.start_date.strftime("%Y-%m")} ~ {end})')
            if edu.description:
                parts.append(f'    描述: {edu.description}')

    # Work experience
    works = resume.work_experiences.all()
    if works.exists():
        parts.append('\n工作经历:')
        for w in works:
            end = w.end_date.strftime('%Y-%m') if w.end_date else '至今'
            parts.append(f'  - {w.company} | {w.position} ({w.start_date.strftime("%Y-%m")} ~ {end})')
            if w.description:
                parts.append(f'    描述: {w.description}')

    # Projects
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

    # Skills
    skills = resume.skills.all()
    if skills.exists():
        parts.append('\n技能列表:')
        for s in skills:
            parts.append(f'  - {s.name} (熟练度: {s.level}%) [{s.category}]')

    # Tags
    tags = resume.tags.all()
    if tags.exists():
        parts.append('\n标签: ' + ', '.join([t.name for t in tags]))

    return '\n'.join(parts)


def generate_system_prompt(intent: str, resume_context: str) -> str:
    """Generate system prompt based on intent and resume data."""
    base_prompt = (
        '你是一个专业的简历助手，帮助用户查询和分析简历信息。'
        '请根据用户提供的简历数据，用专业、友好的语气回答问题。'
        '回答应该结构化、清晰，必要时使用列表格式。'
    )

    intent_prompts = {
        'education': '用户正在询问教育背景相关信息，请重点提取和展示教育经历部分。',
        'work_experience': '用户正在询问工作经历相关信息，请重点提取和展示工作经历部分。',
        'project': '用户正在询问项目经历相关信息，请重点提取和展示项目经历部分，包括技术栈和具体贡献。',
        'skill': '用户正在询问技能相关信息，请重点提取和展示技能列表，并给出专业评价。',
        'summary': '用户正在询问个人简介，请综合简历信息给出全面的个人概述。',
    }

    intent_note = intent_prompts.get(intent, '请综合分析简历信息来回答用户的问题。')

    return f'{base_prompt}\n\n{intent_note}\n\n以下是从数据库获取的用户简历数据:\n{resume_context}'


def ask_ai(user, query: str) -> dict:
    """
    Main AI query function.
    Returns dict with: response, intent, tokens_used
    """
    intent = detect_intent(query)
    resume_context = build_resume_context(user)

    api_key = settings.OPENAI_API_KEY
    if api_key:
        return _call_openai_api(api_key, intent, resume_context, query)
    else:
        return _generate_local_response(intent, resume_context, query, user)


def polish_text(text: str, module_name: str = '', user=None) -> dict:
    """
    Polish/optimize resume text using AI.
    Returns dict with: original_text, polished_text, tokens_used, status
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

    # Local fallback: simple text optimization
    return _local_polish(text)


def _call_openai_polish(api_key: str, text: str, module_name: str) -> dict:
    """Call OpenAI API for text polishing."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=settings.OPENAI_BASE_URL)

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
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': text},
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
        logger.error(f'OpenAI polish call failed: {e}')
        return {
            'original_text': text,
            'polished_text': text,
            'tokens_used': 0,
            'status': 'failed',
            'error': str(e),
        }


def _local_polish(text: str) -> dict:
    """Simple local text polish fallback."""
    polished = text.strip()
    # Remove redundant whitespace
    polished = re.sub(r'\n{3,}', '\n\n', polished)
    polished = re.sub(r' {2,}', ' ', polished)
    # Remove filler words
    fillers = ['然后', '就是', '那个', '基本上', '大概', '差不多']
    for filler in fillers:
        polished = polished.replace(filler, '')

    return {
        'original_text': text,
        'polished_text': polished,
        'tokens_used': 0,
        'status': 'success',
    }


def classify_resume_file(resume) -> dict:
    """
    Parse uploaded resume file content and classify into modules.
    Returns dict with: success, classification, modules_assigned
    """
    file_path = None
    if resume.file:
        file_path = resume.file.path
    else:
        return {'success': False, 'error': 'No file attached'}

    # Read file content
    raw_text = _extract_text_from_file(file_path)
    if not raw_text:
        return {'success': False, 'error': '无法解析文件内容'}

    # Try AI classification
    api_key = settings.OPENAI_API_KEY
    if api_key:
        return _call_openai_classify(api_key, raw_text, resume)

    # Local fallback: keyword-based classification
    return _local_classify(raw_text, resume)


def _extract_text_from_file(file_path: str) -> str:
    """Extract text content from uploaded file."""
    try:
        if file_path.endswith('.txt') or file_path.endswith('.md'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_path.endswith('.pdf'):
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                text = ''
                for page in doc:
                    text += page.get_text()
                return text
            except ImportError:
                logger.warning('PyMuPDF not installed, trying basic read')
                with open(file_path, 'rb') as f:
                    return f.read().decode('utf-8', errors='ignore')
        elif file_path.endswith('.doc') or file_path.endswith('.docx'):
            try:
                import docx
                doc = docx.Document(file_path)
                return '\n'.join([p.text for p in doc.paragraphs])
            except ImportError:
                logger.warning('python-docx not installed')
                return ''
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        logger.error(f'File extraction failed: {e}')
        return ''


def _call_openai_classify(api_key: str, raw_text: str, resume) -> dict:
    """Call OpenAI API for resume content classification."""
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

        # Truncate text to avoid token limits
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
        # Try to parse JSON from response
        # Handle markdown code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', result_text)
        if json_match:
            result_text = json_match.group(1).strip()

        classification = json.loads(result_text)
        modules_assigned = [k for k in classification.keys() if k in Resume.CONFIGURABLE_MODULES]

        # Update resume module_data
        if classification:
            current_data = resume.module_data or {}
            for key, value in classification.items():
                if key in Resume.CONFIGURABLE_MODULES and value:
                    current_data[key] = value
            resume.module_data = current_data
            # Enable modules that have content
            existing_enabled = set(resume.enabled_modules or [])
            new_modules = set(modules_assigned) | existing_enabled
            # Cap at MAX_CONFIGURABLE
            resume.enabled_modules = list(new_modules)[:Resume.MAX_CONFIGURABLE]
            resume.save()

        # Log classification
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
        logger.error(f'AI classification JSON parse failed: {e}')
        return _local_classify(raw_text, resume)
    except Exception as e:
        logger.error(f'OpenAI classify call failed: {e}')
        return _local_classify(raw_text, resume)


def _local_classify(raw_text: str, resume) -> dict:
    """Local keyword-based classification fallback."""
    classification = {}
    modules_assigned = []

    text_lower = raw_text.lower()

    for module, keywords in MODULE_KEYWORDS.items():
        score = 0
        matched_sections = []
        for kw in keywords:
            if kw in text_lower:
                score += 1
                # Try to extract surrounding context
                idx = text_lower.index(kw)
                start = max(0, idx - 20)
                end = min(len(raw_text), idx + len(kw) + 100)
                matched_sections.append(raw_text[start:end].strip())

        if score >= 2:  # Require at least 2 keyword matches
            # Extract relevant section from text
            section_text = _extract_section(raw_text, module)
            if section_text:
                classification[module] = section_text
                modules_assigned.append(module)

    # Update resume if classification found
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

    # Log classification
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
    """Extract a section from text based on module type."""
    lines = text.split('\n')
    keywords = MODULE_KEYWORDS.get(module, [])
    section_lines = []
    capturing = False

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            if capturing:
                section_lines.append('')
            continue

        # Check if this line starts a relevant section
        if any(kw in line_stripped.lower() for kw in keywords):
            capturing = True
            section_lines.append(line_stripped)
            continue

        if capturing:
            # Check if we hit a new section (different module keywords)
            is_new_section = False
            for other_module, other_kws in MODULE_KEYWORDS.items():
                if other_module != module:
                    if any(kw in line_stripped.lower() for kw in other_kws):
                        is_new_section = True
                        break
            if is_new_section:
                break
            section_lines.append(line_stripped)

    return '\n'.join(section_lines).strip() if section_lines else ''


def _call_openai_api(api_key: str, intent: str, resume_context: str, query: str) -> dict:
    """Call OpenAI API for response generation."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=settings.OPENAI_BASE_URL)
        system_prompt = generate_system_prompt(intent, resume_context)

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': query},
            ],
            temperature=0.7,
            max_tokens=1000,
        )

        answer = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0

        return {'response': answer, 'intent': intent, 'tokens_used': tokens}

    except Exception as e:
        logger.error(f'OpenAI API call failed: {e}')
        return _generate_local_response(intent, resume_context, query, None)


def _generate_local_response(intent: str, resume_context: str, query: str, user) -> dict:
    """
    Generate a simple local response when OpenAI API is not available.
    This is a fallback that extracts relevant sections from resume data.
    """
    section_map = {
        'education': ('教育经历', '以下是您的教育背景信息'),
        'work_experience': ('工作经历', '以下是您的工作经历信息'),
        'project': ('项目经历', '以下是您的项目经历信息'),
        'skill': ('技能列表', '以下是您的技能信息'),
        'summary': ('个人简介', '以下是您的个人概述'),
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
                if line.strip() and not line.startswith(' ') and not line.startswith('  '):
                    if any(k in line for k in ['教育经历', '工作经历', '项目经历', '技能列表', '简历标题']):
                        break
                relevant.append(line)

        if relevant:
            answer = f'{intro}:\n\n' + '\n'.join(relevant)
        else:
            answer = f'抱歉，暂未找到与"{section_key}"相关的信息。请确认您已完善简历内容。'
    else:
        if resume_context == '该用户暂无简历信息。':
            answer = '抱歉，您还没有填写简历信息。请先完善您的简历，然后就可以向我提问了。'
        else:
            answer = f'以下是您的简历概况:\n\n{resume_context}\n\n如需了解某个方面的详细信息，请具体提问，例如"我的项目经历有哪些"或"我的技能列表"。'

    return {'response': answer, 'intent': intent, 'tokens_used': 0}



def build_resume_context_from_resume(resume) -> str:
    """Build resume context string directly from a Resume object (for visitor AI)."""
    from apps.resumes.models import Resume

    parts = [f'resume title: {resume.title}']
    if resume.summary:
        parts.append(f'personal summary: {resume.summary}')

    # Module data
    if resume.module_data:
        for module_key, content in resume.module_data.items():
            if content:
                parts.append(f'\n{module_key}: {content}')

    # Education
    educations = resume.educations.all()
    if educations.exists():
        parts.append('\neducation:')
        for edu in educations:
            end = edu.end_date.strftime('%Y-%m') if edu.end_date else 'present'
            parts.append(f'  - {edu.school} | {edu.degree} | {edu.major} ({edu.start_date.strftime("%Y-%m")} ~ {end})')
            if edu.description:
                parts.append(f'    desc: {edu.description}')

    # Work experience
    works = resume.work_experiences.all()
    if works.exists():
        parts.append('\nwork experience:')
        for w in works:
            end = w.end_date.strftime('%Y-%m') if w.end_date else 'present'
            parts.append(f'  - {w.company} | {w.position} ({w.start_date.strftime("%Y-%m")} ~ {end})')
            if w.description:
                parts.append(f'    desc: {w.description}')

    # Projects
    projects = resume.projects.all()
    if projects.exists():
        parts.append('\nprojects:')
        for p in projects:
            date_range = ''
            if p.start_date:
                end = p.end_date.strftime('%Y-%m') if p.end_date else 'present'
                date_range = f' ({p.start_date.strftime("%Y-%m")} ~ {end})'
            parts.append(f'  - {p.name}{date_range}')
            if p.role:
                parts.append(f'    role: {p.role}')
            if p.tech_stack:
                parts.append(f'    tech stack: {p.tech_stack}')
            if p.description:
                parts.append(f'    desc: {p.description}')

    # Skills
    skills = resume.skills.all()
    if skills.exists():
        parts.append('\nskills:')
        for s in skills:
            parts.append(f'  - {s.name} (level: {s.level}%) [{s.category}]')

    # Tags
    tags = resume.tags.all()
    if tags.exists():
        parts.append('\ntags: ' + ', '.join([t.name for t in tags]))

    return '\n'.join(parts)


def ask_ai_for_visitor(resume, query: str) -> dict:
    """
    AI query function for HR visitors. Works without a user object.
    Returns dict with: response, intent, tokens_used
    """
    intent = detect_intent(query)
    resume_context = build_resume_context_from_resume(resume)

    api_key = settings.OPENAI_API_KEY
    if api_key:
        return _call_openai_api(api_key, intent, resume_context, query)
    else:
        return _generate_local_response(intent, resume_context, query, None)


def polish_text_for_visitor(resume, text: str, module_name: str = '') -> dict:
    """
    Polish/optimize text for HR visitors. Works without a user object.
    Returns dict with: original_text, polished_text, tokens_used, status
    """
    if not text or not text.strip():
        return {
            'original_text': text,
            'polished_text': text,
            'tokens_used': 0,
            'status': 'failed',
            'error': 'text is empty',
        }

    api_key = settings.OPENAI_API_KEY
    if api_key:
        return _call_openai_polish(api_key, text, module_name)

    return _local_polish(text)
