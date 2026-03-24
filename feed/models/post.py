from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4


class PostVisibility(models.TextChoices):
    PUBLIC = "public", _("Public")
    FOLLOWERS = "followers", _("Followers Only")
    PRIVATE = "private", _("Private")


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name=_("Author"),
    )
    content = models.TextField(_("Content"), blank=True, default="")
    image = models.ImageField(
        _("Image"), upload_to="feed/posts/", blank=True, null=True
    )
    visibility = models.CharField(
        _("Visibility"),
        max_length=20,
        choices=PostVisibility.choices,
        default=PostVisibility.PUBLIC,
        db_index=True,
    )
    # Denormalised counters — updated via signals for performance
    likes_count = models.PositiveIntegerField(_("Likes"), default=0, editable=False)
    comments_count = models.PositiveIntegerField(
        _("Comments"), default=0, editable=False
    )
    shares_count = models.PositiveIntegerField(_("Shares"), default=0, editable=False)

    # Sharing — when a user shares a post, a new Post row is created with this FK set
    shared_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shares",
        verbose_name=_("Shared From"),
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author} — {self.content[:60]}"
