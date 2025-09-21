from django.urls import path
from . import views

urlpatterns = [
    # Badges
    path('badges/', views.BadgeListView.as_view(), name='badge_list'),
    path('badges/user/', views.UserBadgeListView.as_view(), name='user_badge_list'),
    path('badges/award/', views.award_badge, name='award_badge'),
    
    # Certificats
    path('certificates/', views.CertificateListView.as_view(), name='certificate_list'),
    path('certificates/user/', views.UserCertificateListView.as_view(), name='user_certificate_list'),
    path('certificates/user/<uuid:certificate_id>/', views.UserCertificateDetailView.as_view(), name='user_certificate_detail'),
    path('certificates/verify/', views.verify_certificate, name='verify_certificate'),
    path('certificates/generate/<int:course_id>/', views.generate_certificate, name='generate_certificate'),
    
    # Parcours d'apprentissage
    path('learning-paths/', views.LearningPathListView.as_view(), name='learning_path_list'),
    path('learning-paths/<slug:slug>/', views.LearningPathDetailView.as_view(), name='learning_path_detail'),
    path('learning-paths/user/', views.UserLearningPathListView.as_view(), name='user_learning_path_list'),
    path('learning-paths/enroll/', views.LearningPathEnrollmentView.as_view(), name='learning_path_enrollment'),
    
    # Réalisations
    path('achievements/', views.AchievementListView.as_view(), name='achievement_list'),
    
    # Sessions d'étude
    path('study-sessions/', views.StudySessionListView.as_view(), name='study_session_list'),
    path('study-sessions/<int:session_id>/end/', views.end_study_session, name='end_study_session'),
    
    # Statistiques
    path('statistics/', views.UserStatisticsView.as_view(), name='user_statistics'),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
    
    # Progression
    path('update-progress/', views.update_progress, name='update_progress'),
]
