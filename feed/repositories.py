from datetime import timedelta

from django.db.models import Case, Count, IntegerField, When
from django.utils import timezone

from .models import Like, Post


class PostRepository:
    @staticmethod
    def get_by_id(post_id, lock=False):
        try:
            queryset = Post.objects.all()
            if lock:
                queryset = queryset.select_for_update()
            return queryset.get(id=post_id)
        except Post.DoesNotExist:
            return None

    @staticmethod
    def create(data):
        post = Post.objects.create(**data)
        return post

    @staticmethod
    def update(post, data):
        for key, value in data.items():
            setattr(post, key, value)
        post.save()
        return post

    @staticmethod
    def delete(post):
        post.delete()

    @staticmethod
    def list_hot(limit, offset=0):
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)

        posts = (
            Post.objects.annotate(
                score=Count(
                    Case(
                        When(likes__created_at__gte=twenty_four_hours_ago, then=1),
                        output_field=IntegerField(),
                    )
                )
            )
            .distinct()
            .order_by("-score", "-created_at")[offset : offset + limit]
        )

        return posts

    @staticmethod
    def get_like_count(post_id):
        try:
            post = Post.objects.get(id=post_id)
            return post.like_count
        except Post.DoesNotExist:
            return 0

    @staticmethod
    def get_score_24h(post_id):
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        return Like.objects.filter(
            post_id=post_id, created_at__gte=twenty_four_hours_ago
        ).count()


class LikeRepository:
    @staticmethod
    def get_or_none(user_id, post_id):
        try:
            return Like.objects.get(user_id=user_id, post_id=post_id)
        except Like.DoesNotExist:
            return None

    @staticmethod
    def create_like(user_id, post_id):
        like = Like.objects.create(user_id=user_id, post_id=post_id)
        return like

    @staticmethod
    def delete_like(like):
        like.delete()

    @staticmethod
    def get_post_likes(post_id, limit=None):
        queryset = Like.objects.filter(post_id=post_id).order_by("-created_at")
        if limit:
            queryset = queryset[:limit]
        return queryset

    @staticmethod
    def exists(user_id, post_id):
        return Like.objects.filter(user_id=user_id, post_id=post_id).exists()
