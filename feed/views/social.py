from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from feed.filters import PostFilter
from feed.models import Post, Follow
from feed.serializers import PostSerializer, FollowSerializer, PublicProfileSerializer

_TAG_FEED = "Feed - Timeline"
_TAG_SOCIAL = "Feed - Social"


# ─── Personalised feed ────────────────────────────────────────


@extend_schema(
    tags=[_TAG_FEED],
    summary="My feed",
    description=(
        "Returns posts from users you follow + your own posts, ordered by newest. "
        "Authentication required. Supports the same filters as the public posts list."
    ),
)
class FeedView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer

    def get(self, request):
        from django.db.models import Q

        following_ids = Follow.objects.filter(follower=request.user).values_list(
            "following_id", flat=True
        )
        qs = (
            Post.objects.filter(Q(author_id__in=following_ids) | Q(author=request.user))
            .exclude(visibility="private")
            .select_related("author", "shared_from__author")
            .prefetch_related("likes")
            .order_by("-created_at")
        )
        qs = PostFilter(request.GET, queryset=qs).qs
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                PostSerializer(page, many=True, context={"request": request}).data
            )
        return Response(
            PostSerializer(qs, many=True, context={"request": request}).data
        )


# ─── User public posts ────────────────────────────────────────


@extend_schema(
    tags=[_TAG_SOCIAL],
    summary="Get posts by a user",
    description=(
        "Returns public posts for a specific user. "
        "If authenticated and following them, followers-only posts are included too. "
        "No authentication required for public posts."
    ),
)
class UserPostsView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PostSerializer

    def get(self, request, user_id):
        from django.db.models import Q

        target = get_object_or_404(User, pk=user_id)
        qs = (
            Post.objects.filter(author=target)
            .select_related("author", "shared_from__author")
            .prefetch_related("likes")
        )

        if (
            request.user.is_authenticated
            and Follow.objects.filter(follower=request.user, following=target).exists()
        ):
            qs = qs.filter(Q(visibility="public") | Q(visibility="followers"))
        else:
            qs = qs.filter(visibility="public")

        qs = PostFilter(request.GET, queryset=qs).qs
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                PostSerializer(page, many=True, context={"request": request}).data
            )
        return Response(
            PostSerializer(qs, many=True, context={"request": request}).data
        )


# ─── Public shareable profile ─────────────────────────────────


_PROFILE_BASE_FIELDS = {
    "id": "3f2e1a...",
    "full_name": "Ali Hassan",
    "user_type": "«varies»",
    "photo": "https://example.com/media/photo.jpg",
    "followers_count": 42,
    "following_count": 15,
    "posts_count": 8,
    "is_following": False,
}


@extend_schema(
    tags=[_TAG_SOCIAL],
    summary="Public profile",
    description=(
        "Shareable public profile for any user. No authentication required.\n\n"
        "**Response shape**\n\n"
        "Always returns the same top-level fields regardless of user type.\n"
        "The `profile` field contains type-specific info.\n"
        "`is_following` is always `false` for unauthenticated callers.\n"
        "`profile` is `null` for admin accounts (they have no profile model).\n\n"
        "**`profile` field per user type**\n\n"
        "| Type | Key profile fields |\n"
        "|---|---|\n"
        "| `coach` | `specialization`, `coaching_level`, `bio`, `years_experience`, `verification_status` |\n"
        "| `player` | `skill_level`, `ranking`, `dominant_hand`, `nationality`, `bio`, `verification_status` |\n"
        "| `referee` | `referee_level`, `bio`, `years_experience`, `itf_badge`, `verification_status` |\n"
        "| `club` | `club_name`, `club_type`, `country`, `city`, `logo`, `website`, `verification_status` |\n"
        "| `federation` | `federation_name`, `sport`, `country`, `logo`, `website`, `verification_status` |\n"
        "| `fan` | `nationality`, `bio`, `favorite_club_name`, `verification_status` |\n"
        "| `admin` | `null` |\n"
    ),
    responses=PublicProfileSerializer,
    examples=[
        OpenApiExample(
            "Coach profile",
            response_only=True,
            value={
                **_PROFILE_BASE_FIELDS,
                "user_type": "coach",
                "profile": {
                    "id": "prof-uuid",
                    "specialization": "Tennis Biomechanics",
                    "coaching_level": "elite",
                    "bio": "10+ years coaching competitive players.",
                    "years_experience": 11,
                    "verification_status": "approved",
                    "verified_at": "2024-06-01T10:00:00Z",
                },
            },
        ),
        OpenApiExample(
            "Player profile",
            response_only=True,
            value={
                **_PROFILE_BASE_FIELDS,
                "user_type": "player",
                "profile": {
                    "id": "prof-uuid",
                    "skill_level": "advanced",
                    "ranking": 14,
                    "dominant_hand": "right",
                    "nationality": "SA",
                    "bio": "Competitive player since 2018.",
                    "verification_status": "approved",
                    "verified_at": "2024-05-10T08:30:00Z",
                },
            },
        ),
        OpenApiExample(
            "Club profile",
            response_only=True,
            value={
                **_PROFILE_BASE_FIELDS,
                "user_type": "club",
                "profile": {
                    "id": "prof-uuid",
                    "club_name": "Elite Tennis Academy",
                    "club_type": "academy",
                    "country": "SA",
                    "city": "Riyadh",
                    "logo": "https://example.com/media/logo.png",
                    "website": "https://elitetennis.sa",
                    "description": "Premier tennis academy in Riyadh.",
                    "facility_count": 8,
                    "verification_status": "approved",
                    "verified_at": "2024-03-20T09:00:00Z",
                },
            },
        ),
        OpenApiExample(
            "Fan profile",
            response_only=True,
            value={
                **_PROFILE_BASE_FIELDS,
                "user_type": "fan",
                "profile": {
                    "id": "prof-uuid",
                    "nationality": "SA",
                    "bio": "Tennis enthusiast and weekend player.",
                    "favorite_club_name": "Elite Tennis Academy",
                    "verification_status": "approved",
                },
            },
        ),
        OpenApiExample(
            "Admin (no profile)",
            response_only=True,
            value={
                **_PROFILE_BASE_FIELDS,
                "user_type": "admin",
                "profile": None,
            },
        ),
    ],
)
class UserProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id, is_active=True)
        return Response(
            PublicProfileSerializer(user, context={"request": request}).data
        )


# ─── Follow / Unfollow ────────────────────────────────────────


@extend_schema(
    tags=[_TAG_SOCIAL],
    summary="Follow a user",
    description="Start following a user. Returns 400 if already following or trying to follow yourself.",
)
class FollowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        target = get_object_or_404(User, pk=user_id, is_active=True)

        if target == request.user:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        follow, created = Follow.objects.get_or_create(
            follower=request.user, following=target
        )
        if not created:
            return Response(
                {"detail": "You are already following this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            FollowSerializer(follow).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=[_TAG_SOCIAL],
    summary="Unfollow a user",
    description="Stop following a user. Returns 404 if not currently following.",
)
class UnfollowView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        target = get_object_or_404(User, pk=user_id)
        deleted, _ = Follow.objects.filter(
            follower=request.user, following=target
        ).delete()
        if not deleted:
            return Response(
                {"detail": "You are not following this user."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
