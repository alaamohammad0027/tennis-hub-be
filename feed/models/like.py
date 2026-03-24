from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4


class Like(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    post = models.ForeignKey(
        "feed.Post",
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name=_("Post"),
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name=_("User"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Like")
        verbose_name_plural = _("Likes")
        unique_together = [("post", "user")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} liked post {self.post_id}"
