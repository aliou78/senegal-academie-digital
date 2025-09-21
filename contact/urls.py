# contact/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Pour créer un message de contact (POST)
    path("", views.ContactMessageViewSet.as_view({'post': 'create'}), name="contact-create"),
    
    # Pour lister les messages (GET) - admin seulement
    path("list/", views.ContactMessageViewSet.as_view({'get': 'list'}), name="contact-list"),
    
    # Pour voir un message spécifique (GET) - admin seulement
    path("<int:pk>/", views.ContactMessageViewSet.as_view({'get': 'retrieve'}), name="contact-detail"),
    
    # Pour marquer comme lu (POST) - admin seulement
    path("<int:pk>/mark_read/", views.ContactMessageViewSet.as_view({'post': 'mark_read'}), name="contact-mark-read"),
]