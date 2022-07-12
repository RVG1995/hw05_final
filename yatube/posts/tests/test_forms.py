import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username="IvanIvanov")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.group2 = Group.objects.create(
            title="Тестовая группа1",
            slug="test-slug1",
            description="Тестовое описание",
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            id=116,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='super',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_base_update(self):
        post_count = Post.objects.count()
        image = self.post.image
        self.assertEqual(image, 'posts/small.gif')
        form_data = {
            "text": self.post.text,
            "group": self.group.id,
        }
        response = self.authorized_client.post(
            reverse(
                "posts:create_post",
            ),
            form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={"username": self.user.username}),
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                group=form_data["group"],
                author=self.user,
            ).exists()
        )

    def test_update_post_base_update(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            "text": self.post.text + " ok",
            "group": self.group2.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:update_post", args=(self.post.id,)),
            form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": self.post.id}),
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data["text"],
                author=self.user,
                group=form_data["group"],
                image='posts/small2.gif'
            ).exists()
        )

    def test_update_post_at_desired_location(self):
        form_data = {
            "text": "Пост от неавторизованного пользователя",
            "group": self.group.id
        }
        response = self.guest_client.post(
            reverse("posts:update_post", args=(self.post.id,)),
            form_data,
            follow=True)

        self.assertRedirects(
            response, "/auth/login/?next=/posts/116/edit/")
        self.assertFalse(Post.objects.filter(text=form_data["text"]).exists())

    def test_create_comment(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'WOW'
        }
        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={'post_id': self.post.id}),
            form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:post_detail",
                kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data["text"],
                author=self.user,
            ).exists()
        )

    def test_comments_at_desired_location(self):
        form_data = {
            "text": "Комментарий от неавторизованного пользователя",
        }
        response = self.guest_client.post(
            reverse("posts:add_comment", kwargs={'post_id': self.post.id}),
            form_data,
            follow=True)

        self.assertRedirects(
            response, "/auth/login/?next=/posts/116/comment/")
        self.assertFalse(
            Comment.objects.filter(
                text=form_data["text"]).exists())
