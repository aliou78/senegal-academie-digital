from rest_framework import serializers
from .models import Forum, Topic, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "topic", "author", "author_username", "content", "edited", "created_at", "updated_at"]
        read_only_fields = ["id", "author", "author_username", "edited", "created_at", "updated_at"]

class TopicListSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    messages_count = serializers.IntegerField(source="messages.count", read_only=True)

    class Meta:
        model = Topic
        fields = ["id", "forum", "title", "slug", "author", "author_username", "pinned", "closed", "created_at", "messages_count"]
        read_only_fields = ["id", "author", "author_username", "created_at", "messages_count"]

class TopicDetailSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = ["id", "forum", "title", "slug", "body", "author", "author_username", "pinned", "closed", "created_at", "updated_at", "messages"]
        read_only_fields = ["id", "author", "author_username", "created_at", "updated_at", "messages"]

class ForumSerializer(serializers.ModelSerializer):
    topics_count = serializers.IntegerField(source="topics.count", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Forum
        fields = ["id", "title", "slug", "description", "created_by", "created_by_username", "created_at", "updated_at", "topics_count"]
        read_only_fields = ["id", "created_by", "created_by_username", "created_at", "updated_at", "topics_count"]
