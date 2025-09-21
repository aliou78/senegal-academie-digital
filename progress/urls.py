# progress/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'enrollments', views.CourseEnrollmentViewSet, basename='enrollment')
router.register(r'progress', views.ProgressViewSet, basename='progress')
router.register(r'lessons', views.LessonProgressViewSet, basename='lesson-progress')
router.register(r'sessions', views.StudySessionViewSet, basename='study-session')
router.register(r'achievements', views.UserAchievementViewSet, basename='achievement')

app_name = 'progress'

urlpatterns = [
    path('api/', include(router.urls)),
]