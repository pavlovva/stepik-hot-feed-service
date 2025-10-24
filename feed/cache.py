from django.core.cache import cache
import json

CACHE_KEY_TEMPLATE = "hotfeed:feed:hot:{limit}"
CACHE_TTL = 60


def get_cached_feed(limit):
    key = CACHE_KEY_TEMPLATE.format(limit=limit)
    data = cache.get(key)
    if data:
        return json.loads(data)
    return None


def set_cached_feed(limit, posts):
    key = CACHE_KEY_TEMPLATE.format(limit=limit)
    cache.set(key, json.dumps(posts), CACHE_TTL)


def invalidate_feed_cache():
    for limit in [10, 20, 50, 100]:
        key = CACHE_KEY_TEMPLATE.format(limit=limit)
        cache.delete(key)
