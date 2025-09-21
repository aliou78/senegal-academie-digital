from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Forum, Topic, Message

@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "created_by", "created_at")
    search_fields = ("title", "description", "created_by__username")

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "forum", "author", "pinned", "closed", "created_at")
    list_filter = ("pinned", "closed", "forum")
    search_fields = ("title", "body", "author__username")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "topic", "author", "created_at")
    search_fields = ("content", "author__username")
