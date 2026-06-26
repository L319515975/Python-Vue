"""PDF generation service using WeasyPrint.

PDF生成服务，使用WeasyPrint库将简历渲染为PDF文件。
WeasyPrint是一个Python库，可以将HTML/CSS转换为PDF。
"""
import io
import logging
from django.template.loader import render_to_string
from .models import Resume

logger = logging.getLogger(__name__)

# 模块显示名称映射：英文key -> 中文显示名
# 这些key与Resume模型中的CONFIGURABLE_MODULES对应
MODULE_NAMES = {
    'personal_info': '个人信息',
    'contact': '联系方式',
    'education': '教育经历',
    'work_experience': '工作经历',
    'project': '项目经历',
    'skill': '技能清单',
    'certificate': '证书资质',
    'award': '获奖荣誉',
    'language': '语言能力',
}


def generate_resume_pdf(resume, selected_modules):
    """
    为简历生成多页PDF文件。

    工作流程：
    1. 第1页固定为个人信息（始终包含）
    2. 根据用户选择的模块，每个模块生成一页
    3. 使用WeasyPrint将HTML渲染为PDF

    参数：
        resume: Resume实例（简历对象）
        selected_modules: 用户选择的模块key列表，如 ['education', 'skill']

    返回：
        io.BytesIO对象，包含PDF文件的二进制数据
    """
    # 延迟导入WeasyPrint，因为它是一个可选依赖
    # 如果没有安装，调用此函数时会报错
    from weasyprint import HTML

    # 获取简历关联的用户信息
    user = resume.user

    # 构建模板上下文数据（传递给HTML模板的数据）
    context = {
        'resume': resume,
        'user': user,
        'modules': [],  # 存放每个模块的数据
    }

    # 第1页：个人信息（始终包含，不需要用户选择）
    personal_data = {
        'key': 'personal_info',
        'name': '个人信息',
        'username': user.username,
        'email': user.email or '未填写',
        'phone': getattr(user, 'phone', '') or '未填写',
        'title': resume.title,
        'summary': resume.summary,
    }
    context['modules'].append(personal_data)

    # 遍历用户选择的模块，构建每个模块的数据
    for module_key in selected_modules:
        module_data = _build_module_data(resume, module_key)
        if module_data:
            context['modules'].append(module_data)

    # 使用Django模板引擎将数据渲染为HTML字符串
    # render_to_string 会在 templates/ 目录下查找 resume_pdf.html
    html_string = render_to_string('resume_pdf.html', context)

    # 使用WeasyPrint将HTML转换为PDF
    pdf_buffer = io.BytesIO()  # 创建内存缓冲区
    HTML(string=html_string).write_pdf(pdf_buffer)  # 写入PDF
    pdf_buffer.seek(0)  # 将读取位置重置到开头
    return pdf_buffer


def _build_module_data(resume, module_key):
    """
    为指定模块构建数据字典。

    根据模块类型从数据库查询对应的数据，
    返回统一格式的字典供HTML模板使用。

    参数：
        resume: Resume实例
        module_key: 模块标识符，如 'education', 'skill'

    返回：
        数据字典，包含 key(模块标识), name(显示名), items/content(数据), type(数据类型)
    """
    name = MODULE_NAMES.get(module_key, module_key)

    if module_key == 'education':
        # 查询所有教育经历，values()返回字典列表而非对象列表
        items = list(resume.educations.all().values(
            'school', 'degree', 'major', 'start_date', 'end_date', 'description'
        ))
        return {'key': module_key, 'name': name, 'items': items, 'type': 'list'}

    elif module_key == 'work_experience':
        items = list(resume.work_experiences.all().values(
            'company', 'position', 'start_date', 'end_date', 'description'
        ))
        return {'key': module_key, 'name': name, 'items': items, 'type': 'list'}

    elif module_key == 'project':
        items = list(resume.projects.all().values(
            'name', 'role', 'start_date', 'end_date', 'tech_stack', 'description'
        ))
        return {'key': module_key, 'name': name, 'items': items, 'type': 'list'}

    elif module_key == 'skill':
        items = list(resume.skills.all().values('name', 'level', 'category'))
        return {'key': module_key, 'name': name, 'items': items, 'type': 'skills'}

    elif module_key == 'certificate':
        # 证书、获奖、语言能力存储在module_data JSON字段中
        data = resume.module_data.get('certificate', '')
        return {'key': module_key, 'name': name, 'content': data, 'type': 'text'}

    elif module_key == 'award':
        data = resume.module_data.get('award', '')
        return {'key': module_key, 'name': name, 'content': data, 'type': 'text'}

    elif module_key == 'language':
        data = resume.module_data.get('language', '')
        return {'key': module_key, 'name': name, 'content': data, 'type': 'text'}

    return None