from django.http import JsonResponse
from django.db.models import Count, Q, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta
from .models import Post


def hot_feed(request):
    limit = int(request.GET.get("limit", 50))
    
    twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
    
    posts = Post.objects.annotate(
        score=Count(
            Case(
                When(likes__created_at__gte=twenty_four_hours_ago, then=1),
                output_field=IntegerField()
            )
        )
    ).order_by('-score', '-created_at')[:limit]
    
    result = []
    for post in posts:
        result.append({
            'id': post.id,
            'like_count': post.like_count,
            'score': post.score,
            'created_at': post.created_at.isoformat(),
        })
    
    return JsonResponse({'posts': result})
