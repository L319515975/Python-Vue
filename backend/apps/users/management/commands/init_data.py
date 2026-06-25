"""Management command to initialize sample data."""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.resumes.models import Resume, Education, WorkExperience, Project, Skill, Tag
from datetime import date, timedelta
import uuid
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = '初始化示例数据：创建管理员和普通用户账号、标签库及示例简历'

    def handle(self, *args, **options):
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('管理员账号创建成功: admin / admin123'))
        else:
            self.stdout.write(self.style.WARNING('管理员账号已存在'))

        # Create normal user
        normal_user, created = User.objects.get_or_create(
            username='zhangsan',
            defaults={
                'email': 'zhangsan@example.com',
                'phone': '13800138000',
                'role': 'user',
            }
        )
        if created:
            normal_user.set_password('user123')
            normal_user.save()
            self.stdout.write(self.style.SUCCESS('普通用户创建成功: zhangsan / user123'))
        else:
            self.stdout.write(self.style.WARNING('普通用户已存在'))

        # Create system tags
        tags_data = [
            ('Python', 'skill'), ('Django', 'skill'), ('Vue.js', 'skill'),
            ('JavaScript', 'skill'), ('TypeScript', 'skill'), ('React', 'skill'),
            ('PostgreSQL', 'skill'), ('MySQL', 'skill'), ('Redis', 'skill'),
            ('Docker', 'skill'), ('Kubernetes', 'skill'), ('Git', 'skill'),
            ('REST API', 'skill'), ('GraphQL', 'skill'), ('Linux', 'skill'),
            ('全栈开发', 'project'), ('后端开发', 'project'), ('前端开发', 'project'),
            ('微服务架构', 'project'), ('数据分析', 'project'),
            ('CET-6', 'certificate'), ('PMP', 'certificate'),
            ('AWS认证', 'certificate'), ('软件设计师', 'certificate'),
            ('优秀员工', 'award'), ('技术竞赛一等奖', 'award'),
            ('英语(流利)', 'language'), ('日语(N2)', 'language'),
        ]
        tag_count = 0
        for name, tag_type in tags_data:
            _, created = Tag.objects.get_or_create(
                name=name, tag_type=tag_type,
                defaults={'is_system': True}
            )
            if created:
                tag_count += 1
        self.stdout.write(self.style.SUCCESS(f'标签库初始化完成，新增 {tag_count} 个标签'))

        # Create sample resume for normal user
        resume, created = Resume.objects.get_or_create(
            user=normal_user,
            defaults={
                'title': '张三的简历',
                'summary': '5年全栈开发经验，擅长Python和JavaScript技术栈，熟悉Django、Vue.js、React等主流框架。对系统架构设计和性能优化有深入理解。',
                'status': 'published',
                'enabled_modules': ['education', 'work_experience', 'project', 'skill', 'certificate'],
                'module_data': {
                    'certificate': 'CET-6 英语六级证书（550分）\nAWS Solutions Architect Associate 认证\nPMP 项目管理专业人士认证',
                    'award': '2023年度公司优秀员工\n2022年公司内部技术竞赛一等奖',
                    'language': '英语：流利（CET-6，可作为工作语言）\n日语：基础（N4水平）',
                },
            }
        )
        if created:
            # Set tags
            resume_tags = Tag.objects.filter(
                name__in=['Python', 'Django', 'Vue.js', 'PostgreSQL', 'Docker', 'REST API', '全栈开发']
            )
            resume.tags.set(resume_tags)

            # Education
            Education.objects.create(
                resume=resume, school='北京大学', degree='硕士',
                major='计算机科学与技术', start_date=date(2016, 9, 1),
                end_date=date(2019, 6, 30), order=1,
            )
            Education.objects.create(
                resume=resume, school='武汉大学', degree='学士',
                major='软件工程', start_date=date(2012, 9, 1),
                end_date=date(2016, 6, 30), order=2,
            )

            # Work Experience
            WorkExperience.objects.create(
                resume=resume, company='某科技有限公司', position='高级后端工程师',
                start_date=date(2022, 3, 1),
                description='负责公司核心业务系统的设计与开发，使用Django REST Framework构建微服务架构。主导数据库优化项目，将查询性能提升60%。带领3人小组完成支付系统重构。',
                order=1,
            )
            WorkExperience.objects.create(
                resume=resume, company='某互联网公司', position='全栈开发工程师',
                start_date=date(2019, 7, 1), end_date=date(2022, 2, 28),
                description='参与电商平台的前后端开发，使用Vue.js和Django技术栈。独立完成用户中心、订单管理等模块的开发。',
                order=2,
            )

            # Projects
            Project.objects.create(
                resume=resume, name='智能客服系统',
                role='技术负责人', start_date=date(2023, 1, 1),
                tech_stack='Python, Django, OpenAI API, Vue3, Redis, Celery',
                description='基于大语言模型的智能客服系统，支持多轮对话、意图识别和知识库检索。日均处理10000+用户咨询，准确率达95%。',
                order=1,
            )
            Project.objects.create(
                resume=resume, name='数据可视化平台',
                role='后端开发', start_date=date(2021, 6, 1), end_date=date(2022, 1, 31),
                tech_stack='Python, Django, ECharts, PostgreSQL, Docker',
                description='企业级数据分析和可视化平台，支持自定义报表、实时数据大屏和数据导出功能。',
                order=2,
            )

            # Skills
            skills_data = [
                ('Python', 90, '编程语言'), ('Django', 85, '后端框架'),
                ('Vue.js', 80, '前端框架'), ('JavaScript', 80, '编程语言'),
                ('PostgreSQL', 75, '数据库'), ('Redis', 70, '数据库'),
                ('Docker', 70, 'DevOps'), ('Git', 85, '工具'),
                ('REST API', 85, '后端'), ('Linux', 70, '运维'),
            ]
            for i, (name, level, category) in enumerate(skills_data):
                Skill.objects.create(
                    resume=resume, name=name, level=level,
                    category=category, order=i,
                )

            # Set up visitor link for demo
            if not resume.visitor_token:
                resume.visitor_token = uuid.uuid4().hex
                resume.visitor_enabled = True
                resume.visitor_expires = timezone.now() + timedelta(days=30)
                resume.visitor_allow_download = True
                resume.public_modules = ['education', 'project', 'skill']
                resume.save()
                self.stdout.write(self.style.SUCCESS('游客分享链接已生成'))
            else:
                self.stdout.write(self.style.WARNING('游客链接已存在'))

            self.stdout.write(self.style.SUCCESS('示例简历数据创建成功'))
        else:
            self.stdout.write(self.style.WARNING('示例简历已存在'))

        self.stdout.write(self.style.SUCCESS('\n初始化完成!'))
        self.stdout.write(f'  管理员: admin / admin123 (可管理所有用户)')
        self.stdout.write(f'  普通用户: zhangsan / user123 (查看个人简历)')

