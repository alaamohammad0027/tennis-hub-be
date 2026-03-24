from django.urls import path, include
from rest_framework.routers import DefaultRouter

from feed.views import (
    PostViewSet,
    CommentViewSet,
    FeedView,
    UserPostsView,
    UserProfileView,
    FollowView,
    UnfollowView,
)

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"comments", CommentViewSet, basename="comment")

urlpatterns = [
    path("", include(router.urls)),
    # Personalised timeline (auth required)
    path("feed/", FeedView.as_view(), name="feed"),
    # Public user-scoped routes (no auth required)
    path("users/<uuid:user_id>/posts/", UserPostsView.as_view(), name="user-posts"),
    path(
        "users/<uuid:user_id>/profile/",
        UserProfileView.as_view(),
        name="user-public-profile",
    ),
    path("users/<uuid:user_id>/follow/", FollowView.as_view(), name="follow"),
    path("users/<uuid:user_id>/unfollow/", UnfollowView.as_view(), name="unfollow"),
]
