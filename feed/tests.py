import json

import factory
from django.core.cache import cache
from django.db import IntegrityError
from django.test import Client, TestCase

from .models import Like, Post


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    like_count = 0


class LikeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Like

    post = factory.SubFactory(PostFactory)
    user_id = factory.Sequence(lambda n: n)


class BaseTestCase(TestCase):
    def setUp(self):
        cache.clear()

    def get_feed(self, limit=50):
        response = Client().get(f"/v1/feed/hot?limit={limit}")
        return json.loads(response.content)["posts"]


class HotFeedCoreTests(BaseTestCase):
    def test_no_n_plus_1_queries(self):
        LikeFactory()

        with self.assertNumQueries(1):
            self.get_feed()

    def test_stable_order(self):
        for i in range(3):
            post = PostFactory()
            LikeFactory.create_batch(i, post=post)

        results = [self.get_feed() for _ in range(5)]
        post_ids = [[p["id"] for p in r] for r in results]

        self.assertEqual(len(set(map(tuple, post_ids))), 1)

    def test_consistent_pagination(self):
        PostFactory.create_batch(5)

        all_ids = [p["id"] for p in self.get_feed(10)]
        first_3_ids = [p["id"] for p in self.get_feed(3)]

        self.assertEqual(first_3_ids, all_ids[:3])


class HotFeedCacheTests(BaseTestCase):
    def test_cache_hit(self):
        PostFactory()

        self.get_feed()

        with self.assertNumQueries(0):
            self.get_feed()

    def test_invalidation_on_like_create(self):
        """
        Проверяем инвалидацию кэша при создании лайка через сервис.
        """
        from feed.services import LikeService

        post = PostFactory()
        LikeService.add_like(user_id=1, post_id=post.id)

        self.get_feed()

        with self.assertNumQueries(0):
            self.get_feed()

        LikeService.add_like(user_id=2, post_id=post.id)

        with self.assertNumQueries(1):
            self.get_feed()


class HotFeedStampedeTests(BaseTestCase):
    def test_stampede_guard_single_update(self):
        from feed.cache import acquire_lock, release_lock

        acquired = acquire_lock(50)
        self.assertTrue(acquired)
        self.assertFalse(acquire_lock(50))

        release_lock(50)
        self.assertTrue(acquire_lock(50))
        release_lock(50)


class LikeSignalTests(BaseTestCase):
    def test_like_updates_count(self):
        from feed.services import LikeService

        post = PostFactory()

        LikeService.add_like(user_id=1, post_id=post.id)
        post.refresh_from_db()
        self.assertEqual(post.like_count, 1)

        LikeService.add_like(user_id=2, post_id=post.id)
        post.refresh_from_db()
        self.assertEqual(post.like_count, 2)

    def test_unique_constraint(self):
        post = PostFactory()
        LikeFactory(post=post, user_id=1)

        with self.assertRaises(IntegrityError):
            LikeFactory(post=post, user_id=1)
