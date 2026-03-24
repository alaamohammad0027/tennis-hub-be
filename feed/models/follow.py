from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4


class Follow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    follower = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name=_("Follower"),
    )
    following = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name=_("Following"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Follow")
        verbose_name_plural = _("Follows")
        unique_together = [("follower", "following")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.follower} → {self.following}"
