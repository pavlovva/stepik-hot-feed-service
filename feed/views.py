import json
from http.client import BAD_REQUEST, OK, CREATED, NOT_FOUND, INTERNAL_SERVER_ERROR, NO_CONTENT

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
        return JsonResponse({"error": str(e)}, status=BAD_REQUEST)

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
        return JsonResponse({"error": "Invalid JSON"}, status=BAD_REQUEST)

    try:
        post = PostService.create_post(**data)
        return JsonResponse(post, status=CREATED)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=BAD_REQUEST)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=INTERNAL_SERVER_ERROR)


@require_http_methods(["GET"])
def post_detail(request, post_id):
    try:
        post = PostService.get_post(post_id)
        return JsonResponse(post, status=OK)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=NOT_FOUND)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def post_update(request, post_id):
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=BAD_REQUEST)

    try:
        post = PostService.update_post(post_id, **data)
        return JsonResponse(post, status=OK)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=NOT_FOUND)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=BAD_REQUEST)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["DELETE"])
def post_delete(request, post_id):
    try:
        PostService.delete_post(post_id)
        return HttpResponse(status=NO_CONTENT)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=NOT_FOUND)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=INTERNAL_SERVER_ERROR)


@require_http_methods(["GET"])
def post_aggregates(request, post_id):
    try:
        aggregates = PostService.get_post_aggregates(post_id)
        return JsonResponse(aggregates, status=OK)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=NOT_FOUND)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["POST"])
def like_create(request, post_id):
    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=BAD_REQUEST)

    user_id = data.get("user_id")
    if user_id is None:
        return JsonResponse({"error": "user_id is required"}, status=BAD_REQUEST)

    try:
        like, created = LikeService.add_like(user_id, post_id)
        status_code = CREATED if created else OK
        return JsonResponse(like, status=status_code)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=BAD_REQUEST)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=NOT_FOUND)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["DELETE"])
def like_delete(request, post_id, user_id):
    try:
        LikeService.remove_like(user_id, post_id)
        return HttpResponse(status=NO_CONTENT)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=BAD_REQUEST)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=NOT_FOUND)
    except LikeNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=NOT_FOUND)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=INTERNAL_SERVER_ERROR)


@require_http_methods(["GET"])
def like_status(request, post_id, user_id):
    try:
        status = LikeService.get_like_status(user_id, post_id)
        return JsonResponse(status, status=OK)
    except ValidationError as e:
        return JsonResponse({"error": str(e)}, status=BAD_REQUEST)
    except PostNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=NOT_FOUND)
    except Exception:
        return JsonResponse({"error": "Internal server error"}, status=INTERNAL_SERVER_ERROR)
