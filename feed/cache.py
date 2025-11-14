import json
import time

from django.core.cache import cache

CACHE_KEY_TEMPLATE = "hotfeed:feed:hot:{limit}"
LOCK_KEY_TEMPLATE = "hotfeed:lock:feed:hot:{limit}"
CACHE_TTL = 60
LOCK_TIMEOUT = 5
LOCK_WAIT_TIMEOUT = 10


def get_cached_feed(limit):
    key = CACHE_KEY_TEMPLATE.format(limit=limit)
    data = cache.get(key)
    if data:
        return json.loads(data)
    return None


def set_cached_feed(limit, posts):
    key = CACHE_KEY_TEMPLATE.format(limit=limit)
    cache.set(key, json.dumps(posts), CACHE_TTL)


def invalidate_feed_cache(limits=None):
    if limits is None:
        limits = [10, 20, 50, 100]

    for limit in limits:
        key = CACHE_KEY_TEMPLATE.format(limit=limit)
        cache.delete(key)


def acquire_lock(limit):
    key = LOCK_KEY_TEMPLATE.format(limit=limit)
    return cache.add(key, 1, LOCK_TIMEOUT)


def release_lock(limit):
    key = LOCK_KEY_TEMPLATE.format(limit=limit)
    cache.delete(key)


def wait_for_cache(limit, max_wait=LOCK_WAIT_TIMEOUT):
    start = time.time()
    while time.time() - start < max_wait:
        cached = get_cached_feed(limit)
        if cached is not None:
            return cached
        time.sleep(0.1)
    return None
