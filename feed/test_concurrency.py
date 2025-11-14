import threading

import factory
from django.db import connection
from django.test import TransactionTestCase

from .models import Like, Post
from .services import LikeService


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    like_count = 0


class LikeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Like

    post = factory.SubFactory(PostFactory)
    user_id = factory.Sequence(lambda n: n)


class ConcurrencyTests(TransactionTestCase):
    def test_concurrent_likes_no_duplicates(self):
        post = PostFactory()
        errors = []
        results = []

        def add_like_thread():
            try:
                connection.close()
                like, created = LikeService.add_like(1, post.id)
                results.append((like, created))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_like_thread) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        post.refresh_from_db()
        self.assertEqual(post.like_count, 1)
        self.assertEqual(Like.objects.filter(post=post, user_id=1).count(), 1)

    def test_concurrent_like_count_updates(self):
        post = PostFactory()
        errors = []

        def add_like_thread(user_id):
            try:
                connection.close()
                LikeService.add_like(user_id, post.id)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=add_like_thread, args=(i,))
            for i in range(1, 11)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        err_count = len(errors)
        self.assertEqual(err_count, 0)
        post.refresh_from_db()
        self.assertEqual(post.like_count, 10)
        likes_count = Like.objects.filter(post=post).count()
        self.assertEqual(likes_count, 10)

    def test_concurrent_add_and_remove_likes(self):
        post = PostFactory()
        for i in range(1, 6):
            LikeFactory(user_id=i, post=post)
        post.refresh_from_db()
        initial_count = post.like_count

        errors = []

        def add_like_thread(user_id):
            try:
                connection.close()
                LikeService.add_like(user_id, post.id)
            except Exception as e:
                errors.append(e)

        def remove_like_thread(user_id):
            try:
                connection.close()
                LikeService.remove_like(user_id, post.id)
            except Exception as e:
                errors.append(e)

        add_threads = [
            threading.Thread(target=add_like_thread, args=(i,))
            for i in range(6, 11)
        ]
        remove_threads = [
            threading.Thread(target=remove_like_thread, args=(i,))
            for i in range(1, 4)
        ]

        all_threads = add_threads + remove_threads
        for t in all_threads:
            t.start()
        for t in all_threads:
            t.join()

        post.refresh_from_db()
        expected_count = initial_count - 3 + 5
        self.assertEqual(post.like_count, expected_count)
