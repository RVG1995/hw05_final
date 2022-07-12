from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UersURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username="IvanIvanov")
        self.authorizied_client = Client()
        self.authorizied_client.force_login(self.user)

    def test_url_signup_at_desired_location(self):
        responce = self.guest_client.get("/auth/signup/")
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_url_login_at_desired_location(self):
        responce = self.guest_client.get("/auth/login/")
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_url_logout_at_desired_location(self):
        responce = self.guest_client.get("/auth/logout/")
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_password_change__at_desired_location_authorized(self):
        responce = self.authorizied_client.get("/auth/password_change/")
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_password_change_at_desired_location(self):
        response = self.guest_client.get("/auth/password_change/", follow=True)
        self.assertRedirects(
            response, "/auth/login/?next=/auth/password_change/"
        )

    def test_password_change_done_at_desired_location_authorized(self):
        responce = self.authorizied_client.get("/auth/password_change/done/")
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_password_change_done_at_desired_location(self):
        response = self.guest_client.get(
            "/auth/password_change/done/", follow=True
        )
        self.assertRedirects(
            response, "/auth/login/?next=/auth/password_change/done/"
        )

    def test_url_password_reset_at_desired_location(self):
        responce = self.guest_client.get("/auth/password_reset/")
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_url_password_reset_done_at_desired_location(self):
        responce = self.guest_client.get("/auth/password_reset/done/")
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_url_password_reset_done_uid64_at_desired_location(self):
        responce = self.guest_client.get(
            "/auth/reset/NQ/616-2518e50d07cb78fdce34/"
        )
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_url_password_reset_complete_at_desired_location(self):
        responce = self.guest_client.get("/auth/reset/done/")
        self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        template_url_names = {
            "/auth/signup/": "users/signup.html",
            "/auth/login/": "users/login.html",
            "/auth/password_change/": "users/password_change_form.html",
            "/auth/password_change/done/": "users/password_change_done.html",
            "/auth/password_reset/": "users/password_reset_form.html",
            "/auth/password_reset/done/": "users/password_reset_done.html",
            "/auth/reset/NQ/616-2518e50d07cb78fdce34/":
                "users/password_reset_confirm.html",
            "/auth/reset/done/": "users/password_reset_complete.html",
            "/auth/logout/": "users/logged_out.html",
        }
        for url, template in template_url_names.items():
            with self.subTest(url=url):
                response = self.authorizied_client.get(url)
                self.assertTemplateUsed(response, template)
