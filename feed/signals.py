from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from .models import Like
from .cache import invalidate_feed_cache


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

