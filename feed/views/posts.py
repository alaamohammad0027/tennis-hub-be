from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny,
)
from rest_framework.response import Response

from feed.filters import PostFilter, CommentFilter
from feed.models import Post, Like, Comment
from feed.serializers import PostSerializer, CommentSerializer, PostShareSerializer

_TAG = "Feed - Posts"


_MARKDOWN_HINT = (
    "\n\n**Rich text (Markdown)**\n\n"
    "The `content` field uses **Markdown** format. "
    "The API stores and returns raw Markdown — the frontend must render it to HTML.\n\n"
    "| Syntax | Result |\n"
    "|---|---|\n"
    "| `**bold**` | **bold** |\n"
    "| `_italic_` | _italic_ |\n"
    "| `[TennisHub](https://...)` | clickable link |\n"
    "| `> quote` | blockquote |\n"
    "| `- item` | bullet list |\n"
    "| `` `code` `` | inline code |\n\n"
    'The response always includes `"content_format": "markdown"` so the frontend '
    "knows which renderer to use."
)

_VISIBILITY_HINT = (
    "\n\n**Visibility**\n\n"
    "| Value | Who can see it |\n"
    "|---|---|\n"
    "| `public` | Everyone (default) |\n"
    "| `followers` | Only users who follow you |\n"
    "| `private` | Only you |\n"
)


