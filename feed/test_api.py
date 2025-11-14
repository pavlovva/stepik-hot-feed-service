import json

import factory
from django.core.cache import cache
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


class PostAPITests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def test_post_create_api(self):
        response = self.client.post(
            "/v1/feed/posts/",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertIn("id", data)
        self.assertEqual(data["like_count"], 0)

    def test_post_get_api(self):
        post = PostFactory()
        response = self.client.get(f"/v1/feed/posts/{post.id}/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["id"], post.id)

    def test_post_not_found_returns_404(self):
        response = self.client.get("/v1/feed/posts/99999/")
        self.assertEqual(response.status_code, 404)

    def test_post_update_api(self):
        post = PostFactory()
        response = self.client.put(
            f"/v1/feed/posts/{post.id}/update/",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

    def test_post_update_like_count_forbidden(self):
        post = PostFactory()
        response = self.client.put(
            f"/v1/feed/posts/{post.id}/update/",
            data=json.dumps({"like_count": 100}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_post_delete_api(self):
        post = PostFactory()
        response = self.client.delete(f"/v1/feed/posts/{post.id}/delete/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Post.objects.filter(id=post.id).exists())

    def test_post_aggregates_api(self):
        post = PostFactory()
        LikeFactory.create_batch(3, post=post)
        response = self.client.get(f"/v1/feed/posts/{post.id}/aggregates/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["total_likes"], 3)
        self.assertIn("score_24h", data)

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            "/v1/feed/posts/",
            data="invalid json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class LikeAPITests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def test_like_create_api(self):
        post = PostFactory()
        response = self.client.post(
            f"/v1/feed/posts/{post.id}/likes/",
            data=json.dumps({"user_id": 1}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["user_id"], 1)
        self.assertEqual(data["post_id"], post.id)

    def test_like_create_twice_idempotent(self):
        post = PostFactory()
        response1 = self.client.post(
            f"/v1/feed/posts/{post.id}/likes/",
            data=json.dumps({"user_id": 1}),
            content_type="application/json",
        )
        self.assertEqual(response1.status_code, 201)

        response2 = self.client.post(
            f"/v1/feed/posts/{post.id}/likes/",
            data=json.dumps({"user_id": 1}),
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 200)

    def test_like_create_missing_user_id_returns_400(self):
        post = PostFactory()
        response = self.client.post(
            f"/v1/feed/posts/{post.id}/likes/",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_like_delete_api(self):
        post = PostFactory()
        LikeFactory(user_id=1, post=post)
        response = self.client.delete(f"/v1/feed/posts/{post.id}/likes/1/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Like.objects.filter(user_id=1, post=post).exists())

    def test_like_delete_nonexistent_returns_404(self):
        post = PostFactory()
        response = self.client.delete(f"/v1/feed/posts/{post.id}/likes/1/")
        self.assertEqual(response.status_code, 404)

    def test_like_status_api(self):
        post = PostFactory()
        LikeFactory(user_id=1, post=post)

        response = self.client.get(f"/v1/feed/posts/{post.id}/likes/1/status/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["liked"])

    def test_like_status_not_exists(self):
        post = PostFactory()
        response = self.client.get(f"/v1/feed/posts/{post.id}/likes/1/status/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data["liked"])


class HotFeedAPITests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def test_hot_feed_returns_posts(self):
        post1 = PostFactory()
        post2 = PostFactory()
        LikeFactory.create_batch(3, post=post1)
        LikeFactory.create_batch(1, post=post2)

        response = self.client.get("/v1/feed/hot?limit=10")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["posts"]), 2)
        self.assertEqual(data["posts"][0]["id"], post1.id)
        self.assertEqual(data["posts"][0]["score"], 3)

    def test_hot_feed_cache_hit(self):
        PostFactory()
        self.client.get("/v1/feed/hot?limit=50")

        with self.assertNumQueries(0):
            response = self.client.get("/v1/feed/hot?limit=50")
            self.assertEqual(response.status_code, 200)
