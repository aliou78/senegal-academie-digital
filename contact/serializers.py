# contact/serializers.py
from rest_framework import serializers
from .models import ContactMessage
from django.core.validators import validate_email

class ContactMessageSerializer(serializers.ModelSerializer):
    # accept a raw password field on input but do not expose it on output
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, min_length=6)
    honeypot = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = ContactMessage
        fields = [
            "id", "full_name", "address", "email", "password", "message",
            "user_agent", "ip_address", "honeypot", "created_at", "is_read"
        ]
        read_only_fields = ["id", "created_at", "is_read", "user_agent", "ip_address"]

    def validate_email(self, value):
        # ensure valid email
        validate_email(value)
        return value

    def validate_honeypot(self, value):
        # honeypot must be empty
        if value:
            raise serializers.ValidationError("Spam detected.")
        return value

    def validate_message(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Le message est trop court.")
        return value

    def create(self, validated_data):
        raw_password = validated_data.pop("password", None)
        # pop honeypot (already validated)
        validated_data.pop("honeypot", None)
        # capture user agent and ip if present in context
        request = self.context.get("request")
        if request:
            validated_data["user_agent"] = request.META.get("HTTP_USER_AGENT", "")[:512]
            # ip detection (X-Forwarded-For fallback)
            xff = request.META.get("HTTP_X_FORWARDED_FOR")
            if xff:
                ip = xff.split(",")[0].strip()
            else:
                ip = request.META.get("REMOTE_ADDR")
            validated_data["ip_address"] = ip
        cm = ContactMessage(**validated_data)
        if raw_password:
            cm.set_password(raw_password)
        cm.save()
        return cm
