from django import forms
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='Testname')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовый тайтл',
            slug='Test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.picture = (
            b'\x00\x80'
            b'\x80\x00'
        )

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list', kwargs={'slug': 'Test_slug'}
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                args=[get_object_or_404(User, username='Testname')]
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail', kwargs={'post_id': f'{self.post.id}'}
            ),
            'posts/create.html': reverse(
                'posts:post_create'
            ),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_group_list_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )
        context_post_list = response.context.get('page_obj').object_list
        db_post_list = list(self.group.posts.all())
        self.assertQuerysetEqual(
            db_post_list,
            context_post_list,
            transform=lambda x: x
        )

    def test_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(response.context.get('post'), self.post)

    def test_post_edit_show_correct_context(self):
        response = (self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Testname')
        cls.group = Group.objects.create(
            title='Тестовый тайтл',
            slug='Test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.bulk_create(
            [
                Post(
                    text=f'Тестовый текст{i}',
                    author=cls.user,
                    group=cls.group
                )
                for i in range(0, 13)
            ]
        )

    def test_first_page_contains(self):
        PAGE_LIMIT = 10
        url_names = {
            reverse('posts:index'): PAGE_LIMIT,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): PAGE_LIMIT,
            reverse(
                'posts:profile',
                args=[self.user]
            ): PAGE_LIMIT,
        }
        for value, expected in url_names.items():
            with self.subTest(value=value):
                response = self.client.get(value + '?page=1')
                self.assertEqual(len(response.context['page_obj']), expected)

    def test_second_page_contains_three_records(self):
        PAGE_LIMIT_SECOND_PAGE = 3
        url_names = {
            reverse(
                'posts:index'
            ): PAGE_LIMIT_SECOND_PAGE,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): PAGE_LIMIT_SECOND_PAGE,
            reverse(
                'posts:profile',
                args=[self.user]
            ): PAGE_LIMIT_SECOND_PAGE,
        }
        for value, expected in url_names.items():
            with self.subTest(value=value):
                response = self.client.get(value + '?page=2')
                self.assertEqual(len(response.context['page_obj']), expected)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='Testname1',
        )
        cls.follower = User.objects.create(
            username='Testname2',
        )
        cls.post = Post.objects.create(
            text='Test_text',
            author=cls.author,
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

    def test_follow_user(self):
        count_follow = Follow.objects.count()
        already_follows = Follow.objects.filter(
            user=self.follower,
            author=self.author
        ).exists()
        self.assertEqual(already_follows, False)
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}))
        already_follows_after = Follow.objects.filter(
            user=self.follower,
            author=self.author
        ).exists()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(already_follows_after, True)

    def test_unfollow_user(self):
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        count_follow = Follow.objects.count()
        check_unfollow = Follow.objects.filter(user=self.follower,
                                               author=self.author)
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username}))
        self.assertFalse(check_unfollow.exists())
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_follow_authors(self):
        Follow.objects.create(
            user=self.follower,
            author=self.author)
        response = self.follower_client.get(
            reverse('posts:follow_index'))
        self.assertIn(self.post, response.context['page_obj'].object_list)

    def test_notfollow_authors(self):
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'].object_list)
