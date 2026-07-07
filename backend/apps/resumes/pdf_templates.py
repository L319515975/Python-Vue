"""PDF template registry and resolution helpers."""

from dataclasses import dataclass
from typing import Any

from django.template import Context, Template
from django.template.loader import render_to_string

from .models import ResumePdfTemplate


BUILTIN_PDF_TEMPLATES = {
    'default': {
        'name': '经典简历',
        'description': '沿用当前蓝灰风格，结构清晰，适合通用导出。',
        'template_name': 'resume_pdf.html',
    },
    'modern': {
        'name': '现代简历',
        'description': '更强的版式分区和视觉层次，适合内容较多的简历。',
        'template_name': 'resume_pdf_modern.html',
    },
}

DEFAULT_PDF_TEMPLATE_KEY = 'default'


@dataclass
class ResolvedPdfTemplate:
    template_key: str
    name: str
    description: str
    is_builtin: bool
    template_name: str | None = None
    template_file_content: str | None = None
    uploaded_template_id: int | None = None


def list_pdf_templates(include_inactive: bool = False) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = [_builtin_template_payload(key, cfg) for key, cfg in BUILTIN_PDF_TEMPLATES.items()]

    queryset = ResumePdfTemplate.objects.all().order_by('-is_active', 'name')
    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    for item in queryset:
        templates.append(_uploaded_template_payload(item))
    return templates


def validate_pdf_template_key(template_key: str | None) -> str:
    key = (template_key or DEFAULT_PDF_TEMPLATE_KEY).strip()
    if key in BUILTIN_PDF_TEMPLATES:
        return key

    if key.startswith('custom:'):
        _, raw_id = key.split(':', 1)
        try:
            template = ResumePdfTemplate.objects.get(pk=int(raw_id))
        except (ValueError, ResumePdfTemplate.DoesNotExist) as exc:
            raise ValueError('PDF模板不存在') from exc
        if not template.is_active:
            raise ValueError('PDF模板已停用')
        return key

    raise ValueError('不支持的PDF模板')


def resolve_pdf_template(template_key: str | None = None) -> ResolvedPdfTemplate:
    key = validate_pdf_template_key(template_key)
    if key in BUILTIN_PDF_TEMPLATES:
        cfg = BUILTIN_PDF_TEMPLATES[key]
        return ResolvedPdfTemplate(
            template_key=key,
            name=cfg['name'],
            description=cfg['description'],
            is_builtin=True,
            template_name=cfg['template_name'],
        )

    raw_id = int(key.split(':', 1)[1])
    template = ResumePdfTemplate.objects.get(pk=raw_id)
    return ResolvedPdfTemplate(
        template_key=key,
        name=template.name,
        description=template.description,
        is_builtin=False,
        template_file_content=_read_uploaded_template_content(template),
        uploaded_template_id=template.id,
    )


def render_pdf_html(context: dict[str, Any], template_key: str | None = None) -> str:
    resolved = resolve_pdf_template(template_key)
    if resolved.is_builtin:
        return render_to_string(resolved.template_name, context)
    return Template(resolved.template_file_content or '').render(Context(context))


def _builtin_template_payload(key: str, cfg: dict[str, str]) -> dict[str, Any]:
    return {
        'template_key': key,
        'name': cfg['name'],
        'description': cfg['description'],
        'is_builtin': True,
        'is_active': True,
        'template_file_name': cfg['template_name'],
    }


def _uploaded_template_payload(template: ResumePdfTemplate) -> dict[str, Any]:
    return {
        'id': template.id,
        'template_key': f'custom:{template.id}',
        'name': template.name,
        'description': template.description,
        'is_builtin': False,
        'is_active': template.is_active,
        'template_file_name': template.template_file.name.split('/')[-1] if template.template_file else '',
        'created_at': template.created_at,
        'updated_at': template.updated_at,
    }


def _read_uploaded_template_content(template: ResumePdfTemplate) -> str:
    with template.template_file.open('rb') as fh:
        return fh.read().decode('utf-8-sig')
