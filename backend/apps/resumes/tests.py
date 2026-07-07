from django.test import SimpleTestCase
from django.urls import resolve


class ResumeUrlsTest(SimpleTestCase):
    def test_static_resume_routes_are_not_shadowed(self):
        cases = {
            '/api/resumes/': 'resume-list',
            '/api/resumes/tags/': 'tag-list',
            '/api/resumes/pdf-templates/': 'resume-pdf-template-list',
            '/api/resumes/educations/': 'education-list',
            '/api/resumes/work-experiences/': 'work-experience-list',
            '/api/resumes/projects/': 'project-list',
            '/api/resumes/skills/': 'skill-list',
        }

        for path, expected_view_name in cases.items():
            with self.subTest(path=path):
                match = resolve(path)
                self.assertEqual(match.view_name, expected_view_name)
