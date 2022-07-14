import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache

from ..models import Comment, Follow, Group, Post, User

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
        cache.clear()

    def test_pages_uses_correct_template(self):
        template_page_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": "test-slug"}
            ): "posts/group_list.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": "116"}
            ): "posts/post_detail.html",
            reverse(
                "posts:profile", kwargs={"username": "IvanIvanov"}
            ): "posts/profile.html",
            reverse("posts:create_post"): "posts/create_post.html",
            reverse(
                "posts:update_post", kwargs={"post_id": "116"}
            ): "posts/create_post.html",
        }
        for reverse_name, template in template_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        image = self.post.image
        self.assertEqual(image, 'posts/small.gif')

        response = self.authorized_client.get(reverse("posts:index"))
        page_obj = response.context.get("page_obj")

        self.assertEqual(1, len(page_obj))
        self.assertListEqual([self.post], page_obj.object_list)

    def test_group_list_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )
        group_posts = self.group.posts.all()[:10]
        page_obj = response.context.get("page_obj")

        image = self.post.image
        self.assertEqual(image, 'posts/small.gif')

        self.assertQuerysetEqual(group_posts, page_obj.object_list)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.user.username})
        )
        user_posts = self.user.posts.all()[:10]
        page_obj = response.context.get("page_obj")

        image = self.post.image
        self.assertEqual(image, 'posts/small.gif')

        self.assertListEqual(list(user_posts), page_obj.object_list)

    def test_posts_detail_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        post = response.context.get("post")
        comments = response.context.get("comments")
        form_fields = {
            'text': forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIn(self.comment, comments)
        self.assertEqual(self.post, post)

        image = self.post.image
        self.assertEqual(image, 'posts/small.gif')

    def test_update_post_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse("posts:update_post", kwargs={"post_id": self.post.id})
        )
        post = response.context.get("post")
        is_edit = response.context.get("is_edit")
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(self.post, post)
        self.assertTrue(is_edit, True)

    def test_create_post_page_show_correct_context(self):
        response = self.authorized_client.get(reverse("posts:create_post"))
        is_edit = response.context.get("is_edit")
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get("form").fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsNone(is_edit)

    def test_create_post(self):
        form_data = {
            "text": "New post",
            "group": self.group.id,
        }
        self.authorized_client.post(reverse("posts:create_post"), form_data)

        created_post = Post.objects.get(
            text=form_data["text"], group=self.group, author=self.user
        )

        urls = [
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
            reverse("posts:profile", kwargs={"username": self.user.username}),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                page_obj = response.context.get("page_obj")
                self.assertIn(created_post, page_obj)

    def test_cache_index(self):
        response = self.guest_client.get(reverse('posts:index'))
        first_post = Post.objects.get(pk=116)

        first_post.text = 'ABCD'
        first_post.save()

        second_response = self.guest_client.get(reverse('posts:index'))

        self.assertEqual(response.content, second_response.content)
        cache.clear()

        third_response = self.guest_client.get(reverse('posts:index'))

        self.assertNotEqual(response.content, third_response.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='follower',
                                                     password='test_pass')
        cls.user_following = User.objects.create_user(username='following',
                                                      password='test_pass')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='test text'

        )

    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)
        cache.clear()

    def test_authenticated_user_can_follow_another_user(self):
        response = self.client_auth_follower.get(reverse(
            "posts:profile_follow",
            args=(self.user_following,)))

        self.assertRedirects(response,
                             reverse('posts:profile',
                                     args=(self.user_following,)))
        self.assertTrue(Follow.objects.filter(
            user=self.user_follower,
            author=self.user_following).exists())
        self.client_auth_follower.get(reverse(
            "posts:profile_follow",
            kwargs={"username": self.user_follower.username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_authenticated_user_can_unfollow_another_user(self):
        self.client_auth_follower.get(reverse(
            "posts:profile_follow",
            kwargs={"username": self.user_follower.username}))
        self.client_auth_follower.get(reverse(
            "posts:profile_unfollow",
            kwargs={'username': self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get(reverse(
            'posts:follow_index'))
        post_text_0 = response.context["page_obj"][0].text
        self.assertEqual(post_text_0, self.post.text)
        response = self.client_auth_following.get(reverse(
            'posts:follow_index'))
        self.assertNotContains(response,
                               self.post.text)

    def test_authenticated_user_can_not_follow_himself(self):
        self.client_auth_follower.get(
            reverse("posts:profile_follow",
                    kwargs={
                        'username': self.user_follower.username
                    }))
        self.assertFalse(Follow.objects.filter(
            user=self.user_follower,
            author=self.user_follower).exists())

    def test_authenticated_user_can_not_follow_another_user_twice(self):
        self.client_auth_follower.get(
            reverse("posts:profile_follow",
                    kwargs={'username': self.user_following.username}))
        self.client_auth_follower.get(
            reverse("posts:profile_follow",
                    kwargs={'username': self.user_following.username}))
        self.assertEqual(Follow.objects.filter(
            user=self.user_follower,
            author=self.user_following).count(), 1)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.user = User.objects.create_user(username="IvanIvanov")
        for i in range(1, 19):
            Post.objects.create(
                author=cls.user, text=f"Тестовый пост {i}", group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_index_first_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse("posts:index"))
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_index_second_page_contains_three_records(self):
        response = self.authorized_client.get(
            reverse("posts:index") + "?page=2"
        )
        self.assertEqual(len(response.context["page_obj"]), 8)

    def test_group_list_first_page_contains_ten_records(self):
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
        )
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_group_list_second_page_contains_three_records(self):
        response = self.authorized_client.get(
            reverse("posts:group_list", kwargs={"slug": self.group.slug})
            + "?page=2"
        )
        self.assertEqual(len(response.context["page_obj"]), 8)

    def test_profile_first_page_contains_ten_records(self):
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.user.username})
        )
        self.assertEqual(len(response.context["page_obj"]), 10)

    def test_profile_second_page_contains_three_records(self):
        response = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.user.username})
            + "?page=2"
        )
        self.assertEqual(len(response.context["page_obj"]), 8)
