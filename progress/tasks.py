# progress/tasks.py
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from .services import ProgressService
from .models import ProgressReport, LearningStreak

User = get_user_model()

@shared_task
def generate_weekly_reports():
    """Générer les rapports hebdomadaires pour tous les utilisateurs actifs"""
    active_users = User.objects.filter(
        courseenrollment__isnull=False,
        is_active=True
    ).distinct()
    
    for user in active_users:
        try:
            ProgressService.generate_progress_report(user, 'weekly')
        except Exception as e:
            print(f"Erreur génération rapport pour {user}: {e}")

@shared_task
def update_learning_streaks():
    """Mettre à jour les séries d'apprentissage quotidiennement"""
    active_streaks = LearningStreak.objects.filter(is_active=True)
    
    for streak in active_streaks:
        ProgressService.update_learning_streak(streak.user)

@shared_task
def cleanup_old_study_sessions():
    """Nettoyer les anciennes sessions d'étude non terminées"""
    from .models import StudySession
    
    # Sessions de plus de 24h non terminées
    cutoff_time = timezone.now() - timedelta(hours=24)
    old_sessions = StudySession.objects.filter(
        ended_at__isnull=True,
        started_at__lt=cutoff_time
    )
    
    for session in old_sessions:
        # Terminer automatiquement la session
        session.ended_at = session.started_at + timedelta(hours=2)  # Durée estimée
        session.duration_minutes = 120
        session.save()