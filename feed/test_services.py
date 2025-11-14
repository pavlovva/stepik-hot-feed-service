import factory
from django.test import TestCase, TransactionTestCase

from .exceptions import (
    LikeNotFoundError,
    PostNotFoundError,
    ValidationError,
)
from .models import Like, Post
from .services import LikeService, PostService


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    like_count = 0


class LikeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Like

    post = factory.SubFactory(PostFactory)
    user_id = factory.Sequence(lambda n: n)


class PostServiceTests(TestCase):
    def test_create_post_success(self):
        post = PostService.create_post()
        self.assertIsNotNone(post)
        self.assertEqual(post["like_count"], 0)
        self.assertIn("id", post)
        self.assertIn("created_at", post)

    def test_get_post_success(self):
        created_post = PostFactory()
        post = PostService.get_post(created_post.id)
        self.assertEqual(post["id"], created_post.id)
        self.assertEqual(post["like_count"], created_post.like_count)

    def test_get_nonexistent_post_raises_404(self):
        with self.assertRaises(PostNotFoundError):
            PostService.get_post(99999)

    def test_update_post_success(self):
        created_post = PostFactory()
        updated = PostService.update_post(created_post.id)
        self.assertEqual(updated["id"], created_post.id)

    def test_update_nonexistent_post_raises_404(self):
        with self.assertRaises(PostNotFoundError):
            PostService.update_post(99999)

    def test_update_post_like_count_directly_forbidden(self):
        created_post = PostFactory()
        with self.assertRaises(ValidationError) as cm:
            PostService.update_post(created_post.id, like_count=100)
        self.assertIn("like_count cannot be updated directly", str(cm.exception))

    def test_delete_post_success(self):
        created_post = PostFactory()
        PostService.delete_post(created_post.id)
        self.assertFalse(Post.objects.filter(id=created_post.id).exists())

    def test_delete_nonexistent_post_raises_404(self):
        with self.assertRaises(PostNotFoundError):
            PostService.delete_post(99999)

    def test_get_aggregates_success(self):
        post = PostFactory()
        LikeFactory.create_batch(5, post=post)
        aggregates = PostService.get_post_aggregates(post.id)
        self.assertEqual(aggregates["post_id"], post.id)
        self.assertEqual(aggregates["total_likes"], 5)
        self.assertIn("score_24h", aggregates)

    def test_list_hot_posts(self):
        post1 = PostFactory()
        post2 = PostFactory()
        LikeFactory.create_batch(3, post=post1)
        LikeFactory.create_batch(1, post=post2)

        posts = PostService.list_hot_posts(limit=10)
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0]["id"], post1.id)
        self.assertEqual(posts[0]["score"], 3)


class LikeServiceTests(TransactionTestCase):
    def test_add_like_success(self):
        post = PostFactory()
        like, created = LikeService.add_like(1, post.id)
        self.assertTrue(created)
        self.assertEqual(like["user_id"], 1)
        self.assertEqual(like["post_id"], post.id)

        post.refresh_from_db()
        self.assertEqual(post.like_count, 1)

    def test_add_like_twice_is_idempotent(self):
        post = PostFactory()
        like1, created1 = LikeService.add_like(1, post.id)
        self.assertTrue(created1)

        like2, created2 = LikeService.add_like(1, post.id)
        self.assertFalse(created2)
        self.assertEqual(like1["id"], like2["id"])

        post.refresh_from_db()
        self.assertEqual(post.like_count, 1)

    def test_add_like_nonexistent_post_raises_404(self):
        with self.assertRaises(PostNotFoundError):
            LikeService.add_like(1, 99999)

    def test_add_like_invalid_user_id(self):
        post = PostFactory()
        with self.assertRaises(ValidationError):
            LikeService.add_like(-1, post.id)

        with self.assertRaises(ValidationError):
            LikeService.add_like(0, post.id)

        with self.assertRaises(ValidationError):
            LikeService.add_like("invalid", post.id)

    def test_remove_like_success(self):
        post = PostFactory()
        LikeFactory(user_id=1, post=post)
        post.refresh_from_db()
        self.assertEqual(post.like_count, 1)

        LikeService.remove_like(1, post.id)
        post.refresh_from_db()
        self.assertEqual(post.like_count, 0)

    def test_remove_nonexistent_like_raises_404(self):
        post = PostFactory()
        with self.assertRaises(LikeNotFoundError):
            LikeService.remove_like(1, post.id)

    def test_remove_like_nonexistent_post_raises_404(self):
        with self.assertRaises(PostNotFoundError):
            LikeService.remove_like(1, 99999)

    def test_get_like_status_exists(self):
        post = PostFactory()
        LikeFactory(user_id=1, post=post)

        status = LikeService.get_like_status(1, post.id)
        self.assertTrue(status["liked"])
        self.assertIn("like", status)

    def test_get_like_status_not_exists(self):
        post = PostFactory()
        status = LikeService.get_like_status(1, post.id)
        self.assertFalse(status["liked"])
