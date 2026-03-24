import django_filters as filters

from feed.models import Post, PostVisibility, Comment


class PostFilter(filters.FilterSet):
    visibility = filters.ChoiceFilter(choices=PostVisibility.choices)
    author = filters.UUIDFilter(field_name="author__id")
    date_from = filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    date_to = filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Post
        fields = ["visibility", "author", "date_from", "date_to"]


class CommentFilter(filters.FilterSet):
    post = filters.UUIDFilter(field_name="post__id")
    author = filters.UUIDFilter(field_name="author__id")
    # top_level=true returns only root comments (parent=null)
    top_level = filters.BooleanFilter(field_name="parent", lookup_expr="isnull")

    class Meta:
        model = Comment
        fields = ["post", "author", "top_level"]
