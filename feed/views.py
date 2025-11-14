import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .cache import (
    acquire_lock,
    get_cached_feed,
    release_lock,
    set_cached_feed,
    wait_for_cache,
)
from .exceptions import (
    LikeNotFoundError,
    PostNotFoundError,
    ValidationError,
)
from .services import LikeService, PostService
from .validators import validate_pagination


def hot_feed(request):
    try:
        limit_param = request.GET.get("limit", 50)
        limit, _ = validate_pagination(limit_param)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)

    cached = get_cached_feed(limit)
    if cached is not None:
        return JsonResponse({"posts": cached})

    if acquire_lock(limit):
        try:
            cached = get_cached_feed(limit)
            if cached is not None:
                return JsonResponse({"posts": cached})

            result = PostService.list_hot_posts(limit)
            set_cached_feed(limit, result)
            return JsonResponse({"posts": result})
        finally:
            release_lock(limit)
    else:
        cached = wait_for_cache(limit)
        if cached is not None:
            return JsonResponse({"posts": cached})

        result = PostService.list_hot_posts(limit)
        return JsonResponse({"posts": result})


@csrf_exempt
@require_http_methods(["POST"])
def post_create(request):
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        post = PostService.create_post(**data)
        return JsonResponse(post, status=201)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)


@require_http_methods(["GET"])
def post_detail(request, post_id):
    try:
        post = PostService.get_post(post_id)
        return JsonResponse(post, status=200)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def post_update(request, post_id):
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        post = PostService.update_post(post_id, **data)
        return JsonResponse(post, status=200)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def post_delete(request, post_id):
    try:
        PostService.delete_post(post_id)
        return HttpResponse(status=204)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)


@require_http_methods(["GET"])
def post_aggregates(request, post_id):
    try:
        aggregates = PostService.get_post_aggregates(post_id)
        return JsonResponse(aggregates, status=200)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def like_create(request, post_id):
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    user_id = data.get("user_id")
    if user_id is None:
        return JsonResponse({"error": "user_id is required"}, status=400)

    try:
        like, created = LikeService.add_like(user_id, post_id)
        status_code = 201 if created else 200
        return JsonResponse(like, status=status_code)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def like_delete(request, post_id, user_id):
    try:
        LikeService.remove_like(user_id, post_id)
        return HttpResponse(status=204)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except LikeNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)


@require_http_methods(["GET"])
def like_status(request, post_id, user_id):
    try:
        status = LikeService.get_like_status(user_id, post_id)
        return JsonResponse(status, status=200)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=500)
