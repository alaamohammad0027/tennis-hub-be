from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    post = models.ForeignKey(
        "feed.Post",
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Post"),
    )
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Author"),
    )
    content = models.TextField(_("Content"))
    # Nested replies — null means top-level comment
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name=_("Parent Comment"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author} on post {self.post_id}: {self.content[:40]}"
