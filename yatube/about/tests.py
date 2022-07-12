from http import HTTPStatus
from django.test import Client, TestCase


class AboutAppTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_url_author_at_desired_location(self):
        response = self.guest_client.get("/about/author/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_tech_at_desired_location(self):
        response = self.guest_client.get("/about/tech/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template_(self):
        template_url_names = {
            "/about/author/": "about/author.html",
            "/about/tech/": "about/tech.html",
        }
        for url, template in template_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
