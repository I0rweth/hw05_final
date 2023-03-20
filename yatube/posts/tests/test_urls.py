from http import HTTPStatus

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
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
            author=cls.user,
            text='Тестовый текст',
        )

    def page_unauthorized_user(self):
        urls = [
            '/',
            '/group/Test_slug/',
            '/profile/Testname/',
            f'/posts/{self.post.id}/',
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def page_authorized_user(self):
        urls = [
            '/',
            '/group/Test_slug/',
            '/profile/Testname/',
            f'/posts/{self.post.id}/',
            '/create/',
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def author_page(self):
        url = f'/posts/{self.post.id}/edit/'
        with self.subTest(url=url):
            post_user = get_object_or_404(User, username='Testname')
            if post_user == self.authorized_client:
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls(self):
        urls = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/Test_slug/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
            'posts/profile.html': '/profile/Testname/',
            'posts/create.html': f'/posts/{self.post.id}/edit/',
        }

        for template, address in urls.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_custom_template_404(self):
        response = self.guest_client.get('/posts/asd/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_url_403_uses_custom_template(self):
        """Проверка статуса 403"""
        response = HttpResponseForbidden(reverse('posts:index'))
        self.assertEqual(response.status_code, 403)
