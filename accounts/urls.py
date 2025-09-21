from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profils
    path('profile/', views.profile, name='profile'),
    path('profile/extended/', views.extended_profile, name='extended_profile'),
    path('profile/instructor/', views.instructor_profile, name='instructor_profile'),
    path('profile/enterprise/', views.enterprise_profile, name='enterprise_profile'),
    
    # Gestion du compte
    path('change-password/', views.change_password, name='change_password'),
    
    # Utilisateurs (admin)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/verify/', views.verify_user, name='verify_user'),
]
