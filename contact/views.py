from django.shortcuts import render

# Create your views here.
# contact/views.py
from rest_framework import viewsets, permissions, throttling, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import ContactMessage
from .serializers import ContactMessageSerializer



# simple throttles to avoid spam: 5 submissions per minute per IP
class ContactBurstThrottle(throttling.AnonRateThrottle):
    scope = "contact_burst"

class ContactSustainedThrottle(throttling.AnonRateThrottle):
    scope = "contact_sustained"

# permission: anyone can create; only staff can list/read/delete
class IsAdminOrCreateOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ("POST",):
            return True
        # for list/detail/delete/patch, require staff
        return request.user and request.user.is_authenticated and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # staff can do anything; others cannot access object endpoints
        return request.user and request.user.is_authenticated and request.user.is_staff

class ContactMessageViewSet(viewsets.ModelViewSet):
    """
    create: public: add a contact message
    list/retrieve/update/destroy: admin/staff only
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAdminOrCreateOnly]
    throttle_classes = [ContactBurstThrottle, ContactSustainedThrottle]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["email", "is_read", "created_at"]
    search_fields = ["full_name", "email", "message"]
    ordering_fields = ["created_at", "full_name"]
    ordering = ["-created_at"]

    def get_permissions(self):
        # allow anonymous create but require staff for others (already in IsAdminOrCreateOnly)
        return [permission() for permission in self.permission_classes]

    def create(self, request, *args, **kwargs):
        """
        Override to send notification email after create.
        """
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        # trigger signal to send email (signals.py handles it), but can also send here synchronously or spawn thread
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def mark_read(self, request, pk=None):
        msg = self.get_object()
        msg.is_read = True
        msg.save()
        return Response({"detail": "Marked as read."}, status=status.HTTP_200_OK)
