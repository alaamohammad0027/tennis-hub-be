from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from feed.filters import CommentFilter
from feed.models import Comment
from feed.serializers import CommentSerializer

_TAG = "Feed - Comments"


@extend_schema_view(
    list=extend_schema(
        tags=[_TAG],
        summary="List comments",
        description="Filter by `?post=<uuid>` and/or `?top_level=true` for root-only.",
    ),
    retrieve=extend_schema(tags=[_TAG], summary="Get a comment with its replies"),
    create=extend_schema(
        tags=[_TAG],
        summary="Create a comment",
        description="Supply `post` (required) and optionally `parent` to reply to another comment.",
    ),
    update=extend_schema(tags=[_TAG], summary="Update a comment (owner only)"),
    partial_update=extend_schema(
        tags=[_TAG], summary="Partially update a comment (owner only)"
    ),
    destroy=extend_schema(tags=[_TAG], summary="Delete a comment (owner or admin)"),
)
class CommentViewSet(viewsets.ModelViewSet):
    queryset = (
        Comment.objects.select_related("author", "post")
        .prefetch_related("replies__author")
        .order_by("created_at")
    )
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CommentFilter

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            from accounts.models.choices import UserType

            if obj.author != request.user and request.user.user_type != UserType.ADMIN:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("You can only modify your own comments.")