@extend_schema_view(
    list=extend_schema(
        tags=[_TAG],
        summary="List posts",
        description=(
            "Returns posts visible to the caller:\n\n"
            "- **Unauthenticated** → public posts only\n"
            "- **Authenticated** → public posts + followers-only posts from people you follow + your own private posts\n\n"
            "Supports filtering via `PostFilter` (see query params)." + _VISIBILITY_HINT
        ),
    ),
    retrieve=extend_schema(
        tags=[_TAG],
        summary="Get a post",
        description=(
            "Returns a single post.\n\n"
            "- Unauthenticated users can only retrieve `public` posts.\n"
            "- Authenticated users follow the same visibility rules as the list endpoint.\n\n"
            "If the post is a share, the original post is nested inside `shared_post`."
        ),
    ),
    create=extend_schema(
        tags=[_TAG],
        summary="Create a post",
        description=(
            "Publish a new post. Authentication required.\n\n"
            "**At least one of `content` or `image` is required.**\n\n"
            "To upload an image, use `multipart/form-data` (not JSON)."
            + _MARKDOWN_HINT
            + _VISIBILITY_HINT
        ),
        request={
            "multipart/form-data": PostSerializer,
            "application/json": PostSerializer,
        },
        examples=[
            OpenApiExample(
                "Plain text post",
                value={
                    "content": "Just had a great training session!",
                    "visibility": "public",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Rich text post",
                value={
                    "content": "**Match report** vs Ali Hassan\n\n_Won 6-4, 7-5_ — great backhand today!\n\n- First set: dominated the baseline\n- Second set: saved 3 break points",
                    "visibility": "followers",
                },
                request_only=True,
            ),
        ],
    ),
    update=extend_schema(
        tags=[_TAG],
        summary="Update a post (owner only)",
        description=(
            "Full replacement of a post's `content`, `image`, and `visibility`. Owner only.\n\n"
            "To upload a new image use `multipart/form-data`." + _MARKDOWN_HINT
        ),
        request={
            "multipart/form-data": PostSerializer,
            "application/json": PostSerializer,
        },
    ),
    partial_update=extend_schema(
        tags=[_TAG],
        summary="Partially update a post (owner only)",
        description=(
            "Update one or more fields of your post. Owner only.\n\n"
            "To replace the image use `multipart/form-data`." + _MARKDOWN_HINT
        ),
        request={
            "multipart/form-data": PostSerializer,
            "application/json": PostSerializer,
        },
    ),
    destroy=extend_schema(
        tags=[_TAG],
        summary="Delete a post (owner or admin)",
        description="Permanently deletes the post. Owner or admin only.",
    ),
    like=extend_schema(
        tags=[_TAG],
        summary="Like / Unlike a post",
        description=(
            "Toggles your like on a post.\n\n"
            "- First call → **like** (`liked: true`)\n"
            "- Second call → **unlike** (`liked: false`)\n\n"
            "Returns the updated `likes_count`."
        ),
    ),
    share=extend_schema(
        tags=[_TAG],
        summary="Share a post",
        description=(
            "Re-shares an existing post into your own feed.\n\n"
            "**What happens:**\n"
            "1. A new Post is created in your feed with `shared_from` pointing to the original.\n"
            "2. The original post's `shares_count` is incremented by 1 (atomic).\n"
            "3. The response is the **new post** (your share), with the original post nested inside `shared_post`.\n\n"
            "Both `content` and `visibility` are optional:\n"
            "- Omit `content` to share silently (empty string stored).\n"
            "- Omit `visibility` to default to `public`.\n" + _MARKDOWN_HINT
        ),
        request=PostShareSerializer,
        examples=[
            OpenApiExample(
                "Share with comment",
                value={
                    "content": "Great point by **Coach Ali** here!",
                    "visibility": "public",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Silent share (no comment)",
                value={},
                request_only=True,
            ),
        ],
    ),
    comments=extend_schema(
        tags=[_TAG],
        summary="List / create comments on a post",
        description=(
            "**GET** — returns top-level comments with their replies nested under `replies`.\n\n"
            "**POST** — add a new comment (authentication required).\n\n"
            "To reply to an existing comment, supply `parent` with the comment's UUID. "
            "Replies are nested one level only (replies-to-replies are not supported).\n\n"
            "Comments support the same Markdown syntax as posts." + _MARKDOWN_HINT
        ),
        request=CommentSerializer,
        examples=[
            OpenApiExample(
                "Top-level comment",
                value={"content": "Great match! **Well played.**"},
                request_only=True,
            ),
            OpenApiExample(
                "Reply to a comment",
                value={
                    "content": "Thanks! _Really tough second set._",
                    "parent": "uuid-of-parent-comment",
                },
                request_only=True,
            ),
        ],
    ),
)
class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PostFilter

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Post.objects.select_related(
            "author", "shared_from__author"
        ).prefetch_related("likes")
        user = self.request.user
        if user.is_authenticated:
            # Show public + followers-only posts from users they follow + own private posts
            from feed.models import Follow

            following_ids = Follow.objects.filter(follower=user).values_list(
                "following_id", flat=True
            )
            from django.db.models import Q

            qs = qs.filter(
                Q(visibility="public")
                | Q(visibility="followers", author_id__in=following_ids)
                | Q(author=user)
            )
        else:
            qs = qs.filter(visibility="public")
        return qs.order_by("-created_at")

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            from accounts.models.choices import UserType

            if obj.author != request.user and request.user.user_type != UserType.ADMIN:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("You can only modify your own posts.")

    # ── Like / Unlike ────────────────────────────────────────

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = Like.objects.get_or_create(post=post, user=request.user)
        if created:
            Post.objects.filter(pk=post.pk).update(likes_count=post.likes_count + 1)
            return Response({"liked": True, "likes_count": post.likes_count + 1})
        # Already liked — unlike
        like.delete()
        Post.objects.filter(pk=post.pk).update(likes_count=max(0, post.likes_count - 1))
        return Response({"liked": False, "likes_count": max(0, post.likes_count - 1)})

    # ── Share ────────────────────────────────────────────────

    @action(detail=True, methods=["post"])
    def share(self, request, pk=None):
        original = self.get_object()
        serializer = PostShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            shared_post = Post.objects.create(
                author=request.user,
                content=data.get("content", ""),
                visibility=data.get("visibility", "public"),
                shared_from=original,
            )
            Post.objects.filter(pk=original.pk).update(
                shares_count=original.shares_count + 1
            )

        return Response(
            PostSerializer(shared_post, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    # ── Comments ─────────────────────────────────────────────

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        post = self.get_object()

        if request.method == "GET":
            qs = (
                post.comments.filter(parent=None)
                .select_related("author")
                .prefetch_related("replies__author")
            )
            qs = CommentFilter(request.GET, queryset=qs).qs
            page = self.paginate_queryset(qs)
            if page is not None:
                return self.get_paginated_response(
                    CommentSerializer(
                        page, many=True, context={"request": request}
                    ).data
                )
            return Response(
                CommentSerializer(qs, many=True, context={"request": request}).data
            )

        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required to comment."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = CommentSerializer(
            data={**request.data, "post": post.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        Post.objects.filter(pk=post.pk).update(comments_count=post.comments_count + 1)
        return Response(
            CommentSerializer(comment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
