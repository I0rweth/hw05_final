from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Testname')
        cls.post = Post.objects.create(
            author=cls.user,
            text='тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()

    def test_pages_uses_correct_template(self):
        response = self.guest_client.get(reverse('posts:index'))
        cached = response.content
        Post.objects.create(text='Второй пост', author=self.user)
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(cached, response.content)
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(cached, response.content)
