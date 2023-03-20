from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create(username='Testname')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовый тайтл',
            slug='Test_slug',
            description='Тестовое описание',
        )
        cls.picture = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    def test_post_create(self):
        Post.objects.all().delete()
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='picture.gif',
            content=self.picture,
            content_type='image/gif'
        )
        my_post = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': uploaded
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=my_post,
        )
        self.assertNotEqual(
            Post.objects.count(),
            post_count
        )

    def test_post_edit(self):
        post_before = {
            'text': 'Пост до редактирования',
            'group': self.group.pk
        }
        post_after = {
            'text': 'Пост после редактирования',
            'group': self.group.pk
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=post_before,
        )
        post = Post.objects.all()[0]
        self.authorized_client.get(
            f'/posts/{post.id}/edit/'
        )
        self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': post.id
                }
            ),
            data=post_after
        )
        edited_post = Post.objects.all()[0]
        self.assertNotEqual(post.text, edited_post.text)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create(username='Testname')
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

    def test_guest_comment(self):
        count_first = Comment.objects.count()
        form_data = {
            'text': 'Комментарий от неавторизованного пользователя',
        }
        self.guest_client.post(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True,
        )
        count_second = Comment.objects.count()
        self.assertEqual(count_first, count_second)

    def test_authorized_comment(self):
        comment_count = self.post.comments.count()
        form_data = {
            'text': 'Комментарий от авторизированного пользователя',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(
            comment_count + 1,
            Comment.objects.filter(post=self.post.pk).count()
        )
        self.assertRedirects(response, f'/posts/{self.post.pk}/')
