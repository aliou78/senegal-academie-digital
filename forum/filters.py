import django_filters
from .models import Topic, Message

class TopicFilter(django_filters.FilterSet):
    forum = django_filters.NumberFilter(field_name="forum__id")
    author = django_filters.CharFilter(field_name="author__username", lookup_expr="icontains")
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    pinned = django_filters.BooleanFilter(field_name="pinned")

    class Meta:
        model = Topic
        fields = ["forum", "author", "title", "pinned"]

class MessageFilter(django_filters.FilterSet):
    topic = django_filters.NumberFilter(field_name="topic__id")
    author = django_filters.CharFilter(field_name="author__username", lookup_expr="icontains")

    class Meta:
        model = Message
        fields = ["topic", "author"]
