from django.db import IntegrityError, transaction
from django.db.models import F

from .cache import invalidate_feed_cache
from .exceptions import LikeNotFoundError, PostNotFoundError

from .repositories import LikeRepository, PostRepository
from .serializers import (
    serialize_like,
    serialize_like_status,
    serialize_post,
    serialize_post_aggregates,
)
from .validators import validate_post_data, validate_user_id


class PostService:
    @staticmethod
    def create_post(**data):
        validated_data = validate_post_data(data)
        post_data = {"like_count": 0}
        post_data.update(validated_data)
        post = PostRepository.create(post_data)

        return serialize_post(post)

    @staticmethod
    def get_post(post_id):
        post = PostRepository.get_by_id(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")

        return serialize_post(post)

    @staticmethod
    def update_post(post_id, **data):
        validated_data = validate_post_data(data)

        post = PostRepository.get_by_id(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")

        if not validated_data:
            # Нет изменений, возвращаем существующий пост
            return serialize_post(post)

        post = PostRepository.update(post, validated_data)
        invalidate_feed_cache()

        return serialize_post(post)

    @staticmethod
    def delete_post(post_id):
        post = PostRepository.get_by_id(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")

        PostRepository.delete(post)

        invalidate_feed_cache()

    @staticmethod
    def list_hot_posts(limit, offset=0):
        posts = PostRepository.list_hot(limit, offset)

        result = []
        for post in posts:
            data = serialize_post(post)
            data["score"] = post.score
            result.append(data)

        return result

    @staticmethod
    def get_post_aggregates(post_id):
        post = PostRepository.get_by_id(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")

        score_24h = PostRepository.get_score_24h(post_id)

        return serialize_post_aggregates(post, score_24h)


class LikeService:
    @staticmethod
    @transaction.atomic
    def add_like(user_id, post_id):
        user_id = validate_user_id(user_id)
        post = PostRepository.get_by_id(post_id, lock=True)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")

        existing_like = LikeRepository.get_or_none(user_id, post_id)
        if existing_like:
            return serialize_like(existing_like), False

        try:
            like = LikeRepository.create_like(user_id, post_id)
            # Явно обновляем like_count в транзакции для атомарности
            post.like_count = F("like_count") + 1
            post.save(update_fields=["like_count"])
            invalidate_feed_cache()
        except IntegrityError:
            like = LikeRepository.get_or_none(user_id, post_id)
            if like:
                return serialize_like(like), False
            raise

        return serialize_like(like), True

    @staticmethod
    @transaction.atomic
    def remove_like(user_id, post_id):
        user_id = validate_user_id(user_id)
        post = PostRepository.get_by_id(post_id, lock=True)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")

        like = LikeRepository.get_or_none(user_id, post_id)
        if not like:
            raise LikeNotFoundError(
                f"Like from user {user_id} on post {post_id} not found"
            )

        LikeRepository.delete_like(like)
        # Явно обновляем like_count в транзакции для атомарности
        post.like_count = F("like_count") - 1
        post.save(update_fields=["like_count"])
        invalidate_feed_cache()

    @staticmethod
    def get_like_status(user_id, post_id):
        user_id = validate_user_id(user_id)
        post = PostRepository.get_by_id(post_id)
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")

        like = LikeRepository.get_or_none(user_id, post_id)

        return serialize_like_status(liked=like is not None, like=like)
