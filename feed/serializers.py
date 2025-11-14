def serialize_post(post):
    return {
        "id": post.id,
        "like_count": post.like_count,
        "created_at": post.created_at.isoformat(),
    }


def serialize_like(like):
    return {
        "id": like.id,
        "post_id": int(like.post_id),
        "user_id": int(like.user_id),
        "created_at": like.created_at.isoformat(),
    }


def serialize_post_aggregates(post, score_24h):
    return {
        "post_id": post.id,
        "total_likes": post.like_count,
        "score_24h": score_24h,
        "created_at": post.created_at.isoformat(),
    }


def serialize_post_list(posts):
    return [serialize_post(post) for post in posts]


def serialize_like_status(liked, like=None):
    result = {"liked": liked}
    if like:
        result["like"] = serialize_like(like)
    return result
