from django.contrib import admin

# Register your models here.
# contact/admin.py
from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "address", "is_read", "created_at")
    search_fields = ("full_name", "email", "message", "ip_address")
    list_filter = ("is_read", "created_at")
    readonly_fields = ("created_at", "user_agent", "ip_address", "password_hash")
    actions = ["mark_as_read"]

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Marquer sélection comme lue"
