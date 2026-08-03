"""PDF generation service."""

import io
import logging

from .pdf_templates import render_pdf_html

logger = logging.getLogger(__name__)

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


def generate_resume_pdf(resume, selected_modules, template_key=None):
    """Render a resume to PDF and return an in-memory buffer."""
    from weasyprint import HTML

    user = resume.user
    context = {
        'resume': resume,
        'user': user,
        'modules': [],
    }

    context['modules'].append({
        'key': 'personal_info',
        'name': '个人信息',
        'username': user.username,
        'email': user.email or '未填写',
        'phone': getattr(user, 'phone', '') or '未填写',
        'title': resume.title,
        'summary': resume.summary,
    })

    for module_key in selected_modules:
        module_data = _build_module_data(resume, module_key)
        if module_data:
            context['modules'].append(module_data)

    html_string = render_pdf_html(context, template_key=template_key)
    pdf_buffer = io.BytesIO()
    HTML(string=html_string).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer


def _build_module_data(resume, module_key):
    name = MODULE_NAMES.get(module_key, module_key)

    if module_key == 'education':
        items = list(resume.educations.all().values(
            'school', 'degree', 'major', 'start_date', 'end_date', 'description'
        ))
        return {'key': module_key, 'name': name, 'items': items, 'type': 'list'}

    if module_key == 'work_experience':
        items = list(resume.work_experiences.all().values(
            'company', 'position', 'start_date', 'end_date', 'description'
        ))
        return {'key': module_key, 'name': name, 'items': items, 'type': 'list'}

    if module_key == 'project':
        items = list(resume.projects.all().values(
            'name', 'role', 'start_date', 'end_date', 'tech_stack', 'description'
        ))
        return {'key': module_key, 'name': name, 'items': items, 'type': 'list'}

    if module_key == 'skill':
        items = list(resume.skills.all().values('name', 'level', 'category'))
        return {'key': module_key, 'name': name, 'items': items, 'type': 'skills'}

    if module_key in ('certificate', 'award', 'language'):
        content = resume.module_data.get(module_key, '')
        return {'key': module_key, 'name': name, 'content': content, 'type': 'text'}

    return None
