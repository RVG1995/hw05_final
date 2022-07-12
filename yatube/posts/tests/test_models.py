from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост test post abc",
        )

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verbose = {
            "text": "Текст поста",
            "pub_date": "Дата публикации",
            "author": "Автор",
            "group": "Группа",
        }
        for key, value in field_verbose.items():
            with self.subTest(key=key):
                self.assertEqual(post._meta.get_field(key).verbose_name, value)

    def test_help_text(self):
        post = PostModelTest.post
        field_help_text = {
            "text": " Введите текст поста",
            "group": "Группа к которой будет относиться пост",
        }
        for key, value in field_help_text.items():
            with self.subTest(key=key):
                self.assertEqual(post._meta.get_field(key).help_text, value)

    def test__models__str__method(self):
        self.assertEqual(str(self.post), self.post.text[:15])
        self.assertEqual(str(self.group), self.group.title)
