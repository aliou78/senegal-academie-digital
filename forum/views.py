# forum/views.py
from rest_framework import viewsets, filters, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
import django_filters.rest_framework

from .models import Forum, Topic, Message
from .serializers import ForumSerializer, TopicListSerializer, TopicDetailSerializer, MessageSerializer
from .permissions import IsAuthorOrReadOnly
from .filters import TopicFilter, MessageFilter
from rest_framework.pagination import PageNumberPagination


# Pagination standard pour tous les ViewSets
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100


# ViewSet pour les Forums
class ForumViewSet(viewsets.ModelViewSet):
    queryset = Forum.objects.all()
    serializer_class = ForumSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ViewSet pour les Topics
class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.select_related("forum", "author").prefetch_related("messages")
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    pagination_class = StandardResultsSetPagination

    # Filtres et recherche
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend
    ]
    filterset_class = TopicFilter
    search_fields = ["title", "body", "author__username", "forum__title"]
    ordering_fields = ["created_at", "pinned"]

    def get_serializer_class(self):
        # Liste vs détail
        if self.action == "list":
            return TopicListSerializer
        return TopicDetailSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # Action personnalisée pour verrouiller un topic
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def lock(self, request, pk=None):
        topic = self.get_object()
        if not request.user.is_staff:
            return Response({"detail": "Permission refusée."}, status=status.HTTP_403_FORBIDDEN)
        topic.closed = True
        topic.save()
        return Response({"detail": "Sujet fermé."})


# ViewSet pour les Messages
class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.select_related("topic", "author")
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    pagination_class = StandardResultsSetPagination

    # Filtres et recherche
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend
    ]
    filterset_class = MessageFilter
    search_fields = ["content", "author__username"]
    ordering_fields = ["created_at"]

    def perform_create(self, serializer):
        topic_id = self.request.data.get("topic")
        if not topic_id:
            raise serializers.ValidationError({"topic": "Le champ topic est requis."})
        topic = get_object_or_404(Topic, pk=topic_id)
        if topic.closed:
            raise serializers.ValidationError({"detail": "Ce sujet est fermé."})
        serializer.save(author=self.request.user, topic=topic)

    def perform_update(self, serializer):
        serializer.save(edited=True)
