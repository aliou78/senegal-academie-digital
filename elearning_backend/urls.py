"""
URL configuration for elearning_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# Vue pour la racine
def api_root(request):
    return JsonResponse({
        "message": "Bienvenue sur l’API Sénégal Académie Digital 🎓",
        "endpoints": {
            "users": "/api/users/",
            "courses": "/api/courses/",
            "progress": "/api/progress/",
            "payments": "/api/payments/",
            "forum": "/api/forum/",
            "contact": "/api/contact/"
        }
    })

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/courses", include("courses_app.urls")),  # si already present
    path("api/urls", include("users.urls")),        # users endpoints
    path('api/payments', include('payments.urls')),
    path("api/forum/", include("forum.urls")),
    path("api/contact/", include("contact.urls")),
    path('api/accounts/', include('accounts.urls')),
    path('api/progress/', include('progress.urls')),
    



]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
