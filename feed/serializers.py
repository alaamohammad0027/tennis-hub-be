from rest_framework import serializers

from feed.models import Post, Comment, Like, Follow


# ─── Author snapshot ──────────────────────────────────────────


class _AuthorSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    full_name = serializers.SerializerMethodField()
    user_type = serializers.CharField(read_only=True)
    photo = serializers.ImageField(read_only=True)

    def get_full_name(self, obj):
        return obj.get_full_name()


# ─── Comment ──────────────────────────────────────────────────


class CommentSerializer(serializers.ModelSerializer):
    author = _AuthorSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "post",
            "author",
            "content",
            "parent",
            "replies",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "replies", "created_at", "updated_at"]
        extra_kwargs = {
            "content": {
                "help_text": (
                    "Comment text in **Markdown** format. "
                    "Same Markdown rules as post content apply. "
                    "The frontend is responsible for rendering this to HTML."
                )
            },
            "parent": {
                "help_text": (
                    "UUID of the comment you are replying to. "
                    "Omit (or set to null) for a top-level comment. "
                    "Only one level of nesting is supported — replies cannot have replies."
                )
            },
        }

    def get_replies(self, obj):
        # Only return replies for top-level comments to avoid infinite nesting
        if obj.parent_id is None:
            return CommentSerializer(
                obj.replies.select_related("author").order_by("created_at"),
                many=True,
                context=self.context,
            ).data
        return []

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


# ─── Post ─────────────────────────────────────────────────────


class PostSerializer(serializers.ModelSerializer):
    author = _AuthorSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    shared_post = serializers.SerializerMethodField()
    content_format = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "content",
            "content_format",
            "image",
            "visibility",
            "likes_count",
            "comments_count",
            "shares_count",
            "is_liked",
            "shared_from",
            "shared_post",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "content_format",
            "likes_count",
            "comments_count",
            "shares_count",
            "is_liked",
            "shared_from",
            "shared_post",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "content": {
                "help_text": (
                    "Post body in **Markdown** format. "
                    "Use standard Markdown syntax: `**bold**`, `_italic_`, `[link](url)`, "
                    "`![image](url)`, `` `code` ``, `> blockquote`, `- list item`. "
                    "The frontend is responsible for rendering this to HTML."
                )
            },
            "shared_from": {
                "help_text": (
                    "Read-only. UUID of the original post this was shared from. "
                    "Set automatically when sharing via `POST /posts/{id}/share/`. "
                    "Null for regular (non-shared) posts."
                ),
            },
            "shared_post": {
                "help_text": (
                    "Read-only. Full data of the original post (same shape as this object). "
                    "Use this to render the embedded original post card. "
                    "Null for regular (non-shared) posts."
                ),
            },
        }

    def get_content_format(self, obj):
        return "markdown"

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_shared_post(self, obj):
        if obj.shared_from_id:
            return PostSerializer(obj.shared_from, context=self.context).data
        return None

    def validate(self, attrs):
        content = attrs.get("content", "").strip()
        image = attrs.get("image")
        # On create (no instance) both empty = error
        if not self.instance and not content and not image:
            raise serializers.ValidationError(
                "A post must have content, an image, or both."
            )
        return attrs

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


class PostShareSerializer(serializers.Serializer):
    """
    Request body for POST /apis/feed/posts/{id}/share/

    Shares an existing post into your own feed. A brand-new Post row is created
    with `shared_from` pointing to the original. The original post's `shares_count`
    is incremented atomically.

    Both fields are optional — you can share silently (no content) or add your
    own comment on top of the original.

    The response is the newly created post object (same shape as PostSerializer),
    with the original post nested inside `shared_post`.
    """

    content = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text=(
            "Optional comment you want to add on top of the shared post. "
            "Supports **Markdown** (same rules as a regular post). "
            "Leave blank to share without a comment."
        ),
    )
    visibility = serializers.ChoiceField(
        choices=Post.visibility.field.choices,
        default="public",
        help_text=(
            "`public` — visible to everyone. "
            "`followers` — visible only to your followers. "
            "`private` — visible only to you."
        ),
    )


# ─── Follow ───────────────────────────────────────────────────


class FollowSerializer(serializers.ModelSerializer):
    follower = _AuthorSerializer(read_only=True)
    following = _AuthorSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ["id", "follower", "following", "created_at"]
        read_only_fields = fields


class PublicProfileSerializer(serializers.Serializer):
    """
    Shareable public profile — returned by GET /feed/users/{id}/profile/

    Always returns the same top-level user fields.
    The `profile` field contains type-specific info (coach stats, club info, etc.)
    using the PUBLIC_FIELDS preset — no internal audit data (rejection reasons, etc.).
    `profile` is null only for admin users (they have no profile model).
    """

    id = serializers.UUIDField()
    full_name = serializers.SerializerMethodField()
    user_type = serializers.CharField()
    photo = serializers.ImageField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_following_count(self, obj):
        return obj.following.count()

    def get_posts_count(self, obj):
        return obj.posts.filter(visibility="public").count()

    def get_is_following(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following=obj).exists()
        return False

    def get_profile(self, obj):
        from accounts.models.choices import UserType
        from accounts.serializers.profiles import (
            FederationProfileSerializer,
            ClubProfileSerializer,
            CoachProfileSerializer,
            RefereeProfileSerializer,
            PlayerProfileSerializer,
            FanProfileSerializer,
        )

        _MAP = {
            UserType.FEDERATION: ("federation_profile", FederationProfileSerializer),
            UserType.CLUB: ("club_profile", ClubProfileSerializer),
            UserType.COACH: ("coach_profile", CoachProfileSerializer),
            UserType.REFEREE: ("referee_profile", RefereeProfileSerializer),
            UserType.PLAYER: ("player_profile", PlayerProfileSerializer),
            UserType.FAN: ("fan_profile", FanProfileSerializer),
        }

        entry = _MAP.get(obj.user_type)
        if not entry:
            return None
        attr, Serializer = entry
        profile = getattr(obj, attr, None)
        if not profile or not profile.is_active:
            return None
        # PUBLIC_FIELDS: safe subset, no `user` FK (already at top level), no audit trail
        return Serializer(
            profile,
            fields=Serializer.PUBLIC_FIELDS,
            context=self.context,
        ).data
