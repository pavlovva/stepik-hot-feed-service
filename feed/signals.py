from django.db.models import F
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache import invalidate_feed_cache
from .models import Like


@receiver(post_save, sender=Like)
def on_like_created(sender, instance, created, **kwargs):
    if created:
        instance.post.like_count = F("like_count") + 1
        instance.post.save(update_fields=["like_count"])
        invalidate_feed_cache()


@receiver(post_delete, sender=Like)
def on_like_deleted(sender, instance, **kwargs):
    instance.post.like_count = F("like_count") - 1
    instance.post.save(update_fields=["like_count"])
    invalidate_feed_cache()
