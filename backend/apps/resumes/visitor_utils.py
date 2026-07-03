"""访客链接工具模块 - 处理HMAC签名生成和验证。

本模块的核心功能是确保访客链接的安全性。

HMAC签名机制（通俗解释）：
1. 用户生成访客链接时，系统用密钥对链接信息进行加密签名
2. 访客打开链接时，系统验证签名是否正确
3. 如果签名被篡改（比如修改了过期时间），验证就会失败
4. 这样可以防止他人伪造或篡改访客链接

安全性保证：
- 密钥只存在服务器端，外部无法伪造签名
- 签名包含token+过期时间+角色，任何一项被篡改都会导致签名失效
- 使用SHA256算法，几乎不可能被破解
"""
import hashlib
import hmac
import logging
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_visitor_secret():
    """获取访客链接签名用的密钥。

    优先使用settings中配置的VISITOR_LINK_SECRET，
    如果没有配置，则使用Django的SECRET_KEY。
    """
    return getattr(settings, 'VISITOR_LINK_SECRET', settings.SECRET_KEY)


def generate_visitor_signature(token: str, expires_timestamp: int, role: str = 'visitor') -> str:
    """生成HMAC-SHA256签名。

    签名过程：
    1. 将token、过期时间戳、角色用冒号拼接成消息字符串
    2. 使用密钥和SHA256算法对消息进行加密
    3. 返回十六进制的签名字符串

    参数：
        token: 访客访问Token
        expires_timestamp: 过期时间的Unix时间戳（秒）
        role: 访客角色（'visitor' 或 'ai'）

    返回：
        64位十六进制签名字符串
    """
    secret = get_visitor_secret()
    # 将签名内容编码为字节串（HMAC要求输入为字节）
    message = f'{token}:{expires_timestamp}:{role}'.encode('utf-8')
    # hmac.new(密钥, 消息, 算法) 生成签名
    signature = hmac.new(
        secret.encode('utf-8'),
        message,
        hashlib.sha256,
    ).hexdigest()
    return signature


def verify_visitor_signature(token: str, expires_timestamp: int, sig: str, role: str = 'visitor') -> bool:
    """验证HMAC-SHA256签名是否正确。

    使用hmac.compare_digest进行安全比较，
    这个函数会用固定时间比较两个字符串，
    防止"时序攻击"（通过比较时间差异来猜测签名）。

    返回：
        True = 签名正确
        False = 签名错误或被篡改
    """
    expected_sig = generate_visitor_signature(token, expires_timestamp, role)
    return hmac.compare_digest(expected_sig, sig)


def is_visitor_link_valid(resume) -> dict:
    """检查简历的访客链接是否当前有效。

    检查条件：
    1. 访客链接是否已启用
    2. 访客Token是否已生成
    3. 链接是否已过期
    4. 简历是否已发布（草稿状态不允许访客访问）

    返回：
        {'valid': True} 或 {'valid': False, 'reason': '原因'}
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
    """构建完整的访客访问URL。

    URL格式示例：
    普通访客：/visitor/{token}?expires=1234567890&sig=abc123...
    AI模式：/visitor/{token}?expires=1234567890&sig=abc123...&role=ai&quota=10

    参数：
        resume: 简历对象
        request: HTTP请求对象（用于获取域名），可选

    返回：
        完整的访客URL字符串
    """
    from datetime import datetime

    if not resume.visitor_token:
        return ''

    # 计算过期时间戳
    expires_ts = 0
    if resume.visitor_expires:
        expires_ts = int(resume.visitor_expires.timestamp())

    # 根据是否启用AI模式决定签名角色
    role = 'ai' if resume.visitor_ai_mode_enabled else 'visitor'
    sig = generate_visitor_signature(resume.visitor_token, expires_ts, role)

    # 构建基础URL
    base_url = ''
    if request:
        base_url = f'{request.scheme}://{request.get_host()}'

    url = f'{base_url}/visitor/{resume.visitor_token}'

    # 构建查询参数
    params = []
    if expires_ts:
        params.append(f'expires={expires_ts}')
    params.append(f'sig={sig}')

    if resume.visitor_ai_mode_enabled:
        params.append(f'role=ai')
        params.append(f'quota={resume.visitor_ai_quota}')

    url += '?' + '&'.join(params)
    return url


def check_visitor_ai_quota(resume) -> dict:
    """检查访客 AI 调用配额是否还有剩余。

    返回：
        {'available': True, 'remaining': 5, 'total': 10}
        或 {'available': False, 'reason': '配额已用尽', ...}
    """
    if not resume.visitor_ai_mode_enabled:
        return {'available': False, 'remaining': 0, 'total': 0, 'reason': 'AI模式未启用'}

    if not resume.visitor_ai_enabled:
        return {'available': False, 'remaining': 0, 'total': resume.visitor_ai_quota, 'reason': 'AI功能已禁用'}

    remaining = max(0, resume.visitor_ai_quota - resume.visitor_ai_used)
    if remaining <= 0:
        return {'available': False, 'remaining': 0, 'total': resume.visitor_ai_quota, 'reason': 'AI调用配额已用尽'}

    return {'available': True, 'remaining': remaining, 'total': resume.visitor_ai_quota}


def filter_visitor_data(resume) -> dict:
    """构建访客可见的简历数据（过滤掉敏感信息）。

    这个函数的职责是：
    1. 只返回用户设置为公开的模块数据
    2. 排除敏感信息（如联系方式、文件路径等）
    3. 如果启用了AI模式，附带相关的元数据（AI配额等）

    返回：
        包含公开简历数据的字典
    """
    public_modules = resume.get_public_modules()

    data = {
        'username': resume.user.username,
        'title': resume.title,
        'summary': resume.summary,
        'tags': [],
        'modules': {},
        'visitor_allow_download': resume.visitor_allow_download,
        # AI模式元数据
        'visitor_ai_mode_enabled': resume.visitor_ai_mode_enabled,
        'ai_enabled': resume.visitor_ai_enabled if resume.visitor_ai_mode_enabled else False,
        'ai_quota': resume.visitor_ai_quota if resume.visitor_ai_mode_enabled else 0,
        'ai_used': resume.visitor_ai_used if resume.visitor_ai_mode_enabled else 0,
        'ai_remaining': max(0, resume.visitor_ai_quota - resume.visitor_ai_used) if resume.visitor_ai_mode_enabled else 0,
    }

    # 标签（公开信息）
    data['tags'] = [
        {'name': t.name, 'type': t.tag_type}
        for t in resume.tags.all()
    ]

    # 教育经历
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

    # 工作经历
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

    # 项目经历
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

    # 技能清单
    if 'skill' in public_modules:
        data['modules']['skill'] = [
            {'name': s.name, 'level': s.level, 'category': s.category}
            for s in resume.skills.all()
        ]

    # 纯文本模块（证书、获奖、语言能力）
    for mod_key in ['certificate', 'award', 'language']:
        if mod_key in public_modules and resume.module_data:
            content = resume.module_data.get(mod_key, '')
            if content:
                data['modules'][mod_key] = content

    return data
