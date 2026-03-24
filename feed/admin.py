from django.contrib import admin
from django.utils.html import format_html

from feed.models import Post, Comment, Like, Follow


# ─── Inlines ──────────────────────────────────────────────────


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("author", "content", "parent", "created_at")
    readonly_fields = ("created_at",)
    raw_id_fields = ("author", "parent")
    show_change_link = True


# ─── Post ─────────────────────────────────────────────────────


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "author",
        "visibility_badge",
        "short_content",
        "likes_count",
        "comments_count",
        "shares_count",
        "is_share",
        "created_at",
    )
    list_filter = ("visibility", "created_at")
    search_fields = (
        "author__email",
        "author__first_name",
        "author__last_name",
        "content",
    )
    raw_id_fields = ("author", "shared_from")
    readonly_fields = (
        "likes_count",
        "comments_count",
        "shares_count",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"
    list_per_page = 50
    list_select_related = True
    inlines = [CommentInline]
    fieldsets = (
        (
            None,
            {"fields": ("author", "visibility", "content", "image")},
        ),
        (
            "Share",
            {"fields": ("shared_from",)},
        ),
        (
            "Counters (read-only)",
            {
                "classes": ("collapse",),
                "fields": ("likes_count", "comments_count", "shares_count"),
            },
        ),
        (
            "Timestamps",
            {"classes": ("collapse",), "fields": ("created_at", "updated_at")},
        ),
    )

    @admin.display(description="Visibility")
    def visibility_badge(self, obj):
        colours = {
            "public": "#155724",
            "followers": "#856404",
            "private": "#721c24",
        }
        colour = colours.get(obj.visibility, "#6c757d")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 6px;'
            'border-radius:3px;font-size:11px">{}</span>',
            colour,
            obj.visibility.capitalize(),
        )

    @admin.display(description="Content")
    def short_content(self, obj):
        text = obj.content or ""
        return (text[:60] + "…") if len(text) > 60 else text or "—"

    @admin.display(description="Share", boolean=True)
    def is_share(self, obj):
        return obj.shared_from_id is not None


# ─── Comment ──────────────────────────────────────────────────


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "is_reply", "short_content", "created_at")
    list_filter = ("created_at",)
    search_fields = ("author__email", "author__first_name", "content")
    raw_id_fields = ("author", "post", "parent")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 50
    list_select_related = True

    @admin.display(description="Reply", boolean=True)
    def is_reply(self, obj):
        return obj.parent_id is not None

    @admin.display(description="Content")
    def short_content(self, obj):
        return (obj.content[:60] + "…") if len(obj.content) > 60 else obj.content


# ─── Like ─────────────────────────────────────────────────────


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")
    search_fields = ("user__email", "user__first_name")
    raw_id_fields = ("user", "post")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50
    list_select_related = True


# ─── Follow ───────────────────────────────────────────────────


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "created_at")
    search_fields = (
        "follower__email",
        "follower__first_name",
        "following__email",
        "following__first_name",
    )
    raw_id_fields = ("follower", "following")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50
    list_select_related = True
