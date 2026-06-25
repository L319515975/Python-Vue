"""PDF generation service using WeasyPrint."""
import io
import logging
from django.template.loader import render_to_string
from .models import Resume

logger = logging.getLogger(__name__)

# Module display names
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
    Generate a multi-page PDF for the resume.

    Args:
        resume: Resume instance
        selected_modules: list of configurable module keys selected by user

    Returns:
        io.BytesIO buffer containing the PDF

    The PDF always includes personal_info as page 1, then each selected module as a separate page.
    """
    from weasyprint import HTML

    # Build context data for each module
    user = resume.user
    context = {
        'resume': resume,
        'user': user,
        'modules': [],
    }

    # Page 1: Personal Info (always included)
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

    # Selected modules
    for module_key in selected_modules:
        module_data = _build_module_data(resume, module_key)
        if module_data:
            context['modules'].append(module_data)

    # Render HTML from template
    html_string = render_to_string('resume_pdf.html', context)

    # Generate PDF
    pdf_buffer = io.BytesIO()
    HTML(string=html_string).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer


def _build_module_data(resume, module_key):
    """Build data dict for a specific module."""
    name = MODULE_NAMES.get(module_key, module_key)

    if module_key == 'education':
        items = list(resume.educations.all().values('school', 'degree', 'major', 'start_date', 'end_date', 'description'))
        return {'key': module_key, 'name': name, 'items': items, 'type': 'list'}

    elif module_key == 'work_experience':
        items = list(resume.work_experiences.all().values('company', 'position', 'start_date', 'end_date', 'description'))
        return {'key': module_key, 'name': name, 'items': items, 'type': 'list'}

    elif module_key == 'project':
        items = list(resume.projects.all().values('name', 'role', 'start_date', 'end_date', 'tech_stack', 'description'))
        return {'key': module_key, 'name': name, 'items': items, 'type': 'list'}

    elif module_key == 'skill':
        items = list(resume.skills.all().values('name', 'level', 'category'))
        return {'key': module_key, 'name': name, 'items': items, 'type': 'skills'}

    elif module_key == 'certificate':
        # Use module_data JSON field
        data = resume.module_data.get('certificate', '')
        return {'key': module_key, 'name': name, 'content': data, 'type': 'text'}

    elif module_key == 'award':
        data = resume.module_data.get('award', '')
        return {'key': module_key, 'name': name, 'content': data, 'type': 'text'}

    elif module_key == 'language':
        data = resume.module_data.get('language', '')
        return {'key': module_key, 'name': name, 'content': data, 'type': 'text'}

    return None
