"""Management command to import test resume data into admin account."""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.resumes.models import Resume, Education, WorkExperience, Project, Skill, Tag
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = 'Import test resume data and create admin account 测试账号/Test@1234'

    def handle(self, *args, **options):
        # ── 1. Create or update admin user with phone as username ──
        username = '测试账号'
        password = 'Test@1234'

        admin_user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': 'test@example.com',
                'phone': '13800000000',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'first_name': '测',
                'last_name': '试',
            }
        )
        if created:
            admin_user.set_password(password)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(
                f'Admin account created: {username} / {password}'
            ))
        else:
            admin_user.role = 'admin'
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.phone = '13800000000'
            admin_user.email = 'test@example.com'
            admin_user.first_name = '测'
            admin_user.last_name = '试'
            admin_user.set_password(password)
            admin_user.save()
            self.stdout.write(self.style.WARNING(
                f'Admin account already existed, updated to: {username} / {password}'
            ))

        # ── 2. Create resume for admin user ──
        resume, created = Resume.objects.get_or_create(
            user=admin_user,
            defaults={
                'title': 'Web前端开发工程师 - 测试账号',
                'summary': (
                    'Web前端开发工程师，测试大学计算机科学与技术专业本科毕业。'
                    '熟练掌握Vue2/Vue3框架，熟悉ES6语法、Node.js、MVVM开发模式。'
                    '具备微信小程序开发与UniApp开发经验，了解前端工程化与模块化开发，'
                    '有丰富的组件化开发和数据可视化实践经验。'
                ),
                'status': 'published',
                'enabled_modules': [
                    'education', 'work_experience', 'project', 'skill', 'award',
                ],
                'module_data': {
                    'certificate': '',
                    'award': (
                        '大学生计算机设计大赛省赛三等奖（水果电商平台）\n'
                        '大学生计算机设计大赛省赛一等奖，并参与国赛获国三（微信智能聊天机器人）'
                    ),
                    'language': '',
                },
            }
        )

        if created:
            Education.objects.create(
                resume=resume,
                school='测试大学',
                degree='本科',
                major='计算机科学与技术',
                start_date=date(2018, 9, 1),
                end_date=date(2022, 6, 30),
                description=(
                    '主修课程：C语言、数据结构、web应用开发、C#应用开发、'
                    'JAVA应用开发、数据库及应用、Python程序语言设计、'
                    '计算机网络、算法设计与分析、软件工程、编译原理等。'
                ),
                order=1,
            )

            WorkExperience.objects.create(
                resume=resume,
                company='测试科技有限公司A',
                position='Web前端开发',
                start_date=date(2024, 6, 1),
                description=(
                    '使用Vue2/Vue3开发公司内部项目，使用H5内嵌对外项目的安卓APP，'
                    '使用Vue+ECharts实现可视化报表需求项目。'
                    '优化历史项目代码，使用混淆压缩项目文件。'
                    '熟练使用Codex和Claude Code等AI工具辅助开发。'
                ),
                order=1,
            )
            WorkExperience.objects.create(
                resume=resume,
                company='测试科技有限公司B',
                position='Web前端开发（实习+工作）',
                start_date=date(2022, 3, 1),
                end_date=date(2024, 5, 31),
                description=(
                    '矿山运维点检系统：后台+APP，完善+优化+新增页面需求，主任务审批+点检。\n'
                    '矿山部门项目需求：领导带班/动火作业小程序（后台+微信小程序）。\n'
                    '矿山数据展示大屏：使用ECharts图表可视化组件+MQTT实时推送做大屏实时展示矿山数据。\n\n'
                    '使用技术：\n'
                    '- jQuery + Bootstrap + C# + SQLServer 添加后台管理功能模块\n'
                    '- Vue2 + ECharts + MQTT 配合 Unity3D 完成实时数据可视化大屏+动态模型\n'
                    '- UniApp + C# 独立完成APP功能模块\n'
                    '- JS + CSS + H5 完成微信小程序开发\n\n'
                    '项目总结：公司开发人员不到10人，从实习至今学到很多东西，主要写前端页面，'
                    '后续自学C#，根据领导要求看需求文档了解业务，独立完成前后端两个项目需求'
                    '（设备开关机记录+润滑设备提醒），既是前端开发也是测试，还找前后端的bug，'
                    '以及写一些简单的增删改查接口。'
                ),
                order=2,
            )

            skills_data = [
                ('Vue2', 85, '前端框架'),
                ('Vue3', 75, '前端框架'),
                ('JavaScript', 85, '编程语言'),
                ('ES6', 80, '编程语言'),
                ('HTML5', 85, '前端基础'),
                ('CSS3', 80, '前端基础'),
                ('ECharts', 75, '数据可视化'),
                ('UniApp', 75, '跨端开发'),
                ('微信小程序', 75, '小程序开发'),
                ('Node.js', 65, '后端'),
                ('TypeScript', 60, '编程语言'),
                ('Python', 70, '编程语言'),
                ('C#', 60, '后端'),
                ('jQuery', 80, '前端库'),
                ('MQTT', 65, '物联网协议'),
                ('Docker', 60, 'DevOps'),
                ('Git', 70, '版本控制'),
            ]
            for i, (name, level, category) in enumerate(skills_data):
                Skill.objects.create(
                    resume=resume, name=name, level=level,
                    category=category, order=i,
                )

            tag_names = ['Vue.js', 'JavaScript', 'TypeScript', 'Docker']
            tags = Tag.objects.filter(name__in=tag_names)
            resume.tags.set(tags)

            self.stdout.write(self.style.SUCCESS('Resume data imported successfully'))
        else:
            self.stdout.write(self.style.WARNING('Resume already exists for this user'))

        self._sync_projects(resume)

        self.stdout.write(self.style.SUCCESS('\n=== Import Complete ==='))
        self.stdout.write(f'  Admin account: {username} / {password}')
        self.stdout.write(f'  Role: admin')
        self.stdout.write(f'  Resume: {resume.title}')

    def _sync_projects(self, resume):
        """Synchronize projects extracted from the resume work experience."""
        project_data = [
            {
                'name': '微信智能聊天机器人',
                'role': 'Python开发（毕业设计）',
                'start_date': date(2021, 9, 1),
                'end_date': date(2022, 3, 31),
                'tech_stack': 'Python, Docker, Ubuntu, Wechaty, Puppet',
                'description': (
                    '该项目是一个微信自动回复聊天的机器人脚本，可以根据收到的消息智能回复，'
                    '特定关键词入群，查天气、火车票等功能（爬虫技术）。\n\n'
                    '职责：\n'
                    '- 主要使用Python + Docker容器 + Ubuntu系统\n'
                    '- 使用Wechaty + 微信iPad协议 + Puppet框架\n'
                    '- 基础Python程序编写与服务器端Shell脚本编写'
                ),
            },
            {
                'name': '矿山运维点检系统',
                'role': 'Web前端开发',
                'start_date': date(2022, 3, 1),
                'end_date': date(2024, 5, 31),
                'tech_stack': 'Vue2, jQuery, Bootstrap, C#, SQLServer, UniApp',
                'description': (
                    '矿山运维点检系统由后台+APP组成，主要任务是完善、优化和新增页面需求，'
                    '核心业务包含审批与点检流程。\n\n'
                    '工作内容：\n'
                    '- 使用jQuery + Bootstrap + C# + SQLServer 添加后台管理功能模块\n'
                    '- 使用UniApp + C# 独立完成APP功能模块\n'
                    '- 参与需求评审，负责前端页面开发、联调与测试'
                ),
            },
            {
                'name': '领导带班/动火作业小程序',
                'role': 'Web前端开发',
                'start_date': date(2022, 3, 1),
                'end_date': date(2024, 5, 31),
                'tech_stack': 'JS, CSS, H5, 微信小程序, Vue2',
                'description': (
                    '面向矿山部门的后台+微信小程序项目，覆盖领导带班和动火作业两类业务场景。\n\n'
                    '工作内容：\n'
                    '- 使用JS + CSS + H5 完成微信小程序端页面开发\n'
                    '- 配合后台管理功能模块完成小程序与后台的数据交互\n'
                    '- 根据业务需求完成页面新增、优化与缺陷修复'
                ),
            },
            {
                'name': '矿山数据展示大屏',
                'role': 'Web前端开发',
                'start_date': date(2022, 3, 1),
                'end_date': date(2024, 5, 31),
                'tech_stack': 'Vue2, ECharts, MQTT, Unity3D',
                'description': (
                    '使用ECharts图表可视化组件+MQTT实时推送，完成矿山数据大屏的实时数据展示。\n\n'
                    '工作内容：\n'
                    '- 使用Vue2 + ECharts + MQTT 完成大屏实时数据可视化\n'
                    '- 配合Unity3D完成动态模型与实时数据联动\n'
                    '- 优化图表展示性能和页面加载体验'
                ),
            },
            {
                'name': '设备开关机记录与润滑设备提醒',
                'role': '前后端开发',
                'start_date': date(2022, 3, 1),
                'end_date': date(2024, 5, 31),
                'tech_stack': 'JS, CSS, H5, C#, SQLServer',
                'description': (
                    '根据领导要求和需求文档独立完成的前后端项目，包括设备开关机记录和润滑设备提醒。\n\n'
                    '工作内容：\n'
                    '- 独立完成前端页面开发和简单增删改查接口\n'
                    '- 负责前后端联调、业务逻辑梳理和功能测试\n'
                    '- 持续定位并修复前后端Bug，保障功能稳定上线'
                ),
            },
            {
                'name': '可视化报表项目',
                'role': 'Web前端开发',
                'start_date': date(2024, 6, 1),
                'end_date': None,
                'tech_stack': 'Vue2, Vue3, ECharts, H5, Android',
                'description': (
                    '使用Vue2/Vue3开发公司内部项目，并通过H5形式嵌入对外项目的安卓App中。\n\n'
                    '工作内容：\n'
                    '- 使用Vue + ECharts实现可视化报表需求项目\n'
                    '- 使用H5完成安卓App内嵌页面，适配移动端交互\n'
                    '- 优化历史项目代码，使用混淆压缩项目文件\n'
                    '- 熟练使用Codex和Claude Code等AI工具辅助开发'
                ),
            },

            {
                'name': '智能简历管理系统（Smart Resume Hub）',
                'role': '全栈开发',
                'start_date': date(2025, 1, 1),
                'end_date': None,
                'tech_stack': 'Vue3, Element Plus, Vite, Pinia, Django, DRF, SimpleJWT, WeasyPrint, SQLite/PostgreSQL',
                'description': (
                    '面向管理员、普通用户和访客的智能简历管理平台，支持简历编辑、访客分享、'
                    'PDF导出、AI问答/润色、自动归类、操作审计等多端功能。\n\n'
                    '工作内容：\n'
                    '- 使用Vue3 + Element Plus完成Web前端页面、路由与状态管理\n'
                    '- 使用Django + DRF + SimpleJWT完成后端接口、角色权限与审计日志\n'
                    '- 实现简历多模块编辑、PDF模板导出和访客签名链接分享\n'
                    '- 实现AI助手问答、文本润色与简历自动归类能力\n'
                    '- 编写Vue到微信小程序的同步脚本，维护多端页面与API一致性'
                ),
            },
        ]

        created_count = 0
        for index, item in enumerate(project_data, start=1):
            project, created = Project.objects.get_or_create(
                resume=resume,
                name=item['name'],
                defaults=item,
            )
            if created:
                created_count += 1
            else:
                for field, value in item.items():
                    setattr(project, field, value)
                project.save()
            project.order = index
            project.save()

        self.stdout.write(self.style.SUCCESS(
            f'Project experience synchronized, {created_count} new project(s) added'
        ))
