from http import HTTPStatus
from django.core.cache import cache

from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="IvanIvanov")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            id=116,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorizied_client = Client()
        self.authorizied_client.force_login(self.user)

    def test_index_url_exists_at_desired_location(self):
        response = self.guest_client.get("/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_list_exists_at_desired_location(self):
        response = self.guest_client.get("/group/test-slug/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_exists_at_desired_location(self):
        response = self.guest_client.get("/profile/IvanIvanov/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail_at_desired_location(self):
        response = self.guest_client.get("/posts/116/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_update_post_at_desired_location(self):
        response = self.guest_client.get("/posts/116/edit/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_update_post_exists_at_desired_location_authorized(self):
        response = self.authorizied_client.get("/posts/116/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_at_desired_location(self):
        response = self.guest_client.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_post_exists_at_desired_location_authorized(self):
        response = self.authorizied_client.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_at_desired_location(self):
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        template_url_names = {
            "/": "posts/index.html",
            "/group/test-slug/": "posts/group_list.html",
            "/profile/IvanIvanov/": "posts/profile.html",
            "/posts/116/": "posts/post_detail.html",
            "/posts/116/edit/": "posts/create_post.html",
            "/create/": "posts/create_post.html",
            "/unexisting_page/": "core/404.html"
        }
        for url, template in template_url_names.items():
            with self.subTest(url=url):
                response = self.authorizied_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_page_template(self):
        response = self.authorizied_client.get("/")
        self.assertTemplateUsed(response, "posts/index.html")
