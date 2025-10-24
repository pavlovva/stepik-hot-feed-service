from django.http import JsonResponse


def hot_feed(request):
    """
    GET /v1/feed/hot?limit=50
    """
    # TODO: Implement cache-aside logic
    # TODO: Implement stampede guard
    # TODO: Filter posts by likes in last 24 hours

    limit = int(request.GET.get("limit", 50))

    return JsonResponse(
        {
            "status": "ok",
            "message": "Hot feed endpoint placeholder",
            "limit": limit,
            "posts": [],
        }
    )
