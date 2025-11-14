from django.db import models


class Post(models.Model):
    like_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "feed_post"
        indexes = [
            models.Index(
                fields=["-like_count", "-created_at"], name="feed_post_hot_idx"
            ),
        ]
        ordering = ["-like_count", "-created_at"]

    def __str__(self):
        return f"Post {self.id} (likes: {self.like_count})"


class Like(models.Model):
    post = models.ForeignKey(Post, related_name="likes", on_delete=models.CASCADE)
    user_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "feed_like"
        unique_together = [["user_id", "post"]]
        indexes = [
            models.Index(fields=["created_at"], name="feed_like_created_idx"),
            models.Index(fields=["post", "created_at"], name="feed_like_post_time_idx"),
        ]

    def __str__(self):
        return f"Like by user {self.user_id} on post {self.post_id}"
