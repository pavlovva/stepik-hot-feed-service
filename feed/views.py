from django.http import JsonResponse
from django.db.models import Count, Q, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta
from .models import Post
from .cache import (
    get_cached_feed,
    set_cached_feed,
    acquire_lock,
    release_lock,
    wait_for_cache,
)


def hot_feed(request):
    limit = int(request.GET.get("limit", 50))

    cached = get_cached_feed(limit)
    if cached is not None:
        return JsonResponse({"posts": cached})

    if acquire_lock(limit):
        try:
            cached = get_cached_feed(limit)
            if cached is not None:
                return JsonResponse({"posts": cached})

            twenty_four_hours_ago = timezone.now() - timedelta(hours=24)

            posts = Post.objects.annotate(
                score=Count(
                    Case(
                        When(likes__created_at__gte=twenty_four_hours_ago, then=1),
                        output_field=IntegerField(),
                    )
                )
            ).order_by("-score", "-created_at")[:limit]

            result = []
            for post in posts:
                result.append(
                    {
                        "id": post.id,
                        "like_count": post.like_count,
                        "score": post.score,
                        "created_at": post.created_at.isoformat(),
                    }
                )

            set_cached_feed(limit, result)
            return JsonResponse({"posts": result})
        finally:
            release_lock(limit)
    else:
        cached = wait_for_cache(limit)
        if cached is not None:
            return JsonResponse({"posts": cached})

        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)

        posts = Post.objects.annotate(
            score=Count(
                Case(
                    When(likes__created_at__gte=twenty_four_hours_ago, then=1),
                    output_field=IntegerField(),
                )
            )
        ).order_by("-score", "-created_at")[:limit]

        result = []
        for post in posts:
            result.append(
                {
                    "id": post.id,
                    "like_count": post.like_count,
                    "score": post.score,
                    "created_at": post.created_at.isoformat(),
                }
            )

        return JsonResponse({"posts": result})
