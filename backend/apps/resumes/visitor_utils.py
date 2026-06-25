"""Visitor link utilities - HMAC signature generation and verification (with HR mode)."""
import hashlib
import hmac
import logging
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_visitor_secret():
    """Get the secret key for visitor link signing."""
    return getattr(settings, 'VISITOR_LINK_SECRET', settings.SECRET_KEY)


def generate_visitor_signature(token: str, expires_timestamp: int, role: str = 'visitor') -> str:
    """
    Generate HMAC-SHA256 signature for a visitor link.
    Signs: token + expires_timestamp + role (to prevent role tampering).
    """
    secret = get_visitor_secret()
    message = f'{token}:{expires_timestamp}:{role}'.encode('utf-8')
    signature = hmac.new(
        secret.encode('utf-8'),
        message,
        hashlib.sha256,
    ).hexdigest()
    return signature


def verify_visitor_signature(token: str, expires_timestamp: int, sig: str, role: str = 'visitor') -> bool:
    """
    Verify the HMAC-SHA256 signature of a visitor link.
    Returns True if valid, False otherwise.
    """
    expected_sig = generate_visitor_signature(token, expires_timestamp, role)
    return hmac.compare_digest(expected_sig, sig)


def is_visitor_link_valid(resume) -> dict:
    """
    Check if a resume's visitor link is currently valid.
    Returns dict with: valid (bool), reason (str if invalid)
    """
    if not resume.visitor_enabled:
        return {'valid': False, 'reason': '游客链接未启用'}

    if not resume.visitor_token:
        return {'valid': False, 'reason': '游客链接未生成'}

    if resume.visitor_expires and resume.visitor_expires < timezone.now():
        return {'valid': False, 'reason': '游客链接已过期'}

    if resume.status != 'published':
        return {'valid': False, 'reason': '简历未发布'}

    return {'valid': True}


def get_visitor_url(resume, request=None) -> str:
    """
    Build the full visitor URL for a resume.
    If HR mode is enabled, includes role=hr and quota parameters.
    Returns URL with signature parameters.
    """
    from datetime import datetime

    if not resume.visitor_token:
        return ''

    expires_ts = 0
    if resume.visitor_expires:
        expires_ts = int(resume.visitor_expires.timestamp())

    # Determine role for signature
    role = 'hr' if resume.visitor_hr_enabled else 'visitor'
    sig = generate_visitor_signature(resume.visitor_token, expires_ts, role)

    base_url = ''
    if request:
        base_url = f'{request.scheme}://{request.get_host()}'

    url = f'{base_url}/visitor/{resume.visitor_token}'
    params = []
    if expires_ts:
        params.append(f'expires={expires_ts}')
    params.append(f'sig={sig}')

    if resume.visitor_hr_enabled:
        params.append(f'role=hr')
        params.append(f'quota={resume.visitor_ai_quota}')

    url += '?' + '&'.join(params)
    return url


def check_hr_ai_quota(resume) -> dict:
    """
    Check if the HR visitor still has AI quota remaining.
    Returns dict with: available (bool), remaining (int), total (int)
    """
    if not resume.visitor_hr_enabled:
        return {'available': False, 'remaining': 0, 'total': 0, 'reason': 'HR模式未启用'}

    if not resume.visitor_ai_enabled:
        return {'available': False, 'remaining': 0, 'total': resume.visitor_ai_quota, 'reason': 'AI功能已禁用'}

    remaining = max(0, resume.visitor_ai_quota - resume.visitor_ai_used)
    if remaining <= 0:
        return {'available': False, 'remaining': 0, 'total': resume.visitor_ai_quota, 'reason': 'AI调用配额已用尽'}

    return {'available': True, 'remaining': remaining, 'total': resume.visitor_ai_quota}


def filter_visitor_data(resume) -> dict:
    """
    Build a filtered resume data dict for visitor view.
    Only includes public modules and non-sensitive fields.
    If HR mode is active, includes HR-specific metadata.
    """
    public_modules = resume.get_public_modules()

    data = {
        'username': resume.user.username,
        'title': resume.title,
        'summary': resume.summary,
        'tags': [],
        'modules': {},
        'visitor_allow_download': resume.visitor_allow_download,
        # HR mode metadata
        'hr_enabled': resume.visitor_hr_enabled,
        'ai_enabled': resume.visitor_ai_enabled if resume.visitor_hr_enabled else False,
        'ai_quota': resume.visitor_ai_quota if resume.visitor_hr_enabled else 0,
        'ai_used': resume.visitor_ai_used if resume.visitor_hr_enabled else 0,
        'ai_remaining': max(0, resume.visitor_ai_quota - resume.visitor_ai_used) if resume.visitor_hr_enabled else 0,
    }

    # Tags (public)
    data['tags'] = [
        {'name': t.name, 'type': t.tag_type}
        for t in resume.tags.all()
    ]

    # Education
    if 'education' in public_modules:
        data['modules']['education'] = [
            {
                'school': e.school,
                'degree': e.degree,
                'major': e.major,
                'start_date': str(e.start_date),
                'end_date': str(e.end_date) if e.end_date else None,
                'description': e.description,
            }
            for e in resume.educations.all()
        ]

    # Work experience (hide sensitive fields)
    if 'work_experience' in public_modules:
        data['modules']['work_experience'] = [
            {
                'company': w.company,
                'position': w.position,
                'start_date': str(w.start_date),
                'end_date': str(w.end_date) if w.end_date else None,
                'description': w.description,
            }
            for w in resume.work_experiences.all()
        ]

    # Projects
    if 'project' in public_modules:
        data['modules']['project'] = [
            {
                'name': p.name,
                'role': p.role,
                'start_date': str(p.start_date) if p.start_date else None,
                'end_date': str(p.end_date) if p.end_date else None,
                'description': p.description,
                'tech_stack': p.tech_stack,
            }
            for p in resume.projects.all()
        ]

    # Skills
    if 'skill' in public_modules:
        data['modules']['skill'] = [
            {
                'name': s.name,
                'level': s.level,
                'category': s.category,
            }
            for s in resume.skills.all()
        ]

    # Module data (certificate, award, language)
    for mod_key in ['certificate', 'award', 'language']:
        if mod_key in public_modules and resume.module_data:
            content = resume.module_data.get(mod_key, '')
            if content:
                data['modules'][mod_key] = content

    return data
